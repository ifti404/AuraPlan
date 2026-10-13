import sqlite3
import os
from contextlib import contextmanager

DB_NAME = "auraplan.db"
SCHEMA_FILE = "schema.sql"

def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r") as f:
            cursor.executescript(f.read())
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT NOT NULL,
                estimated_duration INTEGER NOT NULL,
                mental_load TEXT CHECK(mental_load IN ('High', 'Low')) NOT NULL,
                status TEXT CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Overdue')) DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Database error occurred: {e}")
    finally:
        conn.close()