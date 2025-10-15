"""SQLite storage for tasks and execution history."""

import sqlite3
import json
from typing import List, Dict, Optional


class TaskStorage:
    """Manages task storage in SQLite database."""

    def __init__(self, db_path: str = "day11_tasks.db"):
        """Initialize task storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                schedule_type TEXT NOT NULL,
                schedule_value TEXT NOT NULL,
                mcp_tool TEXT NOT NULL,
                tool_args TEXT,
                use_ai_summary BOOLEAN DEFAULT 1,
                notification_level TEXT DEFAULT 'all',
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                next_run TIMESTAMP
            )
        """)

        # Task execution history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                duration_ms INTEGER,
                raw_data TEXT,
                ai_summary TEXT,
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    def create_task(self, task_data: Dict) -> int:
        """Create a new task.

        Args:
            task_data: Task configuration dictionary

        Returns:
            Task ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks (
                name, description, schedule_type, schedule_value,
                mcp_tool, tool_args, use_ai_summary, notification_level, enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data['name'],
            task_data.get('description', ''),
            task_data['schedule_type'],
            task_data['schedule_value'],
            task_data['mcp_tool'],
            json.dumps(task_data.get('tool_args', {})),
            task_data.get('use_ai_summary', True),
            task_data.get('notification_level', 'all'),
            task_data.get('enabled', True)
        ))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return task_id

    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            task = dict(row)
            task['tool_args'] = json.loads(task['tool_args']) if task['tool_args'] else {}
            return task
        return None

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks.

        Returns:
            List of task dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks ORDER BY id")
        rows = cursor.fetchall()
        conn.close()

        tasks = []
        for row in rows:
            task = dict(row)
            task['tool_args'] = json.loads(task['tool_args']) if task['tool_args'] else {}
            tasks.append(task)

        return tasks

    def get_enabled_tasks(self) -> List[Dict]:
        """Get all enabled tasks.

        Returns:
            List of enabled task dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE enabled = 1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()

        tasks = []
        for row in rows:
            task = dict(row)
            task['tool_args'] = json.loads(task['tool_args']) if task['tool_args'] else {}
            tasks.append(task)

        return tasks

    def update_task(self, task_id: int, updates: Dict):
        """Update task fields.

        Args:
            task_id: Task ID
            updates: Dictionary of fields to update
        """
        if not updates:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build UPDATE query dynamically
        fields = []
        values = []
        for key, value in updates.items():
            if key == 'tool_args':
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"

        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def delete_task(self, task_id: int):
        """Delete a task.

        Args:
            task_id: Task ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    def add_history(self, history_data: Dict) -> int:
        """Add task execution history entry.

        Args:
            history_data: History entry dictionary

        Returns:
            History entry ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO task_history (
                task_id, status, duration_ms, raw_data, ai_summary, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            history_data['task_id'],
            history_data['status'],
            history_data.get('duration_ms'),
            history_data.get('raw_data'),
            history_data.get('ai_summary'),
            history_data.get('error_message')
        ))

        history_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return history_id

    def get_task_history(self, task_id: int, limit: int = 10) -> List[Dict]:
        """Get execution history for a task.

        Args:
            task_id: Task ID
            limit: Maximum number of entries to return

        Returns:
            List of history entry dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM task_history
            WHERE task_id = ?
            ORDER BY run_time DESC
            LIMIT ?
        """, (task_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_latest_result(self, task_id: int) -> Optional[Dict]:
        """Get the most recent execution result.

        Args:
            task_id: Task ID

        Returns:
            Latest history entry or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM task_history
            WHERE task_id = ?
            ORDER BY run_time DESC
            LIMIT 1
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
