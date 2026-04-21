"""Repository for test_case_marks table.

Provides data access methods for ground truth marks in evaluation_results.db.
"""

import sqlite3


def create_test_case_marks_batch(
    test_case_id: int,
    marks: dict[int, int],
    conn: sqlite3.Connection,
) -> None:
    """Create multiple test case mark records in one query.

    Does NOT commit - caller manages transaction.

    Args:
        test_case_id: Test case ID
        marks: Dictionary mapping criterion_index to marks_awarded_human
        conn: Database connection (to evaluation_results.db)

    Raises:
        sqlite3.IntegrityError: If any mark already exists
    """
    # Prepare batch data: list of (test_case_id, criterion_index, marks_awarded)
    batch_data = [
        (test_case_id, criterion_index, marks_awarded)
        for criterion_index, marks_awarded in marks.items()
    ]

    conn.executemany(
        """
        INSERT INTO test_case_marks (
            test_case_id,
            criterion_index,
            marks_awarded_human
        ) VALUES (?, ?, ?)
        """,
        batch_data,
    )


def count_marks(test_case_id: int, conn: sqlite3.Connection) -> int:
    """Count marks for a test case.

    Args:
        test_case_id: Test case ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Number of mark records for this test case
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_case_marks WHERE test_case_id = ?",
        (test_case_id,),
    )
    return int(cursor.fetchone()[0])


def get_marks(test_case_id: int, conn: sqlite3.Connection) -> dict[int, int]:
    """Get all marks for a test case.

    Args:
        test_case_id: Test case ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Dictionary mapping criterion_index to marks_awarded_human
    """
    cursor = conn.execute(
        """
        SELECT criterion_index, marks_awarded_human
        FROM test_case_marks
        WHERE test_case_id = ?
        ORDER BY criterion_index
        """,
        (test_case_id,),
    )
    return {int(row[0]): int(row[1]) for row in cursor.fetchall()}
