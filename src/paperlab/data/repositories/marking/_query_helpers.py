"""Shared query helpers for marking repositories.

Provides common SQL patterns and utilities used across multiple repository modules.
"""


def subject_where_clause() -> str:
    """Standard WHERE clause for subject-level queries.

    Returns:
        SQL WHERE clause string for filtering by (exam_board, exam_level, subject)

    Usage:
        cursor = conn.execute(
            f"SELECT * FROM exam_types {subject_where_clause()}",
            subject_where_params(board, level, subject)
        )
    """
    return "WHERE exam_board = ? AND exam_level = ? AND subject = ?"


def subject_where_params(exam_board: str, exam_level: str, subject: str) -> tuple[str, str, str]:
    """Standard parameter tuple for subject-level queries.

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name

    Returns:
        Tuple of (exam_board, exam_level, subject) for parameterized queries

    Usage:
        cursor = conn.execute(
            f"SELECT * FROM exam_types {subject_where_clause()}",
            subject_where_params(board, level, subject)
        )
    """
    return (exam_board, exam_level, subject)
