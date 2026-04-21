"""Shared validation helpers for paper and mark scheme loading.

Cross-validation functions used by both paper and mark scheme loaders.
"""

import sqlite3
from collections.abc import Sequence

from paperlab.data.repositories.marking import papers, question_parts, questions
from paperlab.loading.models.marks import QuestionMarkScheme
from paperlab.loading.models.papers import Question
from paperlab.loading.models.shared import PaperInstanceBase


def validate_parts_match(
    question_id: int,
    question: Question | QuestionMarkScheme,
    conn: sqlite3.Connection,
) -> None:
    """Validate that question parts in database match JSON structure.

    Validates only part identity (part_letter, sub_part_letter), not marks.

    Args:
        question_id: Database ID of question
        question: Question from JSON (either Question or QuestionMarkScheme)
        conn: Database connection

    Raises:
        ValueError: If part identities don't match
    """
    # Get existing parts from database via repository
    db_parts = question_parts.get_parts_for_question(question_id, conn)

    if not db_parts:
        # No parts exist yet - will be created by loader
        return

    # Extract parts from JSON (handling both Question and QuestionMarkScheme)
    if isinstance(question, Question):
        # Question has explicit parts list (includes NULL part at display_order=0)
        json_parts_data = [
            (p.part_letter, p.sub_part_letter, p.display_order) for p in question.parts
        ]
    else:
        # QuestionMarkScheme: parts are directly in question_parts
        json_parts_data = [
            (p.part_letter, p.sub_part_letter, p.display_order) for p in question.question_parts
        ]

    # Compare parts - only identity (letter, subletter), not marks
    db_parts_set = {(p[0], p[1]) for p in db_parts}  # (letter, subletter)
    json_parts_set = {(p[0], p[1]) for p in json_parts_data}

    if db_parts_set != json_parts_set:
        # Sort with None values handled (None sorts before any string)
        def sort_key(part_tuple: tuple[str | None, str | None]) -> tuple[str, str]:
            return (part_tuple[0] or "", part_tuple[1] or "")

        db_parts_sorted = sorted(db_parts_set, key=sort_key)
        json_parts_sorted = sorted(json_parts_set, key=sort_key)

        raise ValueError(
            f"Question {question.question_number} parts mismatch between paper and mark scheme:\n"
            f"  Paper (database) has: {db_parts_sorted}\n"
            f"  Mark scheme (JSON) has: {json_parts_sorted}\n"
            f"  Missing from mark scheme: {sorted(db_parts_set - json_parts_set, key=sort_key)}\n"
            f"  Extra in mark scheme: {sorted(json_parts_set - db_parts_set, key=sort_key)}"
        )


def validate_paper_structure_exists(
    paper_identifier: str,
    paper_metadata: PaperInstanceBase,
    questions_list: Sequence[Question | QuestionMarkScheme],
    conn: sqlite3.Connection,
) -> None:
    """Validate that paper structure exists in database and matches JSON (mark scheme loading).

    Used by mark scheme loader to ensure paper was loaded first and structure matches exactly.

    Validates hierarchy from paper → questions → parts, but NOT content blocks
    (paper and mark scheme have different content blocks attached to the same parts).

    Args:
        paper_identifier: Generated paper identifier (from exam_type + exam_date)
        paper_metadata: Paper metadata from JSON
        questions_list: Questions from JSON (QuestionMarkScheme)
        conn: Database connection

    Raises:
        ValueError: If paper doesn't exist or structure doesn't match JSON input
    """
    # Check if paper exists and get paper metadata via repository
    paper_result = papers.get_paper_with_marks(paper_identifier, conn)

    if paper_result is None:
        raise ValueError(
            f"Paper '{paper_identifier}' not found in database. "
            "Load paper structure before mark scheme."
        )

    paper_id, db_total_marks = paper_result

    # Validate metadata matches (total_marks from papers table)
    if db_total_marks != paper_metadata.total_marks:
        raise ValueError(
            f"Paper total_marks mismatch for '{paper_identifier}': "
            f"database has {db_total_marks}, JSON has {paper_metadata.total_marks}"
        )

    # Validate questions match
    for question in questions_list:
        question_result = questions.get_question_with_marks(
            paper_id, question.question_number, conn
        )

        if question_result is None:
            raise ValueError(
                f"Question {question.question_number} not found in database for paper "
                f"'{paper_identifier}'. "
                "Paper structure must be loaded before mark scheme."
            )

        question_id, db_question_marks = question_result

        # Get expected marks from JSON (both Question and QuestionMarkScheme have total_marks)
        json_question_marks = question.total_marks

        if db_question_marks != json_question_marks:
            raise ValueError(
                f"Question {question.question_number} total_marks mismatch: "
                f"database has {db_question_marks}, JSON has {json_question_marks}"
            )

        # Validate parts match
        validate_parts_match(question_id, question, conn)
