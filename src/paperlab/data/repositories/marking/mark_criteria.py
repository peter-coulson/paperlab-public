"""Repository for mark_criteria table.

Provides data access methods for mark criteria (marking guidance for questions).
"""

import sqlite3
from typing import Any

from paperlab.config import ErrorMessages
from paperlab.constants.fields import CriterionFields


def create_criterion(
    question_id: int,
    part_id: int,
    mark_type_id: int,
    criterion_index: int,
    marks_available: int,
    depends_on_criterion_index: int | None,
    conn: sqlite3.Connection,
) -> int:
    """Create mark criterion.

    Does NOT commit - caller manages transaction.

    Args:
        question_id: Database ID of parent question
        part_id: Database ID of question part this criterion applies to
        mark_type_id: Database ID of mark type (M, A, B, etc.)
        criterion_index: Sequential index for criterion within question (from JSON display_order)
        marks_available: Marks available for this criterion (0 for GENERAL type)
        depends_on_criterion_index: Index of criterion this depends on, or None
        conn: Database connection

    Returns:
        criterion_id

    Raises:
        sqlite3.IntegrityError: If criterion already exists (duplicate criterion_index)
        ValueError: If failed to get criterion_id after INSERT

    Note:
        criterion_index maps directly from JSON display_order field.
        Database enforces depends_on_criterion_index < criterion_index via CHECK constraint.
    """
    cursor = conn.execute(
        """
        INSERT INTO mark_criteria (
            question_id,
            question_part_id,
            mark_type_id,
            criterion_index,
            marks_available,
            depends_on_criterion_index
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            question_id,
            part_id,
            mark_type_id,
            criterion_index,
            marks_available,
            depends_on_criterion_index,
        ),
    )

    criterion_id = cursor.lastrowid
    if criterion_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="criterion"))
    return criterion_id


def criteria_exists_for_paper(exam_identifier: str, conn: sqlite3.Connection) -> bool:
    """Check if any mark criteria exist for a paper (for duplicate check).

    Args:
        exam_identifier: Unique exam identifier
        conn: Database connection

    Returns:
        True if mark criteria exist, False otherwise
    """
    cursor = conn.execute(
        """
        SELECT EXISTS(
            SELECT 1
            FROM mark_criteria mc
            JOIN questions q ON mc.question_id = q.id
            JOIN papers p ON q.paper_id = p.id
            WHERE p.exam_identifier = ?
        )
        """,
        (exam_identifier,),
    )

    row = cursor.fetchone()
    return bool(row[0])


def count_criteria(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count all mark criteria for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Number of mark criteria
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM mark_criteria mc
        JOIN questions q ON mc.question_id = q.id
        WHERE q.paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def sum_marks_from_criteria(paper_id: int, conn: sqlite3.Connection) -> int:
    """Sum all marks_available from mark criteria for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Total marks from all criteria
    """
    cursor = conn.execute(
        """
        SELECT COALESCE(SUM(mc.marks_available), 0)
        FROM mark_criteria mc
        JOIN questions q ON mc.question_id = q.id
        WHERE q.paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def sum_marks_for_question(question_id: int, conn: sqlite3.Connection) -> int:
    """Sum all marks_available from mark criteria for a question.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        Total marks from all criteria for the question
    """
    cursor = conn.execute(
        """
        SELECT COALESCE(SUM(marks_available), 0)
        FROM mark_criteria
        WHERE question_id = ?
        """,
        (question_id,),
    )

    row = cursor.fetchone()
    return int(row[0])


def get_criteria_info_for_question(question_id: int, conn: sqlite3.Connection) -> dict[int, int]:
    """Get criterion indices and marks_available for a question.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        Dictionary mapping criterion_index -> marks_available
        (e.g., {0: 1, 1: 2, 2: 1})
    """
    cursor = conn.execute(
        """
        SELECT criterion_index, marks_available
        FROM mark_criteria
        WHERE question_id = ?
        ORDER BY criterion_index
        """,
        (question_id,),
    )

    return {int(row[0]): int(row[1]) for row in cursor.fetchall()}


def get_mark_scheme_for_question(
    question_id: int, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Fetch complete mark scheme grouped by part and criterion.

    Single query with JOINs to fetch entire mark scheme hierarchy.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        [
            {
                'part_id': int,
                'part_letter': str | None,
                'sub_part_letter': str | None,
                'part_display_order': int,
                'expected_answer': str | None,
                'criteria': [
                    {
                        'criterion_id': int,
                        'criterion_index': int,
                        'marks_available': int,
                        'mark_type_code': str,
                        'mark_type_name': str,
                        'depends_on': int | None,
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
            },
            ...
        ]
    """
    # Use Row factory for named column access
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        """
        SELECT
            qp.id AS part_id,
            qp.part_letter,
            qp.sub_part_letter,
            qp.display_order AS part_display_order,
            qp.expected_answer,

            mc.id AS criterion_id,
            mc.criterion_index,
            mc.marks_available,
            mc.depends_on_criterion_index,

            mt.code AS mark_type_code,
            mt.display_name AS mark_type_name,

            mcb.id AS content_block_id,
            mcb.block_type,
            mcb.display_order AS block_display_order,
            mcb.content_text,
            mcb.diagram_description

        FROM question_parts qp
        JOIN mark_criteria mc ON mc.question_part_id = qp.id
        JOIN mark_types mt ON mc.mark_type_id = mt.id
        LEFT JOIN mark_criteria_content_blocks mcb ON mcb.mark_criteria_id = mc.id

        WHERE qp.question_id = ?

        ORDER BY
            qp.display_order,
            mc.criterion_index,
            mcb.display_order
        """,
        (question_id,),
    )

    rows = cursor.fetchall()

    # Group flat rows into hierarchy
    parts_dict = {}  # part_id -> part dict
    criteria_dict = {}  # criterion_id -> criterion dict

    for row in rows:
        part_id = int(row["part_id"])
        criterion_id = int(row["criterion_id"])
        content_block_id = row["content_block_id"]

        # Build part structure (if first time seeing this part)
        if part_id not in parts_dict:
            parts_dict[part_id] = {
                "part_id": part_id,
                "part_letter": row["part_letter"],
                "sub_part_letter": row["sub_part_letter"],
                "part_display_order": int(row["part_display_order"]),
                "expected_answer": row["expected_answer"],
                "criteria": [],
            }

        # Build criterion structure (if first time seeing this criterion)
        if criterion_id not in criteria_dict:
            criterion = {
                CriterionFields.CRITERION_ID: criterion_id,
                "criterion_index": int(row["criterion_index"]),
                CriterionFields.MARKS_AVAILABLE: int(row[CriterionFields.MARKS_AVAILABLE]),
                "depends_on": row["depends_on_criterion_index"],
                "mark_type_code": row["mark_type_code"],
                "mark_type_name": row["mark_type_name"],
                "content_blocks": [],
            }
            criteria_dict[criterion_id] = criterion
            parts_dict[part_id]["criteria"].append(criterion)

        # Add content block (if exists - LEFT JOIN means might be NULL)
        if content_block_id is not None:
            block = {
                "block_type": row["block_type"],
                "content_text": row["content_text"],
                "diagram_description": row["diagram_description"],
            }
            criteria_dict[criterion_id]["content_blocks"].append(block)

    # Return parts in order (already sorted by ORDER BY)
    return list(parts_dict.values())


def delete_mark_criteria_for_paper(paper_id: int, conn: sqlite3.Connection) -> None:
    """Delete all mark criteria, content, and marking results for a paper.

    Used when updating mark schemes - removes existing marking data
    before inserting updated version.

    Manually cascades to delete:
    - question_marking_results (depends on mark_criteria_id)
    - mark_criteria_content_blocks
    - mark_criteria

    Note: Schema does not use ON DELETE CASCADE, so manual deletion required.
    Order matters - must delete in reverse dependency order.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Raises:
        ValueError: If paper not found
    """
    # Check paper exists
    cursor = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,))
    if cursor.fetchone() is None:
        raise ValueError(f"Paper ID {paper_id} not found")

    # Delete in correct order to avoid FK constraint errors

    # 1. Delete question_marking_results first (depends on mark_criteria_id)
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

    # 2. Delete mark criteria content blocks
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

    # 3. Delete mark criteria
    conn.execute(
        """
        DELETE FROM mark_criteria
        WHERE question_id IN (
            SELECT id FROM questions WHERE paper_id = ?
        )
        """,
        (paper_id,),
    )
