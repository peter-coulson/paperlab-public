"""Repository for status derivation queries.

Provides read-only queries for deriving attempt status.
Used by API status endpoints for polling.

All database queries in repository layer, not API layer (per CLAUDE.md).
"""

from dataclasses import dataclass
from sqlite3 import Connection
from typing import Any

from paperlab.config.constants import Tables


@dataclass
class MarkingStats:
    """Marking statistics for paper attempt."""

    total_questions: int
    successful: int
    failed: int

    @property
    def total_marked(self) -> int:
        return self.successful + self.failed


def get_paper_marking_stats(
    attempt_id: int,
    paper_id: int,
    conn: Connection,
) -> MarkingStats:
    """Get marking statistics for paper attempt.

    Args:
        attempt_id: Paper attempt ID
        paper_id: Paper ID (for total question count)
        conn: Database connection

    Returns:
        MarkingStats with total_questions, successful, and failed counts
    """
    # Count total questions for paper
    total = conn.execute(
        f"SELECT COUNT(*) FROM {Tables.QUESTIONS} WHERE paper_id = ?",
        (paper_id,),
    ).fetchone()[0]

    # Get marking stats (latest attempt per submission)
    # Only count questions that have been submitted for this paper attempt
    query = f"""
        SELECT
            SUM(CASE WHEN ma.status = 'success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN ma.status != 'success' THEN 1 ELSE 0 END) as failed
        FROM {Tables.QUESTION_ATTEMPTS} qa
        JOIN {Tables.QUESTION_SUBMISSIONS} qs ON qa.submission_id = qs.id
        LEFT JOIN {Tables.MARKING_ATTEMPTS} ma ON qs.id = ma.submission_id
            AND ma.id = (
                SELECT id FROM {Tables.MARKING_ATTEMPTS}
                WHERE submission_id = qs.id
                ORDER BY attempted_at DESC
                LIMIT 1
            )
        WHERE qa.paper_attempt_id = ?
    """
    row = conn.execute(query, (attempt_id,)).fetchone()

    return MarkingStats(
        total_questions=total,
        successful=row[0] or 0,
        failed=row[1] or 0,
    )


def get_failed_questions(
    attempt_id: int,
    conn: Connection,
) -> list[dict[str, Any]]:
    """Get list of failed questions with error details.

    Args:
        attempt_id: Paper attempt ID
        conn: Database connection

    Returns:
        List of dicts with question_number, error_type (from status), error_message
    """
    query = f"""
        SELECT
            q.question_number,
            ma.status as error_type,
            ma.error_message
        FROM {Tables.QUESTION_ATTEMPTS} qa
        JOIN {Tables.QUESTION_SUBMISSIONS} qs ON qa.submission_id = qs.id
        JOIN {Tables.QUESTIONS} q ON qs.question_id = q.id
        JOIN {Tables.MARKING_ATTEMPTS} ma ON qs.id = ma.submission_id
        WHERE qa.paper_attempt_id = ?
        AND ma.status != 'success'
        AND ma.id = (
            SELECT id FROM {Tables.MARKING_ATTEMPTS}
            WHERE submission_id = qs.id
            ORDER BY attempted_at DESC
            LIMIT 1
        )
        ORDER BY q.question_number
    """
    rows = conn.execute(query, (attempt_id,)).fetchall()

    return [
        {
            "question_number": row[0],
            "error_type": row[1],
            "error_message": row[2],
        }
        for row in rows
    ]


def get_latest_marking_attempt(
    submission_id: int | None,
    conn: Connection,
) -> dict[str, Any] | None:
    """Get latest marking attempt for submission.

    Args:
        submission_id: Question submission ID (can be None for drafts)
        conn: Database connection

    Returns:
        Dict with id, status, error_message, or None if no attempts
    """
    if submission_id is None:
        return None

    query = f"""
        SELECT id, status, error_message
        FROM {Tables.MARKING_ATTEMPTS}
        WHERE submission_id = ?
        ORDER BY attempted_at DESC
        LIMIT 1
    """
    row = conn.execute(query, (submission_id,)).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "status": row[1],  # 'success', 'parse_error', 'rate_limit', 'timeout', 'llm_error'
        "error_message": row[2],  # NULL for success, populated for failures
    }
