"""Paper finalization service for Flow 2 API.

Handles the finalization of paper attempts including validation that all
questions have been submitted.

Per CLAUDE.md: API is transport, business logic lives here.
"""

from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Connection

from paperlab.data.repositories.marking import (
    paper_attempts,
    question_attempts,
    questions,
)


class PaperSubmissionError(ValueError):
    """Raised when paper submission validation fails."""

    pass


@dataclass
class PaperSubmissionResult:
    """Result of finalizing a paper attempt."""

    attempt_id: int
    submitted_at: datetime


def finalize_paper_attempt(
    attempt_id: int,
    conn: Connection,
) -> PaperSubmissionResult:
    """Finalize paper attempt after validating all questions submitted.

    Validates that all questions have submissions before marking as submitted.
    Does NOT commit - caller manages transaction.

    Args:
        attempt_id: Paper attempt ID to finalize
        conn: Database connection

    Returns:
        PaperSubmissionResult with attempt ID and submitted timestamp

    Raises:
        PaperSubmissionError: If not all questions have been submitted
        ValueError: If attempt not found
    """
    # Get attempt (raises ValueError if not found)
    attempt = paper_attempts.get_attempt(attempt_id, conn)

    # Validate all questions have submissions
    paper_questions = questions.get_all_with_marks(attempt.paper_id, conn)
    question_attempts_list = question_attempts.get_all_latest_attempts(attempt_id, conn)

    expected_count = len(paper_questions)
    actual_count = len(question_attempts_list)

    if actual_count != expected_count:
        raise PaperSubmissionError(
            f"Missing questions. Expected {expected_count}, got {actual_count}"
        )

    # Mark as submitted
    paper_attempts.mark_as_submitted(attempt_id, conn)

    # Get updated attempt for timestamp
    updated = paper_attempts.get_attempt(attempt_id, conn)
    if updated.submitted_at is None:
        raise PaperSubmissionError("Failed to set submitted_at timestamp")

    return PaperSubmissionResult(
        attempt_id=attempt_id,
        submitted_at=updated.submitted_at,
    )
