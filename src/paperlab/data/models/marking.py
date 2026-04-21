"""Data models for marking domain.

These dataclasses represent rows from marking database tables.
They provide type safety and structured access to database records.

Models are kept minimal - pure data containers with no business logic.
Business logic lives in repositories and domain services.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaperAttempt:
    """Paper attempt record from paper_attempts table.

    Represents one sitting of a paper by a student (Attempt #1, #2, etc.).
    """

    id: int
    attempt_uuid: str
    student_id: int
    paper_id: int
    inherited_from_attempt: int | None
    submitted_at: datetime | None
    completed_at: datetime | None
    deleted_at: datetime | None
    deleted_by: int | None
    created_at: datetime


@dataclass
class QuestionAttempt:
    """Question attempt record from question_attempts table.

    Links paper attempts to question submissions.
    Supports multiple attempts per question (re-submissions).
    """

    id: int
    paper_attempt_id: int
    submission_id: int
    inherited_from_attempt: int | None
    created_at: datetime


@dataclass
class PaperResult:
    """Paper result record from paper_results table.

    Stores calculated grade for a completed paper attempt.
    """

    id: int
    paper_attempt_id: int
    total_marks_awarded: int
    total_marks_available: int
    percentage: float
    indicative_grade: str | None
    calculated_at: datetime


@dataclass
class GradeBoundary:
    """Grade boundary record from grade_boundaries table.

    Notional component grade boundaries for individual papers.
    """

    id: int
    paper_id: int
    grade: str
    min_raw_marks: int
    display_order: int
    created_at: datetime
