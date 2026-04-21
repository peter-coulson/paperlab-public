"""Repository for question_submissions table.

Handles submission record creation and retrieval.
Submissions are created BEFORE marking attempts.
"""

import sqlite3
from typing import Any


def create(
    student_id: int,
    question_id: int,
    submission_uuid: str,
    conn: sqlite3.Connection,
) -> int:
    """Create submission record.

    Args:
        student_id: Student who submitted work
        question_id: Question being submitted
        submission_uuid: Unique identifier for this submission
        conn: Database connection

    Returns:
        submission_id: Database ID of created submission

    Raises:
        sqlite3.IntegrityError: If UUID already exists
    """
    cursor = conn.execute(
        """
        INSERT INTO question_submissions (student_id, question_id, submission_uuid)
        VALUES (?, ?, ?)
        """,
        (student_id, question_id, submission_uuid),
    )
    submission_id = cursor.lastrowid
    if submission_id is None:
        raise RuntimeError("Failed to create submission - no ID returned")
    return submission_id


def exists(submission_id: int, conn: sqlite3.Connection) -> bool:
    """Check if submission exists.

    Args:
        submission_id: Submission to check
        conn: Database connection

    Returns:
        True if submission exists, False otherwise
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM question_submissions WHERE id = ?",
        (submission_id,),
    )
    result = cursor.fetchone()
    return result[0] > 0 if result else False


def get_by_uuid(submission_uuid: str, conn: sqlite3.Connection) -> dict[str, Any] | None:
    """Get submission by UUID.

    Args:
        submission_uuid: UUID to look up
        conn: Database connection

    Returns:
        Dict with submission data, or None if not found
    """
    cursor = conn.execute(
        """
        SELECT id, student_id, question_id, submission_uuid, submitted_at
        FROM question_submissions
        WHERE submission_uuid = ?
        """,
        (submission_uuid,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": row[0],
        "student_id": row[1],
        "question_id": row[2],
        "submission_uuid": row[3],
        "submitted_at": row[4],
    }


def get_by_id(submission_id: int, conn: sqlite3.Connection) -> dict[str, Any] | None:
    """Get submission by ID.

    Args:
        submission_id: Submission ID to look up
        conn: Database connection

    Returns:
        Dict with submission data, or None if not found
    """
    cursor = conn.execute(
        """
        SELECT id, student_id, question_id, submission_uuid, submitted_at
        FROM question_submissions
        WHERE id = ?
        """,
        (submission_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": row[0],
        "student_id": row[1],
        "question_id": row[2],
        "submission_uuid": row[3],
        "submitted_at": row[4],
    }


def get_by_first_image(
    first_image_path: str,
    conn: sqlite3.Connection,
) -> dict[str, Any] | None:
    """Get submission by its first image path.

    Used for retry-extraction to find existing submissions when rebuilding correlation.

    Args:
        first_image_path: Path to first image (logical path)
        conn: Database connection

    Returns:
        Dict with submission data (id, student_id, question_id, submission_uuid, submitted_at),
        or None if not found
    """
    cursor = conn.execute(
        """
        SELECT qs.id, qs.student_id, qs.question_id, qs.submission_uuid, qs.submitted_at
        FROM question_submissions qs
        JOIN submission_images si ON si.submission_id = qs.id
        WHERE si.image_path = ?
          AND si.image_sequence = 1
        """,
        (first_image_path,),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": row[0],
        "student_id": row[1],
        "question_id": row[2],
        "submission_uuid": row[3],
        "submitted_at": row[4],
    }
