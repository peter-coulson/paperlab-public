"""Grading service for paper marking workflow.

Pipeline 5: Calculate final grade from marking results.
"""

import sqlite3

from paperlab.config import ErrorMessages
from paperlab.data.models.marking import PaperResult
from paperlab.data.repositories.marking import (
    grade_boundaries,
    paper_attempts,
    paper_results,
    papers,
    question_attempts,
    question_marking_results,
)


def grade_paper_attempt(paper_attempt_id: int, conn: sqlite3.Connection) -> PaperResult:
    """Calculate grade for paper attempt (Pipeline 5).

    Validates all questions marked successfully.
    Calculates total marks, applies grade boundaries.
    Sets completed_at (freezes paper attempt - immutable after this).

    Transaction: Does NOT commit - caller manages transaction.

    Args:
        paper_attempt_id: Paper attempt to grade
        conn: Database connection (caller-managed transaction)

    Returns:
        PaperResult with calculated grade

    Raises:
        ValueError: If already graded, missing marks, or validation fails
    """
    # 1. Validate paper attempt exists
    attempt = paper_attempts.get_attempt(paper_attempt_id, conn)
    if attempt is None:
        raise ValueError(ErrorMessages.PAPER_ATTEMPT_NOT_FOUND.format(attempt_id=paper_attempt_id))

    # 2. Validate not already graded
    if attempt.completed_at is not None:
        raise ValueError(
            ErrorMessages.PAPER_ALREADY_COMPLETE.format(
                attempt_id=paper_attempt_id, completed_at=attempt.completed_at
            )
        )

    # 3. Get latest submissions and validate completeness
    latest_attempts = question_attempts.get_all_latest_attempts(paper_attempt_id, conn)
    total_questions = papers.get_question_count(attempt.paper_id, conn)

    if len(latest_attempts) != total_questions:
        raise ValueError(
            f"Cannot grade incomplete paper: "
            f"expected {total_questions} questions, found {len(latest_attempts)}"
        )

    # 4. Calculate total marks from marking results
    total_marks_awarded = 0

    for qa in latest_attempts:
        # Get successful marking results for this submission
        results = question_marking_results.get_results_for_submission(qa.submission_id, conn)

        if not results:
            raise ValueError(
                f"Submission {qa.submission_id} has no successful marking results. "
                f"Cannot grade paper with unmarked questions."
            )

        # Sum marks awarded across all criteria for this question
        total_marks_awarded += sum(r["marks_awarded"] for r in results)

    # 5. Get total marks available and calculate percentage
    total_marks_available = papers.get_total_marks(attempt.paper_id, conn)

    # Defensive check: Validate marks in valid range
    if total_marks_available == 0:
        raise ValueError(f"Paper {attempt.paper_id} has zero total marks (data corruption)")

    if total_marks_awarded > total_marks_available:
        raise ValueError(
            f"Marking error: awarded {total_marks_awarded} marks but only "
            f"{total_marks_available} available (possible LLM hallucination or "
            f"mark scheme error)"
        )

    percentage = round((total_marks_awarded / total_marks_available) * 100, 2)

    # 6. Apply grade boundaries (see specs/grade-boundaries.md)
    indicative_grade = grade_boundaries.calculate_grade(
        raw_marks=total_marks_awarded, paper_id=attempt.paper_id, conn=conn
    )

    # 7. Store paper result (UNIQUE constraint prevents duplicate grading on race condition)
    try:
        paper_results.create_result(
            paper_attempt_id=paper_attempt_id,
            total_marks_awarded=total_marks_awarded,
            total_marks_available=total_marks_available,
            percentage=percentage,
            indicative_grade=indicative_grade,
            conn=conn,
        )
    except sqlite3.IntegrityError as e:
        # UNIQUE constraint on paper_attempt_id - concurrent grading detected
        if "paper_attempt_id" in str(e).lower() or "unique" in str(e).lower():
            raise ValueError(
                f"Paper attempt {paper_attempt_id} already graded (concurrent grading detected)"
            ) from e
        raise

    # 8. AUTO-DELETE SOURCE ATTEMPT (enforce invariant: no two completed attempts in chain)
    # This happens BEFORE setting completed_at to ensure atomic operation
    if attempt.inherited_from_attempt is not None:
        # Source attempt is guaranteed to be completed (validated at creation time)
        # This keeps UI clean - student only sees latest attempt, not similar previous attempts
        paper_attempts.soft_delete_attempt(
            paper_attempt_id=attempt.inherited_from_attempt,
            deleted_by=attempt.student_id,
            conn=conn,
        )

    # 9. Set completed_at (freeze paper attempt - IMMUTABLE after this)
    paper_attempts.mark_as_complete(paper_attempt_id, conn)

    # 10. Return result - caller commits transaction
    result = paper_results.get_result(paper_attempt_id, conn)
    if result is None:
        # Should never happen - we just created the result
        raise RuntimeError(f"Paper result not found after creation for attempt {paper_attempt_id}")
    return result
