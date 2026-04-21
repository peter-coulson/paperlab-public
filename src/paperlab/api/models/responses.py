"""API response models for home screen endpoints.

These models transform domain data into API responses.
Uses from_domain() pattern to filter internal fields.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PaperAttemptListItem(BaseModel):
    """Response model for paper attempts in list (Home screen - Papers tab)."""

    id: int
    attempt_uuid: str
    paper_name: str
    exam_date: str
    created_at: datetime
    submitted_at: datetime | None
    completed_at: datetime | None
    grade: str | None

    model_config = ConfigDict(populate_by_name=True)  # Allow snake_case

    @classmethod
    def from_domain(cls, attempt: dict[str, Any]) -> "PaperAttemptListItem":
        """Convert domain dict to API response.

        Args:
            attempt: Dict from paper_attempts.get_attempts_for_student()
                    Contains: id, attempt_uuid, paper_name, exam_date,
                             created_at, submitted_at, completed_at, grade

        Returns:
            PaperAttemptListItem with public fields only
        """
        return cls(
            id=attempt["id"],
            attempt_uuid=attempt["attempt_uuid"],
            paper_name=attempt["paper_name"],
            exam_date=str(attempt["exam_date"]) if attempt["exam_date"] is not None else "",
            created_at=attempt["created_at"],
            submitted_at=attempt["submitted_at"],
            completed_at=attempt["completed_at"],
            grade=attempt["grade"],
        )


class QuestionAttemptResponse(BaseModel):
    """Response model for practice question attempts (Home screen - Questions tab)."""

    id: int
    attempt_uuid: str
    question_display: str  # e.g., "Q13"
    paper_name: str  # e.g., "Paper 3 (Calculator)"
    exam_date: str  # e.g., "2023-11-13"
    created_at: datetime
    submitted_at: datetime | None
    completed_at: datetime | None
    marks_awarded: int | None  # Sum of marks awarded (only for completed)
    marks_available: int | None  # Total marks available (only for completed)

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_domain(cls, attempt: dict[str, Any]) -> "QuestionAttemptResponse":
        """Convert domain dict to API response.

        Args:
            attempt: Dict from practice.get_attempts_for_student()
                    Contains: id, attempt_uuid, question_display, paper_name,
                             exam_date, created_at, submitted_at, completed_at,
                             marks_awarded, marks_available

        Returns:
            QuestionAttemptResponse with public fields only
        """
        return cls(
            id=attempt["id"],
            attempt_uuid=attempt["attempt_uuid"],
            question_display=attempt["question_display"],
            paper_name=attempt["paper_name"],
            exam_date=str(attempt["exam_date"]) if attempt["exam_date"] is not None else "",
            created_at=attempt["created_at"],
            submitted_at=attempt["submitted_at"],
            completed_at=attempt["completed_at"],
            marks_awarded=attempt["marks_awarded"],
            marks_available=attempt["marks_available"],
        )
