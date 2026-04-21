"""Repository for database metadata and schema introspection.

Provides safe access to database schema information for diagnostic and
administrative operations.
"""

import sqlite3

from paperlab.config import Tables


def get_all_table_names(conn: sqlite3.Connection) -> list[str]:
    """Get all table names from database schema.

    Args:
        conn: Database connection

    Returns:
        List of table names sorted alphabetically

    Example:
        >>> with connection() as conn:
        ...     tables = metadata.get_all_table_names(conn)
        ...     print(tables)
        ['exam_types', 'llm_models', 'mark_criteria', ...]
    """
    cursor = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_row_count(table_name: str, conn: sqlite3.Connection) -> int:
    """Get row count for a specific table.

    Security: Validates table name against whitelist to prevent SQL injection.

    Args:
        table_name: Name of table to count
        conn: Database connection

    Returns:
        Number of rows in table

    Raises:
        ValueError: If table_name not in allowed tables list

    Example:
        >>> with connection() as conn:
        ...     count = metadata.get_table_row_count('students', conn)
        ...     print(f"Students: {count}")
    """
    # Security: Validate against whitelist to prevent SQL injection
    all_allowed_tables = Tables.REFERENCE_TABLES + Tables.OPERATIONAL_TABLES
    if table_name not in all_allowed_tables:
        raise ValueError(
            f"Table '{table_name}' not in allowed tables list. "
            f"Allowed tables: {', '.join(all_allowed_tables)}"
        )

    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def table_exists(table_name: str, conn: sqlite3.Connection) -> bool:
    """Check if table exists in database schema.

    Args:
        table_name: Name of table to check
        conn: Database connection

    Returns:
        True if table exists, False otherwise

    Example:
        >>> with connection() as conn:
        ...     if metadata.table_exists('students', conn):
        ...         print("Students table exists")
    """
    cursor = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_table_counts_dict(conn: sqlite3.Connection) -> dict[str, int]:
    """Get row counts for all known tables.

    Returns counts for all tables defined in Tables config class.
    Tables that don't exist will have count of 0.

    Args:
        conn: Database connection

    Returns:
        Dictionary mapping table name to row count

    Example:
        >>> with connection() as conn:
        ...     counts = metadata.get_table_counts_dict(conn)
        ...     for table, count in counts.items():
        ...         print(f"{table}: {count} rows")
    """
    counts = {}
    for table in Tables.REFERENCE_TABLES + Tables.OPERATIONAL_TABLES:
        try:
            counts[table] = get_table_row_count(table, conn)
        except (sqlite3.OperationalError, ValueError):
            # Table doesn't exist or other error
            counts[table] = 0
    return counts
