"""Orchestrate LLM models configuration loading from JSON into database.

This module coordinates the workflow for loading LLM model metadata:
- Parse and validate JSON input (Pydantic models)
- Validate business rules (provider consistency)
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

from paperlab.data.repositories.marking import llm_models
from paperlab.loaders.json_utils import load_and_parse_json
from paperlab.loaders.update_framework import handle_update_mode
from paperlab.loading.llm_models_diff_calculator import LLMModelsDiff, LLMModelsDiffCalculator
from paperlab.loading.models.config import LLMModelsInput


def _handle_replace_mode(
    models_input: LLMModelsInput,
    conn: sqlite3.Connection,
    force: bool,
) -> tuple[bool, LLMModelsDiff]:
    """Handle replace mode for existing models configuration.

    Args:
        models_input: Models configuration from JSON
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
    # For LLM models, we consider the entire file as the entity
    def lookup_by_file(_: LLMModelsInput, connection: sqlite3.Connection) -> dict[str, int] | None:
        # Return a dummy dict if any models exist, None otherwise
        count = llm_models.count_models(connection)
        return {"id": 1} if count > 0 else None

    # Diff calculator
    diff_calculator = LLMModelsDiffCalculator()

    # Delete function (deletes ALL models)
    def delete_all_models(_: int, connection: sqlite3.Connection) -> None:
        # Check for FK constraint - if any marking attempts exist, block deletion
        # Count marking attempts across all statuses (success, failure, etc.)
        from paperlab.data.repositories.marking import marking_attempts

        attempt_count = marking_attempts.count_all(connection)

        if attempt_count > 0:
            raise ValueError(
                f"Cannot replace LLM models - {attempt_count} marking attempt(s) exist.\n\n"
                "Deleting LLM models would orphan marking history.\n"
                "This is blocked because schema lacks CASCADE DELETE "
                "(intentional data protection).\n\n"
                "To replace LLM models configuration, you must first:\n"
                "  1. Delete all marking attempts manually, OR\n"
                "  2. Add CASCADE DELETE to schema (requires migration)\n\n"
                "Note: Deleting marking attempts will also delete "
                "all question_marking_results."
            )
        llm_models.delete_all(connection)

    # Use generic update framework
    should_proceed, diff = handle_update_mode(
        json_entity=models_input,
        natural_key_lookup=lookup_by_file,
        diff_calculator=diff_calculator,
        delete_func=delete_all_models,
        conn=conn,
        force=force,
    )
    # Type narrowing: diff_calculator returns LLMModelsDiff
    assert isinstance(diff, LLMModelsDiff)
    return should_proceed, diff


def load_llm_models(
    json_path: str,
    conn: sqlite3.Connection,
    replace: bool = False,
    force: bool = False,
) -> int:
    """Load LLM models configuration from JSON into database.

    Args:
        json_path: Path to models JSON file
        conn: Database connection (transaction managed by CLI layer)
        replace: If True, replace existing models configuration
        force: If True, skip confirmation prompts

    Returns:
        Number of models loaded

    Raises:
        ValueError: If models already exist and replace=False
        FileNotFoundError: If JSON file doesn't exist
        ValidationError: If JSON doesn't match schema or validation fails
        sqlite3.Error: If database operations fail

    Transaction semantics:
        - CLI layer manages all transactions (commit/rollback)
        - This function receives connection and performs operations
        - Exceptions bubble to CLI layer for rollback
        - Caller manages connection lifecycle (use context manager)

    Example (CLI layer usage):
        # This function receives a connection from the CLI layer.
        # Business logic NEVER opens connections - they are provided by the caller.

        >>> from paperlab.data.database import connection
        >>> json_path = str(settings.config_path / "llm_models.json")
        >>> # Connection opened by CLI layer:
        >>> with connection() as conn:
        ...     count = load_llm_models(json_path, conn)
        >>> print(f"Loaded {count} models")
    """

    # Load and parse JSON (with Pydantic validation)
    models_input = load_and_parse_json(json_path, LLMModelsInput)

    # Handle replace mode if requested
    if replace:
        should_proceed, _diff = _handle_replace_mode(models_input, conn, force)
        if not should_proceed:
            print("No changes detected. Skipping load.")
            return 0
    else:
        # Create mode: ensure no models exist
        # (For LLM models, we check if ANY models exist, not specific identifier)
        if llm_models.count_models(conn) > 0:
            raise ValueError(
                "LLM models already exist in database. Use --replace flag to update them."
            )

    # Create all models from JSON (single batch INSERT)
    models_data = [
        {
            "model_identifier": model.model_identifier,
            "display_name": model.display_name,
            "provider": model.provider,
        }
        for model in models_input.models
    ]

    rows_inserted = llm_models.create_models_batch(models_data, conn)

    # Verify loaded data (count-based check)
    expected_count = len(models_input.models)

    if rows_inserted != expected_count:
        raise ValueError(
            f"Verification failed: Expected to insert {expected_count} models, "
            f"but inserted {rows_inserted}"
        )

    return rows_inserted
