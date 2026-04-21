"""Cross-context validation for question submissions.

This module enforces the core rule: Each submission belongs to exactly ONE context.

Contexts:
- Practice: Individual question practice (student-controlled lifecycle)
- Paper: Full paper attempt (paper attempt-controlled lifecycle)

The validation prevents data integrity violations by ensuring a submission
cannot be linked to both practice_question_attempts AND question_attempts.

Design Rationale:
- Centralized validation prevents duplicate logic in both context repositories
- Single source of truth for cross-context rules
- Clear module boundary (one responsibility: context validation)
- No circular dependencies (only imports Tables constants, no other repositories)

Usage:
    from paperlab.data.repositories.marking import submission_contexts

    # Before linking to ANY context (practice or paper)
    submission_contexts.validate_submission_unlinked(submission_id, conn)
"""

from sqlite3 import Connection

from paperlab.config.constants import Tables


def validate_submission_unlinked(
    submission_id: int,
    conn: Connection,
) -> None:
    """Validate submission not linked to any context.

    Enforces rule: Submission must be unlinked before assigning to a context.

    This validation must be called before linking a submission to either
    practice_question_attempts or question_attempts tables.

    Args:
        submission_id: Submission to validate
        conn: Database connection

    Raises:
        ValueError: If submission already linked to practice or paper context

    Example:
        >>> # Before creating practice attempt
        >>> validate_submission_unlinked(123, conn)
        >>> # Raises if submission 123 already in either context

        >>> # Before creating question attempt
        >>> validate_submission_unlinked(456, conn)
        >>> # Raises if submission 456 already in either context
    """
    # Check practice context
    in_practice = conn.execute(
        f"SELECT 1 FROM {Tables.PRACTICE_QUESTION_ATTEMPTS} WHERE submission_id = ?",
        (submission_id,),
    ).fetchone()

    if in_practice:
        raise ValueError(f"Submission {submission_id} already linked to practice context.")

    # Check paper context
    in_paper = conn.execute(
        f"SELECT 1 FROM {Tables.QUESTION_ATTEMPTS} WHERE submission_id = ?",
        (submission_id,),
    ).fetchone()

    if in_paper:
        raise ValueError(f"Submission {submission_id} already linked to paper context.")
