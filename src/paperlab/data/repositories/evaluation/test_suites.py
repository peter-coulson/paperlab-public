"""Repository for test_suites table.

Provides data access methods for test suites in evaluation_results.db.
"""

import sqlite3

from paperlab.config import ErrorMessages


def create_test_suite(
    name: str,
    description: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create test suite record.

    Does NOT commit - caller manages transaction.

    Args:
        name: Suite name (must be unique)
        description: Optional suite description
        conn: Database connection (to evaluation_results.db)

    Returns:
        test_suite_id

    Raises:
        ValueError: If failed to get test_suite_id after INSERT
        sqlite3.IntegrityError: If suite name already exists (UNIQUE constraint)
    """
    cursor = conn.execute(
        """
        INSERT INTO test_suites (name, description)
        VALUES (?, ?)
        """,
        (name, description),
    )

    test_suite_id = cursor.lastrowid
    if test_suite_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="test_suite"))
    return test_suite_id


def suite_name_exists(name: str, conn: sqlite3.Connection) -> bool:
    """Check if suite name already exists.

    Args:
        name: Suite name to check
        conn: Database connection (to evaluation_results.db)

    Returns:
        True if suite name exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_suites WHERE name = ?",
        (name,),
    )
    count = int(cursor.fetchone()[0])
    return count > 0


def test_suite_exists(test_suite_id: int, conn: sqlite3.Connection) -> bool:
    """Check if test suite exists.

    Args:
        test_suite_id: Test suite ID to check
        conn: Database connection (to evaluation_results.db)

    Returns:
        True if test suite exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_suites WHERE id = ?",
        (test_suite_id,),
    )
    count = int(cursor.fetchone()[0])
    return count == 1


def get_by_id(test_suite_id: int, conn: sqlite3.Connection) -> dict[str, int | str | None]:
    """Get suite information by ID.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Dict with id, name, and description

    Raises:
        ValueError: If test suite not found
    """
    cursor = conn.execute(
        "SELECT id, name, description FROM test_suites WHERE id = ?",
        (test_suite_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Test suite not found with id: {test_suite_id}\n"
            "Ensure the test suite exists in evaluation_results.db."
        )
    return {"id": int(row[0]), "name": str(row[1]), "description": row[2]}


def get_by_name(name: str, conn: sqlite3.Connection) -> dict[str, int | str | None] | None:
    """Get suite information by name.

    Args:
        name: Suite name
        conn: Database connection (to evaluation_results.db)

    Returns:
        Dict with id, name, and description, or None if not found
    """
    cursor = conn.execute(
        "SELECT id, name, description FROM test_suites WHERE name = ?",
        (name,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {"id": int(row[0]), "name": str(row[1]), "description": row[2]}


def update_description(
    test_suite_id: int, description: str | None, conn: sqlite3.Connection
) -> None:
    """Update suite description.

    Does NOT commit - caller manages transaction.

    Args:
        test_suite_id: Test suite ID
        description: New description
        conn: Database connection (to evaluation_results.db)
    """
    conn.execute(
        "UPDATE test_suites SET description = ? WHERE id = ?",
        (description, test_suite_id),
    )


def delete_suite(test_suite_id: int, conn: sqlite3.Connection) -> None:
    """Delete test suite record (CASCADE will delete associations).

    Does NOT commit - caller manages transaction.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)
    """
    conn.execute(
        "DELETE FROM test_suites WHERE id = ?",
        (test_suite_id,),
    )


def list_all_names(conn: sqlite3.Connection) -> list[str]:
    """List all test suite names.

    Args:
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of suite names, ordered alphabetically

    Note:
        Used for displaying available suites in error messages.
    """
    cursor = conn.execute("SELECT name FROM test_suites ORDER BY name")
    return [row[0] for row in cursor.fetchall()]
