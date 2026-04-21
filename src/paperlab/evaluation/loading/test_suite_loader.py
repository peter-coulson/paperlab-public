"""Orchestrate test suite loading from JSON into evaluation_results.db.

This module coordinates the workflow for loading test suites:
- Parse and validate JSON input (Pydantic models)
- Validate business rules (validators)
- Create database records (repositories)

Transaction management:
- Wraps all database operations in a single transaction
- Commits on success, rolls back on any exception
- Caller must manage connection lifecycle (use context manager)
"""

import sqlite3

from paperlab.data.repositories.evaluation import test_suite_cases, test_suites
from paperlab.evaluation.loading.suite_diff_calculator import SuiteDiff, SuiteDiffCalculator
from paperlab.evaluation.models import TestSuiteInput
from paperlab.evaluation.validators import validate_test_suite
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import ensure_entity_does_not_exist, handle_update_mode


def _lookup_test_suite_by_name(
    suite: TestSuiteInput, conn: sqlite3.Connection
) -> dict[str, int | str | None] | None:
    """Look up test suite by its natural key (name).

    Args:
        suite: Test suite input with name
        conn: Database connection

    Returns:
        Test suite record or None if not found
    """
    return test_suites.get_by_name(suite.name, conn)


def _parse_suite_json(test_suite_json_path: str) -> TestSuiteInput:
    """Parse and validate test suite JSON file.

    Args:
        test_suite_json_path: Path to test suite JSON file

    Returns:
        Validated TestSuiteInput model

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
    """
    return load_and_parse_json(test_suite_json_path, TestSuiteInput)


def _handle_replace_mode(
    test_suite: TestSuiteInput,
    evaluation_conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, SuiteDiff]:
    """Handle replace mode for existing test suite.

    Args:
        test_suite: Test suite from JSON
        evaluation_conn: Connection to evaluation_results.db
        force: If True, skip confirmation prompts

    Returns:
        Tuple of (should_proceed, diff)
        - should_proceed: True if should continue with insert, False if no changes
        - diff: Calculated differences

    Raises:
        ValueError: If suite doesn't exist or user cancels operation
    """
    # Diff calculator
    diff_calculator = SuiteDiffCalculator()

    # Delete function
    def delete_suite(suite_id: int, conn: sqlite3.Connection) -> None:
        test_suites.delete_suite(suite_id, conn)

    # Use generic update framework
    should_proceed, diff = handle_update_mode(
        json_entity=test_suite,
        natural_key_lookup=_lookup_test_suite_by_name,
        diff_calculator=diff_calculator,
        delete_func=delete_suite,
        conn=evaluation_conn,
        force=force,
    )
    # Type narrowing: diff_calculator returns SuiteDiff
    if not isinstance(diff, SuiteDiff):
        raise TypeError(f"Expected SuiteDiff, got {type(diff)}")
    return should_proceed, diff


def _create_suite_and_associations(
    test_suite: TestSuiteInput,
    evaluation_conn: sqlite3.Connection,
) -> int:
    """Create test suite record and associations with test cases.

    Args:
        test_suite: Test suite from JSON
        evaluation_conn: Connection to evaluation_results.db

    Returns:
        test_suite_id

    Raises:
        ValueError: If validation fails or test cases not found
    """
    # Validate business rules
    validate_test_suite(test_suite, evaluation_conn)

    # Create test suite record
    test_suite_id = test_suites.create_test_suite(
        test_suite.name,
        test_suite.description,
        evaluation_conn,
    )

    # Lookup test case IDs from JSON paths (single batch query)
    path_to_id = test_suite_cases.get_test_case_ids_batch(
        test_suite.test_case_json_paths, evaluation_conn
    )

    # Check all paths were found (defensive - validation should catch this)
    missing_paths = set(test_suite.test_case_json_paths) - set(path_to_id.keys())
    if missing_paths:
        raise ValueError(f"Test cases not found for JSON paths: {sorted(missing_paths)}")

    # Preserve order from JSON
    test_case_ids = [path_to_id[path] for path in test_suite.test_case_json_paths]

    # Batch insert suite-case associations
    test_suite_cases.create_suite_case_associations_batch(
        test_suite_id,
        test_case_ids,
        evaluation_conn,
    )

    # Verify loaded data BEFORE committing
    verify_test_suite_loaded(test_suite_id, len(test_case_ids), evaluation_conn)

    return test_suite_id


def load_test_suite(
    test_suite_json_path: str,
    evaluation_conn: sqlite3.Connection,
    replace: bool = False,
    force: bool = False,
) -> int:
    """Load test suite from JSON into evaluation_results.db.

    Args:
        test_suite_json_path: Path to test suite JSON file
        evaluation_conn: Connection to evaluation_results.db (transaction managed by this function)
        replace: If True and suite exists, replace test case associations
        force: If True, skip confirmation prompts (for CI/automation)

    Returns:
        test_suite_id

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails or user cancels operation
        sqlite3.Error: If database operations fail

    Workflow (create mode):
        1. Parse and validate JSON (Pydantic)
        2. Check suite doesn't exist
        3. Create test suite record and associations
        4. Commit transaction
        5. Return test_suite_id

    Workflow (replace mode):
        1. Parse and validate JSON (Pydantic)
        2. Check suite exists
        3. Calculate diff between JSON and database
        4. If removals detected, prompt for confirmation (unless force=True)
        5. Delete existing suite (CASCADE deletes associations)
        6. Create test suite record and associations
        7. Commit transaction
        8. Return test_suite_id
    """
    # Parse and validate JSON
    test_suite = _parse_suite_json(test_suite_json_path)

    try:
        # Handle replace mode
        if replace:
            should_proceed, diff = _handle_replace_mode(test_suite, evaluation_conn, force)

            # Early return if no changes
            if not should_proceed:
                evaluation_conn.commit()
                # Need to get existing suite ID for return
                existing_suite = test_suites.get_by_name(test_suite.name, evaluation_conn)
                if existing_suite is None:
                    raise ValueError(f"Test suite not found after update: {test_suite.name}")
                test_suite_id = existing_suite["id"]
                if not isinstance(test_suite_id, int):
                    raise TypeError(f"Test suite ID must be an integer, got {type(test_suite_id)}")
                return test_suite_id

            # Suite was deleted, now recreate it with new associations
            test_suite_id = _create_suite_and_associations(test_suite, evaluation_conn)

        # Handle create mode
        else:
            # Check suite doesn't exist
            ensure_entity_does_not_exist(
                natural_key_lookup=_lookup_test_suite_by_name,
                json_entity=test_suite,
                conn=evaluation_conn,
                entity_type_name=f"Test suite '{test_suite.name}'",
            )

            # Create suite and associations
            test_suite_id = _create_suite_and_associations(test_suite, evaluation_conn)

        # Commit transaction (only if all operations succeeded)
        evaluation_conn.commit()

        return test_suite_id

    except Exception:
        # Rollback on any error
        evaluation_conn.rollback()
        raise


def verify_test_suite_loaded(
    test_suite_id: int,
    expected_case_count: int,
    conn: sqlite3.Connection,
) -> None:
    """Verify test suite loaded correctly using repository queries.

    Performs post-load integrity checks by comparing expected counts
    (from input JSON) against actual database counts.

    This ensures:
    1. Test suite record was created
    2. All suite-case associations were created
    3. No silent failures occurred

    Args:
        test_suite_id: Test suite ID to verify
        expected_case_count: Number of test cases from input JSON
        conn: Database connection (to evaluation_results.db)

    Raises:
        ValueError: If any verification check fails
    """
    # Check test suite exists
    if not test_suites.test_suite_exists(test_suite_id, conn):
        raise ValueError(f"Test suite verification failed: suite {test_suite_id} not found")

    # Check case count
    actual_case_count = test_suite_cases.count_suite_cases(test_suite_id, conn)
    if actual_case_count != expected_case_count:
        raise ValueError(
            f"Suite case count mismatch: expected {expected_case_count}, got {actual_case_count}"
        )
