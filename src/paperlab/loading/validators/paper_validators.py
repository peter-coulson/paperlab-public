"""Validators for paper structure loading.

Business rule validation for paper JSON input.
"""

import sqlite3

from paperlab.data.repositories.marking import exam_types
from paperlab.loading.models.papers import PaperStructureInput


def validate_paper_references(
    paper: PaperStructureInput,
    conn: sqlite3.Connection,
) -> None:
    """Validate paper database references.

    Database checks:
    1. exam_type (board/level/subject/paper_code) must exist

    Args:
        paper: Complete paper structure from JSON
        conn: Database connection

    Raises:
        ValueError: If exam_type doesn't exist
    """
    # Check exam type exists
    exam_types.get_by_exam_type(
        paper.exam_type.exam_board,
        paper.exam_type.exam_level,
        paper.exam_type.subject,
        paper.exam_type.paper_code,
        conn,
    )
