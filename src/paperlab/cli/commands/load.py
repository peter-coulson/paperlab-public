"""Loading commands for papers, mark schemes, and configuration."""

import sqlite3

from paperlab.cli.loading_utils import run_loader_command
from paperlab.config import settings
from paperlab.loading.exam_config_helpers import construct_config_path
from paperlab.loading.exam_config_loader import load_exam_config
from paperlab.loading.llm_models_loader import load_llm_models
from paperlab.loading.marks_loader import load_mark_scheme
from paperlab.loading.paper_loader import load_paper
from paperlab.loading.validation_types_loader import load_validation_types


def paper(json_path: str, replace: bool = False, force: bool = False) -> int:
    """Load paper structure from JSON into database.

    Args:
        json_path: Path to paper JSON file
        replace: If True, replace existing paper with same identifier
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    production_db = settings.db_path

    # Wrapper to call load_paper with connection
    def load_with_connection(conn: sqlite3.Connection) -> int:
        return load_paper(
            json_path,
            conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    if replace:
        success_message = "✅ Paper structure updated successfully (ID: {result})"
    else:
        success_message = "✅ Paper structure loaded successfully (ID: {result})"

    return run_loader_command(
        load_with_connection,
        db_paths=[production_db],
        db_schema_paths={production_db: None},
        success_message=success_message,
    )


def marks(json_path: str, replace: bool = False, force: bool = False) -> int:
    """Load mark scheme from JSON into database.

    Args:
        json_path: Path to mark scheme JSON file
        replace: If True, replace existing mark scheme with same paper identifier
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    production_db = settings.db_path

    # Wrapper to call load_mark_scheme with connection
    def load_with_connection(conn: sqlite3.Connection) -> int:
        return load_mark_scheme(
            json_path,
            conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    if replace:
        success_message = "✅ Mark scheme updated successfully (paper ID: {result})"
    else:
        success_message = "✅ Mark scheme loaded successfully (paper ID: {result})"

    return run_loader_command(
        load_with_connection,
        db_paths=[production_db],
        db_schema_paths={production_db: None},
        success_message=success_message,
    )


def llm_models(json_path: str | None = None, replace: bool = False, force: bool = False) -> int:
    """Load LLM models configuration from JSON into database.

    Args:
        json_path: Path to models JSON file (if None, uses default: data/config/llm_models.json)
        replace: If True, replace existing models configuration
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    production_db = settings.db_path

    # Use default path if not provided (from config)
    if json_path is None:
        json_path = str(settings.config_path / "llm_models.json")

    # Wrapper to call load_llm_models with connection
    def load_with_connection(conn: sqlite3.Connection) -> int:
        return load_llm_models(
            json_path,
            conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    if replace:
        success_message = "✅ LLM models configuration updated successfully ({result} models)"
    else:
        success_message = "✅ LLM models configuration loaded successfully ({result} models)"

    return run_loader_command(
        load_with_connection,
        db_paths=[production_db],
        db_schema_paths={production_db: None},
        success_message=success_message,
    )


def validation_types(
    json_path: str | None = None, replace: bool = False, force: bool = False
) -> int:
    """Load validation types configuration from JSON into database.

    Args:
        json_path: Path to validation types JSON file
                  (if None, uses default: data/evaluation/config/validation_types.json)
        replace: If True, replace existing validation types configuration
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    evaluation_db = settings.evaluation_db_path

    # Use default path if not provided (from config)
    if json_path is None:
        json_path = str(settings.evaluation_config_path / "validation_types.json")

    # Wrapper to call load_validation_types with connection
    def load_with_connection(conn: sqlite3.Connection) -> int:
        return load_validation_types(
            json_path,
            conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    if replace:
        success_message = "✅ Validation types configuration updated successfully ({result} types)"
    else:
        success_message = "✅ Validation types configuration loaded successfully ({result} types)"

    return run_loader_command(
        load_with_connection,
        db_paths=[evaluation_db],
        db_schema_paths={evaluation_db: None},
        success_message=success_message,
    )


def exam_config(
    board: str,
    level: str,
    subject: str,
    json_path: str | None = None,
    replace: bool = False,
    force: bool = False,
) -> int:
    """Load exam configuration (papers + mark types) from JSON into database.

    Args:
        board: Exam board name (e.g., 'Pearson Edexcel')
        level: Qualification level (e.g., 'GCSE')
        subject: Subject name (e.g., 'Mathematics')
        json_path: Path to config JSON file
                  (if None, constructs default: data/config/{board}/{level}/{subject}.json)
        replace: If True, replace existing configuration for this subject
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        exam_config('Pearson Edexcel', 'GCSE', 'Mathematics')
        → loads from data/config/pearson-edexcel/gcse/mathematics.json
    """
    production_db = settings.db_path

    # Use default path if not provided (construct from board/level/subject)
    if json_path is None:
        json_path = str(construct_config_path(board, level, subject, settings.config_path))

    # Wrapper to call load_exam_config with connection
    def load_with_connection(conn: sqlite3.Connection) -> None:
        return load_exam_config(
            json_path,
            conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    if replace:
        success_message = f"✅ Exam configuration updated successfully ({board} {level} {subject})"
    else:
        success_message = f"✅ Exam configuration loaded successfully ({board} {level} {subject})"

    return run_loader_command(
        load_with_connection,
        db_paths=[production_db],
        db_schema_paths={production_db: None},
        success_message=success_message,
    )
