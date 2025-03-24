import sqlite3
from sqlite3 import Connection
from datetime import datetime
from typing import List, Tuple


def init_db(db_path: str = "chat_messages.db") -> Connection:
    """
    Initializes the SQLite database and creates the messages table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            timestamp TEXT,
            message TEXT
        )
    """)
    conn.commit()
    return conn


def store_message(conn: Connection, sender: str, message: bytes) -> None:
    """
    Stores a message into the database with sender information and a timestamp.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_text = message.decode('utf-8')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, timestamp, message) VALUES (?, ?, ?)",
                   (sender, timestamp, message_text))
    conn.commit()


def load_messages(conn: Connection) -> List[Tuple]:
    """
    Loads all messages from the database.

    :return: A list of tuples (id, sender, timestamp, message) for each stored message.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, timestamp, message FROM messages ORDER BY id ASC")
    return cursor.fetchall()