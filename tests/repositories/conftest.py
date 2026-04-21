"""Fixtures for repository tests.

Provides helper functions to seed required reference data (exam_types, mark_types)
that repository methods depend on via foreign key relationships.
"""

import sqlite3

import pytest

# =============================================================================
# Test Data Constants
# =============================================================================

# Standard test values for exam types
TEST_EXAM_BOARD = "pearson-edexcel"
TEST_EXAM_LEVEL = "gcse"
TEST_SUBJECT = "mathematics"
TEST_PAPER_CODE = "1MA1/1H"
TEST_DISPLAY_NAME = "GCSE Mathematics Paper 1 (Calculator)"

# Standard test values for papers
TEST_EXAM_DATE = "2023-11-08"
TEST_TOTAL_MARKS = 80
TEST_EXAM_IDENTIFIER = "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"

# Mark type codes for GCSE Mathematics
MARK_TYPE_M = "M"  # Method mark
MARK_TYPE_A = "A"  # Accuracy mark
MARK_TYPE_B = "B"  # Independent mark


# =============================================================================
# Helper Functions for Seeding Reference Data
# =============================================================================


def seed_exam_type(conn: sqlite3.Connection) -> int:
    """Create a test exam type and return its ID.

    Args:
        conn: Database connection

    Returns:
        exam_type_id
    """
    cursor = conn.execute(
        """
        INSERT INTO exam_types (exam_board, exam_level, subject, paper_code, display_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (TEST_EXAM_BOARD, TEST_EXAM_LEVEL, TEST_SUBJECT, TEST_PAPER_CODE, TEST_DISPLAY_NAME),
    )
    exam_type_id = cursor.lastrowid
    assert exam_type_id is not None
    return exam_type_id


def seed_mark_types(conn: sqlite3.Connection, exam_type_id: int) -> dict[str, int]:
    """Create standard mark types for an exam type.

    Args:
        conn: Database connection
        exam_type_id: Parent exam type ID

    Returns:
        Dictionary mapping mark type code to ID: {'M': 1, 'A': 2, 'B': 3}
    """
    mark_types = [
        (exam_type_id, MARK_TYPE_M, "Method", "Method mark for correct process"),
        (exam_type_id, MARK_TYPE_A, "Accuracy", "Accuracy mark for correct answer"),
        (exam_type_id, MARK_TYPE_B, "Independent", "Independent mark"),
    ]

    conn.executemany(
        """
        INSERT INTO mark_types (exam_type_id, code, display_name, description)
        VALUES (?, ?, ?, ?)
        """,
        mark_types,
    )

    # Fetch IDs
    cursor = conn.execute(
        "SELECT code, id FROM mark_types WHERE exam_type_id = ?",
        (exam_type_id,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def seed_paper(conn: sqlite3.Connection, exam_type_id: int) -> int:
    """Create a test paper and return its ID.

    Args:
        conn: Database connection
        exam_type_id: Parent exam type ID

    Returns:
        paper_id
    """
    cursor = conn.execute(
        """
        INSERT INTO papers (exam_type_id, exam_date, total_marks, exam_identifier)
        VALUES (?, ?, ?, ?)
        """,
        (exam_type_id, TEST_EXAM_DATE, TEST_TOTAL_MARKS, TEST_EXAM_IDENTIFIER),
    )
    paper_id = cursor.lastrowid
    assert paper_id is not None
    return paper_id


def seed_question(
    conn: sqlite3.Connection,
    paper_id: int,
    question_number: int,
    total_marks: int,
) -> int:
    """Create a test question and return its ID.

    Args:
        conn: Database connection
        paper_id: Parent paper ID
        question_number: Question number
        total_marks: Total marks for question

    Returns:
        question_id
    """
    cursor = conn.execute(
        """
        INSERT INTO questions (paper_id, question_number, total_marks)
        VALUES (?, ?, ?)
        """,
        (paper_id, question_number, total_marks),
    )
    question_id = cursor.lastrowid
    assert question_id is not None
    return question_id


def seed_question_part(
    conn: sqlite3.Connection,
    question_id: int,
    part_letter: str | None = None,
    sub_part_letter: str | None = None,
    display_order: int = 0,
) -> int:
    """Create a test question part and return its ID.

    Args:
        conn: Database connection
        question_id: Parent question ID
        part_letter: Part letter (a, b, c) or None for NULL part
        sub_part_letter: Sub-part letter (i, ii) or None
        display_order: Display order within question

    Returns:
        part_id
    """
    cursor = conn.execute(
        """
        INSERT INTO question_parts (question_id, part_letter, sub_part_letter, display_order)
        VALUES (?, ?, ?, ?)
        """,
        (question_id, part_letter, sub_part_letter, display_order),
    )
    part_id = cursor.lastrowid
    assert part_id is not None
    return part_id


def seed_question_content_block(
    conn: sqlite3.Connection,
    part_id: int,
    block_type: str = "text",
    display_order: int = 0,
    content_text: str | None = "Test content",
    diagram_description: str | None = None,
) -> int:
    """Create a test question content block and return its ID.

    Args:
        conn: Database connection
        part_id: Parent question part ID
        block_type: 'text' or 'diagram'
        display_order: Display order within part
        content_text: Text content (for text blocks)
        diagram_description: Diagram description (for diagram blocks)

    Returns:
        content_block_id
    """
    cursor = conn.execute(
        """
        INSERT INTO question_content_blocks (
            question_part_id, block_type, display_order, content_text,
            diagram_description
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (part_id, block_type, display_order, content_text, diagram_description),
    )
    content_id = cursor.lastrowid
    assert content_id is not None
    return content_id


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def exam_type_id(test_conn: sqlite3.Connection) -> int:
    """Provide a seeded exam type ID."""
    return seed_exam_type(test_conn)


@pytest.fixture
def mark_type_ids(test_conn: sqlite3.Connection, exam_type_id: int) -> dict[str, int]:
    """Provide seeded mark type IDs."""
    return seed_mark_types(test_conn, exam_type_id)


@pytest.fixture
def paper_id(test_conn: sqlite3.Connection, exam_type_id: int) -> int:
    """Provide a seeded paper ID."""
    return seed_paper(test_conn, exam_type_id)


@pytest.fixture
def question_with_parts(test_conn: sqlite3.Connection, paper_id: int) -> tuple[int, list[int]]:
    """Provide a seeded question with multiple parts.

    Returns:
        Tuple of (question_id, [part_id_1, part_id_2])
    """
    question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=4)

    # Create two parts: NULL part (intro) and part (a)
    part_null = seed_question_part(test_conn, question_id, None, None, 0)
    part_a = seed_question_part(test_conn, question_id, "a", None, 1)

    # Add content blocks
    seed_question_content_block(test_conn, part_null, "text", 0, "Solve the following equation.")
    seed_question_content_block(test_conn, part_a, "text", 0, "Find the value of $x$.")

    return (question_id, [part_null, part_a])
