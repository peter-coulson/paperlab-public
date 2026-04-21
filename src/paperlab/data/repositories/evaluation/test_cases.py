"""Repository for test_cases table.

Provides data access methods for test cases in evaluation_results.db.
"""

import sqlite3
from dataclasses import dataclass

from paperlab.config import ErrorMessages


@dataclass
class TestCaseKey:
    """Natural key for a test case (paper + question)."""

    paper_identifier: str
    question_number: int


def create_test_case(
    test_case_json_path: str,
    paper_identifier: str,
    question_number: int,
    validation_type_id: int,
    notes: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create test case record with JSON path as natural key.

    Does NOT commit - caller manages transaction.

    Args:
        test_case_json_path: Logical path to JSON (relative to project root)
        paper_identifier: Paper identifier
            (e.g., 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08')
        question_number: Question number within the paper
        validation_type_id: Validation type ID from validation_types table
        notes: Optional notes about this test case
        conn: Database connection (to evaluation_results.db)

    Returns:
        test_case_id

    Raises:
        ValueError: If failed to get test_case_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO test_cases (
            test_case_json_path,
            paper_identifier,
            question_number,
            validation_type_id,
            notes
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (test_case_json_path, paper_identifier, question_number, validation_type_id, notes),
    )

    test_case_id = cursor.lastrowid
    if test_case_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="test_case"))
    return test_case_id


def test_case_exists(test_case_id: int, conn: sqlite3.Connection) -> bool:
    """Check if test case exists.

    Args:
        test_case_id: Test case ID to check
        conn: Database connection (to evaluation_results.db)

    Returns:
        True if test case exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_cases WHERE id = ?",
        (test_case_id,),
    )
    count = int(cursor.fetchone()[0])
    return count == 1


def test_case_exists_by_json_path(json_path: str, conn: sqlite3.Connection) -> bool:
    """Check if test case exists by JSON path.

    Args:
        json_path: Test case JSON path (logical path, relative to project root)
        conn: Database connection (to evaluation_results.db)

    Returns:
        True if test case with this JSON path exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT 1 FROM test_cases WHERE test_case_json_path = ?",
        (json_path,),
    )
    return cursor.fetchone() is not None


def get_by_id(
    test_case_id: int,
    conn: sqlite3.Connection,
) -> dict[str, int | str | None] | None:
    """Get test case by ID.

    Args:
        test_case_id: Test case ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Test case record with keys: id, test_case_json_path, paper_identifier,
        question_number, validation_type_id, notes, created_at
        Returns None if not found
    """
    cursor = conn.execute(
        """
        SELECT
            id,
            test_case_json_path,
            paper_identifier,
            question_number,
            validation_type_id,
            notes,
            created_at
        FROM test_cases
        WHERE id = ?
        """,
        (test_case_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return dict(row)


def get_by_json_path(
    json_path: str,
    conn: sqlite3.Connection,
) -> dict[str, int | str | None] | None:
    """Get test case by JSON path (natural key lookup).

    Args:
        json_path: Test case JSON path (logical path, relative to project root)
        conn: Database connection (to evaluation_results.db)

    Returns:
        Test case record with keys: id, test_case_json_path, paper_identifier,
        question_number, validation_type_id, notes, created_at
        Returns None if not found
    """
    cursor = conn.execute(
        """
        SELECT
            id,
            test_case_json_path,
            paper_identifier,
            question_number,
            validation_type_id,
            notes,
            created_at
        FROM test_cases
        WHERE test_case_json_path = ?
        """,
        (json_path,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return dict(row)


def count_all(conn: sqlite3.Connection) -> int:
    """Count all test cases in database.

    Args:
        conn: Database connection (to evaluation_results.db)

    Returns:
        Total number of test cases

    Note:
        Used to check if any test cases exist before
        allowing deletion of validation types (FK protection).
    """
    cursor = conn.execute("SELECT COUNT(*) FROM test_cases")
    return int(cursor.fetchone()[0])


def delete_test_case(test_case_id: int, conn: sqlite3.Connection) -> None:
    """Delete test case and all associated marks.

    Args:
        test_case_id: Database ID of test case to delete
        conn: Database connection (to evaluation_results.db)

    Raises:
        ValueError: If test case not found
    """
    # Check test case exists
    if not test_case_exists(test_case_id, conn):
        raise ValueError(f"Test case ID {test_case_id} not found")

    # Delete test case marks first (child records)
    conn.execute("DELETE FROM test_case_marks WHERE test_case_id = ?", (test_case_id,))

    # Delete test case
    conn.execute("DELETE FROM test_cases WHERE id = ?", (test_case_id,))


def get_sanity_cases_by_validation_type(
    validation_type_id: int,
    conn: sqlite3.Connection,
) -> list[TestCaseKey]:
    """Get all test cases for a specific validation type.

    Args:
        validation_type_id: Validation type ID to filter by
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of test case keys (paper_identifier, question_number)

    Note:
        Used for audit workflows to find existing test cases.
    """
    cursor = conn.execute(
        """
        SELECT DISTINCT paper_identifier, question_number
        FROM test_cases
        WHERE validation_type_id = ?
        ORDER BY paper_identifier, question_number
        """,
        (validation_type_id,),
    )

    return [
        TestCaseKey(paper_identifier=row[0], question_number=row[1]) for row in cursor.fetchall()
    ]


def get_json_paths_by_folder(folder_pattern: str, conn: sqlite3.Connection) -> list[str]:
    """Get all JSON paths matching a folder pattern.

    Used for bulk loading to identify which test cases are already loaded.

    Args:
        folder_pattern: SQL LIKE pattern for folder path
            (e.g., 'data/evaluation/test_cases/pearson-edexcel/gcse/mathematics/%')
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of JSON paths already loaded from matching folders

    Example:
        >>> pattern = 'data/evaluation/test_cases/pearson-edexcel/gcse/mathematics/%'
        >>> loaded_paths = get_json_paths_by_folder(pattern, conn)
        >>> # Returns all JSON paths starting with the pattern
    """
    cursor = conn.execute(
        "SELECT test_case_json_path FROM test_cases WHERE test_case_json_path LIKE ?",
        (folder_pattern,),
    )
    return [row[0] for row in cursor.fetchall()]
