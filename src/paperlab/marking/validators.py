"""Business rule validators for LLM marking responses.

This module provides Layer 2 validation (business logic) for the marking pipeline.
Layer 1 (structural validation) is handled by Pydantic models in models.py.
Layer 3 (data integrity) is handled by database constraints in schema.sql.

Design principles:
- Functional approach with explicit database connection passing
- Cross-validation against database (mark scheme)
- Fail fast with clear error messages
- No duplication of database constraint checks
"""

import sqlite3
from typing import Any

from paperlab.config import MarkType
from paperlab.constants.fields import CriterionFields
from paperlab.data.repositories.marking import mark_criteria
from paperlab.marking.models import LLMMarkingResponse


def _format_part_for_error(part_letter: str | None, sub_part_letter: str | None) -> str:
    """Format part identifier for error messages.

    Note: This is for error messages only (business logic layer).
    Display formatting lives in markdown/ layer.

    Args:
        part_letter: Part letter (e.g., 'a', 'b') or None for NULL part
        sub_part_letter: Sub-part letter (e.g., 'i', 'ii') or None

    Returns:
        Formatted label string for error messages

    Examples:
        >>> _format_part_for_error(None, None)
        ''
        >>> _format_part_for_error('a', None)
        '(a)'
        >>> _format_part_for_error('a', 'i')
        '(a)(i)'
    """
    if part_letter is None:
        return ""

    label = f"({part_letter})"
    if sub_part_letter:
        label += f"({sub_part_letter})"

    return label


def validate_marking_response(
    response: LLMMarkingResponse,
    question_id: int,
    conn: sqlite3.Connection,
) -> None:
    """Validate LLM response against mark scheme (business rules).

    Layer 2 validation - business logic and database cross-validation.

    Business rules:
    1. All criterion_ids must exist in mark_criteria for this question
    2. No GENERAL criteria (guidance only, not marking criteria)
    3. All marking criteria covered (no missing criteria)
    4. No duplicate criteria (each criterion marked exactly once)
    5. marks_awarded in valid range [0, marks_available]

    Args:
        response: Parsed LLM response (Layer 1 validated)
        question_id: Database ID of question being marked
        conn: Database connection

    Raises:
        ValueError: If validation fails with detailed error message

    Example:
        >>> # After Pydantic parsing
        >>> response = LLMMarkingResponse.model_validate_json(json_str)
        >>> # Cross-validate against database
        >>> validate_marking_response(response, question_id=1, conn)
    """
    # Get expected mark scheme from database
    expected_criteria = mark_criteria.get_mark_scheme_for_question(question_id, conn)

    # Build lookup: criterion_id → (marks_available, mark_type_code, part_label)
    # Excludes GENERAL criteria (guidance only)
    expected_by_id = {}
    for part in expected_criteria:
        for criterion in part["criteria"]:
            mark_type_code = criterion["mark_type_code"]

            # Skip GENERAL criteria - should not be marked
            if mark_type_code == MarkType.GENERAL:
                continue

            expected_by_id[criterion[CriterionFields.CRITERION_ID]] = {
                CriterionFields.MARKS_AVAILABLE: criterion[CriterionFields.MARKS_AVAILABLE],
                "mark_type_code": mark_type_code,
                "part_label": _format_part_for_error(
                    part.get("part_letter"), part.get("sub_part_letter")
                ),
            }

    # Validation B3: Question must have at least one marking criterion
    if not expected_by_id:
        raise ValueError(
            f"Question {question_id} has no marking criteria. "
            f"Cannot mark a question with no criteria to evaluate."
        )

    # Track which criteria we've seen (for duplicate detection)
    seen_criterion_ids = set()

    # Validate each result
    for result in response.results:
        criterion_id = result.criterion_id

        # Rule 1: Criterion must exist in mark scheme
        if criterion_id not in expected_by_id:
            # Check if it's a GENERAL criterion (special error message)
            if _is_general_criterion(criterion_id, expected_criteria):
                raise ValueError(
                    f"Invalid criterion_id {criterion_id} in LLM response: "
                    f"{MarkType.GENERAL} criteria are guidance only and must NOT be marked. "
                    f"Only mark criteria that award marks."
                )

            # Not in mark scheme at all
            valid_ids = sorted(expected_by_id.keys())
            raise ValueError(
                f"Invalid criterion_id {criterion_id} in LLM response. "
                f"Valid marking criterion IDs for question {question_id}: {valid_ids}"
            )

        # Rule 4: No duplicates
        if criterion_id in seen_criterion_ids:
            raise ValueError(
                f"Duplicate criterion_id {criterion_id} in LLM response. "
                f"Each criterion must be marked exactly once."
            )
        seen_criterion_ids.add(criterion_id)

        # Get expected values for this criterion
        expected = expected_by_id[criterion_id]
        marks_available = expected[CriterionFields.MARKS_AVAILABLE]

        # Rule 5: Marks in valid range
        if result.marks_awarded > marks_available:
            raise ValueError(
                f"Criterion {criterion_id} ({expected['mark_type_code']}): "
                f"marks_awarded ({result.marks_awarded}) "
                f"exceeds marks_available ({marks_available})"
            )

    # Rule 3: All marking criteria must be covered
    expected_ids = set(expected_by_id.keys())
    missing_ids = expected_ids - seen_criterion_ids

    if missing_ids:
        missing_details = [
            f"  - Criterion {cid}: {expected_by_id[cid]['mark_type_code']} "
            f"(part {expected_by_id[cid]['part_label']}, "
            f"{expected_by_id[cid]['marks_available']} marks)"
            for cid in sorted(missing_ids)
        ]
        raise ValueError(
            f"LLM response missing {len(missing_ids)} marking criteria:\n"
            + "\n".join(missing_details)
            + f"\n\nExpected {len(expected_ids)} criteria, got {len(seen_criterion_ids)}."
        )


def _is_general_criterion(criterion_id: int, mark_scheme_data: list[dict[str, Any]]) -> bool:
    """Check if criterion_id is a GENERAL criterion.

    Helper to provide better error messages when LLM incorrectly marks
    GENERAL criteria.

    Args:
        criterion_id: ID to check
        mark_scheme_data: Full mark scheme from repository

    Returns:
        True if criterion exists and is GENERAL type
    """
    for part in mark_scheme_data:
        for criterion in part["criteria"]:
            if criterion["criterion_id"] == criterion_id:
                return bool(criterion["mark_type_code"] == MarkType.GENERAL)
    return False
