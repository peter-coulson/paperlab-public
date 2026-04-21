"""Validators for mark scheme loading.

Business rule validation for mark scheme JSON input.
"""

import sqlite3

from paperlab.config import MarkType
from paperlab.data.repositories.marking import exam_types, mark_types
from paperlab.loading.models.marks import MarkSchemeInput
from paperlab.loading.validators.shared import validate_paper_structure_exists


def validate_mark_scheme_structure(marks: MarkSchemeInput) -> None:
    """Validate mark scheme business rules (no database required).

    Business rules:
    1. If mark_type_code = None, then marks_available MUST = 0
       (structural NULL criterion, not inserted to database)
    2. If mark_type_code = 'GENERAL', then marks_available MUST = 0
       (GENERAL is for guidance, never awards marks)
    3. If mark_type_code != 'GENERAL' and not None, then marks_available MUST > 0
       (all other mark types must award at least 1 mark)
    4. Parts with marking criteria must have expected_answer

    Note: Does NOT require "at least one marking criterion" - this would break
    subject-agnostic design. Essay subjects can have all marks on NULL part
    with single criterion (holistic assessment).

    These rules are subject-agnostic and enforce the semantic meaning of the
    GENERAL mark type across all exam specifications.

    Args:
        marks: Complete mark scheme from JSON

    Raises:
        ValueError: If mark type rules are violated
    """
    # Validate mark type rules
    for question in marks.questions:
        for part in question.question_parts:
            for criterion in part.mark_criteria:
                if criterion.mark_type_code is None:
                    # Structural NULL criterion - validated in Pydantic model
                    # Must have marks_available = 0 (already checked in model)
                    continue
                elif criterion.mark_type_code == MarkType.GENERAL:
                    if criterion.marks_available != 0:
                        raise ValueError(
                            f"Question {question.question_number}, "
                            f"criterion at display_order={criterion.display_order}: "
                            f"GENERAL mark type must have marks_available = 0, "
                            f"got {criterion.marks_available}"
                        )
                else:
                    if criterion.marks_available <= 0:
                        raise ValueError(
                            f"Question {question.question_number}, "
                            f"criterion at display_order={criterion.display_order}: "
                            f"Non-GENERAL mark type '{criterion.mark_type_code}' "
                            f"must have marks_available > 0, "
                            f"got {criterion.marks_available}"
                        )

    # Validate expected_answer requirements
    validate_expected_answer_requirements(marks)


def validate_expected_answer_requirements(marks: MarkSchemeInput) -> None:
    """Validate expected_answer is provided when required.

    Validation Rule:
    - Parts with actual marking criteria (non-NULL, non-GENERAL) must have expected_answer
    - NULL parts with only GENERAL criteria do not need expected_answer
    - Empty parts (no criteria) do not need expected_answer

    This validation enforces business requirements before any database operations occur.

    Args:
        marks: Complete mark scheme from JSON

    Raises:
        ValueError: If expected_answer is missing when required
    """
    for question in marks.questions:
        for part in question.question_parts:
            # Check if part has actual marking criteria (non-NULL, non-GENERAL)
            has_actual_criteria = any(
                criterion.mark_type_code is not None
                and criterion.mark_type_code != MarkType.GENERAL
                for criterion in part.mark_criteria
            )

            # If part has actual criteria, expected_answer is required
            if has_actual_criteria and part.expected_answer is None:
                part_desc = "NULL part" if part.part_letter is None else f"part ({part.part_letter}"
                if part.sub_part_letter:
                    part_desc += f")({part.sub_part_letter}"
                part_desc += ")"

                criteria_count = len(
                    [
                        c
                        for c in part.mark_criteria
                        if c.mark_type_code not in (None, MarkType.GENERAL)
                    ]
                )
                raise ValueError(
                    f"Question {question.question_number}, {part_desc}: "
                    f"expected_answer is required for parts with marking criteria. "
                    f"This part has {criteria_count} marking criteria "
                    f"but no expected_answer provided."
                )


def validate_mark_scheme_references(
    marks: MarkSchemeInput,
    conn: sqlite3.Connection,
) -> None:
    """Validate mark scheme database references.

    Database checks:
    1. exam_type (board/level/subject/paper_code) must exist
    2. All mark_type_codes must exist in mark_types for this exam type
    3. Paper structure must exist and match mark scheme structure

    Note: Paper MUST be loaded before mark scheme. This function validates that
    paper exists and structure matches exactly.

    Args:
        marks: Complete mark scheme from JSON
        conn: Database connection

    Raises:
        ValueError: If exam_type or mark_type_codes don't exist, paper doesn't exist,
                   or structure doesn't match
    """
    # Check exam type exists
    exam_type_id = exam_types.get_by_exam_type(
        marks.exam_type.exam_board,
        marks.exam_type.exam_level,
        marks.exam_type.subject,
        marks.exam_type.paper_code,
        conn,
    )

    # Check all mark_type_codes exist for this exam type
    for question in marks.questions:
        for part in question.question_parts:
            for criterion in part.mark_criteria:
                # Skip structural NULL criteria (mark_type_code=None)
                if criterion.mark_type_code is None:
                    continue
                # This will raise ValueError if mark type doesn't exist
                mark_types.get_by_code(criterion.mark_type_code, exam_type_id, conn)

    # Validate paper structure exists and matches (REQUIRED - paper must be loaded first)
    # Use computed paper_identifier property (derived from exam_type + exam_date)
    validate_paper_structure_exists(
        marks.paper_identifier, marks.paper_instance, marks.questions, conn
    )
