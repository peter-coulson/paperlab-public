"""Repository for question_content_blocks table.

Provides data access methods for question content blocks.
"""

import sqlite3

from paperlab.config import ErrorMessages


def create_content_block(
    part_id: int,
    block_type: str,
    display_order: int,
    content_text: str | None,
    diagram_description: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create content block for a question part.

    NOT idempotent - each call creates new block. Caller must ensure not duplicate.
    Does NOT commit - caller manages transaction.

    Args:
        part_id: Database ID of parent question part
        block_type: 'text' or 'diagram'
        display_order: Display order within part
        content_text: Text content (required if block_type='text')
        diagram_description: Diagram description (required if block_type='diagram')
        conn: Database connection

    Returns:
        content_block_id

    Raises:
        sqlite3.IntegrityError: If duplicate display_order for this part
        ValueError: If failed to get content_block_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO question_content_blocks (
            question_part_id,
            block_type,
            display_order,
            content_text,
            diagram_description
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            part_id,
            block_type,
            display_order,
            content_text,
            diagram_description,
        ),
    )

    content_id = cursor.lastrowid
    if content_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="content"))
    return content_id


def content_exists_for_paper(exam_identifier: str, conn: sqlite3.Connection) -> bool:
    """Check if any content blocks exist for a paper (for duplicate check).

    Args:
        exam_identifier: Unique exam identifier
        conn: Database connection

    Returns:
        True if content blocks exist, False otherwise
    """
    cursor = conn.execute(
        """
        SELECT EXISTS(
            SELECT 1
            FROM question_content_blocks qcb
            JOIN question_parts qp ON qcb.question_part_id = qp.id
            JOIN questions q ON qp.question_id = q.id
            JOIN papers p ON q.paper_id = p.id
            WHERE p.exam_identifier = ?
        )
        """,
        (exam_identifier,),
    )

    row = cursor.fetchone()
    return bool(row[0])


def get_content_for_question(
    question_id: int, conn: sqlite3.Connection
) -> list[dict[str, list[dict[str, str | None]] | int | str | None]]:
    """Fetch question content blocks grouped by part.

    Returns question text content (not mark scheme content) for display
    in question results view.

    Args:
        question_id: Database ID of question
        conn: Database connection

    Returns:
        List of dicts with keys:
        - part_id: int
        - part_letter: str | None
        - sub_part_letter: str | None
        - display_order: int
        - content_blocks: list of dicts with block_type, content_text,
          diagram_description

    Note:
        Returns empty list if no parts/content found for question.
        Parts are ordered by display_order.
        Diagram image paths are derived from convention at API layer.
    """
    cursor = conn.execute(
        """
        SELECT
            qp.id AS part_id,
            qp.part_letter,
            qp.sub_part_letter,
            qp.display_order,
            qcb.block_type,
            qcb.content_text,
            qcb.diagram_description
        FROM question_parts qp
        LEFT JOIN question_content_blocks qcb ON qcb.question_part_id = qp.id
        WHERE qp.question_id = ?
        ORDER BY qp.display_order, qcb.display_order
        """,
        (question_id,),
    )

    # Group flat rows into hierarchy
    parts_dict: dict[int, dict[str, list[dict[str, str | None]] | int | str | None]] = {}
    parts_list: list[dict[str, list[dict[str, str | None]] | int | str | None]] = []

    for row in cursor.fetchall():
        part_id = int(row[0])
        block_type = row[4]

        # Build part structure (if first time seeing this part)
        if part_id not in parts_dict:
            part: dict[str, list[dict[str, str | None]] | int | str | None] = {
                "part_id": part_id,
                "part_letter": row[1],
                "sub_part_letter": row[2],
                "display_order": int(row[3]),
                "content_blocks": [],
            }
            parts_dict[part_id] = part
            parts_list.append(part)

        # Add content block (if exists - LEFT JOIN means might be NULL)
        if block_type is not None:
            content_blocks = parts_dict[part_id]["content_blocks"]
            if isinstance(content_blocks, list):
                content_blocks.append(
                    {
                        "block_type": block_type,
                        "content_text": row[5],
                        "diagram_description": row[6],
                    }
                )

    return parts_list
