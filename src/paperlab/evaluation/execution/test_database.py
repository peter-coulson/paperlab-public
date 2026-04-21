"""Test database lifecycle management.

This module manages the creation and deletion of ephemeral test_execution.db:
- Creates fresh database from production schema
- Creates synthetic test student
- Validates schema was applied correctly
- Provides safe deletion with existence checks

Design principles:
- Simple and focused: DB lifecycle only
- Fail fast: Validates schema application
- Safe: Checks before delete, clear error messages
- No hardcoded SQL or table names (uses config constants)
"""

import sqlite3
from pathlib import Path

from paperlab.config import settings
from paperlab.config.constants import DatabaseSettings, Tables
from paperlab.data.repositories.marking import metadata, students


def create_test_execution_db(db_path: Path) -> int:
    """Create ephemeral test_execution.db from production schema.

    Creates a fresh SQLite database with identical schema to production marking.db,
    then creates a synthetic test student for test execution.

    This database is used for isolated test execution and will be deleted after
    results are extracted.

    Args:
        db_path: Path where test_execution.db should be created

    Returns:
        student_id of the synthetic test student

    Raises:
        FileExistsError: If database already exists at db_path
        FileNotFoundError: If production schema file doesn't exist
        sqlite3.Error: If database creation or schema execution fails

    Example:
        >>> test_db = Path("data/db/test_execution.db")
        >>> student_id = create_test_execution_db(test_db)
        # Database created with production schema and test student
    """
    # Fail fast if database already exists
    if db_path.exists():
        raise FileExistsError(
            f"Test database already exists: {db_path}\n"
            "This should not happen - test database should be deleted after each run.\n"
            "If this is from a previous failed run, delete it manually: "
            f"rm {db_path}"
        )

    # Validate production schema exists
    schema_path = settings.schema_path
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Production schema not found: {schema_path}\n"
            "Cannot create test database without schema."
        )

    # Create database and apply schema
    try:
        # Create parent directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create database connection (creates file)
        conn = sqlite3.connect(db_path)

        try:
            # Read and execute schema SQL
            schema_sql = schema_path.read_text()
            conn.executescript(schema_sql)
            conn.commit()

            # Verify schema was applied by checking for key tables
            _verify_schema_applied(conn)

            # Create synthetic test student
            student_id = _create_test_student(conn)
            conn.commit()

            return student_id

        finally:
            conn.close()

    except Exception:
        # Clean up partially created database on error
        if db_path.exists():
            db_path.unlink()
        raise


def delete_test_execution_db(db_path: Path) -> None:
    """Delete test_execution.db after results have been extracted.

    Safely removes ephemeral test database. Should only be called after
    verifying results were successfully extracted to evaluation_results.db.

    Args:
        db_path: Path to test_execution.db

    Raises:
        FileNotFoundError: If database doesn't exist (already deleted or never created)

    Example:
        >>> test_db = Path("data/db/test_execution.db")
        >>> # ... run tests, extract results ...
        >>> delete_test_execution_db(test_db)
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Test database not found: {db_path}\n"
            "Cannot delete - database doesn't exist.\n"
            "This may indicate a logic error in test execution flow."
        )

    # Delete database file
    db_path.unlink()


def _verify_schema_applied(conn: sqlite3.Connection) -> None:
    """Verify production schema was applied correctly.

    Checks for existence of all expected tables to ensure schema execution succeeded.

    Args:
        conn: Database connection

    Raises:
        ValueError: If expected tables are missing
    """
    actual_tables = set(metadata.get_all_table_names(conn))
    expected_tables = set(Tables.all_tables())
    missing_tables = expected_tables - actual_tables

    if missing_tables:
        raise ValueError(
            f"Schema verification failed - missing tables: {sorted(missing_tables)}\n"
            "Production schema may not have been applied correctly."
        )


def _create_test_student(conn: sqlite3.Connection) -> int:
    """Create synthetic test student for test execution.

    Uses a fixed email/name to identify this as a test execution student.

    Args:
        conn: Database connection (to test_execution.db)

    Returns:
        student_id of created student

    Raises:
        ValueError: If failed to get student_id after INSERT
    """
    return students.get_or_create_by_supabase_uid(
        DatabaseSettings.TEST_STUDENT_SUPABASE_UID,
        conn,
    )
