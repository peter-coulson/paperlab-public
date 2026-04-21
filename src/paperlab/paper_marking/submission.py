"""Paper submission service.

Handles paper attempt submission (validation + timestamp update).

Usage:
    from paperlab.paper_marking import submission
    from paperlab.data.database import connection

    with connection() as conn:
        submission.submit_paper_attempt(attempt_id, conn)
        conn.commit()
"""

from sqlite3 import Connection

from paperlab.data.repositories.marking import paper_attempts
from paperlab.paper_marking import validation


def submit_paper_attempt(paper_attempt_id: int, conn: Connection) -> None:
    """Mark paper attempt as submitted.

    Validates all questions submitted, sets submitted_at timestamp.
    Does NOT trigger marking (orchestration decides when to mark).
    Does NOT commit (caller controls transaction).

    Args:
        paper_attempt_id: Paper attempt ID
        conn: Database connection

    Raises:
        ValueError: If validation fails (uses ErrorMessages constants)
    """
    # 1. Validate ready for submission (delegated to validation service)
    validation.validate_paper_attempt_ready_for_submission(paper_attempt_id, conn)

    # 2. Update submitted_at timestamp (delegated to repository)
    paper_attempts.mark_as_submitted(paper_attempt_id, conn)

    # Caller commits transaction
