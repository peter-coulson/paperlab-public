"""Models for marking domain.

Contains:
- MarkingRequest: Domain value object for LLM marking requests (input)
- MarkingCriterionResult: Single criterion result from LLM (output)
- LLMMarkingResponse: Complete LLM response structure (output)

Design principles:
- Strict validation of required fields and types
- Basic constraints via Pydantic Field validators
- Clear field naming matching database schema
- Layer 1 only - business logic lives in validators.py

Model to SQL Table Mapping:
- MarkingCriterionResult → question_marking_results (per criterion)
- LLMMarkingResponse → validation only (not stored directly)
  - Stored across marking_attempts (metadata) + question_marking_results (results)
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field

# =============================================================================
# Request Models (Input to LLM)
# =============================================================================


@dataclass(frozen=True)
class MarkingRequest:
    """Domain value object containing all data needed for marking.

    This is a provider-agnostic data structure. Each LLM client is responsible
    for formatting this into its specific prompt/API format.

    Attributes:
        system_instructions: Role, principles, marking constraints
        question_content: Question and mark scheme (interleaved format)
        abbreviations: Mark scheme abbreviation table (M, A, B, etc.)
        expected_structure: Criterion IDs and marks for validation/schema

    Design:
        - Immutable (frozen=True) - value object semantics
        - Provider-agnostic - no knowledge of Claude/OpenAI differences
        - Contains WHAT to mark, not HOW to format the request
    """

    system_instructions: str
    question_content: str
    abbreviations: str
    expected_structure: dict[str, list[dict[str, int | str]]]


# =============================================================================
# Response Models (Output from LLM)
# =============================================================================


class MarkingCriterionResult(BaseModel):
    """Single criterion marking result from LLM response.

    Represents one criterion's marking outcome. LLM response contains
    a list of these, one per marking criterion.

    IMPORTANT: GENERAL criteria must NOT appear in responses - they are
    guidance only, not marking criteria.

    Layer 1 validation (this model):
    - Types correct (int, str, float)
    - marks_awarded >= 0
    - confidence_score in range [0.0, 1.0]
    - feedback is non-empty string

    Layer 2 validation (validators.py):
    - criterion_id exists in database
    - marks_awarded <= marks_available for this criterion
    - No GENERAL criteria present
    - All expected criteria marked (no missing)
    - No duplicate criteria
    """

    criterion_id: int = Field(
        description="Database ID of mark criterion being evaluated",
        gt=0,  # Must be positive (valid database ID)
    )

    observation: str = Field(
        default="",
        description="Internal reasoning about the student work (not shown to students)",
    )

    feedback: str = Field(
        description="Specific feedback for this criterion",
        min_length=1,  # Must provide feedback
    )

    marks_awarded: int = Field(
        description="Marks awarded for this criterion",
        ge=0,  # Cannot be negative
    )

    confidence_score: float = Field(
        description="LLM confidence in this marking decision (0.0 = low, 1.0 = high)",
        ge=0.0,
        le=1.0,
    )


class LLMMarkingResponse(BaseModel):
    """Complete LLM marking response structure.

    Top-level validation model for LLM JSON responses. Contains list of
    criterion results that match the expected JSON structure from prompt.

    This model is for validation only - storage happens across TWO tables:
    1. marking_attempts (metadata: submission, model, timing, status, raw response)
    2. question_marking_results (individual criterion results from this model)

    Layer 1 validation (this model):
    - Structure matches expected JSON
    - Each result passes MarkingCriterionResult validation

    Layer 2 validation (validators.py):
    - Results match mark scheme for question
    - No GENERAL criteria present
    - All marking criteria covered
    - No duplicates

    Example JSON:
        {
          "results": [
            {
              "criterion_id": 1,
              "marks_awarded": 1,
              "feedback": "Correct application of power rule",
              "confidence_score": 0.95
            },
            {
              "criterion_id": 2,
              "marks_awarded": 0,
              "feedback": "Answer incorrect: expected 2x+5, got 2x",
              "confidence_score": 0.90
            }
          ]
        }
    """

    results: list[MarkingCriterionResult] = Field(
        description="List of criterion marking results",
        min_length=1,  # Must mark at least one criterion
    )
