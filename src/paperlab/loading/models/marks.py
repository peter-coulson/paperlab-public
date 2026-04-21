"""Pydantic models for mark scheme loading.

These models define the contract for mark scheme JSON files that will be loaded
into the database. They provide type safety and validation before business
rule validation and database insertion.

Model to SQL Table Mapping:
- ExamTypeBase → exam_types (lookup only)
- PaperInstanceBase → papers (lookup only)
- QuestionMarkScheme → questions (validation only)
- QuestionPartMarks → question_parts (mark scheme perspective, with expected_answer)
- MarkCriterion → mark_criteria
- ContentBlock → mark_criteria_content_blocks

Key Concepts:
- NULL part: display_order=0, part_letter=None, contains general guidance
- Display ordering: Criteria display_order is absolute within question
- Hierarchical mark schemes: question_parts → mark_criteria (not flat)
- Loading order: Paper must be loaded before mark scheme
"""

from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from paperlab.config import (
    DisplayOrder,
    FieldLengthLimits,
    MarkType,
    ValidationLimits,
    generate_paper_identifier,
)
from paperlab.loading.models.papers import ContentBlock
from paperlab.loading.models.shared import (
    ExamTypeBase,
    PaperInstanceBase,
    QuestionPartBase,
    validate_no_consecutive_diagrams,
    validate_null_entity_exists,
    validate_sequential_numbering,
    validate_sum_equals_total,
    validate_unique_numbers,
)

# Type aliases for convenience
QuestionDict = dict[str, Any]
ValidationErrorTuple = tuple[int | str, ValidationError]


# ============================================================================
# Mark Scheme Models
# ============================================================================


class MarkCriterion(BaseModel):
    """A single marking criterion - criterion-specific fields only.

    Part identity comes from parent QuestionPartMarks.
    Contains only criterion-specific fields: marks, type, dependencies, content.

    Display order is absolute within the question (for cross-part dependencies).
    """

    display_order: int = Field(
        ..., ge=0, description="Absolute display order within question (for dependencies)"
    )
    mark_type_code: str | None = Field(
        None,
        max_length=FieldLengthLimits.MARK_TYPE_CODE_MAX,
        description=(
            "Mark type code (e.g., 'M1', 'A1', 'GENERAL') or None for structural NULL criterion"
        ),
    )
    marks_available: int = Field(..., ge=0, description="Marks awarded by this criterion")
    depends_on_display_order: int | None = Field(
        None,
        description="Display order of criterion this depends on (e.g., A1 depends on M1)",
    )
    content_blocks: list[ContentBlock] = Field(
        ...,
        min_length=0,
        max_length=ValidationLimits.MAX_CONTENT_BLOCKS_PER_PART,
        description="Criterion description and marking guidance",
    )

    @field_validator("content_blocks")
    @classmethod
    def validate_display_order_sequence(cls, blocks: list[ContentBlock]) -> list[ContentBlock]:
        """Ensure display_order is sequential starting from 1 (if blocks exist)."""
        if blocks:
            validate_sequential_numbering(
                blocks, "display_order", start_from=DisplayOrder.FIRST_CONTENT_BLOCK
            )
        return blocks

    @field_validator("content_blocks")
    @classmethod
    def validate_no_adjacent_diagrams(cls, blocks: list[ContentBlock]) -> list[ContentBlock]:
        """Ensure no two diagram blocks are adjacent (if blocks exist)."""
        if blocks:
            validate_no_consecutive_diagrams(blocks)
        return blocks

    @model_validator(mode="after")
    def validate_mark_type_consistency(self) -> "MarkCriterion":
        """Validate mark_type_code and marks_available consistency.

        Rules:
        - If mark_type_code is None: marks_available must be 0 (structural NULL criterion)
        - If mark_type_code is None: content_blocks must be empty (no actual content)
        """
        if self.mark_type_code is None:
            if self.marks_available != 0:
                raise ValueError(
                    f"Criterion at display_order={self.display_order}: "
                    f"Structural NULL criterion (mark_type_code=None) must have marks_available=0"
                )
            if len(self.content_blocks) > 0:
                raise ValueError(
                    f"Criterion at display_order={self.display_order}: "
                    "Structural NULL (mark_type_code=None) must have empty content_blocks"
                )
        return self


class QuestionPartMarks(QuestionPartBase):
    """Question part in mark scheme - contains criteria and expected answer.

    Inherits part identity (part_letter, sub_part_letter, display_order) from QuestionPartBase.
    Adds expected_answer and mark_criteria for marking information.

    This represents the same question parts as in papers, but from the mark scheme perspective.
    Papers show question text; mark schemes show criteria and answers.
    """

    expected_answer: str | None = Field(
        None, description="Expected answer for this part (LaTeX format for maths)"
    )
    mark_criteria: list[MarkCriterion] = Field(
        ...,
        min_length=0,  # Can be empty for structural NULL parts
        max_length=ValidationLimits.MAX_CRITERIA_PER_QUESTION,
        description="Marking criteria for this part",
    )


class QuestionMarkScheme(BaseModel):
    """Mark scheme for a single question.

    Uses hierarchical structure: question_parts → mark_criteria
    Each part contains its expected_answer and associated criteria.

    Parts include:
    - NULL part (display_order=0, part_letter=None) - general guidance
    - Lettered parts (display_order=1+) - part-specific criteria and answers
    """

    question_number: int = Field(..., ge=1, description="Question number")
    question_parts: list[QuestionPartMarks] = Field(
        ...,
        min_length=1,
        max_length=ValidationLimits.MAX_PARTS_PER_QUESTION,
        description="All parts with marking criteria including NULL part (display_order=0)",
    )

    @field_validator("question_parts")
    @classmethod
    def validate_parts_order(cls, parts: list[QuestionPartMarks]) -> list[QuestionPartMarks]:
        """Ensure parts display_order is sequential starting from 0."""
        validate_sequential_numbering(parts, "display_order", start_from=DisplayOrder.NULL_PART)
        return parts

    @field_validator("question_parts")
    @classmethod
    def validate_criteria_display_order_across_parts(
        cls, parts: list[QuestionPartMarks]
    ) -> list[QuestionPartMarks]:
        """Ensure all criteria across all parts have unique, sequential display_order.

        Criteria display_order is absolute within question, not relative to part.
        Sequential numbering (0, 1, 2, 3...) automatically guarantees uniqueness.
        """
        all_criteria = [c for part in parts for c in part.mark_criteria]
        if all_criteria:
            validate_sequential_numbering(
                all_criteria, "display_order", start_from=DisplayOrder.NULL_PART
            )
        return parts

    @field_validator("question_parts")
    @classmethod
    def validate_dependencies_reference_valid_display_order(
        cls, parts: list[QuestionPartMarks]
    ) -> list[QuestionPartMarks]:
        """Ensure all dependency references point to valid display_order values."""
        all_criteria = [c for part in parts for c in part.mark_criteria]
        valid_orders = {c.display_order for c in all_criteria}

        for criterion in all_criteria:
            if (
                criterion.depends_on_display_order is not None
                and criterion.depends_on_display_order not in valid_orders
            ):
                raise ValueError(
                    f"Criterion at display_order={criterion.display_order} depends on "
                    f"display_order={criterion.depends_on_display_order} which doesn't exist"
                )
        return parts

    @model_validator(mode="after")
    def validate_null_part_exists(self) -> "QuestionMarkScheme":
        """Ensure NULL part exists at display_order=0 with correct properties."""
        validate_null_entity_exists(
            entities=self.question_parts,
            question_number=self.question_number,
            entity_type="part",
        )
        return self

    @property
    def total_marks(self) -> int:
        """Calculate total marks from all criteria across all parts.

        Excludes:
        - Criteria with mark_type_code = None (structural NULL criterion)
        - Criteria with mark_type_code = 'GENERAL' (guidance only)
        """
        return sum(
            c.marks_available
            for part in self.question_parts
            for c in part.mark_criteria
            if c.mark_type_code is not None and c.mark_type_code != MarkType.GENERAL
        )


class MarkSchemeInput(BaseModel):
    """Complete mark scheme from LLM-generated JSON.

    Top-level model for mark scheme loading pipeline. Validates the entire mark scheme
    JSON file before business rule validation and database insertion.
    """

    exam_type: ExamTypeBase = Field(
        ..., description="Exam type (board, level, subject, paper code, display name)"
    )
    paper_instance: PaperInstanceBase = Field(
        ..., description="Paper instance this mark scheme applies to"
    )
    questions: list[QuestionMarkScheme] = Field(
        ...,
        min_length=1,
        max_length=ValidationLimits.MAX_QUESTIONS_PER_PAPER,
        description="Mark schemes for each question",
    )

    @property
    def paper_identifier(self) -> str:
        """Generate paper identifier from exam_type and paper_instance fields.

        This is a computed property that derives the unique paper identifier
        from the source fields. It ensures consistency and eliminates the
        possibility of user input errors.

        Returns:
            Standardized paper identifier
            (e.g., 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08')
        """
        return generate_paper_identifier(
            self.exam_type.exam_board,
            self.exam_type.exam_level,
            self.exam_type.subject,
            self.exam_type.paper_code,
            self.paper_instance.exam_date,
        )

    @classmethod
    def validate_questions_batch(cls, questions: list[QuestionDict]) -> list[ValidationErrorTuple]:
        """Validate mark scheme questions individually, returning errors with question numbers.

        Useful for debugging large mark scheme JSONs - validates each question independently
        and reports which questions have errors without stopping at the first failure.

        Args:
            questions: List of question mark scheme dictionaries to validate

        Returns:
            List of tuples (question_number, error) for questions that failed validation.
            Empty list if all questions are valid.

        Example:
            errors = MarkSchemeInput.validate_questions_batch(questions_data)
            for q_num, error in errors:
                print(f"Question {q_num}: {error}")
        """
        errors = []
        for q in questions:
            try:
                QuestionMarkScheme(**q)
            except ValidationError as e:
                errors.append((q.get("question_number", "unknown"), e))
        return errors

    @field_validator("questions")
    @classmethod
    def validate_question_numbers_unique(
        cls, questions: list[QuestionMarkScheme]
    ) -> list[QuestionMarkScheme]:
        """Ensure question numbers are unique."""
        question_numbers = [q.question_number for q in questions]
        validate_unique_numbers(question_numbers, "Question numbers")
        return questions

    @model_validator(mode="after")
    def validate_marks_total(self) -> "MarkSchemeInput":
        """Validate paper total_marks equals sum of all question marks from criteria.

        For each question, sums only non-GENERAL criteria (GENERAL has 0 marks).
        Then validates paper total matches sum of question totals.
        """
        calculated_paper_total = sum(question.total_marks for question in self.questions)

        validate_sum_equals_total(
            calculated_paper_total,
            self.paper_instance.total_marks,
            "Mark scheme paper",
        )

        return self
