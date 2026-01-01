import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Database connection & initialization
# ---------------------------------------------------------------------------

def get_connection(db_path: str = "messages_cache.db") -> sqlite3.Connection:
    """
    Create and return a SQLite connection with sane defaults.
    """
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )

    # Better performance & concurrency safety
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Initialize the messages_cache table if it does not already exist.
    Safe to call multiple times.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages_cache (
            id INTEGER PRIMARY KEY,
            message_hash TEXT UNIQUE,
            extracted_json TEXT,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_last_seen
        ON messages_cache(last_seen);
        """
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_message_hash(text: str) -> str:
    """
    Compute a deterministic SHA-256 hash of normalized message text.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cache lookup & mutation
# ---------------------------------------------------------------------------

def get_cached_message(
    conn: sqlite3.Connection,
    message_hash: str
) -> Optional[Tuple[int, str]]:
    """
    Check for an exact duplicate message by hash.

    Returns:
        (row_id, extracted_json) if found
        None if not found
    """
    cursor = conn.execute(
        """
        SELECT id, extracted_json
        FROM messages_cache
        WHERE message_hash = ?
        """,
        (message_hash,),
    )
    return cursor.fetchone()


def touch_message(conn: sqlite3.Connection, row_id: int) -> None:
    """
    Update last_seen timestamp for an existing cached message.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")  # UTC time with microseconds
    conn.execute(
        """
        UPDATE messages_cache
        SET last_seen = ?
        WHERE id = ?
        """,
        (now, row_id),
    )
    conn.commit()


import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Database connection & initialization
# ---------------------------------------------------------------------------

def get_connection(db_path: str = "messages_cache.db") -> sqlite3.Connection:
    """
    Create and return a SQLite connection with sane defaults.
    """
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )

    # Better performance & concurrency safety
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Initialize the messages_cache table if it does not already exist.
    Safe to call multiple times.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages_cache (
            id INTEGER PRIMARY KEY,
            message_hash TEXT UNIQUE,
            extracted_json TEXT,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_last_seen
        ON messages_cache(last_seen);
        """
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_message_hash(text: str) -> str:
    """
    Compute a deterministic SHA-256 hash of normalized message text.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cache lookup & mutation
# ---------------------------------------------------------------------------

def get_cached_message(
    conn: sqlite3.Connection,
    message_hash: str
) -> Optional[Tuple[int, str]]:
    """
    Check for an exact duplicate message by hash.

    Returns:
        (row_id, extracted_json) if found
        None if not found
    """
    cursor = conn.execute(
        """
        SELECT id, extracted_json
        FROM messages_cache
        WHERE message_hash = ?
        """,
        (message_hash,),
    )
    return cursor.fetchone()


def touch_message(conn: sqlite3.Connection, row_id: int) -> None:
    """
    Update last_seen timestamp for an existing cached message.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")  # UTC time with microseconds
    conn.execute(
        """
        UPDATE messages_cache
        SET last_seen = ?
        WHERE id = ?
        """,
        (now, row_id),
    )
    conn.commit()


def insert_message(
    conn: sqlite3.Connection,
    message_hash: str,
    extracted_json: str
) -> None:
    """
    Insert a new message into the cache.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")  # Use timezone-aware datetime

    conn.execute(
        """
        INSERT INTO messages_cache (
            message_hash,
            extracted_json,
            first_seen,
            last_seen
        )
        VALUES (?, ?, ?, ?)
        """,
        (message_hash, extracted_json, now, now),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Cleanup / retention
# ---------------------------------------------------------------------------

def cleanup_old_messages(conn: sqlite3.Connection, days: int = 5) -> None:
    """
    Delete cached messages that have not been seen in the last `days`.
    """
    conn.execute(
        """
        DELETE FROM messages_cache
        WHERE last_seen < datetime('now', ?)
        """,
        (f"-{days} days",),
    )
    conn.commit()



# ---------------------------------------------------------------------------
# Cleanup / retention
# ---------------------------------------------------------------------------

def cleanup_old_messages(conn: sqlite3.Connection, days: int = 5) -> None:
    """
    Delete cached messages that have not been seen in the last `days`.
    """
    conn.execute(
        """
        DELETE FROM messages_cache
        WHERE last_seen < datetime('now', ?)
        """,
        (f"-{days} days",),
    )
    conn.commit()
