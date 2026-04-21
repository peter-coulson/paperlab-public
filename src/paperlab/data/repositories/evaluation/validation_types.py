"""Repository for validation_types table.

Provides data access methods for validation types (e.g., mark_scheme_sanity, nuanced_marking).
"""

import sqlite3
from dataclasses import dataclass


@dataclass
class ValidationTypeInfo:
    """Validation type information from database."""

    code: str
    display_name: str
    description: str


def get_by_code(
    code: str,
    conn: sqlite3.Connection,
) -> int:
    """Look up validation_type_id for a given code.

    Args:
        code: Validation type code (e.g., 'mark_scheme_sanity', 'nuanced_marking')
        conn: Database connection (to evaluation_results.db)

    Returns:
        validation_type_id

    Raises:
        ValueError: If validation type doesn't exist
    """
    cursor = conn.execute(
        """
        SELECT id FROM validation_types
        WHERE code = ?
        """,
        (code,),
    )

    row = cursor.fetchone()
    if row is None:
        # Query available types from database for helpful error message
        all_types = get_all(conn)
        valid_codes = ", ".join(f"'{t.code}'" for t in all_types)
        raise ValueError(
            f"Validation type '{code}' not found. "
            f"Valid types: {valid_codes}. "
            "Check your test case JSON or add the type to "
            "data/evaluation/config/validation_types.json."
        )

    return int(row[0])


def create_validation_types_batch(
    types_data: list[dict[str, str]],
    conn: sqlite3.Connection,
) -> int:
    """Create multiple validation types in a single batch operation.

    Args:
        types_data: List of dicts with keys: code, display_name, description
        conn: Database connection (to evaluation_results.db)

    Returns:
        Number of rows inserted

    Note:
        Uses executemany() for efficient batch insert.
        Caller must commit transaction.
    """
    cursor = conn.executemany(
        """
        INSERT INTO validation_types (code, display_name, description)
        VALUES (:code, :display_name, :description)
        """,
        types_data,
    )
    return cursor.rowcount


def get_all(conn: sqlite3.Connection) -> list[ValidationTypeInfo]:
    """Get all validation types from database.

    Args:
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of validation type information

    Note:
        Used for diff calculation in replace mode.
    """
    cursor = conn.execute(
        """
        SELECT code, display_name, description
        FROM validation_types
        ORDER BY code
        """
    )

    return [
        ValidationTypeInfo(code=row[0], display_name=row[1], description=row[2])
        for row in cursor.fetchall()
    ]


def count_validation_types(conn: sqlite3.Connection) -> int:
    """Count total number of validation types in database.

    Args:
        conn: Database connection (to evaluation_results.db)

    Returns:
        Count of validation types

    Note:
        Used for verification after loading.
    """
    cursor = conn.execute("SELECT COUNT(*) FROM validation_types")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def delete_all(conn: sqlite3.Connection) -> None:
    """Delete all validation types from database.

    Args:
        conn: Database connection (to evaluation_results.db)

    Note:
        Used in replace mode.
        Caller must commit transaction.
    """
    conn.execute("DELETE FROM validation_types")
