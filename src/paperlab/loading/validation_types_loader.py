"""Orchestrate validation types configuration loading from JSON into database.

This module coordinates the workflow for loading validation type metadata:
- Parse and validate JSON input (Pydantic models)
- Validate business rules (code format, uniqueness)
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
"""

import sqlite3

from paperlab.data.repositories.evaluation import test_cases, validation_types
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import handle_update_mode
from paperlab.loading.models.config import ValidationTypesInput
from paperlab.loading.validation_types_diff_calculator import (
    ValidationTypesDiff,
    ValidationTypesDiffCalculator,
)


def _handle_replace_mode(
    types_input: ValidationTypesInput,
    conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, ValidationTypesDiff]:
    """Handle replace mode for existing validation types configuration.

    Args:
        types_input: Validation types configuration from JSON
        conn: Database connection
        force: If True, skip confirmation prompts

    Returns:
        Tuple of (should_proceed, diff)
        - should_proceed: True if should continue with insert, False if no changes
        - diff: Calculated differences

    Raises:
        ValueError: If user cancels operation
    """

    # Natural key lookup function (file-level, not row-level)
    # For validation types, we consider the entire file as the entity
    def lookup_by_file(
        _: ValidationTypesInput, connection: sqlite3.Connection
    ) -> dict[str, int] | None:
        # Return a dummy dict if any types exist, None otherwise
        count = validation_types.count_validation_types(connection)
        return {"id": 1} if count > 0 else None

    # Diff calculator
    diff_calculator = ValidationTypesDiffCalculator()

    # Delete function (deletes ALL validation types)
    def delete_all_types(_: int, connection: sqlite3.Connection) -> None:
        # Check for FK constraint - if any test cases exist, block deletion
        test_case_count = test_cases.count_all(connection)
        if test_case_count > 0:
            raise ValueError(
                f"Cannot replace validation types - {test_case_count} test case(s) exist.\n\n"
                "Deleting validation types would orphan test cases.\n"
                "This is blocked because schema has explicit ON DELETE RESTRICT "
                "(intentional data protection).\n\n"
                "To replace validation types configuration, you must first:\n"
                "  1. Delete all test cases manually, OR\n"
                "  2. Remove ON DELETE RESTRICT from schema (requires migration)\n\n"
                "Note: Deleting test cases will also delete all test_case_marks."
            )
        validation_types.delete_all(connection)

    # Use generic update framework
    should_proceed, diff = handle_update_mode(
        json_entity=types_input,
        natural_key_lookup=lookup_by_file,
        diff_calculator=diff_calculator,
        delete_func=delete_all_types,
        conn=conn,
        force=force,
    )
    # Type narrowing: diff_calculator returns ValidationTypesDiff
    assert isinstance(diff, ValidationTypesDiff)
    return should_proceed, diff


def load_validation_types(
    json_path: str,
    conn: sqlite3.Connection,
    replace: bool = False,
    force: bool = False,
) -> int:
    """Load validation types configuration from JSON into database.

    Args:
        json_path: Path to validation types JSON file
        conn: Database connection (transaction managed by CLI layer)
        replace: If True, replace existing validation types configuration
        force: If True, skip confirmation prompts

    Returns:
        Number of validation types loaded

    Raises:
        ValueError: If validation types already exist and replace=False
        FileNotFoundError: If JSON file doesn't exist
        ValidationError: If JSON doesn't match schema or validation fails
        sqlite3.Error: If database operations fail

    Transaction semantics:
        - CLI layer manages all transactions (commit/rollback)
        - This function receives connection and performs operations
        - Exceptions bubble to CLI layer for rollback
        - Caller manages connection lifecycle (use context manager)

    Example:
        >>> from paperlab.data.database import connection
        >>> from paperlab.config import settings
        >>> json_path = str(settings.evaluation_config_path / "validation_types.json")
        >>> with connection(settings.evaluation_db_path) as conn:
        ...     count = load_validation_types(json_path, conn)
        >>> print(f"Loaded {count} validation types")
    """

    # Load and parse JSON (with Pydantic validation)
    types_input = load_and_parse_json(json_path, ValidationTypesInput)

    # Handle replace mode if requested
    if replace:
        should_proceed, _diff = _handle_replace_mode(types_input, conn, force)
        if not should_proceed:
            print("No changes detected. Skipping load.")
            return 0
    else:
        # Create mode: ensure no validation types exist
        # (For validation types, we check if ANY types exist, not specific code)
        if validation_types.count_validation_types(conn) > 0:
            raise ValueError(
                "Validation types already exist in database. Use --replace flag to update them."
            )

    # Create all validation types from JSON (single batch INSERT)
    types_data = [
        {
            "code": vtype.code,
            "display_name": vtype.display_name,
            "description": vtype.description,
        }
        for vtype in types_input.validation_types
    ]

    rows_inserted = validation_types.create_validation_types_batch(types_data, conn)

    # Verify loaded data (count-based check)
    expected_count = len(types_input.validation_types)

    if rows_inserted != expected_count:
        raise ValueError(
            f"Verification failed: Expected to insert {expected_count} validation types, "
            f"but inserted {rows_inserted}"
        )

    return rows_inserted
