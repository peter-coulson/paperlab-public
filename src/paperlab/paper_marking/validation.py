"""Paper marking validation service.

Validates paper attempts are ready for submission.

Usage:
    from paperlab.paper_marking import validation
    from paperlab.data.database import get_connection

    conn = get_connection()
    try:
        validation.validate_paper_attempt_ready_for_submission(attempt_id, conn)
        # Proceed with submission
    except ValueError as e:
        print(f"Validation failed: {e}")
"""

from sqlite3 import Connection

from paperlab.config.constants import ErrorMessages
from paperlab.data.repositories.marking import paper_attempts, question_attempts, questions


def validate_paper_attempt_ready_for_submission(
    paper_attempt_id: int,
    conn: Connection,
) -> None:
    """Validate paper attempt can be submitted.

    Checks:
    1. Attempt exists and not already complete (completed_at IS NULL)
    2. All questions have latest submissions
    3. At least one non-inherited submission (prevents zero-effort retry)

    Note: Does NOT check submitted_at to allow retry workflow.
    If marking fails after Phase 1 (submitted_at set), user can retry by
    calling attempt_submit again. Idempotent marking skips already-marked questions.

    Args:
        paper_attempt_id: Paper attempt ID
        conn: Database connection

    Raises:
        ValueError: If validation fails with ErrorMessages constant
    """
    # 1. Check attempt exists and not already complete
    attempt = paper_attempts.get_attempt(paper_attempt_id, conn)
    if attempt.completed_at is not None:
        raise ValueError(
            ErrorMessages.PAPER_ALREADY_COMPLETE.format(
                attempt_id=paper_attempt_id, completed_at=attempt.completed_at
            )
        )

    # 2. Get total questions for this paper (delegate to repository)
    total_questions = questions.count_questions(attempt.paper_id, conn)

    # 3. Check all questions have latest submissions
    latest = question_attempts.get_all_latest_attempts(paper_attempt_id, conn)
    if len(latest) != total_questions:
        raise ValueError(
            ErrorMessages.PAPER_INCOMPLETE.format(expected=total_questions, found=len(latest))
        )

    # 4. Check at least one non-inherited submission (delegate to repository)
    new_count = question_attempts.count_non_inherited_attempts(paper_attempt_id, conn)

    if new_count == 0:
        source_id = attempt.inherited_from_attempt or "unknown"
        raise ValueError(
            ErrorMessages.NO_NEW_SUBMISSIONS.format(count=len(latest), source_id=source_id)
        )
