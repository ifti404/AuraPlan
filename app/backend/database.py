"""SQLite connection and initialization helpers for AuraPlan."""
from __future__ import annotations

import sqlite3
import os
import sys
from contextlib import contextmanager
from pathlib import Path


def _default_db_path() -> Path:
    """Keep development data beside the backend, and packaged data in AppData."""
    if getattr(sys, "frozen", False):
        app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return app_data / "AuraPlan" / "auraplan.sqlite3"
    return Path(__file__).with_name("auraplan.sqlite3")


DEFAULT_DB_PATH = _default_db_path()


def connect(db_path=DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a configured connection. Pass ``:memory:`` for an in-memory DB."""
    path = str(db_path)
    if path != ":memory:":
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


@contextmanager
def connection(db_path=DEFAULT_DB_PATH):
    """Yield a connection, commit/rollback its transaction, and always close it."""
    conn = connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database(db_path=DEFAULT_DB_PATH) -> None:
    """Create or update the local database schema without losing task rows."""
    schema_path = Path(__file__).with_name("schema.sql")
    if not schema_path.is_file() and getattr(sys, "frozen", False):
        # The backend modules are bundled into PyInstaller's PYZ archive,
        # while schema.sql is a data file under app/backend inside _internal.
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        schema_path = bundle_root / "app" / "backend" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")
    with connection(db_path) as conn:
        conn.executescript(schema)
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
        ).fetchone()
        if row and "medium" not in (row["sql"] or "").casefold():
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("ALTER TABLE tasks RENAME TO tasks_before_load_migration")
                conn.execute("""
                    CREATE TABLE tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                        description TEXT NOT NULL DEFAULT '',
                        deadline TEXT,
                        estimated_minutes INTEGER NOT NULL DEFAULT 30 CHECK(estimated_minutes >= 0),
                        load_level TEXT NOT NULL DEFAULT 'high'
                            CHECK(load_level IN ('high', 'medium', 'low')),
                        status TEXT NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
                        scheduled_date TEXT,
                        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                    )
                """)
                expected = ("id", "title", "description", "deadline", "estimated_minutes",
                            "load_level", "status", "scheduled_date", "created_at", "updated_at")
                old_columns = {column["name"] for column in
                               conn.execute("PRAGMA table_info(tasks_before_load_migration)")}
                columns = [column for column in expected if column in old_columns]
                quoted = ", ".join(f'"{column}"' for column in columns)
                conn.execute(f"INSERT INTO tasks ({quoted}) SELECT {quoted} "
                             "FROM tasks_before_load_migration")
                conn.execute("DROP TABLE tasks_before_load_migration")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                conn.commit()
            except Exception:
                conn.rollback()
                raise

