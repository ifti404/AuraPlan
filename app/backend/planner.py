"""Multi-day planning: spread work across days so deadlines are met.

``generate_schedule`` answers "what should I do now?". ``plan_week`` answers
"will everything get done in time, and when should I do each part?" It splits
long tasks into sessions, never schedules work after a task's deadline day,
and reports tasks that cannot fit as ``at_risk`` with how many minutes short.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Mapping, Sequence

from priority_engine import (_datetime, explain_priority, is_active, priority_score,
                             task_load, task_minutes)

DEFAULT_MAX_SESSION = 90   # minutes; long tasks are split into sessions this size


def _get(task: Mapping[str, Any] | Any, key: str, default=None):
    return task.get(key, default) if isinstance(task, Mapping) else getattr(task, key, default)


def _per_day(value, index, default):
    if value is None:
        return default
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value[index] if index < len(value) else value[-1] if value else default
    return value


def _deadline_date(task, tz):
    dt = _datetime(_get(task, "deadline"))
    if dt is None:
        return None
    if dt.tzinfo is not None and tz is not None:
        dt = dt.astimezone(tz)
    return dt.date()


def plan_week(tasks, *, daily_minutes=180, days: int = 7, energy=3, now=None,
              max_session: int = DEFAULT_MAX_SESSION) -> dict:
    """Plan ``days`` days starting today. ``max_session`` is the longest single
    sitting taken per pass; a task gets at most one block per day (``part`` n of ``parts`` days).

    ``daily_minutes`` and ``energy`` may be a single value or a list with one
    entry per day (the last entry repeats). Returns::

        {"days": [{"date", "energy", "available_minutes", "used_minutes",
                   "blocks": [{"id", "title", "minutes", "part", "parts",
                               "load_level", "deadline", "reason"}]}],
         "at_risk": [{"id", "title", "deadline", "short_minutes", "reason"}],
         "late": [...]}   # work that has to happen after its deadline
    """
    if days < 1:
        raise ValueError("days must be at least 1")
    if max_session < 1:
        raise ValueError("max_session must be positive")
    now = _datetime(now) if now is not None else datetime.now().astimezone()
    tz = now.tzinfo
    active = [t for t in tasks if is_active(t)]
    remaining = {id(t): task_minutes(t) for t in active}
    parts_done = {id(t): 0 for t in active}
    deadline_day = {id(t): _deadline_date(t, tz) for t in active}
    plan_days = []

    for d in range(days):
        day = (now + timedelta(days=d)).date()
        day_energy = int(_per_day(energy, d, 3))
        budget = max(0, int(_per_day(daily_minutes, d, 180)))
        stamp = now if d == 0 else datetime.combine(day, time(8, 0), tzinfo=tz)
        entry = {"date": day.isoformat(), "energy": day_energy,
                 "available_minutes": budget, "used_minutes": 0, "blocks": []}
        left = budget
        candidates = [t for t in active if remaining[id(t)] > 0
                      and (deadline_day[id(t)] is None or deadline_day[id(t)] >= day
                           or deadline_day[id(t)] < now.date())]
        ranked = sorted(candidates, key=lambda t: (-priority_score(t, now=stamp, energy=day_energy),
                                                   str(_get(t, "id", _get(t, "title", "")))))
        first_pass, progress = True, True
        while left > 0 and progress:      # extra passes let a lone urgent task fill the day
            progress = False
            for task in ranked:
                if left <= 0:
                    break
                if remaining[id(task)] <= 0:
                    continue
                chunk = min(remaining[id(task)], left, max_session)
                # First pass: leave long tasks for a day with room rather than a sliver.
                if first_pass and chunk < remaining[id(task)] and chunk < min(30, remaining[id(task)]):
                    continue
                remaining[id(task)] -= chunk
                left -= chunk
                progress = True
                block = next((x for x in entry["blocks"] if x["_key"] == id(task)), None)
                if block:                 # same task again today: one longer block
                    block["minutes"] += chunk
                    continue
                parts_done[id(task)] += 1
                entry["blocks"].append({
                    "id": _get(task, "id"), "title": _get(task, "title", ""), "minutes": chunk,
                    "part": parts_done[id(task)], "parts": 0, "_key": id(task),
                    "load_level": task_load(task), "deadline": _get(task, "deadline"),
                    "reason": explain_priority(task, now=stamp, energy=day_energy),
                })
            first_pass = False
        entry["used_minutes"] = budget - left
        plan_days.append(entry)

    for entry in plan_days:
        for block in entry["blocks"]:
            block["parts"] = parts_done[block.pop("_key")]
    at_risk, late = [], []
    for task in active:
        short = remaining[id(task)]
        if short <= 0:
            continue
        dd = deadline_day[id(task)]
        info = {"id": _get(task, "id"), "title": _get(task, "title", ""),
                "deadline": _get(task, "deadline"), "short_minutes": short}
        if dd is not None and dd < now.date():
            info["reason"] = "already overdue and doesn't fit the plan"
            late.append(info)
        elif dd is not None and dd < now.date() + timedelta(days=days):
            info["reason"] = f"{short} min won't fit before its deadline"
            at_risk.append(info)
    return {"days": plan_days, "at_risk": at_risk, "late": late}
