"""Validators for evaluation loading.

Business logic validation (Layer 2) for test cases and test suites.
Layer 1 (structural) is handled by Pydantic models.
Layer 3 (data integrity) is handled by database constraints.
"""

import sqlite3

from paperlab.data.repositories.evaluation import test_cases, test_suites, validation_types
from paperlab.data.repositories.marking import mark_criteria, questions
from paperlab.evaluation.messages import CLICommands, ErrorMessages
from paperlab.evaluation.models import TestCaseInput, TestSuiteInput


def format_first_image_collision_error(
    image_path: str,
    existing_case_id: int,
    existing_json_path: str,
    paper_identifier: str,
    question_number: int,
    context: str = "validation",
) -> str:
    """Format first image collision error message.

    First image uniqueness is CRITICAL for correlation - if two test cases
    share the same first image, we cannot determine which test case a
    marking response belongs to.

    Args:
        image_path: The colliding image path (logical path)
        existing_case_id: Test case ID that already uses this image
        existing_json_path: JSON path of existing test case
        paper_identifier: Paper identifier of existing test case
        question_number: Question number of existing test case
        context: Where collision was detected (e.g., "load time", "runtime")

    Returns:
        Formatted multi-line error message with reason and fix

    Example:
        >>> error = format_first_image_collision_error(
        ...     image_path="data/evaluation/test_cases/.../q01_ms_001.png",
        ...     existing_case_id=42,
        ...     existing_json_path="data/evaluation/test_cases/.../q01_ms_001.json",
        ...     paper_identifier="PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08",
        ...     question_number=1,
        ...     context="load time"
        ... )
        >>> print(error)
        First image path collision detected at load time!
        Image: data/evaluation/test_cases/.../q01_ms_001.png
        Already used by test case 42 (JSON: data/evaluation/test_cases/.../q01_ms_001.json)
        Paper: PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08, Q1
        ...
    """
    return (
        f"First image path collision detected at {context}!\n"
        f"Image: {image_path}\n"
        f"Already used by test case {existing_case_id} "
        f"(JSON: {existing_json_path})\n"
        f"Paper: {paper_identifier}, Q{question_number}\n\n"
        f"REASON: Correlation requires unique first image paths.\n"
        f"Cannot determine which test case a marking response belongs to "
        f"if multiple test cases share the same first image.\n\n"
        f"FIX: Use different images for different test cases, "
        f"even if testing the same question."
    )


def validate_test_case(
    test_case: TestCaseInput,
    production_conn: sqlite3.Connection,
    evaluation_conn: sqlite3.Connection,
) -> int:
    """Validate test case against production and evaluation databases.

    Checks:
    1. Validation type exists in evaluation DB
    2. Question exists in production DB
    3. Criterion indices match exactly (completeness + validity)
    4. Marks awarded don't exceed marks available

    Note: Image existence is validated earlier by Pydantic validator

    Args:
        test_case: Test case input from JSON
        production_conn: Connection to production marking.db
        evaluation_conn: Connection to evaluation_results.db

    Returns:
        validation_type_id

    Raises:
        ValueError: If validation fails
    """
    # Check validation type exists
    validation_type_id = validation_types.get_by_code(test_case.validation_type, evaluation_conn)

    # Check question exists
    question = questions.get_question_by_paper_identifier(
        test_case.paper_identifier,
        test_case.question_number,
        production_conn,
    )
    if question is None:
        raise ValueError(
            ErrorMessages.QUESTION_NOT_FOUND.format(
                paper_identifier=test_case.paper_identifier,
                question_number=test_case.question_number,
                load_paper_instruction=ErrorMessages.LOAD_PAPER_FIRST,
                load_markscheme_instruction=ErrorMessages.LOAD_MARKSCHEME_FIRST,
            )
        )

    question_id = question["id"]

    # Get criterion indices and marks_available from production DB
    criteria_info = mark_criteria.get_criteria_info_for_question(question_id, production_conn)

    # Check question has mark criteria defined
    if not criteria_info:
        raise ValueError(
            f"Question has no mark criteria: {test_case.paper_identifier} "
            f"Q{test_case.question_number}. "
            f"{ErrorMessages.LOAD_MARKSCHEME_FIRST}"
        )

    production_indices = set(criteria_info.keys())

    # Convert test case criterion indices from string keys to integers
    try:
        test_case_indices = {int(k) for k in test_case.expected_marks}
    except ValueError as e:
        raise ValueError(
            f"Invalid criterion_index key in expected_marks: must be numeric strings. Error: {e}"
        ) from None

    # Compare criterion indices (exact match required - validates both completeness and validity)
    if test_case_indices != production_indices:
        missing = production_indices - test_case_indices  # In prod but not in test case
        extra = test_case_indices - production_indices  # In test case but not in prod

        error_parts = []
        if missing:
            error_parts.append(f"Missing: {sorted(missing)}")
        if extra:
            error_parts.append(f"Extra: {sorted(extra)}")

        raise ValueError(
            f"Criterion indices mismatch for {test_case.paper_identifier} "
            f"Q{test_case.question_number}. "
            f"{' | '.join(error_parts)}. Expected: {sorted(production_indices)}"
        )

    # Validate marks awarded don't exceed marks available for each criterion
    for criterion_index_str, marks_awarded in test_case.expected_marks.items():
        criterion_index = int(criterion_index_str)  # Already validated as numeric above
        marks_available = criteria_info[criterion_index]

        if marks_awarded > marks_available:
            raise ValueError(
                f"Marks awarded ({marks_awarded}) exceed marks available ({marks_available}) "
                f"for criterion {criterion_index} in question "
                f"{test_case.paper_identifier} Q{test_case.question_number}"
            )

    return validation_type_id


def validate_test_suite(
    test_suite: TestSuiteInput,
    conn: sqlite3.Connection,
) -> None:
    """Validate test suite against evaluation database.

    Checks:
    1. Suite name is unique (no duplicate suite names)
    2. No duplicate image paths within the suite
    3. All referenced image paths exist in test_cases table

    Args:
        test_suite: Test suite input from JSON
        conn: Connection to evaluation_results.db

    Raises:
        ValueError: If validation fails

    Note:
        In replace mode, the existing suite is deleted before validation,
        so the name uniqueness check will pass.
    """
    # Check suite name uniqueness
    if test_suites.suite_name_exists(test_suite.name, conn):
        suite = test_suites.get_by_name(test_suite.name, conn)
        suite_id = suite["id"] if suite else "unknown"
        raise ValueError(
            ErrorMessages.SUITE_NAME_EXISTS.format(suite_name=test_suite.name, suite_id=suite_id)
        )

    # Check for duplicate paths in input
    unique_paths = set(test_suite.test_case_json_paths)
    if len(unique_paths) != len(test_suite.test_case_json_paths):
        # Find duplicates for error message
        seen = set()
        duplicates = set()
        for path in test_suite.test_case_json_paths:
            if path in seen:
                duplicates.add(path)
            seen.add(path)

        raise ValueError(
            f"Duplicate JSON paths in suite: {sorted(duplicates)}. "
            f"Each test case should only appear once per suite."
        )

    # Check all JSON paths exist in test_cases table
    missing_paths = []
    for json_path in test_suite.test_case_json_paths:
        if not test_cases.test_case_exists_by_json_path(json_path, conn):
            missing_paths.append(json_path)

    if missing_paths:
        formatted_paths = "\n".join(f"  - {p}" for p in missing_paths)
        raise ValueError(
            f"Test cases not found for the following image paths:\n"
            f"{formatted_paths}\n"
            f"Load these test cases first using '{CLICommands.LOAD_TEST_CASE}'."
        )
