"""Repository for mark_criteria_content_blocks table.

Provides data access methods for mark criteria content blocks.
"""

import sqlite3

from paperlab.config import ErrorMessages


def create_content_block(
    criterion_id: int,
    block_type: str,
    display_order: int,
    content_text: str | None,
    diagram_description: str | None,
    conn: sqlite3.Connection,
) -> int:
    """Create content block for a mark criterion.

    NOT idempotent - each call creates new block. Caller must ensure not duplicate.
    Does NOT commit - caller manages transaction.

    Args:
        criterion_id: Database ID of parent mark criterion
        block_type: 'text' or 'diagram'
        display_order: Display order within criterion
        content_text: Text content (required if block_type='text')
        diagram_description: Diagram description (required if block_type='diagram')
        conn: Database connection

    Returns:
        content_block_id

    Raises:
        sqlite3.IntegrityError: If duplicate display_order for this criterion
        ValueError: If failed to get content_block_id after INSERT
    """
    cursor = conn.execute(
        """
        INSERT INTO mark_criteria_content_blocks (
            mark_criteria_id,
            block_type,
            display_order,
            content_text,
            diagram_description
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            criterion_id,
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


def count_content_blocks_for_paper(paper_id: int, conn: sqlite3.Connection) -> int:
    """Count all criteria content blocks for a paper.

    Args:
        paper_id: Database ID of paper
        conn: Database connection

    Returns:
        Number of criteria content blocks
    """
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM mark_criteria_content_blocks mcb
        JOIN mark_criteria mc ON mcb.mark_criteria_id = mc.id
        JOIN questions q ON mc.question_id = q.id
        WHERE q.paper_id = ?
        """,
        (paper_id,),
    )

    row = cursor.fetchone()
    return int(row[0])
