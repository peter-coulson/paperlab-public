"""Database utility functions and context managers."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def ensure_database_exists(
    db_path: Path, creation_command: str, error_context: str | None = None
) -> bool:
    """Check if database exists and print helpful error if not.

    Args:
        db_path: Path to database file
        creation_command: Command to create the database (for error message)
        error_context: Optional additional context to display in error message

    Returns:
        True if database exists, False otherwise
    """
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        if error_context:
            print(f"\n{error_context}")
        print(f"\nCreate it with:\n  {creation_command}")
        return False
    return True


def validate_databases_exist(
    db_configs: list[tuple[Path, str]],
) -> bool:
    """Validate that multiple databases exist.

    Args:
        db_configs: List of (db_path, creation_command) tuples

    Returns:
        True if all databases exist, False if any are missing

    Example:
        >>> from paperlab.config import settings
        >>> configs = [
        ...     (settings.db_path, "uv run paperlab db init"),
        ...     (settings.evaluation_db_path, f"sqlite3 {settings.evaluation_db_path} < ..."),
        ... ]
        >>> if not validate_databases_exist(configs):
        ...     return 1
    """
    for db_path, creation_command in db_configs:
        if not ensure_database_exists(db_path, creation_command):
            return False
    return True


@contextmanager
def attach_database(
    conn: sqlite3.Connection, db_path: Path, alias: str
) -> Generator[None, None, None]:
    """Context manager for attaching and detaching a database.

    Args:
        conn: Connection to attach database to
        db_path: Path to database file to attach
        alias: Alias name for attached database

    Yields:
        None

    Example:
        >>> with attach_database(conn, Path("test.db"), "test_db"):
        ...     conn.execute("SELECT * FROM test_db.some_table")
    """
    conn.execute(f"ATTACH DATABASE '{db_path}' AS {alias}")
    try:
        yield
    finally:
        conn.execute(f"DETACH DATABASE {alias}")
