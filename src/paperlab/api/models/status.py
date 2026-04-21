"""API models for status endpoints (Flow 3).

Pydantic models for polling marking status.
"""

from typing import Literal

from pydantic import BaseModel


class ProgressInfo(BaseModel):
    """Marking progress for paper attempt."""

    questions_total: int
    questions_completed: int
    questions_in_progress: int
    questions_failed: int


class FailedQuestion(BaseModel):
    """Details of a failed question marking."""

    question_number: int
    error_type: str  # 'parse_error', 'rate_limit', 'timeout', 'llm_error'
    error_message: str


class ErrorInfo(BaseModel):
    """Error details for failed paper attempt."""

    message: str
    failed_questions: list[FailedQuestion]


class PaperStatusResponse(BaseModel):
    """Response for GET /api/attempts/papers/{id}/status."""

    attempt_id: int
    status: Literal["draft", "submitted", "marking", "ready_for_grading", "completed", "failed"]
    progress: ProgressInfo | None = None
    error: ErrorInfo | None = None


class QuestionErrorInfo(BaseModel):
    """Error details for failed question attempt."""

    error_type: str
    error_message: str
    can_retry: bool


class QuestionStatusResponse(BaseModel):
    """Response for GET /api/attempts/questions/{id}/status."""

    attempt_id: int
    status: Literal["draft", "submitted", "completed", "failed"]
    error: QuestionErrorInfo | None = None
