"""Repository for mark_types table.

Provides data access methods for mark types (e.g., M, A, GENERAL).
"""

import sqlite3
from typing import Any

from paperlab.data.repositories.marking._query_helpers import (
    subject_where_params,
)


def get_by_code(
    code: str,
    exam_type_id: int,
    conn: sqlite3.Connection,
) -> int:
    """Look up mark_type_id for a given code and exam type.

    Args:
        code: Mark type code (e.g., 'M', 'A', 'GENERAL')
        exam_type_id: Exam type ID
        conn: Database connection

    Returns:
        mark_type_id

    Raises:
        ValueError: If mark type doesn't exist for this exam type
    """
    cursor = conn.execute(
        """
        SELECT id FROM mark_types
        WHERE exam_type_id = ? AND code = ?
        """,
        (exam_type_id, code),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Mark type '{code}' not found for exam_type_id={exam_type_id}. "
            "Ensure the mark type exists in the mark_types table for this exam type."
        )

    return int(row[0])


def get_mark_types_for_exam_type(
    exam_type_id: int, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Fetch all mark types for an exam type.

    Args:
        exam_type_id: Exam type ID
        conn: Database connection

    Returns:
        [
            {
                'mark_type_id': int,
                'code': str,
                'display_name': str,
                'description': str | None,
            },
            ...
        ]
        Ordered by code for consistent output
    """
    cursor = conn.execute(
        """
        SELECT id, code, display_name, description
        FROM mark_types
        WHERE exam_type_id = ?
        ORDER BY code
        """,
        (exam_type_id,),
    )

    return [
        {
            "mark_type_id": int(row[0]),
            "code": row[1],
            "display_name": row[2],
            "description": row[3],
        }
        for row in cursor.fetchall()
    ]


def create_mark_types_batch(
    mark_types: list[tuple[int, str, str, str]], conn: sqlite3.Connection
) -> None:
    """Create multiple mark types in a single batch operation.

    Args:
        mark_types: List of (exam_type_id, code, display_name, description) tuples
        conn: Database connection

    Note:
        Uses executemany() for efficient batch insertion.
        This is used during mark_type_group expansion in exam config loader.
    """
    conn.executemany(
        """
        INSERT INTO mark_types (exam_type_id, code, display_name, description)
        VALUES (?, ?, ?, ?)
        """,
        mark_types,
    )


def count_mark_types_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> int:
    """Count all mark types for a specific subject (across all papers).

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Returns:
        Total number of mark_types records for this subject across all papers
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM mark_types mt
        JOIN exam_types et ON mt.exam_type_id = et.id
        WHERE et.exam_board = ? AND et.exam_level = ? AND et.subject = ?
        """,
        subject_where_params(exam_board, exam_level, subject),
    )
    return int(cursor.fetchone()[0])


def delete_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> None:
    """Delete all mark types for a specific subject (across all papers).

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Note:
        This deletes mark_types records that reference exam_types for this subject.
        Must be called BEFORE deleting exam_types to avoid FK constraint errors.
        Used in exam config replace mode.
    """
    conn.execute(
        """
        DELETE FROM mark_types
        WHERE exam_type_id IN (
            SELECT id FROM exam_types
            WHERE exam_board = ? AND exam_level = ? AND subject = ?
        )
        """,
        subject_where_params(exam_board, exam_level, subject),
    )


def get_all_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Fetch all mark types for a subject (across all papers).

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Returns:
        [
            {
                'mark_type_id': int,
                'exam_type_id': int,
                'paper_code': str,
                'code': str,
                'display_name': str,
                'description': str,
            },
            ...
        ]
        Ordered by paper_code, then code for consistent output
    """
    # Use Row factory for dict-like access
    original_factory = conn.row_factory
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(
            """
            SELECT mt.id, mt.exam_type_id, et.paper_code, mt.code, mt.display_name, mt.description
            FROM mark_types mt
            JOIN exam_types et ON mt.exam_type_id = et.id
            WHERE et.exam_board = ? AND et.exam_level = ? AND et.subject = ?
            ORDER BY et.paper_code, mt.code
            """,
            subject_where_params(exam_board, exam_level, subject),
        )

        return [
            {
                "mark_type_id": row["id"],
                "exam_type_id": row["exam_type_id"],
                "paper_code": row["paper_code"],
                "code": row["code"],
                "display_name": row["display_name"],
                "description": row["description"],
            }
            for row in cursor.fetchall()
        ]
    finally:
        # Restore original row factory
        conn.row_factory = original_factory
