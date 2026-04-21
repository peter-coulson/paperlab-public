"""Repository for papers table.

Provides data access methods for exam papers.
"""

import sqlite3

from paperlab.config import ErrorMessages
from paperlab.data.repositories.marking._query_helpers import subject_where_params


def create_paper(
    exam_type_id: int,
    exam_date: str,
    total_marks: int,
    exam_identifier: str,
    conn: sqlite3.Connection,
) -> int:
    """Create paper record (instance of an exam type).

    Does NOT commit - caller manages transaction.

    Args:
        exam_type_id: Database ID of exam type
        exam_date: Exam date in ISO format (YYYY-MM-DD)
        total_marks: Total marks for this paper
        exam_identifier: Unique exam identifier
        conn: Database connection

    Returns:
        paper_id

    Raises:
        sqlite3.IntegrityError: If paper with exam_identifier already exists
        ValueError: If failed to get paper_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO papers (
            exam_type_id,
            exam_date,
            total_marks,
            exam_identifier
        ) VALUES (?, ?, ?, ?)
        """,
        (
            exam_type_id,
            exam_date,
            total_marks,
            exam_identifier,
        ),
    )

    paper_id = cursor.lastrowid
    if paper_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="paper"))
    return paper_id


def get_paper_id(exam_identifier: str, conn: sqlite3.Connection) -> int:
    """Look up paper ID by exam_identifier.

    Args:
        exam_identifier: Unique exam identifier
        conn: Database connection

    Returns:
        paper_id

    Raises:
        ValueError: If paper not found
    """
    cursor = conn.execute(
        """
        SELECT id FROM papers
        WHERE exam_identifier = ?
        """,
        (exam_identifier,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"Paper not found with exam_identifier='{exam_identifier}'. "
            "Ensure the paper has been loaded before attempting to load mark scheme."
        )

    return int(row[0])


def get_exam_type_id(paper_id: int, conn: sqlite3.Connection) -> int:
    """Get exam type ID for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        exam_type_id for this paper

    Raises:
        ValueError: If paper not found
    """
    cursor = conn.execute(
        """
        SELECT exam_type_id FROM papers
        WHERE id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Paper ID {paper_id} not found")

    return int(row[0])


def get_total_marks(paper_id: int, conn: sqlite3.Connection) -> int:
    """Get total marks for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        total_marks for this paper

    Raises:
        ValueError: If paper not found
    """
    cursor = conn.execute(
        """
        SELECT total_marks FROM papers
        WHERE id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Paper ID {paper_id} not found")

    return int(row[0])


def count_papers_for_subject(
    exam_board: str, exam_level: str, subject: str, conn: sqlite3.Connection
) -> int:
    """Count paper instances for a specific subject.

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        conn: Database connection

    Returns:
        Number of paper instances (loaded papers) for this subject

    Note:
        This counts actual paper instances in the papers table, not exam_types.
        Used to check if replace mode would trigger CASCADE deletes.
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM papers p
        JOIN exam_types et ON p.exam_type_id = et.id
        WHERE et.exam_board = ? AND et.exam_level = ? AND et.subject = ?
        """,
        subject_where_params(exam_board, exam_level, subject),
    )

    row = cursor.fetchone()
    return int(row[0])


def count_content_blocks(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count all content blocks for a paper (across all parts).

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Number of content blocks
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM question_content_blocks qcb
        JOIN question_parts qp ON qcb.question_part_id = qp.id
        JOIN questions q ON qp.question_id = q.id
        WHERE q.paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def get_paper_with_marks(
    exam_identifier: str,
    conn: sqlite3.Connection,
) -> tuple[int, int] | None:
    """Get paper ID and total marks by exam identifier.

    Args:
        exam_identifier: Unique exam identifier
        conn: Database connection

    Returns:
        Tuple of (paper_id, total_marks) if found, None otherwise
    """
    cursor = conn.execute(
        """
        SELECT id, total_marks
        FROM papers
        WHERE exam_identifier = ?
        """,
        (exam_identifier,),
    )

    row = cursor.fetchone()
    if row is None:
        return None

    return (int(row[0]), int(row[1]))


def get_paper_full(paper_id: int, conn: sqlite3.Connection) -> dict[str, int | str]:
    """Fetch complete paper with exam type information.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        {
            'paper_id': int,
            'exam_identifier': str,
            'exam_date': str,
            'total_marks': int,
            'exam_board': str,
            'exam_level': str,
            'subject': str,
            'paper_code': str,
            'display_name': str,
        }

    Raises:
        ValueError: If paper not found
    """
    cursor = conn.execute(
        """
        SELECT
            p.id,
            p.exam_identifier,
            p.exam_date,
            p.total_marks,
            et.exam_board,
            et.exam_level,
            et.subject,
            et.paper_code,
            et.display_name
        FROM papers p
        JOIN exam_types et ON p.exam_type_id = et.id
        WHERE p.id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Paper ID {paper_id} not found")

    return {
        "paper_id": int(row[0]),
        "exam_identifier": row[1],
        "exam_date": row[2],
        "total_marks": int(row[3]),
        "exam_board": row[4],
        "exam_level": row[5],
        "subject": row[6],
        "paper_code": row[7],
        "display_name": row[8],
    }


def delete_paper(paper_id: int, conn: sqlite3.Connection) -> None:
    """Delete paper and all associated data (questions, parts, content, criteria, marking).

    Manually cascades to delete:
    - question_marking_results (marking data)
    - marking_attempts (marking metadata)
    - submission_images (student work images)
    - question_submissions (submissions)
    - mark_criteria_content_blocks
    - mark_criteria
    - question_content_blocks
    - question_parts
    - questions

    Note: Schema does not use ON DELETE CASCADE, so manual deletion required.
    Order matters - must delete in reverse dependency order (children first).

    Args:
        paper_id: Database ID of paper to delete
        conn: Database connection

    Raises:
        ValueError: If paper not found
    """
    # Check paper exists
    cursor = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,))
    if cursor.fetchone() is None:
        raise ValueError(f"Paper ID {paper_id} not found")

    # Delete child records manually (order matters to avoid FK violations)
    # Order: deepest dependencies first, working up to paper

    # 1. Delete question_marking_results (depends on mark_criteria_id AND marking_attempt_id)
    conn.execute(
        """
        DELETE FROM question_marking_results
        WHERE mark_criteria_id IN (
            SELECT mc.id FROM mark_criteria mc
            JOIN questions q ON mc.question_id = q.id
            WHERE q.paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 2. Delete marking_attempts (depends on submission_id via question_submissions)
    conn.execute(
        """
        DELETE FROM marking_attempts
        WHERE submission_id IN (
            SELECT qs.id FROM question_submissions qs
            JOIN questions q ON qs.question_id = q.id
            WHERE q.paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 3. Delete submission_images (depends on submission_id)
    conn.execute(
        """
        DELETE FROM submission_images
        WHERE submission_id IN (
            SELECT qs.id FROM question_submissions qs
            JOIN questions q ON qs.question_id = q.id
            WHERE q.paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 4. Delete question_submissions (depends on question_id)
    conn.execute(
        """
        DELETE FROM question_submissions
        WHERE question_id IN (
            SELECT id FROM questions WHERE paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 5. Delete mark criteria content blocks
    conn.execute(
        """
        DELETE FROM mark_criteria_content_blocks
        WHERE mark_criteria_id IN (
            SELECT mc.id FROM mark_criteria mc
            JOIN questions q ON mc.question_id = q.id
            WHERE q.paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 6. Delete mark criteria
    conn.execute(
        """
        DELETE FROM mark_criteria
        WHERE question_id IN (
            SELECT id FROM questions WHERE paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 7. Delete question content blocks
    conn.execute(
        """
        DELETE FROM question_content_blocks
        WHERE question_part_id IN (
            SELECT qp.id FROM question_parts qp
            JOIN questions q ON qp.question_id = q.id
            WHERE q.paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 8. Delete question parts
    conn.execute(
        """
        DELETE FROM question_parts
        WHERE question_id IN (
            SELECT id FROM questions WHERE paper_id = ?
        )
        """,
        (paper_id,),
    )

    # 9. Delete questions
    conn.execute("DELETE FROM questions WHERE paper_id = ?", (paper_id,))

    # 10. Finally delete paper
    conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))


def get_question_count(paper_id: int, conn: sqlite3.Connection) -> int:
    """Get total number of questions for a paper.

    Used by grading validation to ensure all questions marked.

    Args:
        paper_id: Paper to count questions for
        conn: Database connection

    Returns:
        Number of questions in paper

    Example:
        >>> get_question_count(1, conn)
        20  # GCSE Maths 1MA1/3H has 20 questions
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*) FROM questions WHERE paper_id = ?
        """,
        (paper_id,),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def list_papers(
    exam_board: str | None,
    exam_level: str | None,
    subject: str | None,
    conn: sqlite3.Connection,
) -> list[dict[str, int | str]]:
    """List papers with optional filters (Flow 2 API).

    Args:
        exam_board: Filter by board (e.g., "pearson-edexcel"), or None for all
        exam_level: Filter by level (e.g., "gcse"), or None for all
        subject: Filter by subject (e.g., "mathematics"), or None for all
        conn: Database connection

    Returns:
        List of dicts with keys:
        - paper_id: int
        - exam_board: str
        - exam_level: str
        - subject: str
        - paper_code: str
        - display_name: str
        - year: int (from exam_date)
        - month: int (from exam_date)
        - total_marks: int
        - question_count: int

    Example:
        >>> list_papers("pearson-edexcel", "gcse", "mathematics", conn)
        [{'paper_id': 1, 'exam_board': 'pearson-edexcel', ...}, ...]
    """
    # Build WHERE clause dynamically based on filters
    where_clauses = []
    params = []

    if exam_board is not None:
        where_clauses.append("et.exam_board = ?")
        params.append(exam_board)

    if exam_level is not None:
        where_clauses.append("et.exam_level = ?")
        params.append(exam_level)

    if subject is not None:
        where_clauses.append("et.subject = ?")
        params.append(subject)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cursor = conn.execute(
        f"""
        SELECT
            p.id,
            et.exam_board,
            et.exam_level,
            et.subject,
            et.paper_code,
            et.display_name,
            p.exam_date,
            p.total_marks,
            COUNT(q.id) as question_count
        FROM papers p
        JOIN exam_types et ON p.exam_type_id = et.id
        LEFT JOIN questions q ON p.id = q.paper_id
        {where_sql}
        GROUP BY p.id, et.exam_board, et.exam_level, et.subject, et.paper_code,
                 et.display_name, p.exam_date, p.total_marks
        ORDER BY p.exam_date DESC
        """,
        params,
    )

    results = []
    for row in cursor.fetchall():
        # Extract year and month from exam_date (YYYY-MM-DD)
        exam_date = row[6]
        year, month, _ = exam_date.split("-")

        results.append(
            {
                "paper_id": int(row[0]),
                "exam_board": row[1],
                "exam_level": row[2],
                "subject": row[3],
                "paper_code": row[4],
                "display_name": row[5],
                "year": int(year),
                "month": int(month),
                "total_marks": int(row[7]),
                "question_count": int(row[8]),
            }
        )

    return results


def get_paper_id_by_metadata(
    exam_board: str,
    exam_level: str,
    subject: str,
    paper_code: str,
    year: int,
    month: int,
    conn: sqlite3.Connection,
) -> int:
    """Look up paper ID by exam metadata (Flow 2 API).

    Args:
        exam_board: e.g., "pearson-edexcel"
        exam_level: e.g., "gcse"
        subject: e.g., "mathematics"
        paper_code: e.g., "1MA1/3H"
        year: e.g., 2023
        month: e.g., 11
        conn: Database connection

    Returns:
        paper_id

    Raises:
        ValueError: If paper not found or multiple papers match

    Note:
        Matches by exam_type + year-month pattern in exam_date.
        Assumes only one paper per exam_type per month.
    """
    # Query by exam_type + year-month pattern
    cursor = conn.execute(
        """
        SELECT p.id
        FROM papers p
        JOIN exam_types et ON p.exam_type_id = et.id
        WHERE et.exam_board = ?
          AND et.exam_level = ?
          AND et.subject = ?
          AND et.paper_code = ?
          AND strftime('%Y', p.exam_date) = ?
          AND strftime('%m', p.exam_date) = ?
        """,
        (exam_board, exam_level, subject, paper_code, str(year), f"{month:02d}"),
    )

    rows = cursor.fetchall()

    if not rows:
        raise ValueError(
            f"Paper not found: {exam_board}/{exam_level}/{subject}/{paper_code} {year}-{month:02d}"
        )

    if len(rows) > 1:
        raise ValueError(
            f"Multiple papers found for {exam_board}/{exam_level}/{subject}/{paper_code} "
            f"{year}-{month:02d}. Cannot determine which paper to use."
        )

    return int(rows[0][0])
