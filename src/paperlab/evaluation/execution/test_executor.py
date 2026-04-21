"""Test execution orchestration helpers for running marking tests.

Provides orchestration functions that receive database connections as parameters.
Connection lifecycle is managed by the CLI layer (eval.py).

Design principles:
- Pure orchestration - receives connections as parameters
- No connection management - CLI layer controls transaction boundaries
- Error handling - raises descriptive exceptions for CLI to handle
- Idempotency - safe to retry phases independently

Note: Connection management follows Pattern A (CLI opens connections).
See CLAUDE.md for architectural guidelines.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from paperlab.config import DatabaseSettings
from paperlab.data.repositories.evaluation import test_suites
from paperlab.data.repositories.evaluation.execution_correlation import CorrelationData
from paperlab.data.repositories.marking import llm_models, students
from paperlab.evaluation.execution.artifact_extractor import extract_test_execution_artifacts
from paperlab.evaluation.execution.request_builder import build_submissions_and_correlation
from paperlab.evaluation.execution.test_database import (
    create_test_execution_db,
    delete_test_execution_db,
)
from paperlab.evaluation.execution.test_execution_loader import load_test_execution_data
from paperlab.marking.batch_marker import BatchMarker, BatchMarkingResult
from paperlab.services.client_factory import get_client_for_provider
from paperlab.utils.git import GitProvider

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class TestSuiteMetadata:
    """Metadata about test suite for orchestration.

    Attributes:
        test_suite_id: ID from evaluation_results.db
        test_suite_name: Human-readable name
        test_db_path: Path to ephemeral test_execution.db
        student_id: Test student ID in test_execution.db
    """

    test_suite_id: int
    test_suite_name: str
    test_db_path: Path
    student_id: int


@dataclass
class MarkingPhaseResult:
    """Results from marking phase execution.

    Attributes:
        submission_ids: Submission IDs that were marked
        correlation_data: Correlation data for mapping results to test cases
        result: Batch marking result (success/failure counts)
        model_id: LLM model ID from database
        provider: LLM provider name
    """

    submission_ids: list[int]
    correlation_data: CorrelationData
    result: BatchMarkingResult
    model_id: int
    provider: str


# ============================================================================
# Phase 1: Setup and Validation
# ============================================================================


def validate_test_suite_exists(
    test_suite_id: int,
    eval_conn: sqlite3.Connection,
) -> str:
    """Validate test suite exists and return its name.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        eval_conn: Connection to evaluation_results.db

    Returns:
        Test suite name

    Raises:
        ValueError: If test suite doesn't exist
    """
    suite = test_suites.get_by_id(test_suite_id, eval_conn)
    return str(suite["name"])


def setup_test_database(test_db_path: Path) -> int:
    """Create ephemeral test database with schema and test student.

    Args:
        test_db_path: Path where test database should be created

    Returns:
        student_id for test student in created database

    Raises:
        FileExistsError: If database already exists at path
        sqlite3.Error: If database creation fails
    """
    return create_test_execution_db(test_db_path)


# ============================================================================
# Phase 2: Data Loading
# ============================================================================


def load_test_data_phase(
    test_suite_id: int,
    eval_conn: sqlite3.Connection,
    test_conn: sqlite3.Connection,
) -> None:
    """Load required data into test database (papers, marks, configs).

    Delegates to test_execution_loader which handles resolution and loading.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        eval_conn: Connection to evaluation_results.db (read-only)
        test_conn: Connection to test_execution.db (write)

    Raises:
        ValueError: If test suite has no test cases
        FileNotFoundError: If required JSON files missing
        sqlite3.Error: If loading fails
    """
    load_test_execution_data(
        test_suite_id=test_suite_id,
        evaluation_conn=eval_conn,
        test_execution_conn=test_conn,
    )


# ============================================================================
# Phase 3: Submission Building
# ============================================================================


def build_submissions_phase(
    test_suite_id: int,
    model_identifier: str,
    student_id: int,
    eval_conn: sqlite3.Connection,
    test_conn: sqlite3.Connection,
) -> tuple[list[int], CorrelationData, int, str]:
    """Build submissions and correlation data.

    Creates all submissions for test suite in test_execution.db.
    This is Phase A of the two-phase marking workflow.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        model_identifier: LLM model identifier (e.g., "claude-sonnet-4-5-20250929")
        student_id: Test student ID from test_execution.db
        eval_conn: Connection to evaluation_results.db (read-only)
        test_conn: Connection to test_execution.db (write)

    Returns:
        Tuple of (submission_ids, correlation_data, model_id, provider)
        - submission_ids: List of submission IDs created in test_execution.db
        - correlation_data: Correlation data for mapping results to test cases
        - model_id: LLM model ID from database
        - provider: LLM provider name (e.g., "anthropic", "openai")

    Raises:
        ValueError: If model not found
        sqlite3.Error: If database queries fail
    """
    # Get model info for client creation
    model_info = llm_models.get_by_identifier(model_identifier, test_conn)
    model_id = int(model_info["id"])
    provider = str(model_info["provider"])

    # Build submissions (Phase A)
    submission_ids, correlation_data = build_submissions_and_correlation(
        test_suite_id=test_suite_id,
        student_id=student_id,
        eval_conn=eval_conn,
        test_conn=test_conn,
    )

    return submission_ids, correlation_data, model_id, provider


# ============================================================================
# Phase 4: Marking Execution
# ============================================================================


def execute_marking_phase(
    submission_ids: list[int],
    model_id: int,
    model_identifier: str,
    provider: str,
    test_db_path: Path,
    progress_callback: "Callable[[int, int], None] | None" = None,
) -> BatchMarkingResult:
    """Execute batch marking with progress reporting.

    This is Phase B of the two-phase marking workflow.
    Submissions must already exist (created in Phase A).

    Note: BatchMarker manages its own connections (one per worker thread).
    This is correct for thread safety and should not be changed.

    Args:
        submission_ids: Submission IDs to mark (from test_execution.db)
        model_id: LLM model ID from database
        model_identifier: LLM model identifier
        provider: LLM provider name (for client creation)
        test_db_path: Path to test_execution.db for marking
        progress_callback: Optional callback(completed, total) for progress updates

    Returns:
        BatchMarkingResult with success/failure counts and timing

    Raises:
        ValueError: If submission_ids empty or client creation fails
        Exception: If marking fails (partial results preserved in database)
    """
    # Create LLM client
    llm_client = get_client_for_provider(provider, model_identifier)

    # Execute batch marking (Phase B)
    # Note: BatchMarker creates one connection per worker thread for thread safety
    batch_marker = BatchMarker(llm_client)
    result = batch_marker.mark_batch(
        submission_ids=submission_ids,
        llm_model_id=model_id,
        progress_callback=progress_callback,
        db_path=test_db_path,
    )

    return result


# ============================================================================
# Phase 5: Artifact Extraction
# ============================================================================


def extract_results_phase(
    test_suite_id: int,
    model_identifier: str,
    correlation_data: CorrelationData,
    test_db_path: Path,
    eval_conn: sqlite3.Connection,
    notes: str | None = None,
) -> int:
    """Extract marking results to evaluation database.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        model_identifier: LLM model identifier
        correlation_data: Correlation data for mapping results to test cases
        test_db_path: Path to test_execution.db file
        eval_conn: Connection to evaluation_results.db (write)
        notes: Optional notes for this test run

    Returns:
        test_run_id from evaluation_results.db

    Raises:
        ValueError: If validation fails
        sqlite3.Error: If extraction fails
    """
    git_provider = GitProvider()

    test_run_id = extract_test_execution_artifacts(
        test_suite_id=test_suite_id,
        model_identifier=model_identifier,
        git_provider=git_provider,
        correlation_data=correlation_data,
        test_execution_db_path=test_db_path,
        evaluation_conn=eval_conn,
        notes=notes,
    )

    return test_run_id


# ============================================================================
# Phase 6: Cleanup
# ============================================================================


def cleanup_test_database(test_db_path: Path) -> None:
    """Delete ephemeral test database.

    Only call after successful extraction to avoid losing expensive LLM results.

    Args:
        test_db_path: Path to test_execution.db to delete

    Raises:
        FileNotFoundError: If database doesn't exist
        OSError: If deletion fails
    """
    delete_test_execution_db(test_db_path)


# ============================================================================
# Retry Helpers
# ============================================================================


def rebuild_correlation_data(
    test_suite_id: int,
    student_id: int,
    eval_conn: sqlite3.Connection,
    test_conn: sqlite3.Connection,
) -> CorrelationData:
    """Rebuild correlation data from preserved test database.

    Used for retry-extraction to reconstruct the mapping without re-marking.
    Submissions must already exist in test database.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        student_id: Test student ID from preserved test database
        eval_conn: Connection to evaluation_results.db (read-only)
        test_conn: Connection to test_execution.db (read-only)

    Returns:
        Correlation data for mapping results to test cases

    Raises:
        sqlite3.Error: If database queries fail
    """
    # Rebuild correlation using existing submissions (retry-extraction mode)
    # CRITICAL: Must use skip_existing=True to avoid IntegrityError
    _, correlation_data = build_submissions_and_correlation(
        test_suite_id=test_suite_id,
        student_id=student_id,
        eval_conn=eval_conn,
        test_conn=test_conn,
        skip_existing=True,  # Reuse existing submissions
    )

    return correlation_data


def get_test_student_id(test_conn: sqlite3.Connection) -> int:
    """Get test student ID from test database.

    Args:
        test_conn: Connection to test_execution.db

    Returns:
        student_id for test student

    Raises:
        ValueError: If test student not found
    """
    student_id = students.get_by_supabase_uid(DatabaseSettings.TEST_STUDENT_SUPABASE_UID, test_conn)
    if student_id is None:
        raise ValueError("Test student not found in test database")
    return student_id
