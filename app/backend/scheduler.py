"""Deterministic daily task ranking and time-budget scheduling."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from priority_engine import (hours_until, is_active, score_breakdown, task_load,
                             task_minutes)

MIN_PARTIAL_MINUTES = 20      # smallest useful chunk of an urgent task
URGENT_HOURS = 48             # "urgent" means due (or overdue) within this window
DO_FIRST_HOURS = 24           # due within a day: always do before energy-based ordering


def _get(task: Mapping[str, Any] | Any, key: str, default=None):
    return task.get(key, default) if isinstance(task, Mapping) else getattr(task, key, default)


def _due_key(task):
    due = _get(task, "deadline")
    try:
        return datetime.fromisoformat(str(due).replace("Z", "+00:00")).timestamp() if due else float("inf")
    except (ValueError, TypeError, OverflowError):
        return float("inf")


def _sequence(items, energy):
    """Order the chosen tasks for doing: urgent first, then by energy fit.

    High energy: hardest work first while sharp. Low energy: easy wins first to
    build momentum. Medium energy keeps plain priority order.
    """
    def key(item):
        hours = item.get("_hours_left")
        urgent = hours is not None and hours <= DO_FIRST_HOURS
        load = item.get("load_level", item.get("mental_load", "low"))
        if energy >= 4:
            fit = {"high": 0, "medium": 1, "low": 2}.get(load, 2)
        elif energy <= 2:
            fit = {"low": 0, "medium": 1, "high": 2}.get(load, 0)
        else:
            fit = 0
        return (0 if urgent else 1, fit, -item["priority_score"])
    return sorted(items, key=key)


def generate_schedule(tasks, *, available_minutes: int, energy: int = 3,
                      now=None, allow_partial: bool = True) -> dict:
    """Return ordered scheduled tasks plus deferred tasks and remaining time.

    Tasks are chosen by priority score (ties: due date, then id/title); one that
    does not fit is skipped so shorter urgent tasks can still use the remaining
    time. An urgent task that does not fit whole may get a partial block
    (``partial`` is True). The chosen tasks are then sequenced for the
    energy level and given ``start_offset_minutes`` and a ``reason``.

    Besides the original keys the result has ``at_risk``: tasks that are
    overdue/urgent but not fully covered by today's budget.
    """
    if available_minutes < 0:
        raise ValueError("available_minutes cannot be negative")
    now = now or datetime.now().astimezone()
    eligible = [t for t in tasks if is_active(t)]
    scored = []
    for task in eligible:
        info = score_breakdown(task, now=now, energy=energy)
        scored.append((task, info))
    def ordering(pair):
        task, info = pair
        hours = info["hours_left"]
        identifier = str(_get(task, "id", _get(task, "title", "")))
        if hours is not None and hours <= URGENT_HOURS:
            # Inside the urgent window, protect the task with the least slack
            # first. A duration bonus must not make a later, longer task take
            # the only remaining time ahead of a nearer deadline.
            slack = info["slack_hours"]
            return (0, slack if slack is not None else float("inf"),
                    -info["score"], _due_key(task), identifier)
        return (1, -info["score"], _due_key(task), identifier)

    scored.sort(key=ordering)

    chosen, deferred, at_risk = [], [], []
    remaining = available_minutes
    for task, info in scored:
        duration = task_minutes(task)
        item = dict(task) if isinstance(task, Mapping) else vars(task).copy()
        item["priority_score"] = info["score"]
        item["reason"] = "; ".join(info["reasons"]).capitalize()
        item["_hours_left"] = info["hours_left"]
        urgent = info["hours_left"] is not None and info["hours_left"] <= URGENT_HOURS
        if duration <= remaining:
            item["scheduled_minutes"] = duration
            item["partial"] = False
            chosen.append(item)
            remaining -= duration
        elif allow_partial and urgent and remaining >= MIN_PARTIAL_MINUTES:
            item["scheduled_minutes"] = remaining
            item["partial"] = True
            item["reason"] += f"; only {remaining} of {duration} min fit today"
            chosen.append(item)
            at_risk.append(item)
            remaining = 0
        else:
            deferred.append(item)
            if urgent:
                at_risk.append(item)

    scheduled = _sequence(chosen, energy)
    offset = 0
    for item in scheduled:
        item["start_offset_minutes"] = offset
        offset += item["scheduled_minutes"]
    for item in scheduled + deferred:
        item.pop("_hours_left", None)
    return {"scheduled": scheduled, "deferred": deferred, "at_risk": at_risk,
            "available_minutes": available_minutes, "remaining_minutes": remaining,
            "energy": energy}
