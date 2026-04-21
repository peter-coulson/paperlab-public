"""Orchestrate mark scheme loading from JSON into database (REFACTORED VERSION).

This module coordinates the workflow for loading exam mark schemes:
- Parse and validate JSON input (Pydantic models)
- Validate business rules (validators module)
- Create database records (repositories)
- Verify loaded data integrity
- Verify cross-file consistency (paper ↔ mark scheme)

Transaction management:
- CLI layer manages all transactions (commit/rollback)
- This module receives connection and performs operations
- Exceptions bubble to CLI layer for rollback

Design principles:
- Orchestration only - no SQL queries in this module
- All SQL operations delegated to repositories
- Clear separation: loading/ orchestrates, repositories/ execute
- REFACTORED: Smaller, focused helper functions for better testability
"""

import sqlite3
from dataclasses import dataclass

from paperlab.data.repositories.marking import (
    criteria_content,
    exam_types,
    mark_criteria,
    mark_types,
    papers,
    question_parts,
    questions,
)
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import ensure_entity_does_not_exist, handle_update_mode
from paperlab.loading.marks_diff_calculator import MarksDiff, MarksDiffCalculator
from paperlab.loading.models.marks import MarkSchemeInput
from paperlab.loading.paper_file_paths import validate_marks_filename_matches_convention
from paperlab.loading.validators.marks_validators import (
    validate_mark_scheme_references,
    validate_mark_scheme_structure,
)


@dataclass
class ExpectedCounts:
    """Expected counts for verification after loading."""

    criteria: int
    blocks: int
    answers_map: dict[tuple[int, str | None, str | None], str | None]


def _handle_replace_mode(
    marks: MarkSchemeInput,
    conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, MarksDiff]:
    """Handle replace mode for existing mark scheme.

    Args:
        marks: Mark scheme from JSON
        conn: Database connection
        force: If True, skip confirmation prompts

    Returns:
        Tuple of (should_proceed, diff)
        - should_proceed: True if should continue with insert, False if no changes
        - diff: Calculated differences

    Raises:
        ValueError: If paper doesn't exist or user cancels operation
    """

    # Natural key lookup function (lookup by paper identifier)
    def lookup_by_identifier(
        m: MarkSchemeInput, connection: sqlite3.Connection
    ) -> dict[str, int | str] | None:
        try:
            paper_id = papers.get_paper_id(m.paper_identifier, connection)
            return papers.get_paper_full(paper_id, connection)
        except ValueError:
            return None

    # Diff calculator
    diff_calculator = MarksDiffCalculator()

    # Delete function (delete just mark criteria, not paper)
    def delete_marks_func(paper_id: int, connection: sqlite3.Connection) -> None:
        mark_criteria.delete_mark_criteria_for_paper(paper_id, connection)

    # Use generic update framework
    should_proceed, diff = handle_update_mode(
        json_entity=marks,
        natural_key_lookup=lookup_by_identifier,
        diff_calculator=diff_calculator,
        delete_func=delete_marks_func,
        conn=conn,
        force=force,
    )
    # Type narrowing: diff_calculator returns MarksDiff
    assert isinstance(diff, MarksDiff)
    return should_proceed, diff


def _parse_and_validate_input(marks_json_path: str, conn: sqlite3.Connection) -> MarkSchemeInput:
    """Parse JSON and validate structure and references.

    Args:
        marks_json_path: Path to mark scheme JSON file
        conn: Database connection for reference validation

    Returns:
        Parsed and validated MarkSchemeInput

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails
    """
    # Parse and validate JSON
    marks = load_and_parse_json(marks_json_path, MarkSchemeInput)

    # Validate filename matches hierarchical convention
    validate_marks_filename_matches_convention(marks_json_path, marks.paper_identifier)

    # Validate business rules (calls repositories for lookups)
    validate_mark_scheme_structure(marks)
    validate_mark_scheme_references(marks, conn)  # Includes duplicate check

    return marks


def _calculate_expected_counts(marks: MarkSchemeInput) -> ExpectedCounts:
    """Calculate expected counts for verification.

    Args:
        marks: Parsed mark scheme input

    Returns:
        ExpectedCounts with criteria, blocks, and answers map
    """
    # Exclude structural NULL criteria (mark_type_code=None) from counts
    expected_criteria = sum(
        sum(1 for p in q.question_parts for c in p.mark_criteria if c.mark_type_code is not None)
        for q in marks.questions
    )

    expected_blocks = sum(
        len(criterion.content_blocks)
        for q in marks.questions
        for p in q.question_parts
        for criterion in p.mark_criteria
        if criterion.mark_type_code is not None
    )

    # Build expected_answers map for verification
    expected_answers_map = {
        (q.question_number, p.part_letter, p.sub_part_letter): p.expected_answer
        for q in marks.questions
        for p in q.question_parts
    }

    return ExpectedCounts(
        criteria=expected_criteria, blocks=expected_blocks, answers_map=expected_answers_map
    )


def _handle_create_mode(marks: MarkSchemeInput, conn: sqlite3.Connection) -> None:
    """Handle create mode - ensure mark scheme doesn't already exist.

    Args:
        marks: Mark scheme from JSON
        conn: Database connection

    Raises:
        ValueError: If mark scheme already exists
    """

    def lookup_by_identifier(
        m: MarkSchemeInput, connection: sqlite3.Connection
    ) -> dict[str, int | str] | None:
        try:
            paper_id = papers.get_paper_id(m.paper_identifier, connection)
            # Return a record if marks exist for this paper
            criteria_count = mark_criteria.count_criteria(paper_id, connection)
            if criteria_count > 0:
                return papers.get_paper_full(paper_id, connection)
            return None
        except ValueError:
            return None

    ensure_entity_does_not_exist(
        natural_key_lookup=lookup_by_identifier,
        json_entity=marks,
        conn=conn,
        entity_type_name=f"Mark scheme for paper '{marks.paper_identifier}'",
    )


def _create_mark_criteria_records(marks: MarkSchemeInput, conn: sqlite3.Connection) -> None:
    """Create mark criteria and content block records.

    Args:
        marks: Parsed mark scheme input
        conn: Database connection

    Raises:
        ValueError: If paper or exam type not found
        sqlite3.Error: If database operations fail
    """
    # Look up paper ID (must exist - validated earlier)
    paper_id = papers.get_paper_id(marks.paper_identifier, conn)

    # Look up exam type ID (used for mark_type_id lookups)
    exam_type_id = exam_types.get_by_exam_type(
        marks.exam_type.exam_board,
        marks.exam_type.exam_level,
        marks.exam_type.subject,
        marks.exam_type.paper_code,
        conn,
    )

    # Create criteria and content blocks for each question
    for question_data in marks.questions:
        question_id = questions.get_question_id(paper_id, question_data.question_number, conn)

        for part in question_data.question_parts:
            # Look up part_id
            part_id = question_parts.get_part_id(
                question_id,
                part.part_letter,
                part.sub_part_letter,
                conn,
            )

            # Update expected_answer for this part
            question_parts.update_expected_answer(part_id, part.expected_answer, conn)

            for criterion in part.mark_criteria:
                # Skip structural NULL criteria (mark_type_code=None)
                if criterion.mark_type_code is None:
                    continue

                # Map display_order to criterion_index
                criterion_index = criterion.display_order

                # Get mark_type_id
                mark_type_id = mark_types.get_by_code(criterion.mark_type_code, exam_type_id, conn)

                # Create criterion
                criterion_id = mark_criteria.create_criterion(
                    question_id,
                    part_id,
                    mark_type_id,
                    criterion_index,
                    criterion.marks_available,
                    criterion.depends_on_display_order,
                    conn,
                )

                # Create content blocks for this criterion
                for block in criterion.content_blocks:
                    criteria_content.create_content_block(
                        criterion_id,
                        block.block_type,
                        block.display_order,
                        block.content_text,
                        block.diagram_description,
                        conn,
                    )


def load_mark_scheme(
    marks_json_path: str, conn: sqlite3.Connection, replace: bool = False, force: bool = False
) -> int:
    """Load mark scheme from JSON into database.

    Args:
        marks_json_path: Path to mark scheme JSON file
        conn: Database connection (transaction managed by CLI layer)
        replace: If True, replace existing mark scheme with same paper identifier
        force: If True, skip confirmation prompts

    Returns:
        paper_id

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails, paper doesn't exist, or user cancels operation
        sqlite3.Error: If database operations fail

    Workflow:
        1. Parse and validate JSON (Pydantic)
        2. Run business validators (validates paper structure exists via repositories)
        3. Call repositories to create criteria and content blocks
        4. Verify loaded data via repositories
        5. Verify cross-file consistency via repositories
        6. Return paper_id

    Transaction management:
        - CLI layer manages all transactions (commit/rollback)
        - This function receives connection and performs operations
        - Exceptions bubble to CLI layer for rollback
        - Caller must manage connection lifecycle (use context manager)

    Example (CLI layer usage):
        ```python
        # This function receives a connection from the CLI layer.
        # Business logic NEVER opens connections - they are provided by the caller.
        # See cli/commands/load.py for actual implementation.

        # In CLI layer (cli/commands/load.py):
        from paperlab.data.database import connection

        with connection() as conn:
            paper_id = load_mark_scheme("data/mark_schemes/exam_marks.json", conn)
        # Connection opened and managed by CLI layer
        ```
    """
    # 1. Parse and validate input
    marks = _parse_and_validate_input(marks_json_path, conn)

    # 2. Calculate expected counts for verification
    expected = _calculate_expected_counts(marks)

    # 3. Handle replace vs create mode
    if replace:
        should_proceed, diff = _handle_replace_mode(marks, conn, force)

        # Early return if no changes
        if not should_proceed:
            paper_id = papers.get_paper_id(marks.paper_identifier, conn)
            return paper_id

        # Mark criteria deleted, now recreate (fall through to create logic)
    else:
        # Create mode: check marks don't already exist
        _handle_create_mode(marks, conn)

    # 4. Create database records
    _create_mark_criteria_records(marks, conn)

    # 5. Get paper_id for verification and return
    paper_id = papers.get_paper_id(marks.paper_identifier, conn)

    # 6. Verify loaded data
    verify_marks_loaded(paper_id, expected.criteria, expected.blocks, conn)
    verify_expected_answers_loaded(paper_id, expected.answers_map, conn)
    verify_paper_marks_consistency(paper_id, conn)

    return paper_id


def verify_marks_loaded(
    paper_id: int,
    expected_criteria: int,
    expected_blocks: int,
    conn: sqlite3.Connection,
) -> None:
    """Verify mark criteria loaded correctly using repository queries.

    Performs post-load integrity checks by comparing expected counts
    (calculated from input JSON) against actual database counts.

    This ensures:
    1. All create operations succeeded
    2. No silent failures occurred
    3. Database state matches input JSON structure

    Args:
        paper_id: Paper ID to verify
        expected_criteria: Number of mark criteria from input JSON
        expected_blocks: Number of content blocks from input JSON
        conn: Database connection

    Raises:
        ValueError: If any count mismatch is detected
    """
    # Check criteria count
    actual_criteria = mark_criteria.count_criteria(paper_id, conn)
    if actual_criteria != expected_criteria:
        raise ValueError(
            f"Mark criteria count mismatch: expected {expected_criteria}, got {actual_criteria}"
        )

    # Check content blocks count via repository
    actual_blocks = criteria_content.count_content_blocks_for_paper(paper_id, conn)
    if actual_blocks != expected_blocks:
        raise ValueError(
            f"Criteria content blocks count mismatch: "
            f"expected {expected_blocks}, got {actual_blocks}"
        )


def verify_paper_marks_consistency(paper_id: int, conn: sqlite3.Connection) -> None:
    """Verify paper and mark scheme are consistent.

    Performs cross-file validation by comparing paper total marks
    against mark scheme total marks. This ensures:
    1. Paper and mark scheme agree on total marks
    2. Questions and criteria are properly aligned

    Checks:
    - Total marks match (paper.total_marks == sum of criteria marks)
    - Question marks match (question.total_marks == sum of criteria for question)

    Args:
        paper_id: Paper ID to verify
        conn: Database connection

    Raises:
        ValueError: If paper and mark scheme are inconsistent
    """
    # Get paper total marks via repository
    paper_total_marks = papers.get_total_marks(paper_id, conn)

    # Get sum of marks from criteria via repository
    criteria_total_marks = mark_criteria.sum_marks_from_criteria(paper_id, conn)

    # Verify totals match
    if paper_total_marks != criteria_total_marks:
        raise ValueError(
            f"Paper/mark scheme total marks mismatch: "
            f"paper has {paper_total_marks}, criteria sum to {criteria_total_marks}"
        )

    # Verify per-question totals match using repository
    questions_data = questions.get_all_with_marks(paper_id, conn)

    for question_id, question_number, question_total_marks in questions_data:
        # Sum marks from criteria for this question via repository
        criteria_sum = mark_criteria.sum_marks_for_question(question_id, conn)

        if question_total_marks != criteria_sum:
            raise ValueError(
                f"Question {question_number} marks mismatch: "
                f"question has {question_total_marks}, criteria sum to {criteria_sum}"
            )


def verify_expected_answers_loaded(
    paper_id: int,
    expected_answers_map: dict[tuple[int, str | None, str | None], str | None],
    conn: sqlite3.Connection,
) -> None:
    """Verify expected_answer values were written correctly to database.

    This is a Tier 2 verification that compares what we intended to write
    (from input JSON) against what was actually written to the database.

    Does NOT validate business rules (that's Tier 1). Simply ensures
    database write operations succeeded correctly.

    Args:
        paper_id: Paper ID to verify
        expected_answers_map: Expected values from input JSON, mapping:
            (question_number, part_letter, sub_part_letter) -> expected_answer
        conn: Database connection

    Raises:
        ValueError: If database values don't match expected values
    """
    # Get actual values from database via repository
    actual_answers_map = question_parts.get_expected_answers_for_paper(paper_id, conn)

    # Compare keys (all parts should exist)
    if set(actual_answers_map.keys()) != set(expected_answers_map.keys()):
        raise ValueError(
            f"Part mismatch when verifying expected_answers. "
            f"Database has {len(actual_answers_map)} parts, expected {len(expected_answers_map)}"
        )

    # Compare values (expected_answer for each part)
    mismatches = []
    for part_key, expected_value in expected_answers_map.items():
        actual_value = actual_answers_map[part_key]
        if actual_value != expected_value:
            question_num, part_letter, sub_part_letter = part_key
            part_desc = f"({part_letter}" if part_letter else "(NULL"
            if sub_part_letter:
                part_desc += f")({sub_part_letter}"
            part_desc += ")"

            mismatches.append(
                f"  Question {question_num} {part_desc}: "
                f"DB has '{actual_value}', expected '{expected_value}'"
            )

    if mismatches:
        raise ValueError(
            f"Expected answer verification failed. {len(mismatches)} mismatch(es):\n"
            + "\n".join(mismatches)
        )
