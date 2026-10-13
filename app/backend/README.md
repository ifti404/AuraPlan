# AuraPlan backend: first progress review

Standalone Python backend modules for task classification, priority scoring,
daily scheduling, and persistent SQLite storage. Python 3.10+; standard library
only.

## Shared task interface

All interfaces share `Task` from `task_model.py`, with `title`, `deadline`
(ISO datetime), `estimated_minutes`, `description`, `load_level` (`high`/`medium`/`low`),
`status`, optional `id`, and optional `scheduled_date`. Repository reads and
writes use this dataclass. The scheduler accepts `Task` instances or matching
dictionaries. Storage contains no scheduling policy.

## Quick start

Run from this directory:

```python
from task_repository import TaskRepository
from task_classifier import classify_task
from scheduler import generate_schedule

repo = TaskRepository()  # persists to auraplan.sqlite3 beside these modules
task = repo.create_task(
    title="Write history essay", deadline="2026-10-15T18:00:00+06:00",
    estimated_minutes=90,
    load_level=classify_task("Write history essay"),
)
tasks = repo.list_tasks(include_completed=False)
plan = generate_schedule(tasks, available_minutes=120, energy=2)
```

`TaskRepository` exposes `create_task`, `get_task`, `list_tasks`, `update_task`,
and `delete_task`. Dates are ISO-formatted. Invalid values raise `ValueError`;
SQLite integrity and connection errors remain standard `sqlite3` exceptions.

The classifier uses whole-word/phrase matches; when both keyword groups match,
high mental load wins. Extend the module keyword sets or pass extra
`high_keywords` / `low_keywords` to `classify_task`.

The score is deterministic for a given `now` and energy level. Deadline urgency
dominates the bounded low-energy penalty, so tiredness cannot demote imminent
or overdue tasks below ordinary work. The scheduler ranks eligible tasks,
allocates tasks that fit the remaining time, and reports those that do not in
`deferred`. Same-time conflicts resolve consistently by score, deadline, then
task ID/title.

## First progress review scenarios

The test suite covers SQLite create/retrieve/update/delete and reopen
persistence, high/medium/low classification, low-energy adjustment, an urgent
deadline while tired, overdue tasks, and time-budget conflicts. Run:

```powershell
python -m unittest discover -s tests -v
```
