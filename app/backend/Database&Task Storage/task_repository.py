from database import get_db_connection, initialize_database

initialize_database()

class TaskRepository:

    @staticmethod
    def insert_task(title: str, description: str, deadline: str, estimated_duration: int, mental_load: str, status: str = "Pending") -> int:
        if mental_load not in ("High", "Low"):
            raise ValueError("mental_load must be either 'High' or 'Low'")
        
        query = """
            INSERT INTO tasks (title, description, deadline, estimated_duration, mental_load, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, description, deadline, estimated_duration, mental_load, status))
            return cursor.lastrowid

    @staticmethod
    def get_task_by_id(task_id: int) -> dict:
        query = "SELECT * FROM tasks WHERE id = ?"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all_tasks() -> list:
        query = "SELECT * FROM tasks ORDER BY deadline ASC"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update_task(task_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        valid_fields = {"title", "description", "deadline", "estimated_duration", "mental_load", "status"}
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key not in valid_fields:
                raise ValueError(f"Invalid field for update: {key}")
            if key == "mental_load" and value not in ("High", "Low"):
                raise ValueError("mental_load must be 'High' or 'Low'")
            set_clauses.append(f"{key} = ?")
            values.append(value)

        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            return cursor.rowcount > 0

    @staticmethod
    def delete_task(task_id: int) -> bool:
        query = "DELETE FROM tasks WHERE id = ?"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
            return cursor.rowcount > 0