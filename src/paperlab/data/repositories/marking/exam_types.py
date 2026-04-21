"""Repository for exam_types table.

Provides data access methods for exam types (board, level, subject, paper_code).
"""

import sqlite3
from typing import Any

from paperlab.data.repositories.marking._query_helpers import (
    subject_where_clause,
    subject_where_params,
)


def get_by_exam_type(
    exam_board: str,
    exam_level: str,
    subject: str,
    paper_code: str,
    conn: sqlite3.Connection,
) -> int:
    """Look up exam_type_id by board, level, subject, and paper code.

    Args:
        exam_board: Exam board name (e.g., 'Pearson Edexcel')
        exam_level: Qualification level (e.g., 'GCSE')
        subject: Subject name (e.g., 'Mathematics')
        paper_code: Paper code (e.g., '1MA1/1H')
        conn: Database connection

    Returns:
        exam_type_id

    Raises:
        ValueError: If exam type doesn't exist in database
    """
    cursor = conn.execute(
        """
        SELECT id FROM exam_types
        WHERE exam_board = ? AND exam_level = ? AND subject = ? AND paper_code = ?
        """,
        (exam_board, exam_level, subject, paper_code),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Exam type not found: {exam_board} {exam_level} {subject} {paper_code}. "
            "Ensure the exam type exists in the exam_types table."
        )

    return int(row[0])


def create_exam_types_batch(
    exam_types: list[tuple[str, str, str, str, str]], conn: sqlite3.Connection
) -> None:
    """Create multiple exam types in a single batch operation.

    Args:
        exam_types: List of (exam_board, exam_level, subject, paper_code, display_name) tuples
        conn: Database connection

    Note:
        Uses executemany() for efficient batch insertion.
        Does NOT return IDs - use get_by_exam_type() to look up afterward.
    """
    conn.executemany(
        """
        INSERT INTO exam_types (exam_board, exam_level, subject, paper_code, display_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        exam_types,
    )


def count_exam_types_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> int:
    """Count exam types for a specific subject.

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Returns:
        Number of exam types (papers) for this subject
    """
    cursor = conn.execute(
        f"""
        SELECT COUNT(*) FROM exam_types
        {subject_where_clause()}
        """,
        subject_where_params(exam_board, exam_level, subject),
    )
    return int(cursor.fetchone()[0])


def delete_exam_types_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> None:
    """Delete all exam types for a specific subject.

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Note:
        CASCADE deletes will remove all dependent mark_types, papers, questions, etc.
        Use with caution - intended for replace mode in config loader.
    """
    conn.execute(
        f"""
        DELETE FROM exam_types
        {subject_where_clause()}
        """,
        subject_where_params(exam_board, exam_level, subject),
    )


def get_all_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Fetch all exam types for a subject.

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Returns:
        [
            {
                'exam_type_id': int,
                'exam_board': str,
                'exam_level': str,
                'subject': str,
                'paper_code': str,
                'display_name': str,
            },
            ...
        ]
        Ordered by paper_code for consistent output
    """
    # Use Row factory for dict-like access
    original_factory = conn.row_factory
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(
            f"""
            SELECT id, exam_board, exam_level, subject, paper_code, display_name
            FROM exam_types
            {subject_where_clause()}
            ORDER BY paper_code
            """,
            subject_where_params(exam_board, exam_level, subject),
        )

        return [
            {
                "exam_type_id": row["id"],
                "exam_board": row["exam_board"],
                "exam_level": row["exam_level"],
                "subject": row["subject"],
                "paper_code": row["paper_code"],
                "display_name": row["display_name"],
            }
            for row in cursor.fetchall()
        ]
    finally:
        # Restore original row factory
        conn.row_factory = original_factory
