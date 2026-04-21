"""Orchestrate test case loading from JSON into evaluation_results.db (REFACTORED).

This module coordinates the workflow for loading test cases:
- Parse and validate JSON input (Pydantic models)
- Validate business rules against production DB (validators)
- Create database records in evaluation DB (repositories)

Transaction management:
- Wraps all database operations in a single transaction
- Commits on success, rolls back on any exception
- Caller must manage connection lifecycle (use context manager)

Design principles:
- REFACTORED: Smaller, focused helper functions
"""

import sqlite3
from pathlib import Path

from paperlab.data.repositories.evaluation import test_case_images, test_case_marks, test_cases
from paperlab.evaluation.loading.test_case_diff_calculator import (
    TestCaseDiff,
    TestCaseDiffCalculator,
)
from paperlab.evaluation.loading.test_case_validators import validate_json_and_images_coupling
from paperlab.evaluation.models import TestCaseInput
from paperlab.evaluation.validators import format_first_image_collision_error, validate_test_case
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.path_utils import to_logical_path
from paperlab.loaders.update_framework import handle_update_mode


def _lookup_test_case_by_json_path(
    tc: TestCaseInput, test_case_json_path: Path, conn: sqlite3.Connection
) -> dict[str, int | str | None] | None:
    """Look up test case by its natural key (JSON path)."""
    logical_json_path = to_logical_path(test_case_json_path)
    return test_cases.get_by_json_path(logical_json_path, conn)


def _handle_replace_mode(
    test_case: TestCaseInput,
    test_case_json_path: Path,
    evaluation_conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, TestCaseDiff]:
    """Handle replace mode for existing test case."""
    diff_calculator = TestCaseDiffCalculator()

    def delete_test_case_func(test_case_id: int, conn: sqlite3.Connection) -> None:
        test_cases.delete_test_case(test_case_id, conn)

    def lookup_wrapper(
        tc: TestCaseInput, conn: sqlite3.Connection
    ) -> dict[str, int | str | None] | None:
        return _lookup_test_case_by_json_path(tc, test_case_json_path, conn)

    should_proceed, diff = handle_update_mode(
        json_entity=test_case,
        natural_key_lookup=lookup_wrapper,
        diff_calculator=diff_calculator,
        delete_func=delete_test_case_func,
        conn=evaluation_conn,
        force=force,
    )
    if not isinstance(diff, TestCaseDiff):
        raise TypeError(f"Expected TestCaseDiff, got {type(diff)}")
    return should_proceed, diff


def _parse_and_validate_input(
    test_case_json_path: str,
    production_conn: sqlite3.Connection,
    evaluation_conn: sqlite3.Connection,
) -> tuple[TestCaseInput, Path, int]:
    """Parse JSON and validate structure, references, and business rules."""
    test_case = load_and_parse_json(test_case_json_path, TestCaseInput)
    test_case_json_path_obj = Path(test_case_json_path)

    validate_json_and_images_coupling(
        test_case_json_path_obj,
        test_case.student_work_image_paths,
        test_case.paper_identifier,
        test_case.question_number,
        test_case.validation_type,
    )

    validation_type_id = validate_test_case(test_case, production_conn, evaluation_conn)

    return test_case, test_case_json_path_obj, validation_type_id


def _handle_create_mode(logical_json_path: str, evaluation_conn: sqlite3.Connection) -> None:
    """Handle create mode - ensure test case doesn't already exist."""
    if test_cases.test_case_exists_by_json_path(logical_json_path, evaluation_conn):
        raise ValueError(
            f"Test case with JSON path '{logical_json_path}' already exists. "
            f"Use --replace to overwrite."
        )


def _create_test_case_records(
    test_case: TestCaseInput,
    test_case_json_path: Path,
    validation_type_id: int,
    evaluation_conn: sqlite3.Connection,
) -> int:
    """Create test case, images, and marks records."""
    logical_json_path = to_logical_path(test_case_json_path)

    test_case_id = test_cases.create_test_case(
        test_case_json_path=logical_json_path,
        paper_identifier=test_case.paper_identifier,
        question_number=test_case.question_number,
        validation_type_id=validation_type_id,
        notes=test_case.notes,
        conn=evaluation_conn,
    )

    # Validate first image uniqueness
    first_image_path = test_case.student_work_image_paths[0]
    first_image_collision: dict[str, int | str] | None = test_case_images.get_by_first_image_path(
        first_image_path, evaluation_conn
    )
    if first_image_collision:
        error_msg = format_first_image_collision_error(
            image_path=first_image_path,
            existing_case_id=int(first_image_collision["test_case_id"]),
            existing_json_path=str(first_image_collision["test_case_json_path"]),
            paper_identifier=str(first_image_collision["paper_identifier"]),
            question_number=int(first_image_collision["question_number"]),
            context="load time",
        )
        raise ValueError(error_msg)

    # Create images
    test_case_images.create_test_case_images_batch(
        test_case_id=test_case_id,
        image_paths=test_case.student_work_image_paths,
        conn=evaluation_conn,
    )

    # Create marks
    marks = {int(k): v for k, v in test_case.expected_marks.items()}
    test_case_marks.create_test_case_marks_batch(
        test_case_id,
        marks,
        evaluation_conn,
    )

    return test_case_id


def load_test_case(
    test_case_json_path: str,
    production_conn: sqlite3.Connection,
    evaluation_conn: sqlite3.Connection,
    project_root: Path,
    replace: bool = False,
    force: bool = False,
) -> int:
    """Load test case from JSON into evaluation_results.db.

    Args:
        test_case_json_path: Path to test case JSON file
        production_conn: Connection to production marking.db (read-only)
        evaluation_conn: Connection to evaluation_results.db (transaction managed by this function)
        project_root: Project root path for resolving image paths
        replace: If True, replace existing test case with same image path
        force: If True, skip confirmation prompts

    Returns:
        test_case_id

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails or user cancels operation
        sqlite3.Error: If database operations fail
    """
    # 1. Parse and validate input
    test_case, test_case_json_path_obj, validation_type_id = _parse_and_validate_input(
        test_case_json_path, production_conn, evaluation_conn
    )

    logical_json_path = to_logical_path(test_case_json_path_obj)

    try:
        # 2. Handle replace vs create mode
        if replace:
            should_proceed, diff = _handle_replace_mode(
                test_case, test_case_json_path_obj, evaluation_conn, force
            )

            if not should_proceed:
                evaluation_conn.commit()
                existing = test_cases.get_by_json_path(logical_json_path, evaluation_conn)
                if existing is None:
                    raise ValueError(f"Test case not found after update: {logical_json_path}")
                result_id = existing["id"]
                if not isinstance(result_id, int):
                    raise TypeError(f"Test case ID must be an integer, got {type(result_id)}")
                return result_id
        else:
            _handle_create_mode(logical_json_path, evaluation_conn)

        # 3. Create database records
        test_case_id = _create_test_case_records(
            test_case, test_case_json_path_obj, validation_type_id, evaluation_conn
        )

        # 4. Verify loaded data
        verify_test_case_loaded(
            test_case_id,
            expected_marks_count=len(test_case.expected_marks),
            expected_images_count=len(test_case.student_work_image_paths),
            conn=evaluation_conn,
        )

        # 5. Commit transaction
        evaluation_conn.commit()

        return test_case_id

    except Exception:
        evaluation_conn.rollback()
        raise


def verify_test_case_loaded(
    test_case_id: int,
    expected_marks_count: int,
    expected_images_count: int,
    conn: sqlite3.Connection,
) -> None:
    """Verify test case loaded correctly using repository queries."""
    if not test_cases.test_case_exists(test_case_id, conn):
        raise ValueError(f"Test case verification failed: test case {test_case_id} not found")

    actual_marks_count = test_case_marks.count_marks(test_case_id, conn)
    if actual_marks_count != expected_marks_count:
        raise ValueError(
            f"Marks count mismatch: expected {expected_marks_count}, got {actual_marks_count}"
        )

    actual_images = test_case_images.count_images_for_test_case(test_case_id, conn)
    if actual_images != expected_images_count:
        raise ValueError(
            f"Image count mismatch for test case {test_case_id}: "
            f"expected {expected_images_count}, got {actual_images}"
        )
