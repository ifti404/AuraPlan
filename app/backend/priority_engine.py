"""Priority scoring for AuraPlan tasks. Higher scores should be scheduled first.

Scoring is deterministic and explainable: ``score_breakdown`` returns the
numeric components plus short human-readable reasons, and ``priority_score``
is the total used for ordering.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

DONE_STATUSES = frozenset({"done", "completed", "cancelled"})


def _get(task: Mapping[str, Any] | Any, key: str, default=None):
    return task.get(key, default) if isinstance(task, Mapping) else getattr(task, key, default)


def _datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def is_active(task) -> bool:
    return str(_get(task, "status", "pending")).casefold() not in DONE_STATUSES


def task_minutes(task, default: int = 30) -> int:
    """Estimated duration in minutes, tolerant of bad data."""
    try:
        return max(0, int(_get(task, "estimated_minutes", _get(task, "estimated_duration", default))))
    except (TypeError, ValueError):
        return default


def task_load(task) -> str:
    return str(_get(task, "load_level", _get(task, "mental_load", "low"))).casefold()


def hours_until(deadline, now) -> float | None:
    """Hours from ``now`` to ``deadline``; naive values are read as local time."""
    deadline, now = _datetime(deadline), _datetime(now)
    if deadline is None:
        return None
    if now is None:
        now = datetime.now().astimezone()
    if deadline.tzinfo is None and now.tzinfo is not None:
        deadline = deadline.replace(tzinfo=now.tzinfo)
    elif now.tzinfo is None and deadline.tzinfo is not None:
        now = now.replace(tzinfo=deadline.tzinfo)
    return (deadline - now).total_seconds() / 3600


def _fmt_hours(hours: float) -> str:
    hours = abs(hours)
    if hours < 1:
        return f"{max(1, round(hours * 60))} min"
    if hours < 48:
        return f"{hours:.0f}h"
    return f"{hours / 24:.0f} days"


def score_breakdown(task, *, now=None, energy: int = 3) -> dict:
    """Return ``{"score", "urgency", "reasons", "at_risk", ...}`` for a task.

    Urgency is based on *slack* (time until the deadline minus the work still
    needed), not on the raw deadline: a 4-hour task due in 5 hours is far more
    urgent than a 20-minute task due in 5 hours.
    Energy is an integer from 1 (very low) through 5 (high).
    """
    if not 1 <= energy <= 5:
        raise ValueError("energy must be from 1 to 5")
    if not is_active(task):
        return {"score": float("-inf"), "urgency": 0.0, "reasons": [], "at_risk": False,
                "hours_left": None, "slack_hours": None}
    now = _datetime(now) if now is not None else datetime.now().astimezone()
    duration = task_minutes(task)
    load = task_load(task)
    hours = hours_until(_get(task, "deadline"), now)
    slack = None if hours is None else hours - duration / 60.0
    reasons: list[str] = []
    at_risk = False

    if hours is None:
        urgency = 0.0
        reasons.append("no deadline")
    elif hours < 0:
        urgency = 125.0 + min(24.0, abs(hours) / 24.0)
        at_risk = True
        reasons.append(f"overdue by {_fmt_hours(hours)}")
    elif slack < 0:
        urgency = 113.0 + min(8.0, -slack)
        at_risk = True
        reasons.append(f"tight: needs {duration} min but only {_fmt_hours(hours)} left")
    elif slack <= 24:
        urgency = 100.0 + (24.0 - slack) / 24.0 * 12.0
        at_risk = slack <= 6
        reasons.append(f"due in {_fmt_hours(hours)}")
    elif slack <= 72:
        urgency = 70.0 + (72.0 - slack) / 48.0 * 30.0
        reasons.append(f"due in {_fmt_hours(hours)}")
    elif slack <= 168:
        urgency = 35.0 + (168.0 - slack) / 96.0 * 35.0
        reasons.append(f"due in {_fmt_hours(hours)}")
    else:
        urgency = max(0.0, 35.0 - (slack - 168.0) / 168.0 * 10.0)
        reasons.append(f"due in {_fmt_hours(hours)}")

    load_points = {"high": 16.0, "medium": 11.0, "low": 6.0}.get(load, 6.0)
    duration_points = min(duration, 240) / 60.0 * 2.0

    adjust = 0.0
    if str(_get(task, "status", "pending")).casefold() == "in_progress":
        adjust += 8.0
        reasons.append("already started, finish it")
    if load == "high":
        if energy == 1:
            adjust -= 12.0
            reasons.append("heavy task, but your energy is very low")
        elif energy == 2:
            adjust -= 7.0
            reasons.append("heavy task, but your energy is low")
        elif energy >= 4:
            adjust += 3.0
            reasons.append("heavy task suits your high energy")
    elif load == "medium":
        if energy == 1:
            adjust -= 5.0
            reasons.append("moderate task may feel harder at very low energy")
        elif energy == 2:
            adjust -= 2.0
            reasons.append("moderate task may take more effort at low energy")
        elif energy >= 4:
            adjust += 1.0
            reasons.append("moderate task fits your available energy")
    elif energy <= 2:
        adjust += 4.0
        reasons.append("light task suits your low energy")

    score = round(urgency + load_points + duration_points + adjust, 3)
    return {"score": score, "urgency": round(urgency, 3), "reasons": reasons,
            "at_risk": at_risk, "hours_left": hours, "slack_hours": slack}


def priority_score(task, *, now=None, energy: int = 3) -> float:
    """Total priority score; ``-inf`` for finished or cancelled tasks."""
    return score_breakdown(task, now=now, energy=energy)["score"]


def explain_priority(task, *, now=None, energy: int = 3) -> str:
    """One short sentence on why a task ranks where it does."""
    reasons = score_breakdown(task, now=now, energy=energy)["reasons"]
    text = "; ".join(reasons)
    return text[:1].upper() + text[1:] if text else ""
