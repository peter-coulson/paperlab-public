"""Repository for test_suite_cases table.

Provides data access methods for many-to-many test suite/case associations.
"""

import sqlite3


def get_test_case_ids_batch(
    json_paths: list[str],
    conn: sqlite3.Connection,
) -> dict[str, int]:
    """Get test case IDs by JSON paths.

    Args:
        json_paths: List of test case JSON paths (natural keys)
        conn: Database connection

    Returns:
        Dict mapping json_path → test_case_id
    """
    if not json_paths:
        return {}

    placeholders = ",".join("?" * len(json_paths))
    cursor = conn.execute(
        f"""
        SELECT test_case_json_path, id
        FROM test_cases
        WHERE test_case_json_path IN ({placeholders})
        """,
        json_paths,
    )

    return {row[0]: row[1] for row in cursor.fetchall()}


def create_suite_case_associations_batch(
    test_suite_id: int,
    test_case_ids: list[int],
    conn: sqlite3.Connection,
) -> None:
    """Create multiple test suite-case associations in one batch.

    Does NOT commit - caller manages transaction.

    Args:
        test_suite_id: Test suite ID
        test_case_ids: List of test case IDs to associate with the suite
        conn: Database connection (to evaluation_results.db)

    Raises:
        sqlite3.IntegrityError: If association already exists (duplicate)
    """
    # Prepare batch data: list of (test_suite_id, test_case_id)
    batch_data = [(test_suite_id, test_case_id) for test_case_id in test_case_ids]

    conn.executemany(
        """
        INSERT INTO test_suite_cases (test_suite_id, test_case_id)
        VALUES (?, ?)
        """,
        batch_data,
    )


def count_suite_cases(test_suite_id: int, conn: sqlite3.Connection) -> int:
    """Count test cases in a suite.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Number of test cases associated with this suite
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_suite_cases WHERE test_suite_id = ?",
        (test_suite_id,),
    )
    return int(cursor.fetchone()[0])


def get_test_cases_for_suite(
    test_suite_id: int, conn: sqlite3.Connection
) -> list[dict[str, int | str]]:
    """Get all test case details for a suite.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of test case records with keys:
            - id: test_case_id
            - test_case_json_path: JSON path
            - paper_identifier: paper identifier
            - question_number: question number
            - validation_type_id: validation type ID
            - notes: notes
    """
    cursor = conn.execute(
        """
        SELECT
            tc.id,
            tc.test_case_json_path,
            tc.paper_identifier,
            tc.question_number,
            tc.validation_type_id,
            tc.notes
        FROM test_cases tc
        JOIN test_suite_cases tsc ON tc.id = tsc.test_case_id
        WHERE tsc.test_suite_id = ?
        ORDER BY tc.test_case_json_path
        """,
        (test_suite_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_unique_paper_identifiers_for_suite(
    test_suite_id: int, conn: sqlite3.Connection
) -> list[str]:
    """Get unique paper identifiers required by a test suite.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of unique paper identifiers, sorted alphabetically

    Example:
        >>> paper_ids = get_unique_paper_identifiers_for_suite(suite_id, conn)
        >>> # Returns: ["PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08", ...]
    """
    cursor = conn.execute(
        """
        SELECT DISTINCT tc.paper_identifier
        FROM test_cases tc
        JOIN test_suite_cases tsc ON tc.id = tsc.test_case_id
        WHERE tsc.test_suite_id = ?
        ORDER BY tc.paper_identifier
        """,
        (test_suite_id,),
    )
    return [row[0] for row in cursor.fetchall()]


def delete_suite_associations(test_suite_id: int, conn: sqlite3.Connection) -> None:
    """Delete all test case associations for a suite.

    Does NOT commit - caller manages transaction.

    Args:
        test_suite_id: Test suite ID
        conn: Database connection (to evaluation_results.db)
    """
    conn.execute(
        "DELETE FROM test_suite_cases WHERE test_suite_id = ?",
        (test_suite_id,),
    )
