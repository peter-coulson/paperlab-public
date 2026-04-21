"""Repository for questions table.

Provides data access methods for exam questions.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.config import ErrorMessages


@dataclass
class QuestionWithPaper:
    """Question with its paper identifier."""

    paper_identifier: str
    question_number: int


def create_question(
    paper_id: int,
    question_number: int,
    total_marks: int,
    conn: sqlite3.Connection,
) -> int:
    """Create question record.

    Does NOT commit - caller manages transaction.

    Args:
        paper_id: Database ID of parent paper
        question_number: Question number
        total_marks: Total marks for question
        conn: Database connection

    Returns:
        question_id

    Raises:
        sqlite3.IntegrityError: If question already exists for this paper
        ValueError: If failed to get question_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO questions (
            paper_id,
            question_number,
            total_marks
        ) VALUES (?, ?, ?)
        """,
        (paper_id, question_number, total_marks),
    )

    question_id = cursor.lastrowid
    if question_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="question"))
    return question_id


def get_question_id(
    paper_id: int,
    question_number: int,
    conn: sqlite3.Connection,
) -> int:
    """Look up question ID.

    Args:
        paper_id: Database ID of parent paper
        question_number: Question number
        conn: Database connection

    Returns:
        question_id

    Raises:
        ValueError: If question not found
    """
    cursor = conn.execute(
        """
        SELECT id FROM questions
        WHERE paper_id = ? AND question_number = ?
        """,
        (paper_id, question_number),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Question {question_number} not found for paper_id={paper_id}. "
            "Ensure the paper structure has been loaded before loading mark scheme."
        )

    return int(row[0])


def get_all_with_marks(paper_id: int, conn: sqlite3.Connection) -> list[tuple[int, int, int]]:
    """Get all questions for a paper with their marks.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        List of tuples: (question_id, question_number, total_marks)
    """
    cursor = conn.execute(
        """
        SELECT id, question_number, total_marks
        FROM questions
        WHERE paper_id = ?
        ORDER BY question_number
        """,
        (paper_id,),
    )

    return [(int(row[0]), int(row[1]), int(row[2])) for row in cursor.fetchall()]


def count_questions(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count questions for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Number of questions
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*) FROM questions
        WHERE paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def get_question_with_marks(
    paper_id: int,
    question_number: int,
    conn: sqlite3.Connection,
) -> tuple[int, int] | None:
    """Get question ID and total marks for a question.

    Args:
        paper_id: Database ID of parent paper
        question_number: Question number
        conn: Database connection

    Returns:
        Tuple of (question_id, total_marks) if found, None otherwise
    """
    cursor = conn.execute(
        """
        SELECT id, total_marks
        FROM questions
        WHERE paper_id = ? AND question_number = ?
        """,
        (paper_id, question_number),
    )

    row = cursor.fetchone()
    if row is None:
        return None

    return (int(row[0]), int(row[1]))


def get_question_structure(question_id: int, conn: sqlite3.Connection) -> dict[str, Any]:
    """Fetch complete question structure with parts and content blocks.

    Single query with JOIN to fetch entire question hierarchy.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        {
            'question_id': int,
            'question_number': int,
            'total_marks': int,
            'parts': [
                {
                    'part_id': int,
                    'part_letter': str | None,
                    'sub_part_letter': str | None,
                    'display_order': int,
                    'content_blocks': [
                        {
                            'block_type': 'text' | 'diagram',
                            'content_text': str | None,
                            'diagram_description': str | None,
                            'diagram_image_path': str | None,
                        },
                        ...
                    ]
                },
                ...
            ]
        }

    Raises:
        ValueError: If question not found
    """
    cursor = conn.execute(
        """
        SELECT
            q.id AS question_id,
            q.question_number,
            q.total_marks,

            qp.id AS part_id,
            qp.part_letter,
            qp.sub_part_letter,
            qp.display_order AS part_display_order,

            qcb.id AS content_block_id,
            qcb.block_type,
            qcb.display_order AS block_display_order,
            qcb.content_text,
            qcb.diagram_description

        FROM questions q
        JOIN question_parts qp ON qp.question_id = q.id
        LEFT JOIN question_content_blocks qcb ON qcb.question_part_id = qp.id

        WHERE q.id = ?

        ORDER BY
            qp.display_order,
            qcb.display_order
        """,
        (question_id,),
    )

    rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"Question with id={question_id} not found")

    # Extract question-level data from first row
    question_data = {
        "question_id": int(rows[0][0]),
        "question_number": int(rows[0][1]),
        "total_marks": int(rows[0][2]),
        "parts": [],
    }

    # Group flat rows into hierarchy
    parts_dict: dict[int, dict[str, Any]] = {}  # part_id -> part dict
    parts_list: list[dict[str, Any]] = []

    for row in rows:
        part_id = int(row[3])
        content_block_id = row[7]

        # Build part structure (if first time seeing this part)
        if part_id not in parts_dict:
            part: dict[str, Any] = {
                "part_id": part_id,
                "part_letter": row[4],
                "sub_part_letter": row[5],
                "display_order": int(row[6]),
                "content_blocks": [],
            }
            parts_dict[part_id] = part
            parts_list.append(part)

        # Add content block (if exists - LEFT JOIN means might be NULL)
        if content_block_id is not None:
            block = {
                "block_type": row[8],
                "content_text": row[10],
                "diagram_description": row[11],
            }
            parts_dict[part_id]["content_blocks"].append(block)

    question_data["parts"] = parts_list
    return question_data


def get_all_with_paper_identifiers(
    conn: sqlite3.Connection,
) -> list[QuestionWithPaper]:
    """Get all questions with their paper identifiers.

    Args:
        conn: Database connection (to marking.db)

    Returns:
        List of questions with paper identifiers, ordered by paper and question number

    Note:
        Used for audit/generation workflows that need to process all questions.
    """
    cursor = conn.execute(
        """
        SELECT p.exam_identifier, q.question_number
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        ORDER BY p.exam_identifier, q.question_number
        """
    )

    return [
        QuestionWithPaper(paper_identifier=row[0], question_number=row[1])
        for row in cursor.fetchall()
    ]


def get_question_id_by_paper(
    paper_identifier: str,
    question_number: int,
    conn: sqlite3.Connection,
) -> int:
    """Get question ID by paper identifier and question number.

    Args:
        paper_identifier: Paper identifier
            (e.g., 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08')
        question_number: Question number within the paper
        conn: Database connection

    Returns:
        question_id

    Raises:
        ValueError: If question not found
    """
    cursor = conn.execute(
        """
        SELECT q.id
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        WHERE p.exam_identifier = ? AND q.question_number = ?
        """,
        (paper_identifier, question_number),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Question not found: paper={paper_identifier}, question_number={question_number}"
        )

    return int(row[0])


def get_question_by_paper_identifier(
    paper_identifier: str,
    question_number: int,
    conn: sqlite3.Connection,
) -> dict[str, Any] | None:
    """Get question by paper identifier and question number.

    Args:
        paper_identifier: Paper identifier
            (e.g., 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08')
        question_number: Question number within the paper
        conn: Database connection

    Returns:
        Question dict with keys: id, paper_id, question_number, total_marks
        Returns None if not found
    """
    cursor = conn.execute(
        """
        SELECT q.id, q.paper_id, q.question_number, q.total_marks
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        WHERE p.exam_identifier = ? AND q.question_number = ?
        """,
        (paper_identifier, question_number),
    )

    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": int(row[0]),
        "paper_id": int(row[1]),
        "question_number": int(row[2]),
        "total_marks": int(row[3]),
    }


def get_question_ids_batch(
    paper_question_pairs: list[tuple[str, int]],
    conn: sqlite3.Connection,
) -> dict[tuple[str, int], int]:
    """Batch lookup question IDs for multiple (paper_identifier, question_number) pairs.

    Args:
        paper_question_pairs: List of (paper_identifier, question_number) tuples
        conn: Database connection

    Returns:
        Dictionary mapping (paper_identifier, question_number) -> question_id

    Note:
        If a paper/question combination is not found, it won't appear in the returned dict.
        Caller should check that all pairs were found.

    Example:
        >>> pairs = [
        ...     ("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08", 1),
        ...     ("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08", 2),
        ... ]
        >>> result = get_question_ids_batch(pairs, conn)
        >>> # Returns: {("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08", 1): 42, ...}
    """
    if not paper_question_pairs:
        return {}

    # Build IN clause for batch query
    # Using VALUES clause for better performance with multiple pairs
    placeholders = ",".join("(?, ?)" for _ in paper_question_pairs)
    query = f"""
        SELECT p.exam_identifier, q.question_number, q.id
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        WHERE (p.exam_identifier, q.question_number) IN (VALUES {placeholders})
    """

    # Flatten list of tuples for parameter binding
    params = [item for pair in paper_question_pairs for item in pair]

    cursor = conn.execute(query, params)

    # Build result dictionary
    return {(row[0], int(row[1])): int(row[2]) for row in cursor.fetchall()}


def list_questions(
    exam_board: str | None,
    exam_level: str | None,
    subject: str | None,
    paper_id: int | None,
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """List questions with optional filters (Flow 2 API - practice selection).

    Args:
        exam_board: Filter by board (e.g., "pearson-edexcel"), or None for all
        exam_level: Filter by level (e.g., "gcse"), or None for all
        subject: Filter by subject (e.g., "mathematics"), or None for all
        paper_id: Filter by specific paper ID, or None for all
        conn: Database connection

    Returns:
        List of dicts with keys:
        - question_id: int
        - paper_id: int
        - paper_name: str
        - exam_date: str (ISO 8601 format: YYYY-MM-DD from SQLite)
        - question_number: int
        - total_marks: int

    Example:
        >>> list_questions(paper_id=1, conn=conn)
        [{'question_id': 1, 'paper_id': 1, 'paper_name': '...',
          'exam_date': '2023-11-13', ...}, ...]
    """
    # Build WHERE clause dynamically based on filters
    where_clauses = []
    params: list[str | int] = []

    if exam_board is not None:
        where_clauses.append("et.exam_board = ?")
        params.append(exam_board)

    if exam_level is not None:
        where_clauses.append("et.exam_level = ?")
        params.append(exam_level)

    if subject is not None:
        where_clauses.append("et.subject = ?")
        params.append(subject)

    if paper_id is not None:
        where_clauses.append("q.paper_id = ?")
        params.append(paper_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Data denormalization: Include paper_name and exam_date directly in question results
    # to avoid frontend lookups. These fields are read-only and sourced from the papers
    # table via JOIN, so they automatically stay in sync with paper data.
    cursor = conn.execute(
        f"""
        SELECT
            q.id,
            q.paper_id,
            COALESCE(et.display_name, p.exam_identifier) as paper_name,
            p.exam_date,
            q.question_number,
            q.total_marks
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        LEFT JOIN exam_types et ON p.exam_type_id = et.id
        {where_sql}
        ORDER BY p.exam_date DESC, q.question_number ASC
        """,
        params,
    )

    return [
        {
            "question_id": int(row[0]),
            "paper_id": int(row[1]),
            "paper_name": row[2],
            "exam_date": row[3],
            "question_number": int(row[4]),
            "total_marks": int(row[5]),
        }
        for row in cursor.fetchall()
    ]


def get_paper_id_for_question(question_id: int, conn: sqlite3.Connection) -> int:
    """Get paper_id for a given question.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        paper_id

    Raises:
        ValueError: If question not found
    """
    cursor = conn.execute(
        """
        SELECT paper_id FROM questions WHERE id = ?
        """,
        (question_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Question {question_id} not found")

    return int(row[0])


def get_subject_for_question(question_id: int, conn: sqlite3.Connection) -> str:
    """Get subject name for a given question.

    Queries exam_types table via paper relationship to find subject.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        Subject name (e.g., 'Mathematics', 'English Language')

    Raises:
        ValueError: If question not found or subject not found

    Example:
        >>> subject = get_subject_for_question(question_id=1, conn)
        >>> # Returns: 'Mathematics'
    """
    cursor = conn.execute(
        """
        SELECT et.subject
        FROM questions q
        JOIN papers p ON q.paper_id = p.id
        JOIN exam_types et ON p.exam_type_id = et.id
        WHERE q.id = ?
        """,
        (question_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(
            f"Subject not found for question_id={question_id}. "
            "Question may not exist or may lack proper exam_type reference."
        )
    subject: str = row["subject"]
    return subject
