"""Paper marking service.

Handles batch marking orchestration for paper attempts.

Usage:
    from paperlab.paper_marking import marking
    from paperlab.services.claude_client import ClaudeClient
    from paperlab.data.database import connection

    llm_client = ClaudeClient(api_key="...")
    with connection() as conn:
        result = marking.mark_paper_attempt(
            paper_attempt_id=1,
            llm_client=llm_client,
            llm_model_id=1,
            conn=conn
        )
"""

from sqlite3 import Connection

from paperlab.data.repositories.marking import marking_attempts, question_attempts
from paperlab.marking.batch_marker import BatchMarker, BatchMarkingResult
from paperlab.services.llm_client import LLMClient


def mark_paper_attempt(
    paper_attempt_id: int,
    llm_client: LLMClient,
    llm_model_id: int,
    conn: Connection,
) -> BatchMarkingResult:
    """Mark all submissions needing marking for paper attempt.

    Idempotent: Skips submissions that already have successful marking.
    Can be called multiple times (e.g., retry after failures).

    This follows the batch orchestrator pattern: queries use the provided
    connection (CLI-controlled transaction), then delegates to BatchMarker
    which creates per-thread connections for parallel marking.

    Args:
        paper_attempt_id: Paper attempt to mark
        llm_client: LLM client for marking
        llm_model_id: Model ID to use for marking
        conn: Database connection (for query phase)

    Returns:
        BatchMarkingResult with successful/failed counts
    """
    # 1. Query phase: Use provided connection (CLI-controlled transaction)
    latest_attempts = question_attempts.get_all_latest_attempts(paper_attempt_id, conn)
    submission_ids = [qa.submission_id for qa in latest_attempts]

    # 2. Filter to submissions needing marking
    unmarked_ids = marking_attempts.get_unmarked_submissions(submission_ids, conn)

    # 3. Marking phase: BatchMarker creates per-thread connections (thread-safe)
    # Note: BatchMarker cannot use provided conn (SQLite threading constraint)
    batch_marker = BatchMarker(llm_client)
    result = batch_marker.mark_batch(
        submission_ids=unmarked_ids,
        llm_model_id=llm_model_id,
    )

    return result
