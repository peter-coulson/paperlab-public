"""Pydantic models for paper structure loading.

These models define the contract for paper JSON files that will be loaded
into the database. They provide type safety and validation before business
rule validation and database insertion.

Model to SQL Table Mapping:
- ExamTypeBase → exam_types (lookup only)
- PaperInstanceBase → papers
- Question → questions
- QuestionPart → question_parts
- ContentBlock → question_content_blocks

Key Concepts:
- NULL part: display_order=0, part_letter=None, contains general content
- Display ordering: Parts start at 0 (NULL), content blocks start at 1
- Loading order: Paper must be loaded before mark scheme
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from paperlab.config import (
    BlockType,
    DisplayOrder,
    FieldLengthLimits,
    ValidationLimits,
    generate_paper_identifier,
)
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
# Grade Boundary Model
# ============================================================================


class GradeBoundaryInput(BaseModel):
    """Grade boundary from notional component boundaries.

    Published by exam boards for individual papers to reflect paper difficulty.
    Used to calculate indicative grades from raw marks.

    Note: Indicative grades are NOT official qualification grades. Official
    grades combine all papers in a qualification using different boundaries.
    """

    grade: str = Field(..., max_length=10, description="Grade label (e.g., '9', '8', 'A*', 'U')")
    min_raw_marks: int = Field(..., ge=0, description="Minimum raw marks required for this grade")
    display_order: int = Field(
        ..., ge=1, description="Display order (1 = highest grade, increasing = lower grades)"
    )


# ============================================================================
# Content Block Model
# ============================================================================


class ContentBlock(BaseModel):
    """A single content block within a question or question part.

    Can be text or diagram only (matches database schema constraints).
    For text blocks: content_text is required.
    For diagram blocks: diagram_description is required.

    Note: Diagram image paths are derived from convention at the API layer,
    not stored in database. See /api/diagrams endpoint.
    """

    block_type: Literal["text", "diagram"] = Field(..., description="Type of content block")
    display_order: int = Field(..., ge=1, description="Display order within parent (starts at 1)")

    # Content fields
    content_text: str | None = Field(
        None,
        max_length=FieldLengthLimits.CONTENT_TEXT_MAX,
        description="Text content (LaTeX math with $...$ or $$...$$)",
    )
    diagram_description: str | None = Field(
        None,
        max_length=FieldLengthLimits.DIAGRAM_DESCRIPTION_MAX,
        description="Natural language description of diagram for LLM context",
    )

    @field_validator("content_text", "diagram_description")
    @classmethod
    def strip_content(cls, v: str | None) -> str | None:
        """Strip whitespace from content fields."""
        if v is not None:
            return v.strip()
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate content fields based on block_type.

        - text: requires content_text, diagram_description must be None
        - diagram: requires diagram_description, content_text must be None
        """
        if self.block_type == BlockType.TEXT:
            if self.content_text is None:
                raise ValueError(
                    f"block_type '{BlockType.TEXT}' requires content_text to be populated"
                )
            if self.diagram_description is not None:
                raise ValueError(f"block_type '{BlockType.TEXT}' cannot have diagram_description")
        elif self.block_type == BlockType.DIAGRAM:
            if self.diagram_description is None:
                raise ValueError(
                    f"block_type '{BlockType.DIAGRAM}' requires diagram_description to be populated"
                )
            if self.content_text is not None:
                raise ValueError(f"block_type '{BlockType.DIAGRAM}' cannot have content_text")


# ============================================================================
# Paper Structure Models
# ============================================================================


class QuestionPart(QuestionPartBase):
    """Question part in paper - contains question text.

    Inherits part identity (part_letter, sub_part_letter, display_order) from QuestionPartBase.
    Adds content_blocks for question text and diagrams.

    Can represent:
    - NULL part (display_order=0, part_letter=None) - general question content
    - Lettered part (display_order=1+, part_letter='a', 'b', etc.)
    - Sub-part (display_order=1+, part_letter='a', sub_part_letter='i')

    The NULL part (display_order=0) contains general content that applies to the whole
    question before any lettered parts.
    """

    content_blocks: list[ContentBlock] = Field(
        ...,
        min_length=0,  # Can be empty for structural NULL parts
        max_length=ValidationLimits.MAX_CONTENT_BLOCKS_PER_PART,
        description="Question text and diagrams",
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


class Question(BaseModel):
    """A complete question with all parts.

    Parts include the NULL part (display_order=0, part_letter=None) which contains
    general question content that applies before any lettered parts.

    All parts are stored in a single list with sequential display_order starting from 0:
    - display_order=0: NULL part (general content)
    - display_order=1+: Lettered parts (a, b, c, etc.)
    """

    question_number: int = Field(..., ge=1, description="Question number on paper")
    total_marks: int = Field(..., ge=0, description="Total marks for this question")
    parts: list[QuestionPart] = Field(
        ...,
        min_length=1,
        max_length=ValidationLimits.MAX_PARTS_PER_QUESTION,
        description="All parts including NULL part (display_order=0)",
    )

    @field_validator("parts")
    @classmethod
    def validate_parts_order(cls, parts: list[QuestionPart]) -> list[QuestionPart]:
        """Ensure parts display_order is sequential starting from 0."""
        validate_sequential_numbering(parts, "display_order", start_from=DisplayOrder.NULL_PART)
        return parts

    @model_validator(mode="after")
    def validate_null_part_exists(self) -> "Question":
        """Ensure NULL part exists at display_order=0 with correct properties.

        Uses shared validation function to enforce NULL entity pattern.
        See validate_null_entity_exists() for detailed requirements.
        """
        validate_null_entity_exists(
            entities=self.parts,
            question_number=self.question_number,
            entity_type="part",
        )
        return self


class PaperStructureInput(BaseModel):
    """Complete paper structure from LLM-generated JSON.

    Top-level model for paper loading pipeline. Validates the entire paper JSON file
    before business rule validation and database insertion.
    """

    exam_type: ExamTypeBase = Field(
        ..., description="Exam type (board, level, subject, paper code, display name)"
    )
    paper_instance: PaperInstanceBase = Field(
        ..., description="Paper instance metadata (date, marks, identifier)"
    )
    grade_boundaries: list[GradeBoundaryInput] = Field(
        ...,
        min_length=1,
        description="Notional component grade boundaries for this paper",
    )
    questions: list[Question] = Field(
        ...,
        min_length=1,
        max_length=ValidationLimits.MAX_QUESTIONS_PER_PAPER,
        description="Questions on this paper",
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
        """Validate questions individually, returning errors with question numbers.

        Useful for debugging large paper JSONs - validates each question independently
        and reports which questions have errors without stopping at the first failure.

        Args:
            questions: List of question dictionaries to validate

        Returns:
            List of tuples (question_number, error) for questions that failed validation.
            Empty list if all questions are valid.

        Example:
            errors = PaperStructureInput.validate_questions_batch(questions_data)
            for q_num, error in errors:
                print(f"Question {q_num}: {error}")
        """
        errors = []
        for q in questions:
            try:
                Question(**q)
            except ValidationError as e:
                errors.append((q.get("question_number", "unknown"), e))
        return errors

    @field_validator("questions")
    @classmethod
    def validate_question_numbers_unique(cls, questions: list[Question]) -> list[Question]:
        """Ensure question numbers are unique."""
        question_numbers = [q.question_number for q in questions]
        validate_unique_numbers(question_numbers, "Question numbers")
        return questions

    @field_validator("questions")
    @classmethod
    def validate_question_numbers_sequential(cls, questions: list[Question]) -> list[Question]:
        """Ensure question numbers are sequential starting from 1.

        This catches data entry errors and ensures questions are in logical order.
        """
        question_numbers = [q.question_number for q in questions]
        validate_sequential_numbering(question_numbers, "question_number", start_from=1)
        return questions

    @model_validator(mode="after")
    def validate_paper_marks_total(self) -> "PaperStructureInput":
        """Validate paper total_marks equals sum of all question total_marks."""
        calculated_paper_total = sum(q.total_marks for q in self.questions)

        validate_sum_equals_total(
            calculated_paper_total,
            self.paper_instance.total_marks,
            "Paper",
        )

        return self

    @model_validator(mode="after")
    def validate_grade_boundaries(self) -> "PaperStructureInput":
        """Validate grade boundary ordering and uniqueness, auto-add U grade."""
        # Check if U grade was provided in input
        u_grades = [b for b in self.grade_boundaries if b.grade == "U"]
        if u_grades:
            # If U grade provided, validate it has min_raw_marks=0
            if u_grades[0].min_raw_marks != 0:
                raise ValueError("'U' grade must have min_raw_marks=0")
            if len(u_grades) > 1:
                raise ValueError("Duplicate 'U' grades in grade_boundaries")
        else:
            # Auto-add U grade at the end
            max_display_order = max((b.display_order for b in self.grade_boundaries), default=0)
            self.grade_boundaries.append(
                GradeBoundaryInput(grade="U", min_raw_marks=0, display_order=max_display_order + 1)
            )

        # Check unique grades (after U grade added)
        grades = [b.grade for b in self.grade_boundaries]
        if len(grades) != len(set(grades)):
            raise ValueError("Duplicate grades in grade_boundaries")

        # Check unique display_order
        orders = [b.display_order for b in self.grade_boundaries]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate display_order in grade_boundaries")

        # Check boundaries are ordered by descending min_raw_marks (excluding U grade)
        boundaries_sorted = sorted(self.grade_boundaries, key=lambda b: b.display_order)
        for i in range(len(boundaries_sorted) - 1):
            current = boundaries_sorted[i]
            next_boundary = boundaries_sorted[i + 1]

            # U grade is special case - skip validation if next is U
            if next_boundary.grade == "U":
                continue

            if current.min_raw_marks <= next_boundary.min_raw_marks:
                raise ValueError(
                    f"Grade boundaries must be ordered by descending min_raw_marks. "
                    f"Grade '{current.grade}' (min {current.min_raw_marks} marks) "
                    f"must have higher threshold than grade '{next_boundary.grade}' "
                    f"(min {next_boundary.min_raw_marks} marks)"
                )

        return self
