"""Validated CRUD interface for academic tasks; scheduling stays elsewhere."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from database import DEFAULT_DB_PATH, connection, initialize_database
from task_model import Task

_FIELDS = {"title", "description", "deadline", "estimated_minutes", "load_level",
           "status", "scheduled_date"}
_STATUSES = {"pending", "in_progress", "completed", "cancelled"}


def _timestamp(value, name, *, date_only=False):
    if value is None or value == "":
        return None
    if isinstance(value, (datetime, date)):
        if date_only and isinstance(value, datetime):
            return value.date().isoformat()
        return value.isoformat()
    text = str(value)
    try:
        date.fromisoformat(text) if date_only else datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO {'date' if date_only else 'datetime'}") from exc
    return text


def _validate(data: Mapping[str, Any], *, creating=False) -> dict:
    unknown = set(data) - _FIELDS
    if unknown:
        raise ValueError(f"unsupported task field(s): {', '.join(sorted(unknown))}")
    result = dict(data)
    if creating and not str(result.get("title", "")).strip():
        raise ValueError("title is required")
    if "title" in result:
        result["title"] = str(result["title"]).strip()
        if not result["title"]:
            raise ValueError("title cannot be blank")
    if "description" in result:
        result["description"] = str(result["description"] or "")
    if "estimated_minutes" in result:
        duration = result["estimated_minutes"]
        if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
            raise ValueError("estimated_minutes must be a non-negative integer")
    if "load_level" in result:
        result["load_level"] = str(result["load_level"]).casefold()
        if result["load_level"] not in {"high", "medium", "low"}:
            raise ValueError("load_level must be 'high', 'medium', or 'low'")
    if "status" in result:
        result["status"] = str(result["status"]).casefold()
        if result["status"] not in _STATUSES:
            raise ValueError(f"status must be one of {', '.join(sorted(_STATUSES))}")
    if "deadline" in result:
        result["deadline"] = _timestamp(result["deadline"], "deadline")
    if "scheduled_date" in result:
        result["scheduled_date"] = _timestamp(result["scheduled_date"], "scheduled_date", date_only=True)
    if "scheduled_start" in result and result["scheduled_start"] is not None:
        result["scheduled_start"] = str(result["scheduled_start"])
    return result


def _task(row) -> Task | None:
    return Task(title=row["title"], deadline=row["deadline"],
                estimated_minutes=row["estimated_minutes"], description=row["description"],
                load_level=row["load_level"], status=row["status"], id=row["id"],
                scheduled_date=row["scheduled_date"])


class TaskRepository:
    """Task CRUD repository. Each operation uses its own short-lived connection."""
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        initialize_database(self.db_path)
        # Keep behavioral history self-contained in the repository layer so
        # deployments can add these files without changing the owned schema.sql.
        with connection(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                energy INTEGER CHECK(energy BETWEEN 1 AND 5),
                load_level TEXT CHECK(load_level IN ('high', 'medium', 'low')),
                planned_minutes INTEGER CHECK(planned_minutes >= 0),
                actual_minutes INTEGER CHECK(actual_minutes >= 0),
                completed INTEGER CHECK(completed IN (0, 1)),
                perceived_difficulty INTEGER CHECK(perceived_difficulty BETWEEN 1 AND 5),
                interrupted INTEGER CHECK(interrupted IN (0, 1)),
                started_at TEXT,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_task ON study_sessions(task_id)")

    def create_task(self, *, title: str, deadline: str, estimated_minutes: int,
                    description: str = "", load_level: str = "high",
                    status: str = "pending", scheduled_date=None) -> Task:
        data = _validate({"title": title, "description": description,
                          "deadline": deadline, "estimated_minutes": estimated_minutes,
                          "load_level": load_level, "status": status,
                          "scheduled_date": scheduled_date}, creating=True)
        columns = list(data)
        marks = ", ".join("?" for _ in columns)
        with connection(self.db_path) as conn:
            cur = conn.execute(f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({marks})",
                                [data[c] for c in columns])
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
            return _task(row)

    def get_task(self, task_id: int) -> Task | None:
        with connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return _task(row) if row else None

    def list_tasks(self, *, status: str | None = None, include_completed: bool = True) -> list[Task]:
        clauses, params = [], []
        if status is not None:
            validated = _validate({"status": status})["status"]
            clauses.append("status = ?")
            params.append(validated)
        elif not include_completed:
            clauses.append("status NOT IN ('completed', 'cancelled')")
        query = "SELECT * FROM tasks" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY id"
        with connection(self.db_path) as conn:
            return [_task(row) for row in conn.execute(query, params).fetchall()]

    def update_task(self, task_id: int, **changes) -> Task | None:
        data = _validate(changes)
        if not data:
            return self.get_task(task_id)
        data["updated_at"] = datetime.now().astimezone().isoformat()
        assignments = ", ".join(f"{field} = ?" for field in data)
        with connection(self.db_path) as conn:
            cur = conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?",
                               [*data.values(), task_id])
            if not cur.rowcount:
                return None
            return _task(conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())

    def delete_task(self, task_id: int) -> bool:
        with connection(self.db_path) as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cur.rowcount > 0

    def record_study_session(self, *, task_id=None, energy=None, load_level=None,
                             planned_minutes=None, actual_minutes=None, completed=None,
                             perceived_difficulty=None, interrupted=None, started_at=None):
        """Persist one locally observed study session; optional fields may be omitted."""
        if energy is not None and (isinstance(energy, bool) or not 1 <= int(energy) <= 5):
            raise ValueError("energy must be from 1 to 5")
        if load_level is not None and str(load_level).casefold() not in {"high", "medium", "low"}:
            raise ValueError("load_level must be high, medium, or low")
        for name, value in (("planned_minutes", planned_minutes), ("actual_minutes", actual_minutes)):
            if value is not None and (isinstance(value, bool) or int(value) < 0):
                raise ValueError(f"{name} must be non-negative")
        values = (task_id, energy, str(load_level).casefold() if load_level else None,
                  planned_minutes, actual_minutes, None if completed is None else int(bool(completed)),
                  perceived_difficulty, None if interrupted is None else int(bool(interrupted)), started_at)
        with connection(self.db_path) as conn:
            cur = conn.execute("""INSERT INTO study_sessions
                (task_id,energy,load_level,planned_minutes,actual_minutes,completed,
                 perceived_difficulty,interrupted,started_at) VALUES (?,?,?,?,?,?,?,?,?)""", values)
            return cur.lastrowid

    def list_study_sessions(self, *, limit=500):
        """Return recent session evidence as dictionaries for local analysis."""
        with connection(self.db_path) as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM study_sessions ORDER BY started_at DESC, id DESC LIMIT ?",
                (max(1, int(limit)),)).fetchall()]

    def study_recommendations(self, *, min_sessions=4):
        from priority_engine import behavioral_insights
        return behavioral_insights(self.list_study_sessions(), min_sessions=min_sessions)

