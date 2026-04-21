"""Repository for test_runs table and related verification queries.

Provides data access methods for test runs and extraction verification.
"""

import sqlite3


def exists(test_run_id: int, conn: sqlite3.Connection) -> bool:
    """Check if test run exists.

    Args:
        test_run_id: Test run ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        True if test run exists, False otherwise

    Example:
        >>> if test_runs.exists(test_run_id=1, conn):
        ...     print("Test run found")
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_runs WHERE id = ?",
        (test_run_id,),
    )
    count = cursor.fetchone()[0]
    return int(count) > 0


def count_executions_for_run(test_run_id: int, conn: sqlite3.Connection) -> int:
    """Count number of test question executions for a test run.

    Args:
        test_run_id: Test run ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Number of executions for this test run

    Example:
        >>> count = test_runs.count_executions_for_run(test_run_id=1, conn)
        >>> print(f"Found {count} executions")
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_question_executions WHERE test_run_id = ?",
        (test_run_id,),
    )
    return int(cursor.fetchone()[0])


def count_criterion_results_for_run(test_run_id: int, conn: sqlite3.Connection) -> int:
    """Count number of criterion results for a test run.

    Counts all criterion results across all executions in the test run.

    Args:
        test_run_id: Test run ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        Number of criterion results for this test run

    Example:
        >>> count = test_runs.count_criterion_results_for_run(test_run_id=1, conn)
        >>> print(f"Found {count} criterion results")
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM test_criterion_results tcr
        JOIN test_question_executions tqe ON tcr.test_question_execution_id = tqe.id
        WHERE tqe.test_run_id = ?
        """,
        (test_run_id,),
    )
    return int(cursor.fetchone()[0])


def get_executions_without_criteria(test_run_id: int, conn: sqlite3.Connection) -> list[int]:
    """Get execution IDs that have no criterion results.

    Used for verification - every execution should have at least one criterion result.

    Args:
        test_run_id: Test run ID
        conn: Database connection (to evaluation_results.db)

    Returns:
        List of execution IDs without criterion results (empty if all valid)

    Example:
        >>> orphans = test_runs.get_executions_without_criteria(test_run_id=1, conn)
        >>> if orphans:
        ...     print(f"Warning: Executions without criteria: {orphans}")
    """
    cursor = conn.execute(
        """
        SELECT tqe.id
        FROM test_question_executions tqe
        LEFT JOIN test_criterion_results tcr ON tcr.test_question_execution_id = tqe.id
        WHERE tqe.test_run_id = ?
        GROUP BY tqe.id
        HAVING COUNT(tcr.test_question_execution_id) = 0
        """,
        (test_run_id,),
    )
    return [int(row[0]) for row in cursor.fetchall()]


def create_test_run(
    test_suite_id: int,
    model_identifier: str,
    git_commit_hash: str,
    notes: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create test_run record in evaluation_results.db.

    Args:
        test_suite_id: Test suite ID
        model_identifier: LLM model identifier
        git_commit_hash: Git commit hash of code that ran the test
        notes: Optional notes for this test run
        conn: Database connection to evaluation_results.db

    Returns:
        test_run_id: Database ID of created test run

    Raises:
        ValueError: If failed to get test_run_id after INSERT

    Example:
        >>> test_run_id = test_runs.create_test_run(
        ...     test_suite_id=1,
        ...     model_identifier="claude-sonnet-4-5",
        ...     git_commit_hash="abc123def",
        ...     notes="Baseline test",
        ...     conn=conn
        ... )
    """
    cursor = conn.execute(
        """
        INSERT INTO test_runs (
            test_suite_id,
            model_identifier,
            git_commit_hash,
            notes
        ) VALUES (?, ?, ?, ?)
        """,
        (test_suite_id, model_identifier, git_commit_hash, notes),
    )

    test_run_id = cursor.lastrowid
    if test_run_id is None:
        raise ValueError("Failed to get test_run_id after INSERT")

    return test_run_id
