"""Shared validators and base models for all loading pipelines.

This module contains:
- Reusable validation functions used across paper, mark, and config models
- Base models for common patterns (ExamTypeBase, PaperInstanceBase, QuestionPartBase)
- Shared utilities for content validation (LaTeX sanitization, sequence validation)

Design principles:
- Single source of truth for validation logic
- Reusable across all model types
- No dependencies on specific model implementations
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from paperlab.config import (
    DisplayOrder,
    FieldLengthLimits,
    ValidationPatterns,
)

# ============================================================================
# Reusable Validators
# ============================================================================


def validate_sequential_numbering(items: list[Any], attr_name: str, start_from: int = 1) -> None:
    """Validate that a sequence of items has sequential numbering starting from start_from.

    Args:
        items: List of items to validate (can be objects or primitives)
        attr_name: Name of the attribute containing the number (for error messages)
        start_from: Starting number for sequence (default: 1)

    Raises:
        ValueError: If numbers are not sequential or don't start from start_from
    """
    if not items:
        return

    # Extract numbers - handle both objects with attributes and direct number lists
    numbers = items if isinstance(items[0], int) else [getattr(item, attr_name) for item in items]

    # Sort to check sequence
    sorted_numbers = sorted(numbers)
    expected = list(range(start_from, start_from + len(items)))

    if sorted_numbers != expected:
        missing = set(expected) - set(sorted_numbers)
        duplicates = [n for n in sorted_numbers if sorted_numbers.count(n) > 1]
        error_details = []
        if missing:
            error_details.append(f"Missing: {sorted(missing)}")
        if duplicates:
            error_details.append(f"Duplicates: {sorted(set(duplicates))}")

        raise ValueError(
            f"Validation Error in {attr_name}:\n"
            f"  Expected: Sequential numbers {expected}\n"
            f"  Found: {sorted_numbers}\n"
            + ("  " + ", ".join(error_details) if error_details else "")
        )


def validate_unique_numbers(numbers: list[int], field_name: str) -> None:
    """Validate that a list of numbers contains only unique values.

    Args:
        numbers: List of numbers to validate
        field_name: Name of the field (for error messages)

    Raises:
        ValueError: If numbers are not unique
    """
    if len(numbers) != len(set(numbers)):
        raise ValueError(f"{field_name} must be unique")


def validate_no_consecutive_diagrams(blocks: list[Any]) -> None:
    """Validate that no two diagram blocks are adjacent.

    Matches database trigger constraint. If diagrams appear side-by-side in source,
    they should be combined into a single image.

    Args:
        blocks: List of ContentBlock objects to validate

    Raises:
        ValueError: If two consecutive blocks are both diagrams
    """
    from paperlab.config import BlockType

    for i in range(len(blocks) - 1):
        if (
            blocks[i].block_type == BlockType.DIAGRAM
            and blocks[i + 1].block_type == BlockType.DIAGRAM
        ):
            raise ValueError(
                "Cannot have adjacent diagram blocks. "
                "Combine diagrams into single image or add text separator."
            )


def validate_sum_equals_total(calculated_total: int, expected_total: int, context: str) -> None:
    """Validate that a calculated sum equals an expected total.

    Reusable validator for marks totals at question, paper, and mark scheme levels.

    Args:
        calculated_total: The calculated sum of marks
        expected_total: The expected total marks
        context: Context string for error message (e.g., "Question 1", "Paper")

    Raises:
        ValueError: If calculated_total does not equal expected_total
    """
    if calculated_total != expected_total:
        raise ValueError(
            f"{context}: total_marks ({expected_total}) "
            f"does not equal calculated sum ({calculated_total})"
        )


def validate_null_entity_exists(
    entities: list[Any],
    question_number: int,
    entity_type: str,
) -> None:
    """Validate that NULL entity exists at display_order=0 with correct properties.

    This function enforces the NULL entity pattern used consistently across both
    paper structure (QuestionPart) and mark schemes (MarkCriterion).

    NULL entity requirements:
    - Must exist at display_order=0
    - Must have part_letter=None and sub_part_letter=None
    - Contains general content/guidance before any lettered entities

    Args:
        entities: List of parts or criteria to validate (must have display_order,
                  part_letter, and sub_part_letter attributes)
        question_number: Question number for error messages
        entity_type: Type name for error messages (e.g., "part", "criterion")

    Raises:
        ValueError: If NULL entity is missing or has incorrect properties
    """
    null_entity = next((e for e in entities if e.display_order == DisplayOrder.NULL_PART), None)

    if null_entity is None:
        raise ValueError(
            f"Question {question_number}: Missing required NULL {entity_type} at display_order=0. "
            f"Found {entity_type}s at positions: {[e.display_order for e in entities]}"
        )

    if null_entity.part_letter is not None or null_entity.sub_part_letter is not None:
        raise ValueError(
            f"Question {question_number}: NULL {entity_type} (display_order=0) "
            f"must have part_letter=None and sub_part_letter=None"
        )


# ============================================================================
# Shared Base Models
# ============================================================================


class ExamTypeBase(BaseModel):
    """Shared exam type metadata.

    Used by both paper and mark scheme JSON to identify the exam context.
    Maps to lookup of exam_type_id in database.

    Exam types define paper specifications (templates), not individual exam instances.
    """

    exam_board: str = Field(
        ...,
        min_length=1,
        max_length=FieldLengthLimits.EXAM_BOARD_MAX,
        description="Exam board name (e.g., 'Pearson Edexcel', 'AQA')",
    )
    exam_level: str = Field(
        ...,
        min_length=1,
        max_length=FieldLengthLimits.EXAM_LEVEL_MAX,
        description="Qualification level (e.g., 'GCSE', 'A-Level')",
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=FieldLengthLimits.SUBJECT_MAX,
        description="Subject name (e.g., 'Mathematics', 'Physics')",
    )
    paper_code: str = Field(
        ...,
        min_length=1,
        max_length=FieldLengthLimits.PAPER_CODE_MAX,
        description="Paper code (e.g., '1MA1/1H')",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
        description="Human-readable paper name (e.g., 'Paper 1 (Non-Calculator)')",
    )

    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        str_strip_whitespace=True,  # Auto-strip whitespace from strings
    )


class PaperInstanceBase(BaseModel):
    """Shared paper instance metadata.

    Used by both paper and mark scheme JSON to identify which paper instance is being referenced.
    Maps to papers table in database.

    Papers are instances (dated sittings) of an exam type, not templates.

    Note: paper_identifier is a computed property derived from exam_type fields + exam_date.
    It is NOT stored in JSON - it's always generated from other fields to ensure consistency.
    """

    exam_date: str = Field(
        ...,
        description="Exam date in ISO format (YYYY-MM-DD)",
        pattern=ValidationPatterns.ISO_DATE_REGEX,
    )
    total_marks: int = Field(..., gt=0, description="Total marks available for this paper instance")

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )


class QuestionPartBase(BaseModel):
    """Shared part identity and ordering for both papers and mark schemes.

    This base class captures the fundamental concept: question parts are the same
    entity whether appearing in a paper (with question text) or mark scheme
    (with criteria and answers).

    Both papers and mark schemes describe the same question parts:
    - Paper parts contain question text (QuestionPart adds content_blocks)
    - Mark scheme parts contain criteria and answers (QuestionPartMarks adds those)
    - Both share identical part identity: part_letter, sub_part_letter, display_order

    Part identity rules:
    - NULL part: part_letter=None, sub_part_letter=None, display_order=0
    - Lettered part: part_letter='a'/'b'/etc., sub_part_letter=None, display_order=1+
    - Sub-part: part_letter='a', sub_part_letter='i'/'ii'/etc., display_order=1+
    - Hierarchy rule: Cannot have sub_part_letter without part_letter
    """

    part_letter: str | None = Field(
        None, description="Part letter (e.g., 'a', 'b') or None for general context"
    )
    sub_part_letter: str | None = Field(
        None, description="Sub-part letter (e.g., 'i', 'ii') or None"
    )
    display_order: int = Field(..., ge=0, description="Display order within question (starts at 0)")

    @field_validator("part_letter")
    @classmethod
    def validate_part_letter_format(cls, v: str | None) -> str | None:
        """Ensure part_letter is a single lowercase character if provided."""
        if v is not None:
            if len(v) != 1:
                raise ValueError("Part letters must be single characters")
            if not v.islower():
                raise ValueError("Part letters must be lowercase")
        return v

    @field_validator("sub_part_letter")
    @classmethod
    def validate_sub_part_letter_format(cls, v: str | None) -> str | None:
        """Ensure sub_part_letter is a valid lowercase roman numeral if provided.

        Accepts roman numerals from i to x (1 to 10), which covers realistic
        exam paper sub-part scenarios.
        """
        if v is not None:
            import re

            if not re.match(ValidationPatterns.ROMAN_NUMERAL_I_TO_X, v):
                raise ValueError(
                    f"Sub-part letters must be lowercase roman numerals (i-x). Got: '{v}'"
                )
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate part identity consistency.

        Cannot have a sub_part_letter without a part_letter - this would create
        an invalid hierarchy (e.g., (i) without (a)).
        """
        if self.sub_part_letter is not None and self.part_letter is None:
            raise ValueError("Cannot have sub_part_letter without part_letter")
