"""CLI utilities for loading commands.

Provides standard error handling, database checks, and connection management
for all loader commands.
"""

import argparse
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from typing import TypeVar

from paperlab.config.constants import CLIMessages
from paperlab.data.database import connection

T = TypeVar("T")


def add_pipeline_args(parser: argparse.ArgumentParser) -> None:
    """Add standard --replace and --force arguments to pipeline command parser.

    These arguments are required for all loading pipeline commands to ensure
    consistent behavior across paper, marks, test case, and test suite loading.

    Args:
        parser: ArgumentParser to add arguments to

    Arguments added:
        --replace: Replace existing entity with same identifier (updates structure)
        --force: Skip confirmation prompts (for CI/automation)
    """
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing entity with same identifier (updates structure)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts (for CI/automation)",
    )


def check_db_exists(db_path: Path, schema_path: Path | None = None) -> bool:
    """Check if database exists, print helpful error if not.

    Args:
        db_path: Path to database file
        schema_path: Optional path to schema (for error message)

    Returns:
        True if exists, False otherwise (and prints error)
    """
    if db_path.exists():
        return True

    print(f"❌ {CLIMessages.DB_NOT_FOUND.format(path=db_path)}")

    if schema_path:
        print(CLIMessages.DB_MANUAL_INIT_HINT.format(db_path=db_path, schema_path=schema_path))
    else:
        print(CLIMessages.DB_INIT_HINT)

    return False


def run_loader_command(
    loader_func: Callable[..., T],
    db_paths: list[Path],
    db_schema_paths: dict[Path, Path | None],
    success_message: str,
) -> int:
    """Execute loader function with standard CLI error handling.

    Handles:
    - Database existence checks
    - Connection management (opens connections for all db_paths dynamically)
    - Standard error handling (FileNotFoundError, ValueError, Exception)
    - Success/error message formatting

    The loader_func will be called with connection objects opened for each
    database in db_paths, in the same order. Supports any number of databases.

    Args:
        loader_func: Function to call to perform loading. Will receive
                    connection objects as arguments (one per db_path)
        db_paths: List of database paths to check and open connections for
        db_schema_paths: Dict mapping db_path -> schema_path for error messages
                        (schema_path can be None for production db)
        success_message: Message to print on success (can use {result} placeholder)

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        >>> def load_with_two_dbs(prod_conn, eval_conn):
        ...     return load_test_case("test.json", prod_conn, eval_conn)
        >>> run_loader_command(
        ...     load_with_two_dbs,
        ...     db_paths=[prod_db, eval_db],
        ...     db_schema_paths={prod_db: None, eval_db: eval_schema},
        ...     success_message="✅ Loaded (ID: {result})"
        ... )
    """
    # Check all databases exist
    for db_path in db_paths:
        schema_path = db_schema_paths.get(db_path)
        if not check_db_exists(db_path, schema_path):
            return 1

    try:
        # Open connections for all databases dynamically
        with ExitStack() as stack:
            # Open all connections and collect them
            connections = [stack.enter_context(connection(db)) for db in db_paths]

            try:
                # Unpack connections when calling loader function
                result = loader_func(*connections)

                # Commit all connections on success
                for conn in connections:
                    conn.commit()

            except Exception:
                # Rollback all connections on error
                for conn in connections:
                    conn.rollback()
                raise

        # Print success message (may contain result like ID)
        print(success_message.format(result=result))
        return 0

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
