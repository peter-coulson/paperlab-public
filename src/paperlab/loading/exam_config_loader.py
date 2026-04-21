"""Orchestrate exam configuration loading from JSON into database.

This module coordinates the workflow for loading exam configuration:
- Parse and validate JSON input (Pydantic models)
- Handle replace mode with diff calculation
- Create exam_types records (papers)
- Expand mark_type_groups and create mark_types records
- Verify loaded data integrity

Transaction management:
- CLI layer manages all transactions (commit/rollback)
- This module receives connection and performs operations
- Exceptions bubble to CLI layer for rollback

Design principles:
- Orchestration only - no SQL queries in this module
- All SQL operations delegated to repositories
- Clear separation: loading/ orchestrates, repositories/ execute
"""

import sqlite3

from paperlab.data.repositories.marking import exam_types, mark_types, papers
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import ensure_entity_does_not_exist
from paperlab.loading.exam_config_diff_calculator import (
    ExamConfigDiff,
    ExamConfigDiffCalculator,
)
from paperlab.loading.exam_config_helpers import (
    calculate_expected_mark_types,
    expand_mark_type_groups,
)
from paperlab.loading.models.config import ExamConfigInput


def _handle_replace_mode(
    config: ExamConfigInput,
    conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, ExamConfigDiff]:
    """Handle replace mode for existing exam config.

    Args:
        config: Exam configuration from JSON
        conn: Database connection
        force: If True, skip confirmation prompts

    Returns:
        Tuple of (should_proceed, diff)
        - should_proceed: True if should continue with insert, False if no changes
        - diff: Calculated differences

    Raises:
        ValueError: If config doesn't exist or user cancels operation
    """
    from paperlab.loaders.update_framework import confirm_destructive_changes

    # Calculate diff
    diff_calculator = ExamConfigDiffCalculator()
    diff = diff_calculator.calculate_diff(config, None, conn)

    # Error if entity doesn't exist
    if not diff.exists:
        raise ValueError(
            "Cannot update exam config - it doesn't exist. "
            "Remove --replace flag to create a new configuration."
        )

    # Early return if no changes
    if not diff.has_changes:
        print("✓ Exam configuration is already up to date (no changes)")
        return False, diff

    # Display diff
    print(diff.format_diff())

    # Prompt for confirmation if destructive changes
    if diff.has_destructive_changes and not force and not confirm_destructive_changes():
        raise ValueError("Operation cancelled by user")

    # Check for CASCADE constraint limitation
    # Schema does not have ON DELETE CASCADE for papers.exam_type_id FK
    # If paper instances exist, delete will fail with FK constraint error
    paper_count = papers.count_papers_for_subject(
        config.exam_board, config.exam_level, config.subject, conn
    )
    if paper_count > 0:
        raise ValueError(
            f"Cannot replace exam config - {paper_count} paper instance(s) exist "
            "for this subject.\n\n"
            "Replace mode requires ON DELETE CASCADE on papers.exam_type_id "
            "foreign key, which is not currently enabled in the schema.\n\n"
            "This is intentional data protection to prevent accidental deletion of:\n"
            "  - Paper instances (exam papers that have been loaded)\n"
            "  - Questions and question parts\n"
            "  - Mark schemes and criteria\n"
            "  - Student work and marking results\n\n"
            "To replace this exam config, you must first manually delete all paper instances "
            "or enable CASCADE DELETE in the schema (requires migration)."
        )

    # Delete in correct order to avoid FK constraint errors
    # 1. Delete mark_types first (they have FK to exam_types)
    mark_types.delete_for_subject(config.exam_board, config.exam_level, config.subject, conn)

    # 2. Delete exam_types (now safe - no FKs reference them except papers, which we checked above)
    exam_types.delete_exam_types_for_subject(
        config.exam_board, config.exam_level, config.subject, conn
    )

    return True, diff


def load_exam_config(
    json_path: str, conn: sqlite3.Connection, replace: bool = False, force: bool = False
) -> None:
    """Load exam configuration from JSON into database.

    Args:
        json_path: Path to exam config JSON file
        conn: Database connection (transaction managed by CLI layer)
        replace: If True, replace existing config for this subject
        force: If True, skip confirmation prompts

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)
        ValueError: If business validation fails or user cancels operation
        sqlite3.Error: If database operations fail

    Workflow (create mode):
        1. Parse and validate JSON (Pydantic)
        2. Check config doesn't exist (via exam_types lookup)
        3. Phase 1: Insert all papers (creates exam_type records)
        4. Phase 2: Expand mark_type_groups and insert mark_types
        5. Verify loaded data

    Workflow (replace mode):
        1. Parse and validate JSON (Pydantic)
        2. Check config exists
        3. Calculate diff and prompt for confirmation (unless force=True)
        4. Delete all exam_types for subject (CASCADE deletes mark_types, papers, etc.)
        5. Phase 1: Insert all papers
        6. Phase 2: Expand mark_type_groups and insert mark_types
        7. Verify loaded data

    Transaction management:
        - CLI layer manages all transactions (commit/rollback)
        - This function receives connection and performs operations
        - Exceptions bubble to CLI layer for rollback
        - Caller must manage connection lifecycle (use context manager)

    Example:
        ```python
        from paperlab.data.database import connection
        from paperlab.config import settings

        # Good - connection automatically closed ✅
        with connection(settings.db_path) as conn:
            load_exam_config("data/config/pearson-edexcel/gcse/mathematics.json", conn)
        # Connection closed here, even if exception occurred
        ```
    """
    # 1. Parse and validate JSON
    config = load_and_parse_json(json_path, ExamConfigInput)

    # Calculate expected counts from input data (single source of truth)
    expected_papers = len(config.papers)
    expected_mark_types = calculate_expected_mark_types(config.mark_type_groups)

    # Handle replace mode
    if replace:
        should_proceed, diff = _handle_replace_mode(config, conn, force)

        # Early return if no changes (CLI will commit empty transaction)
        if not should_proceed:
            return

        # Config was deleted, now recreate it (fall through to create logic below)
    else:
        # Create mode: check config doesn't already exist
        def lookup_by_subject(
            cfg: ExamConfigInput, connection: sqlite3.Connection
        ) -> dict[str, int | str] | None:
            papers = exam_types.get_all_for_subject(
                cfg.exam_board, cfg.exam_level, cfg.subject, connection
            )
            if papers:
                return {"exists": True}
            return None

        entity_name = f"Exam config '{config.exam_board} {config.exam_level} {config.subject}'"
        ensure_entity_does_not_exist(
            natural_key_lookup=lookup_by_subject,
            json_entity=config,
            conn=conn,
            entity_type_name=entity_name,
        )

    # Phase 1: Create exam_types records (papers)
    # Build list of tuples: (board, level, subject, paper_code, display_name)
    exam_type_tuples = [
        (
            config.exam_board,
            config.exam_level,
            config.subject,
            paper.paper_code,
            paper.display_name,
        )
        for paper in config.papers
    ]
    exam_types.create_exam_types_batch(exam_type_tuples, conn)

    # Phase 2: Expand mark_type_groups and create mark_types
    # Looks up exam_type_ids and creates tuples for batch insert
    mark_type_tuples = expand_mark_type_groups(config, conn)
    mark_types.create_mark_types_batch(mark_type_tuples, conn)

    # Verify loaded data (staged transaction visible to this connection)
    # CLI handles commit/rollback - orchestrator just validates and returns
    verify_exam_config_loaded(
        config.exam_board,
        config.exam_level,
        config.subject,
        expected_papers,
        expected_mark_types,
        conn,
    )


def verify_exam_config_loaded(
    exam_board: str,
    exam_level: str,
    subject: str,
    expected_papers: int,
    expected_mark_types: int,
    conn: sqlite3.Connection,
) -> None:
    """Verify exam configuration loaded correctly using repository queries.

    Performs post-load integrity checks by comparing expected counts
    (calculated from input JSON) against actual database counts.

    This ensures:
    1. All create operations succeeded
    2. No silent failures occurred
    3. Database state matches input JSON structure

    Args:
        exam_board: Exam board name
        exam_level: Qualification level
        subject: Subject name
        expected_papers: Number of papers from input JSON
        expected_mark_types: Number of mark_types after expansion from input JSON
        conn: Database connection

    Raises:
        ValueError: If any count mismatch is detected
    """
    # Check papers count
    actual_papers = exam_types.count_exam_types_for_subject(exam_board, exam_level, subject, conn)
    if actual_papers != expected_papers:
        raise ValueError(f"Papers count mismatch: expected {expected_papers}, got {actual_papers}")

    # Check mark_types count
    actual_mark_types = mark_types.count_mark_types_for_subject(
        exam_board, exam_level, subject, conn
    )
    if actual_mark_types != expected_mark_types:
        raise ValueError(
            f"Mark types count mismatch: expected {expected_mark_types}, got {actual_mark_types}"
        )
