"""Repository for marking_attempts table.

Handles marking attempt records (success and failure).
Each submission can have multiple attempts, but only one success.
"""

import sqlite3
from typing import Any


def create(
    submission_id: int,
    llm_model_id: int,
    system_prompt: str,
    user_prompt: str,
    status: str,
    processing_time_ms: int,
    input_tokens: int,
    output_tokens: int,
    raw_response: str | None,
    response_received: str | None,
    error_message: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create marking attempt record.

    Args:
        submission_id: Submission being marked
        llm_model_id: Model used for marking
        system_prompt: System prompt sent to LLM
        user_prompt: User prompt sent to LLM
        status: 'success', 'parse_error', 'rate_limit', 'timeout', 'llm_error'
        processing_time_ms: Time taken for marking
        input_tokens: Tokens in prompt
        output_tokens: Tokens in response
        raw_response: Raw LLM response (can be None if call failed)
        response_received: Validated JSON (only for status='success')
        error_message: Error details (only for status!='success')
        conn: Database connection

    Returns:
        attempt_id: Database ID of created attempt

    Raises:
        sqlite3.IntegrityError: If CHECK constraint violated
    """
    cursor = conn.execute(
        """
        INSERT INTO marking_attempts (
            submission_id, llm_model_id, system_prompt, user_prompt,
            status, processing_time_ms, input_tokens, output_tokens,
            raw_response, response_received, error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id,
            llm_model_id,
            system_prompt,
            user_prompt,
            status,
            processing_time_ms,
            input_tokens,
            output_tokens,
            raw_response,
            response_received,
            error_message,
        ),
    )
    attempt_id = cursor.lastrowid
    if attempt_id is None:
        raise RuntimeError("Failed to create marking attempt - no ID returned")
    return attempt_id


def exists(attempt_id: int, conn: sqlite3.Connection) -> bool:
    """Check if attempt exists.

    Args:
        attempt_id: Attempt to check
        conn: Database connection

    Returns:
        True if attempt exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM marking_attempts WHERE id = ?",
        (attempt_id,),
    )
    result = cursor.fetchone()
    return result[0] > 0 if result else False


def count_all(conn: sqlite3.Connection) -> int:
    """Count total marking attempts across all statuses.

    Used for FK constraint checking (e.g., before deleting LLM models).

    Args:
        conn: Database connection

    Returns:
        Total count of marking attempts
    """
    cursor = conn.execute("SELECT COUNT(*) FROM marking_attempts")
    result = cursor.fetchone()
    return result[0] if result else 0


def get_successful_attempt_for_submission(
    submission_id: int,
    conn: sqlite3.Connection,
) -> dict[str, Any] | None:
    """Get successful marking attempt.

    Args:
        submission_id: Submission to get marking for
        conn: Database connection

    Returns:
        Dict with attempt data, or None if not marked yet
    """
    cursor = conn.execute(
        """
        SELECT id, llm_model_id, attempted_at, processing_time_ms,
               input_tokens, output_tokens, response_received
        FROM marking_attempts
        WHERE submission_id = ? AND status = 'success'
        ORDER BY attempted_at DESC
        LIMIT 1
        """,
        (submission_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": row[0],
        "llm_model_id": row[1],
        "attempted_at": row[2],
        "processing_time_ms": row[3],
        "input_tokens": row[4],
        "output_tokens": row[5],
        "response_received": row[6],
    }


def has_successful_attempt(
    submission_id: int,
    conn: sqlite3.Connection,
) -> bool:
    """Check if submission already successfully marked.

    Used for one-success-per-submission validation (pre-API check).
    Application layer enforces this before calling LLM API to avoid
    duplicate expensive API calls.

    Args:
        submission_id: Submission to check
        conn: Database connection

    Returns:
        True if submission has successful marking, False otherwise
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*) FROM marking_attempts
        WHERE submission_id = ? AND status = 'success'
        """,
        (submission_id,),
    )
    result = cursor.fetchone()
    return result[0] > 0 if result else False


def get_unmarked_submissions(
    submission_ids: list[int],
    conn: sqlite3.Connection,
) -> list[int]:
    """Filter submissions to those needing marking.

    Returns submission_ids that either:
    - Have no marking_attempt record, OR
    - Have only failed marking_attempts (error_type IS NOT NULL)

    Skips submissions with successful marking (error_type IS NULL).
    Used by batch marking to implement idempotency.

    Args:
        submission_ids: List of submission IDs to check
        conn: Database connection

    Returns:
        Filtered list of submission IDs needing marking

    Example:
        >>> all_ids = [1, 2, 3, 4]  # 4 submissions
        >>> # submission 1: marked successfully
        >>> # submission 2: marking failed
        >>> # submission 3: no marking attempt
        >>> # submission 4: marked successfully
        >>> get_unmarked_submissions(all_ids, conn)
        [2, 3]  # Returns failed + never marked
    """
    if not submission_ids:
        return []

    # Get submissions with successful marking
    placeholders = ",".join("?" * len(submission_ids))
    cursor = conn.execute(
        f"""
        SELECT DISTINCT submission_id
        FROM marking_attempts
        WHERE submission_id IN ({placeholders})
          AND status = 'success'
    """,
        submission_ids,
    )

    marked_ids = {row[0] for row in cursor.fetchall()}

    # Return submissions NOT in marked set
    return [sid for sid in submission_ids if sid not in marked_ids]
