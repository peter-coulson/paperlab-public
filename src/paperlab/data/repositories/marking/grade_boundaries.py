"""Grade boundaries repository - manages notional component boundaries.

This module handles grade boundary data for papers. Grade boundaries are used
to calculate indicative grades from raw marks.

Key concepts:
- Notional component boundaries: Published by exam boards for individual papers
- Indicative grades: Estimates based on paper-level performance (NOT official grades)
- Raw marks: Total marks awarded across all marking criteria
- Descending threshold order: Higher grades require higher min_raw_marks
"""

import sqlite3


def create_boundary(
    paper_id: int,
    grade: str,
    min_raw_marks: int,
    display_order: int,
    conn: sqlite3.Connection,
) -> int:
    """Create grade boundary for paper.

    Args:
        paper_id: Paper this boundary applies to
        grade: Grade label (e.g., '9', '8', 'A*', 'U')
        min_raw_marks: Minimum raw marks required for this grade
        display_order: Display ordering (1 = highest grade, increasing = lower grades)
        conn: Database connection

    Returns:
        Boundary ID (auto-increment primary key)

    Raises:
        sqlite3.IntegrityError: If duplicate grade for paper or FK violation
    """
    cursor = conn.execute(
        """
        INSERT INTO grade_boundaries (paper_id, grade, min_raw_marks, display_order)
        VALUES (?, ?, ?, ?)
        """,
        (paper_id, grade, min_raw_marks, display_order),
    )
    boundary_id = cursor.lastrowid
    if boundary_id is None:
        raise ValueError("Failed to create grade boundary - no ID returned")
    return boundary_id


def get_boundaries_for_paper(paper_id: int, conn: sqlite3.Connection) -> list[dict[str, int | str]]:
    """Get all grade boundaries for a paper, ordered by display_order.

    Args:
        paper_id: Paper ID

    Returns:
        List of boundary dicts with keys: id, paper_id, grade, min_raw_marks,
        display_order, created_at. Empty list if no boundaries found.
    """
    cursor = conn.execute(
        """
        SELECT id, paper_id, grade, min_raw_marks, display_order, created_at
        FROM grade_boundaries
        WHERE paper_id = ?
        ORDER BY display_order ASC
        """,
        (paper_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def calculate_grade(raw_marks: int, paper_id: int, conn: sqlite3.Connection) -> str:
    """Calculate indicative grade from raw marks using grade boundaries.

    Finds the highest grade where raw_marks >= min_raw_marks.

    Args:
        raw_marks: Total marks awarded (sum across all criteria)
        paper_id: Paper ID to look up boundaries for
        conn: Database connection

    Returns:
        Grade string (e.g., '9', '8', 'A*', 'U')

    Raises:
        ValueError: If no grade boundaries exist for paper_id

    Example:
        >>> calculate_grade(67, paper_id=1, conn)
        '9'  # If grade 9 boundary is 67 marks
        >>> calculate_grade(5, paper_id=1, conn)
        'U'  # Below grade 4 threshold
    """
    # Validate boundaries exist
    if not boundaries_exist(paper_id, conn):
        raise ValueError(f"No grade boundaries found for paper_id {paper_id}")

    cursor = conn.execute(
        """
        SELECT grade
        FROM grade_boundaries
        WHERE paper_id = ?
          AND min_raw_marks <= ?
        ORDER BY min_raw_marks DESC
        LIMIT 1
        """,
        (paper_id, raw_marks),
    )
    row = cursor.fetchone()
    return row["grade"] if row else "U"


def boundaries_exist(paper_id: int, conn: sqlite3.Connection) -> bool:
    """Check if boundaries exist for paper.

    Args:
        paper_id: Paper ID

    Returns:
        True if at least one boundary exists, False otherwise
    """
    cursor = conn.execute("SELECT COUNT(*) FROM grade_boundaries WHERE paper_id = ?", (paper_id,))
    row = cursor.fetchone()
    return bool(row[0] > 0)


def count_boundaries_for_paper(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count grade boundaries for a paper.

    Used by verification logic to ensure all boundaries loaded correctly.

    Args:
        paper_id: Paper ID

    Returns:
        Number of boundaries for this paper
    """
    cursor = conn.execute("SELECT COUNT(*) FROM grade_boundaries WHERE paper_id = ?", (paper_id,))
    return int(cursor.fetchone()[0])


def delete_boundaries_for_paper(paper_id: int, conn: sqlite3.Connection) -> int:
    """Delete all grade boundaries for a paper.

    Used during paper replacement (--replace mode). The ON DELETE CASCADE
    constraint will handle this automatically when paper is deleted, but
    this method is provided for explicit deletion if needed.

    Args:
        paper_id: Paper ID

    Returns:
        Number of boundaries deleted
    """
    cursor = conn.execute("DELETE FROM grade_boundaries WHERE paper_id = ?", (paper_id,))
    return cursor.rowcount
