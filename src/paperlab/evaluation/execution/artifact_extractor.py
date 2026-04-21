"""Extract marking artifacts from test_execution.db to evaluation_results.db.

Performs bulk extraction of marking results from ephemeral test database
to permanent evaluation database before test database deletion.

Design principles:
- Bulk operations: Single INSERT-SELECT per table (no loops)
- Explicit correlation: Uses pre-built correlation mapping (no schema archaeology)
- Fail fast: Validates extraction completeness before commit
- All-or-nothing: Single transaction with verification

SQLite ATTACH/DETACH/COMMIT Protocol
-------------------------------------
When using ATTACH to merge databases for bulk operations:

1. Ensure no existing connections to the database being attached
   - SQLite cannot ATTACH a database with active connections from other Connection objects
   - Solution: Open/close connections in isolated scopes before ATTACH

2. Execute queries involving the attached database
   - Use ATTACHED_DB_ALIAS prefix for attached tables
   - Queries can span both databases in single SQL statement

3. COMMIT before DETACH
   - CRITICAL: SQLite cannot DETACH while uncommitted transactions involve attached tables
   - Any INSERT/UPDATE/DELETE on attached or local tables starts a transaction
   - Must call conn.commit() before DETACH or "database is locked" error occurs

4. DETACH the database
   - Only after commit, safe to DETACH
   - Releases file locks and connection resources

This protocol is enforced in _execute_with_attached_db() helper function.
"""

import sqlite3
from pathlib import Path
from typing import Protocol

from paperlab.config.constants import (
    DatabaseSettings,
    ImageSequence,
    MarkingAttemptStatus,
    Tables,
    TimeConversions,
)
from paperlab.data.repositories.evaluation import execution_correlation, test_runs
from paperlab.data.repositories.evaluation.execution_correlation import CorrelationData
from paperlab.utils.database import attach_database


class GitProvider(Protocol):
    """Protocol for getting git commit hash."""

    def get_commit_hash(self) -> str:
        """Get current git commit hash."""
        ...


def _execute_with_attached_db(
    evaluation_conn: sqlite3.Connection,
    test_execution_db_path: Path,
    query: str,
    params: tuple[int | str, ...],
) -> int:
    """Execute query with attached test_execution.db following ATTACH/COMMIT/DETACH protocol.

    This helper enforces the correct SQLite protocol documented in module docstring.
    See "SQLite ATTACH/DETACH/COMMIT Protocol" above for full details.

    Args:
        evaluation_conn: Connection to evaluation_results.db
        test_execution_db_path: Path to test_execution.db file
        query: SQL query to execute (should reference ATTACHED_DB_ALIAS)
        params: Query parameters tuple (can contain int or str values)

    Returns:
        Number of rows affected (cursor.rowcount)

    Raises:
        sqlite3.Error: If any database operation fails
    """
    with attach_database(
        evaluation_conn, test_execution_db_path, DatabaseSettings.ATTACHED_TEST_DB_ALIAS
    ):
        cursor = evaluation_conn.execute(query, params)
        rowcount = cursor.rowcount

        # Protocol step 3: COMMIT before DETACH (see module docstring)
        evaluation_conn.commit()

        return rowcount


def extract_test_execution_artifacts(
    test_suite_id: int,
    model_identifier: str,
    git_provider: GitProvider,
    correlation_data: CorrelationData,
    test_execution_db_path: Path,
    evaluation_conn: sqlite3.Connection,
    notes: str | None = None,
) -> int:
    """Extract all marking artifacts from test_execution.db to evaluation_results.db.

    Bulk extraction strategy:
    1. Create correlation table in test_execution.db (metadata about source data)
    2. Create test_run record in evaluation_results.db
    3. Bulk extract marking_attempts (successful) → test_question_executions (using correlation)
    4. Bulk extract question_marking_results → test_criterion_results (using correlation)
    5. Verify extraction completeness
    6. Drop correlation table from test_execution.db

    Key insight: We already know the correlation mapping from submission building,
    so we store it as metadata in test_execution.db and use simple JOINs instead
    of complex schema archaeology. The correlation uses first image path to find
    submission → marking attempt.

    Disaster recovery behavior:
    - On failure: evaluation_results.db unchanged (transaction rollback)
    - On failure: test_execution.db preserved with all marking results
    - Retry strategy: Call this function again with same test_execution.db
                     (creates new test_run_id for each attempt)
    - Idempotency: Safe to retry - each attempt is independent test run
    - Cleanup: Caller must delete test_execution.db after successful extraction
    - Cost protection: Never deletes expensive LLM results without successful extraction

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        model_identifier: LLM model identifier (e.g., "claude-sonnet-4-5")
        git_provider: Provider for git commit hash
        correlation_data: Pre-built mapping of (question_id, test_case_id, first_image_path)
                         from submission building phase
        test_execution_db_path: Path to test_execution.db file
        evaluation_conn: Connection to evaluation_results.db (write)
        notes: Optional notes for this test run

    Returns:
        test_run_id: Database ID of created test run

    Raises:
        ValueError: If extraction verification fails
        sqlite3.Error: If database operations fail

    Example:
        >>> from paperlab.data.evaluation_database import evaluation_connection
        >>> from pathlib import Path
        >>>
        >>> correlation_data = [(1, 42, "path/to/image.png"), ...]
        >>> test_db_path = Path("data/db/test_execution.db")
        >>> with evaluation_connection() as eval_conn:
        ...     test_run_id = extract_test_execution_artifacts(
        ...         test_suite_id=1,
        ...         model_identifier="claude-sonnet-4-5",
        ...         git_provider=git_provider,
        ...         correlation_data=correlation_data,
        ...         test_execution_db_path=test_db_path,
        ...         evaluation_conn=eval_conn
        ...     )
    """
    # Validate inputs before expensive operations
    if not correlation_data:
        raise ValueError(
            "Cannot extract - correlation_data is empty.\n"
            "This indicates no marking requests were built.\n"
            "\n"
            "Possible causes:\n"
            "  - Test suite has no test cases\n"
            "  - Request building failed silently\n"
            "  - All test cases filtered out during request building"
        )

    # Get git commit hash
    git_commit_hash = git_provider.get_commit_hash()

    try:
        # Step 1: Create correlation table in test_execution.db (metadata about source data)
        # CRITICAL: Must open/close test_execution.db connection BEFORE attaching
        # SQLite cannot ATTACH a database that has active connections
        from paperlab.data.database import connection

        with connection(test_execution_db_path) as test_conn:
            execution_correlation.create_correlation_table(correlation_data, test_conn)
            test_conn.commit()

        # Step 2: Create test run record
        test_run_id = test_runs.create_test_run(
            test_suite_id=test_suite_id,
            model_identifier=model_identifier,
            git_commit_hash=git_commit_hash,
            notes=notes,
            conn=evaluation_conn,
        )

        # Step 3: Bulk extract executions (all marking_attempts)
        execution_count = _bulk_extract_executions(
            test_run_id=test_run_id,
            test_execution_db_path=test_execution_db_path,
            evaluation_conn=evaluation_conn,
        )

        # Step 4: Bulk extract criterion results (all question_marking_results)
        criterion_count = _bulk_extract_criterion_results(
            test_run_id=test_run_id,
            test_execution_db_path=test_execution_db_path,
            evaluation_conn=evaluation_conn,
        )

        # Step 5: Verify extraction completeness
        _verify_extraction(
            test_run_id=test_run_id,
            expected_executions=execution_count,
            expected_criteria=criterion_count,
            evaluation_conn=evaluation_conn,
        )

        # Step 6: Commit evaluation_conn transaction
        evaluation_conn.commit()

        return test_run_id

    except Exception:
        # Rollback evaluation_results.db to clean state (all-or-nothing extraction)
        # Note: test_execution.db correlation table remains intact for retry (committed in Step 1)
        evaluation_conn.rollback()
        raise


def _bulk_extract_executions(
    test_run_id: int,
    test_execution_db_path: Path,
    evaluation_conn: sqlite3.Connection,
) -> int:
    """Bulk extract ALL successful marking_attempts → test_question_executions.

    Uses ATTACH to access test_execution.db from evaluation_conn,
    then single INSERT-SELECT to copy all rows with proper mapping.

    Mapping strategy:
    - Uses pre-built execution_correlation table in test_execution.db
    - Direct lookup: (question_id, first_image_path) → test_case_id
    - Correlate via: submission_images (first_image) → question_submissions →
      marking_attempts (successful only)
    - Same-database JOINs within test_execution.db (optimal performance)
    - No complex cross-schema archaeology required

    Args:
        test_run_id: Test run ID from evaluation_results.db
        test_execution_db_path: Path to test_execution.db file
        evaluation_conn: Connection to evaluation_results.db

    Returns:
        Number of executions extracted (rowcount)

    Raises:
        sqlite3.Error: If extraction fails
    """
    query = f"""
        INSERT INTO test_question_executions (
            test_run_id,
            test_case_id,
            system_prompt,
            user_prompt,
            llm_response,
            input_tokens,
            output_tokens,
            response_time_seconds
        )
        SELECT
            ? AS test_run_id,
            ec.test_case_id,
            ma.system_prompt,
            ma.user_prompt,
            ma.response_received,
            ma.input_tokens,
            ma.output_tokens,
            ma.processing_time_ms / {TimeConversions.MS_TO_SECONDS}
        FROM {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.marking_attempts ma
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.question_submissions qs ON
            qs.id = ma.submission_id
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.submission_images si ON
            si.submission_id = qs.id
            AND si.image_sequence = {ImageSequence.FIRST}
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.{Tables.EXECUTION_CORRELATION} ec ON
            ec.question_id = qs.question_id
            AND ec.first_image_path = si.image_path
        WHERE ma.status = ?
        ORDER BY ma.attempted_at DESC, ma.id DESC
        """

    return _execute_with_attached_db(
        evaluation_conn=evaluation_conn,
        test_execution_db_path=test_execution_db_path,
        query=query,
        params=(test_run_id, MarkingAttemptStatus.SUCCESS),
    )


def _bulk_extract_criterion_results(
    test_run_id: int,
    test_execution_db_path: Path,
    evaluation_conn: sqlite3.Connection,
) -> int:
    """Bulk extract ALL question_marking_results → test_criterion_results.

    Mapping strategy:
    - Map mark_criteria_id → criterion_index via mark_criteria JOIN
    - Map marking_attempt_id → test_question_execution_id via correlation
    - Uses pre-built execution_correlation table in test_execution.db
    - Correlate via: question_marking_results → marking_attempts → question_submissions →
      submission_images (first_image) → execution_correlation
    - All source data (qmr, mc, ma, qs, si, ec) in same database for optimal performance

    Args:
        test_run_id: Test run ID from evaluation_results.db
        test_execution_db_path: Path to test_execution.db file
        evaluation_conn: Connection to evaluation_results.db

    Returns:
        Number of criterion results extracted (rowcount)

    Raises:
        sqlite3.Error: If extraction fails
    """
    query = f"""
        INSERT INTO test_criterion_results (
            test_question_execution_id,
            criterion_index,
            marks_awarded_predicted,
            feedback,
            confidence_score
        )
        SELECT
            tqe.id AS test_question_execution_id,
            mc.criterion_index,
            qmr.marks_awarded,
            qmr.feedback,
            qmr.confidence_score
        FROM {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.question_marking_results qmr
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.mark_criteria mc
            ON qmr.mark_criteria_id = mc.id
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.marking_attempts ma
            ON qmr.marking_attempt_id = ma.id
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.question_submissions qs
            ON ma.submission_id = qs.id
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.submission_images si ON
            si.submission_id = qs.id
            AND si.image_sequence = {ImageSequence.FIRST}
        JOIN {DatabaseSettings.ATTACHED_TEST_DB_ALIAS}.{Tables.EXECUTION_CORRELATION} ec ON
            ec.question_id = qs.question_id
            AND ec.first_image_path = si.image_path
        JOIN test_question_executions tqe ON
            tqe.test_run_id = ?
            AND tqe.test_case_id = ec.test_case_id
        WHERE ma.status = ?
        ORDER BY tqe.id, mc.criterion_index
        """

    return _execute_with_attached_db(
        evaluation_conn=evaluation_conn,
        test_execution_db_path=test_execution_db_path,
        query=query,
        params=(test_run_id, MarkingAttemptStatus.SUCCESS),
    )


def _verify_extraction(
    test_run_id: int,
    expected_executions: int,
    expected_criteria: int,
    evaluation_conn: sqlite3.Connection,
) -> None:
    """Verify extraction completeness before commit.

    Checks:
    0. Expected counts are non-zero (sanity check)
    1. Test run record exists
    2. Execution count matches expected
    3. Criterion results count matches expected
    4. Each execution has at least one criterion result

    Args:
        test_run_id: Test run ID
        expected_executions: Expected number of executions
        expected_criteria: Expected number of criterion results
        evaluation_conn: Connection to evaluation_results.db

    Raises:
        ValueError: If verification fails
    """
    # 0. CRITICAL: Detect 0-row extraction (indicates JOIN failure)
    if expected_executions == 0 or expected_criteria == 0:
        raise ValueError(
            f"Extraction produced 0 rows (executions: {expected_executions}, "
            f"criteria: {expected_criteria}).\n"
            "This indicates a critical failure in the extraction queries.\n"
            "\n"
            "Common causes:\n"
            "  - Correlation table is empty or has incorrect data\n"
            "  - JOIN conditions don't match any rows in test_execution.db\n"
            "  - test_execution.db has no marking results to extract\n"
            "  - Image paths in correlation don't match submission_images\n"
            "  - No successful marking attempts (status='success')\n"
            "\n"
            "The test_execution.db will be preserved for debugging.\n"
            "Check correlation table: SELECT * FROM execution_correlation LIMIT 5;\n"
            "Check marking results: SELECT COUNT(*) FROM marking_attempts WHERE status='success';"
        )

    # 1. Verify test run exists
    if not test_runs.exists(test_run_id, evaluation_conn):
        raise ValueError(
            f"Test run {test_run_id} not found after INSERT. "
            "Storage operation may have failed silently."
        )

    # 2. Verify execution count
    actual_executions = test_runs.count_executions_for_run(test_run_id, evaluation_conn)
    if actual_executions != expected_executions:
        raise ValueError(
            f"Execution count mismatch for test run {test_run_id}: "
            f"expected {expected_executions}, got {actual_executions}. "
            "Bulk extraction may have failed partially."
        )

    # 3. Verify criterion results count
    actual_criteria = test_runs.count_criterion_results_for_run(test_run_id, evaluation_conn)
    if actual_criteria != expected_criteria:
        raise ValueError(
            f"Criterion results count mismatch for test run {test_run_id}: "
            f"expected {expected_criteria}, got {actual_criteria}. "
            "Bulk extraction may have failed partially."
        )

    # 4. Verify each execution has at least one criterion result
    execution_ids = test_runs.get_executions_without_criteria(test_run_id, evaluation_conn)
    if execution_ids:
        raise ValueError(
            f"Found {len(execution_ids)} executions without criterion results: {execution_ids}. "
            "Each execution must have at least one criterion result."
        )
