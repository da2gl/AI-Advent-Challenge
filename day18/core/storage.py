"""SQLite storage manager for conversation dialogs."""

import sqlite3
import os
from typing import List, Dict, Optional


class SQLiteStorage:
    """Manages persistent storage of conversation dialogs using SQLite."""

    def __init__(self, db_path: str = "data/conversations.db"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Create dialogs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                model TEXT,
                message_count INTEGER DEFAULT 0
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dialog_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                FOREIGN KEY (dialog_id) REFERENCES dialogs(id) ON DELETE CASCADE
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_dialog
            ON messages(dialog_id, timestamp)
        """)

        self.conn.commit()

    def create_dialog(self, model: str, title: str = "Untitled") -> int:
        """Create a new dialog.

        Args:
            model: Model name used for this dialog
            title: Dialog title (default: "Untitled")

        Returns:
            Dialog ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dialogs (title, model, message_count)
            VALUES (?, ?, 0)
        """, (title, model))
        self.conn.commit()
        return cursor.lastrowid

    def save_message(
        self,
        dialog_id: int,
        role: str,
        content: str,
        tokens: int = 0
    ):
        """Save a message to the database.

        Args:
            dialog_id: Dialog ID
            role: Message role ('user' or 'model')
            content: Message content
            tokens: Token count for this message
        """
        cursor = self.conn.cursor()

        # Insert message
        cursor.execute("""
            INSERT INTO messages (dialog_id, role, content, tokens)
            VALUES (?, ?, ?, ?)
        """, (dialog_id, role, content, tokens))

        # Update dialog metadata
        cursor.execute("""
            UPDATE dialogs
            SET last_updated = CURRENT_TIMESTAMP,
                message_count = message_count + 1
            WHERE id = ?
        """, (dialog_id,))

        self.conn.commit()

    def load_dialog(self, dialog_id: int) -> List[Dict]:
        """Load all messages from a dialog.

        Args:
            dialog_id: Dialog ID

        Returns:
            List of messages with role, content, tokens, timestamp
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT role, content, tokens, timestamp
            FROM messages
            WHERE dialog_id = ?
            ORDER BY timestamp ASC
        """, (dialog_id,))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row['role'],
                'content': row['content'],
                'tokens': row['tokens'],
                'timestamp': row['timestamp']
            })

        return messages

    def get_dialog_info(self, dialog_id: int) -> Optional[Dict]:
        """Get dialog metadata.

        Args:
            dialog_id: Dialog ID

        Returns:
            Dictionary with dialog info or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, created_at, last_updated, model, message_count
            FROM dialogs
            WHERE id = ?
        """, (dialog_id,))

        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'last_updated': row['last_updated'],
                'model': row['model'],
                'message_count': row['message_count']
            }
        return None

    def list_dialogs(self) -> List[Dict]:
        """List all dialogs ordered by last updated.

        Returns:
            List of dialog metadata dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, created_at, last_updated, model, message_count
            FROM dialogs
            ORDER BY last_updated DESC
        """)

        dialogs = []
        for row in cursor.fetchall():
            dialogs.append({
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'last_updated': row['last_updated'],
                'model': row['model'],
                'message_count': row['message_count']
            })

        return dialogs

    def delete_dialog(self, dialog_id: int) -> bool:
        """Delete a dialog and all its messages.

        Args:
            dialog_id: Dialog ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM dialogs WHERE id = ?", (dialog_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_dialog_title(self, dialog_id: int, title: str):
        """Update dialog title.

        Args:
            dialog_id: Dialog ID
            title: New title
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE dialogs SET title = ? WHERE id = ?
        """, (title, dialog_id))
        self.conn.commit()

    def update_dialog_timestamp(self, dialog_id: int):
        """Update dialog last_updated timestamp.

        Args:
            dialog_id: Dialog ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE dialogs
            SET last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (dialog_id,))
        self.conn.commit()

    def delete_empty_dialogs(self) -> int:
        """Delete all dialogs with no messages.

        Returns:
            Number of dialogs deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM dialogs WHERE message_count = 0
        """)
        self.conn.commit()
        return cursor.rowcount

    def close(self):
        """Close database connection."""
        self.conn.close()
