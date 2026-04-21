"""Repository for paper_results table.

Provides data access methods for paper grading results.
"""

import sqlite3

from paperlab.config import Tables
from paperlab.data.models.marking import PaperResult


def create_result(
    paper_attempt_id: int,
    total_marks_awarded: int,
    total_marks_available: int,
    percentage: float,
    indicative_grade: str,
    conn: sqlite3.Connection,
) -> None:
    """Create paper result after grade calculation.

    Does NOT commit - caller manages transaction.

    Args:
        paper_attempt_id: Paper attempt being graded
        total_marks_awarded: Sum of marks from all question marking results
        total_marks_available: Total marks for paper (from questions table)
        percentage: Calculated percentage (2 decimal places)
        indicative_grade: Grade from boundaries (e.g., '9', '8', '7', ..., 'U')
        conn: Database connection

    Raises:
        sqlite3.IntegrityError: If paper_attempt_id already has result (UNIQUE constraint)
            This catches concurrent grading race conditions.
    """
    conn.execute(
        f"""
        INSERT INTO {Tables.PAPER_RESULTS} (
            paper_attempt_id,
            total_marks_awarded,
            total_marks_available,
            percentage,
            indicative_grade
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            paper_attempt_id,
            total_marks_awarded,
            total_marks_available,
            percentage,
            indicative_grade,
        ),
    )


def get_result(paper_attempt_id: int, conn: sqlite3.Connection) -> PaperResult | None:
    """Get result for paper attempt.

    Args:
        paper_attempt_id: Paper attempt to get result for
        conn: Database connection

    Returns:
        PaperResult if graded, None if not yet graded (completed_at IS NULL)
    """
    cursor = conn.execute(
        f"""
        SELECT
            id,
            paper_attempt_id,
            total_marks_awarded,
            total_marks_available,
            percentage,
            indicative_grade,
            calculated_at
        FROM {Tables.PAPER_RESULTS}
        WHERE paper_attempt_id = ?
        """,
        (paper_attempt_id,),
    )

    row = cursor.fetchone()
    if row is None:
        return None

    return PaperResult(
        id=row[0],
        paper_attempt_id=row[1],
        total_marks_awarded=row[2],
        total_marks_available=row[3],
        percentage=row[4],
        indicative_grade=row[5],
        calculated_at=row[6],
    )
