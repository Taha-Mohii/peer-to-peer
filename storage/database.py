import sqlite3
import os 

DB_PATH = "storage/localchat.db"


def init_db():
    """Creates the messages table if it doesn't exist."""
    os.makedirs("storage", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            from_id TEXT NOT NULL,
            from_name TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_message(room: str, from_id: str, from_name: str, text: str, timestamp:int):
    """Save a message to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (room, from_id, from_name, text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        (room, from_id, from_name, text, timestamp),
    )
    conn.commit()
    conn.close()


def get_messages(room: str, limit: int = 1000) -> list:
    """Returns messages for a room, oldest first."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT from_id, from_name, text, timestamp
        FROM messages
        WHERE room = ?
        ORDER BY timestamp ASC
        LIMIT ?
    """,
        (room, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"from_id": r[0], "from_name": r[1], "text": r[2], "timestamp": r[3]}
        for r in rows
    ]

def clear_messages(room: str):
    """Delete all messages for a room."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE room = ?',(room,))
    conn.commit()
    conn.close()