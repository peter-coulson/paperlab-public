"""Database connection management for marking engine.

Responsibilities:
- Provide database connections with foreign keys enabled
- Fail fast if database file doesn't exist
- Ensure connections are always closed (context manager support)

Design:
- Minimal and simple
- No schema validation (queries will fail fast if schema is wrong)
- Single responsibility: connection lifecycle only
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from paperlab.config import DatabaseSettings, settings


class DatabaseError(Exception):
    """Database configuration error."""

    pass


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get database connection with foreign keys enabled.

    Args:
        db_path: Path to database file (default: uses settings.db_path)

    Returns:
        SQLite connection with Row factory for dict-like access

    Raises:
        DatabaseError: If database file does not exist

    Note:
        Caller is responsible for closing connection.
        Prefer using connection() context manager for automatic cleanup.
    """
    if db_path is None:
        db_path = settings.db_path

    if not db_path.exists():
        raise DatabaseError(
            f"Database not found: {db_path}\nRun: uv run paperlab db init to create database"
        )

    conn = sqlite3.connect(db_path)

    # Enable foreign key constraints (SQLite default is OFF)
    conn.execute(DatabaseSettings.FOREIGN_KEYS_PRAGMA)

    # Use Row factory for dict-like column access
    # Example: row["column_name"] instead of row[0]
    conn.row_factory = sqlite3.Row

    return conn


@contextmanager
def connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connection with guaranteed cleanup.

    Ensures connection is always closed, even if exception occurs.
    Does NOT automatically commit - caller must explicitly commit.

    Args:
        db_path: Path to database file (default: uses settings.db_path)

    Yields:
        SQLite connection with foreign keys enabled

    Raises:
        DatabaseError: If database file does not exist

    Example:
        >>> with connection() as conn:
        ...     try:
        ...         conn.execute("INSERT INTO papers (...) VALUES (...)")
        ...         conn.commit()
        ...     except Exception:
        ...         conn.rollback()
        ...         raise
        # Connection automatically closed here, even if exception occurred
    """
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        # Always close, even if exception occurred
        conn.close()
