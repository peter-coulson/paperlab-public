"""Orchestrate paper structure loading from JSON into database (REFACTORED).

This module coordinates the workflow for loading exam paper structure:
- Parse and validate JSON input (Pydantic models)
- Validate business rules (validators module)
- Create database records (repositories)
- Verify loaded data integrity

Transaction management:
- CLI layer manages all transactions (commit/rollback)
- This module receives connection and performs operations
- Exceptions bubble to CLI layer for rollback

Design principles:
- Orchestration only - no SQL queries in this module
- All SQL operations delegated to repositories
- Clear separation: loading/ orchestrates, repositories/ execute
- REFACTORED: Smaller, focused helper functions
"""

import sqlite3
from dataclasses import dataclass

from paperlab.data.repositories.marking import (
    exam_types,
    grade_boundaries,
    papers,
    question_content,
    question_parts,
    questions,
)
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import ensure_entity_does_not_exist, handle_update_mode
from paperlab.loading.models.papers import PaperStructureInput
from paperlab.loading.paper_diff_calculator import PaperDiff, PaperDiffCalculator
from paperlab.loading.paper_file_paths import validate_paper_filename_matches_convention
from paperlab.loading.validators.paper_validators import validate_paper_references


@dataclass
class ExpectedCounts:
    """Expected counts for verification after loading."""

    questions: int
    parts: int
    blocks: int
    boundaries: int


def _handle_replace_mode(
    paper: PaperStructureInput,
    conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, PaperDiff]:
    """Handle replace mode for existing paper."""

    def lookup_by_identifier(
        p: PaperStructureInput, connection: sqlite3.Connection
    ) -> dict[str, int | str] | None:
        try:
            return papers.get_paper_full(
                papers.get_paper_id(p.paper_identifier, connection), connection
            )
        except ValueError:
            return None

    diff_calculator = PaperDiffCalculator()

    def delete_paper_func(paper_id: int, connection: sqlite3.Connection) -> None:
        papers.delete_paper(paper_id, connection)

    should_proceed, diff = handle_update_mode(
        json_entity=paper,
        natural_key_lookup=lookup_by_identifier,
        diff_calculator=diff_calculator,
        delete_func=delete_paper_func,
        conn=conn,
        force=force,
    )
    assert isinstance(diff, PaperDiff)
    return should_proceed, diff


def _parse_and_validate_input(
    paper_json_path: str, conn: sqlite3.Connection
) -> PaperStructureInput:
    """Parse JSON and validate structure and references."""
    paper = load_and_parse_json(paper_json_path, PaperStructureInput)
    validate_paper_filename_matches_convention(paper_json_path, paper.paper_identifier)
    validate_paper_references(paper, conn)
    return paper


def _calculate_expected_counts(paper: PaperStructureInput) -> ExpectedCounts:
    """Calculate expected counts for verification."""
    expected_questions = len(paper.questions)
    expected_parts = sum(len(q.parts) for q in paper.questions)
    expected_blocks = sum(len(part.content_blocks) for q in paper.questions for part in q.parts)
    expected_boundaries = len(paper.grade_boundaries)
    return ExpectedCounts(
        questions=expected_questions,
        parts=expected_parts,
        blocks=expected_blocks,
        boundaries=expected_boundaries,
    )


def _handle_create_mode(paper: PaperStructureInput, conn: sqlite3.Connection) -> None:
    """Handle create mode - ensure paper doesn't already exist."""

    def lookup_by_identifier(
        p: PaperStructureInput, connection: sqlite3.Connection
    ) -> dict[str, int | str] | None:
        try:
            return papers.get_paper_full(
                papers.get_paper_id(p.paper_identifier, connection), connection
            )
        except ValueError:
            return None

    ensure_entity_does_not_exist(
        natural_key_lookup=lookup_by_identifier,
        json_entity=paper,
        conn=conn,
        entity_type_name=f"Paper '{paper.paper_identifier}'",
    )


def _create_paper_records(paper: PaperStructureInput, conn: sqlite3.Connection) -> int:
    """Create paper, questions, parts, content blocks, and grade boundaries."""
    exam_type_id = exam_types.get_by_exam_type(
        paper.exam_type.exam_board,
        paper.exam_type.exam_level,
        paper.exam_type.subject,
        paper.exam_type.paper_code,
        conn,
    )

    paper_id = papers.create_paper(
        exam_type_id,
        paper.paper_instance.exam_date,
        paper.paper_instance.total_marks,
        paper.paper_identifier,
        conn,
    )

    for question in paper.questions:
        question_id = questions.create_question(
            paper_id,
            question.question_number,
            question.total_marks,
            conn,
        )

        for part in question.parts:
            part_id = question_parts.create_part(
                question_id,
                part.part_letter,
                part.sub_part_letter,
                part.display_order,
                conn,
            )

            for block in part.content_blocks:
                question_content.create_content_block(
                    part_id,
                    block.block_type,
                    block.display_order,
                    block.content_text,
                    block.diagram_description,
                    conn,
                )

    for boundary in paper.grade_boundaries:
        grade_boundaries.create_boundary(
            paper_id,
            boundary.grade,
            boundary.min_raw_marks,
            boundary.display_order,
            conn,
        )

    return paper_id


def load_paper(
    paper_json_path: str, conn: sqlite3.Connection, replace: bool = False, force: bool = False
) -> int:
    """Load paper structure from JSON into database.

    Args:
        paper_json_path: Path to paper JSON file
        conn: Database connection (transaction managed by CLI layer)
        replace: If True, replace existing paper with same identifier
        force: If True, skip confirmation prompts

    Returns:
        paper_id

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails or user cancels operation
        sqlite3.Error: If database operations fail
    """
    # 1. Parse and validate input
    paper = _parse_and_validate_input(paper_json_path, conn)

    # 2. Calculate expected counts for verification
    expected = _calculate_expected_counts(paper)

    # 3. Handle replace vs create mode
    if replace:
        should_proceed, diff = _handle_replace_mode(paper, conn, force)
        if not should_proceed:
            paper_id = papers.get_paper_id(paper.paper_identifier, conn)
            return paper_id
    else:
        _handle_create_mode(paper, conn)

    # 4. Create database records
    paper_id = _create_paper_records(paper, conn)

    # 5. Verify loaded data
    verify_paper_loaded(
        paper_id, expected.questions, expected.parts, expected.blocks, expected.boundaries, conn
    )

    return paper_id


def verify_paper_loaded(
    paper_id: int,
    expected_questions: int,
    expected_parts: int,
    expected_blocks: int,
    expected_boundaries: int,
    conn: sqlite3.Connection,
) -> None:
    """Verify paper loaded correctly using repository queries."""
    actual_questions = questions.count_questions(paper_id, conn)
    if actual_questions != expected_questions:
        raise ValueError(
            f"Question count mismatch: expected {expected_questions}, got {actual_questions}"
        )

    actual_parts = question_parts.count_parts(paper_id, conn)
    if actual_parts != expected_parts:
        raise ValueError(f"Parts count mismatch: expected {expected_parts}, got {actual_parts}")

    actual_blocks = papers.count_content_blocks(paper_id, conn)
    if actual_blocks != expected_blocks:
        raise ValueError(
            f"Content blocks count mismatch: expected {expected_blocks}, got {actual_blocks}"
        )

    actual_boundaries = grade_boundaries.count_boundaries_for_paper(paper_id, conn)
    if actual_boundaries != expected_boundaries:
        raise ValueError(
            f"Grade boundaries count mismatch: expected {expected_boundaries}, "
            f"got {actual_boundaries}"
        )
