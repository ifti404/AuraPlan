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