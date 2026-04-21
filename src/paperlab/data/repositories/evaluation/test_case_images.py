"""Test case images repository.

Manages multiple images per test case with sequence ordering.
Mirrors the pattern used in production (submission_images).

Design principles:
- Bulk operations for performance
- Sequence ordering preserves image presentation order
- Cascading deletes via foreign key
- First image uniqueness enforced at schema level (prevents correlation collisions)
"""

import sqlite3


def create_test_case_image(
    test_case_id: int,
    image_path: str,
    image_sequence: int,
    conn: sqlite3.Connection,
) -> int:
    """Create single test case image.

    Args:
        test_case_id: Test case ID
        image_path: Path to image (logical path, relative to project root)
        image_sequence: Sequence number (1-indexed, determines order)
        conn: Database connection

    Returns:
        Image record ID
    """
    cursor = conn.execute(
        """
        INSERT INTO test_case_images (
            test_case_id,
            image_path,
            image_sequence
        )
        VALUES (?, ?, ?)
        """,
        (test_case_id, image_path, image_sequence),
    )
    image_id = cursor.lastrowid
    if image_id is None:
        raise ValueError("Failed to get image_id after INSERT")
    return image_id


def create_test_case_images_batch(
    test_case_id: int,
    image_paths: list[str],
    conn: sqlite3.Connection,
) -> None:
    """Create multiple images for test case in bulk.

    Automatically assigns sequence numbers starting from 1.

    Args:
        test_case_id: Test case ID
        image_paths: List of image paths (order determines sequence)
        conn: Database connection
    """
    if not image_paths:
        raise ValueError("Must provide at least one image path")

    # Build batch data with sequence numbers
    batch_data = [
        (test_case_id, image_path, idx) for idx, image_path in enumerate(image_paths, start=1)
    ]

    conn.executemany(
        """
        INSERT INTO test_case_images (
            test_case_id,
            image_path,
            image_sequence
        )
        VALUES (?, ?, ?)
        """,
        batch_data,
    )


def get_images_for_test_case(
    test_case_id: int,
    conn: sqlite3.Connection,
) -> list[dict[str, int | str]]:
    """Get all images for test case, ordered by sequence.

    Returns:
        List of dicts with keys: id, image_path, image_sequence, created_at
    """
    cursor = conn.execute(
        """
        SELECT
            id,
            image_path,
            image_sequence,
            created_at
        FROM test_case_images
        WHERE test_case_id = ?
        ORDER BY image_sequence
        """,
        (test_case_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_first_image_for_test_case(
    test_case_id: int,
    conn: sqlite3.Connection,
) -> str | None:
    """Get first image path for test case (sequence = 1).

    Convenience function for correlation/display purposes.

    Returns:
        First image path, or None if no images exist
    """
    from paperlab.config.constants import ImageSequence

    cursor = conn.execute(
        """
        SELECT image_path
        FROM test_case_images
        WHERE test_case_id = ? AND image_sequence = ?
        """,
        (test_case_id, ImageSequence.FIRST),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def count_images_for_test_case(
    test_case_id: int,
    conn: sqlite3.Connection,
) -> int:
    """Count images for test case."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM test_case_images WHERE test_case_id = ?",
        (test_case_id,),
    )
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def get_by_first_image_path(
    first_image_path: str,
    conn: sqlite3.Connection,
) -> dict[str, int | str] | None:
    """Get test case by first image path.

    Used for validation: ensures first image paths are unique across test cases.
    This is critical for correlation - if two test cases use the same first image,
    we cannot determine which test case a marking response belongs to.

    Args:
        first_image_path: Path to first image (image_sequence = 1)
        conn: Database connection

    Returns:
        Dict with test_case_id if found, None otherwise

    Example:
        >>> # Check for collision before creating test case
        >>> existing = get_by_first_image_path("data/work/answer.png", conn)
        >>> if existing:
        ...     test_case_id = existing['test_case_id']
        ...     raise ValueError(f"First image already used by test case {test_case_id}")
    """
    from paperlab.config.constants import ImageSequence

    cursor = conn.execute(
        """
        SELECT
            tci.test_case_id,
            tc.test_case_json_path,
            tc.paper_identifier,
            tc.question_number
        FROM test_case_images tci
        JOIN test_cases tc ON tc.id = tci.test_case_id
        WHERE tci.image_path = ? AND tci.image_sequence = ?
        """,
        (first_image_path, ImageSequence.FIRST),
    )
    row = cursor.fetchone()
    return dict(row) if row else None
