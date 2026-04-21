"""Repository for submission_images table.

Handles image storage for student submissions.
Images are linked to submissions, not marking attempts.
"""

import sqlite3
from typing import Any


def create(
    submission_id: int,
    image_path: str,
    image_sequence: int,
    conn: sqlite3.Connection,
) -> int:
    """Store image for submission.

    Args:
        submission_id: Submission this image belongs to
        image_path: Path to image (logical path or R2 key)
        image_sequence: Sequence number (1-based)
        conn: Database connection

    Returns:
        image_id: Database ID of created image record

    Raises:
        sqlite3.IntegrityError: If sequence already exists for submission
    """
    cursor = conn.execute(
        """
        INSERT INTO submission_images (submission_id, image_path, image_sequence)
        VALUES (?, ?, ?)
        """,
        (submission_id, image_path, image_sequence),
    )
    image_id = cursor.lastrowid
    if image_id is None:
        raise RuntimeError("Failed to create submission image - no ID returned")
    return image_id


def count_images_for_submission(
    submission_id: int,
    conn: sqlite3.Connection,
) -> int:
    """Count images for verification.

    Args:
        submission_id: Submission to count images for
        conn: Database connection

    Returns:
        Number of images for this submission
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM submission_images WHERE submission_id = ?",
        (submission_id,),
    )
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def get_images_for_submission(
    submission_id: int,
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Get all images for submission (ordered by sequence).

    Args:
        submission_id: Submission to get images for
        conn: Database connection

    Returns:
        List of dicts with image data, ordered by sequence
    """
    cursor = conn.execute(
        """
        SELECT id, image_path, image_sequence, created_at
        FROM submission_images
        WHERE submission_id = ?
        ORDER BY image_sequence ASC
        """,
        (submission_id,),
    )

    images = []
    for row in cursor.fetchall():
        images.append(
            {
                "id": row[0],
                "image_path": row[1],
                "image_sequence": row[2],
                "created_at": row[3],
            }
        )

    return images
