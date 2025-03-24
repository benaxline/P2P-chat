import sqlite3
from datetime import datetime
from sqlite3 import Connection
from typing import List, Tuple



def init_db(db_path: str = "chat_messages.db") -> Connection:
    """
    This initializes SQLite database and creates the messages table if
    it doesn't yet exist

    :param db_path: path to the SQLite database file
    :return: the SQLite DB connection
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
    Stores message into database
    includes sender info and timestamp

    :param conn: the SQLite DB connection
    :param sender: the sender's address
    :param message: the message to store
    :return: None
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_text = message.decode('utf-8')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, timestamp, message) VALUES (?, ?, ?)",
                   (sender, timestamp, message_text))
    conn.commit()


def load_messages(conn: Connection) -> List[Tuple]:
    """
    load messages from the SQLite DB

    :param conn: the SQLite DB connection
    :return: a list of tuples
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender, timestamp, message
        FROM messages 
        ORDER BY id ASC
    """)
    return cursor.fetchall()