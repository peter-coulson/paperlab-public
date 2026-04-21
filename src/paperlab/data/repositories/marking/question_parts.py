"""Repository for question_parts table.

Provides data access methods for question parts (including NULL parts).
"""

import sqlite3

from paperlab.config import ErrorMessages


def create_part(
    question_id: int,
    part_letter: str | None,
    sub_part_letter: str | None,
    display_order: int,
    conn: sqlite3.Connection,
) -> int:
    """Create question part record.

    Does NOT commit - caller manages transaction.

    Args:
        question_id: Database ID of parent question
        part_letter: Part letter or None for NULL part
        sub_part_letter: Sub-part letter or None
        display_order: Display order within question (0 for NULL part)
        conn: Database connection

    Returns:
        part_id

    Raises:
        sqlite3.IntegrityError: If part already exists for this question
        ValueError: If failed to get part_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO question_parts (
            question_id,
            part_letter,
            sub_part_letter,
            display_order
        ) VALUES (?, ?, ?, ?)
        """,
        (question_id, part_letter, sub_part_letter, display_order),
    )

    part_id = cursor.lastrowid
    if part_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="part"))
    return part_id


def get_part_id(
    question_id: int,
    part_letter: str | None,
    sub_part_letter: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Look up part ID by identity.

    Args:
        question_id: Database ID of parent question
        part_letter: Part letter or None for NULL part
        sub_part_letter: Sub-part letter or None
        conn: Database connection

    Returns:
        part_id

    Raises:
        ValueError: If part not found
    """
    cursor = conn.execute(
        """
        SELECT id FROM question_parts
        WHERE question_id = ? AND part_letter IS ? AND sub_part_letter IS ?
        """,
        (question_id, part_letter, sub_part_letter),
    )

    row = cursor.fetchone()
    if row is None:
        part_desc = f"({part_letter or 'NULL'}"
        if sub_part_letter:
            part_desc += f", {sub_part_letter}"
        part_desc += ")"
        raise ValueError(
            f"Question part {part_desc} not found for question_id={question_id}. "
            "Ensure the paper structure has been loaded before loading mark scheme."
        )

    return int(row[0])


def count_parts(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count all parts for a paper (across all questions).

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Number of parts
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM question_parts qp
        JOIN questions q ON qp.question_id = q.id
        WHERE q.paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def get_parts_for_question(
    question_id: int,
    conn: sqlite3.Connection,
) -> list[tuple[str | None, str | None, int]]:
    """Get all parts for a question with their identity.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        List of (part_letter, sub_part_letter, display_order) tuples ordered by display_order
    """
    cursor = conn.execute(
        """
        SELECT part_letter, sub_part_letter, display_order
        FROM question_parts
        WHERE question_id = ?
        ORDER BY display_order
        """,
        (question_id,),
    )

    return [(row[0], row[1], row[2]) for row in cursor.fetchall()]


def update_expected_answer(
    part_id: int,
    expected_answer: str | None,
    conn: sqlite3.Connection,
) -> None:
    """Update expected answer for a question part.

    Does NOT commit - caller manages transaction.

    Args:
        part_id: Database ID of question part
        expected_answer: Expected answer (LaTeX format for maths), or None
        conn: Database connection
    """
    conn.execute(
        "UPDATE question_parts SET expected_answer = ? WHERE id = ?",
        (expected_answer, part_id),
    )


def get_expected_answers_for_paper(
    paper_id: int,
    conn: sqlite3.Connection,
) -> dict[tuple[int, str | None, str | None], str | None]:
    """Get all expected answers for a paper (for verification).

    Returns mapping of (question_number, part_letter, sub_part_letter) to expected_answer.
    Used by marks_loader to verify expected_answers were written correctly.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Dictionary mapping part identity to expected_answer:
        {(question_number, part_letter, sub_part_letter): expected_answer}
    """
    cursor = conn.execute(
        """
        SELECT
            q.question_number,
            qp.part_letter,
            qp.sub_part_letter,
            qp.expected_answer
        FROM question_parts qp
        JOIN questions q ON qp.question_id = q.id
        WHERE q.paper_id = ?
        ORDER BY q.question_number, qp.display_order
        """,
        (paper_id,),
    )

    return {(int(row[0]), row[1], row[2]): row[3] for row in cursor.fetchall()}
