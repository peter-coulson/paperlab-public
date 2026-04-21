"""Database management commands."""

import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from paperlab.config import DatabaseSettings, DateTimeFormats, Tables, settings
from paperlab.data.database import connection
from paperlab.data.repositories.marking import metadata


def _check_environment() -> None:
    """Prevent running in production."""
    if settings.is_production:
        print("🔴 ERROR: Cannot initialize database in production environment")
        print("This script is for development/testing only.")
        sys.exit(1)


def _get_table_counts(db_path: Path) -> dict[str, int]:
    """Get record counts for all tables."""
    if not db_path.exists():
        return {}

    with connection(db_path) as conn:
        return metadata.get_table_counts_dict(conn)


def _show_database_status(db_path: Path) -> None:
    """Display current database contents."""
    counts = _get_table_counts(db_path)

    print(f"\n⚠️  Database already exists: {db_path}")
    print("\nCurrent database contents:")

    # Operational tables (data we care about)
    operational_data = False
    for table in Tables.OPERATIONAL_TABLES:
        count = counts.get(table, 0)
        if count > 0:
            print(f"  - {table}: {count} records")
            operational_data = True

    if not operational_data:
        print("  (only reference data - safe to reinitialize)")

    print("\n🔴 THIS WILL DELETE ALL DATA ABOVE")


def _create_backup(db_path: Path) -> Path:
    """Create timestamped backup of database."""
    timestamp = datetime.now().strftime(DateTimeFormats.BACKUP_TIMESTAMP)
    backup_path = db_path.parent / f"{DatabaseSettings.BACKUP_PREFIX}{timestamp}.db"
    shutil.copy(db_path, backup_path)
    return backup_path


def _confirm_deletion(db_path: Path, force: bool, backup: bool) -> bool:
    """Get user confirmation for database deletion."""
    if not db_path.exists():
        return True  # No database to delete

    if force:
        return True  # Force flag bypasses confirmation

    _show_database_status(db_path)

    # Offer backup
    if backup:
        backup_path = _create_backup(db_path)
        print(f"\n✓ Backup created: {backup_path}")
    else:
        backup_offer = input("\nCreate backup before deletion? (y/n): ")
        if backup_offer.lower() == "y":
            backup_path = _create_backup(db_path)
            print(f"✓ Backup created: {backup_path}")

    # Require explicit "yes"
    print("\nType 'yes' to confirm deletion: ", end="")
    response = input()

    return response == "yes"


def _execute_sql_file(conn: sqlite3.Connection, sql_file: Path) -> None:
    """Execute SQL file against database connection."""
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    sql = sql_file.read_text()

    # Execute with foreign keys enabled
    conn.execute(DatabaseSettings.FOREIGN_KEYS_PRAGMA)
    conn.executescript(sql)
    conn.commit()


def _verify_database(conn: sqlite3.Connection) -> None:
    """Verify database structure and config data."""
    # Check tables exist
    tables = metadata.get_all_table_names(conn)

    for table in Tables.all_tables():
        if table not in tables:
            raise ValueError(f"Missing table: {table}")

    # Check config data
    mark_types_count = metadata.get_table_row_count("mark_types", conn)
    if mark_types_count == 0:
        raise ValueError("Config data not loaded: mark_types is empty")

    models_count = metadata.get_table_row_count("llm_models", conn)
    if models_count == 0:
        raise ValueError("Config data not loaded: llm_models is empty")

    exam_types_count = metadata.get_table_row_count("exam_types", conn)
    if exam_types_count == 0:
        raise ValueError("Config data not loaded: exam_types is empty")

    print("\n✓ Database structure verified")
    print(f"  - {len(tables)} tables created")
    print(f"  - {exam_types_count} exam types loaded")
    print(f"  - {mark_types_count} mark types loaded")
    print(f"  - {models_count} LLM models loaded")


def _load_config_data(conn: sqlite3.Connection, project_root: Path) -> None:
    """Load configuration data from JSON files."""
    from paperlab.loading.exam_config_loader import load_exam_config
    from paperlab.loading.llm_models_loader import load_llm_models

    # Load sample data configuration
    config_path = settings.sample_config_path

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration: {e}") from e

    config_section = config.get("config")
    if not config_section:
        raise ValueError("No 'config' section found in sample_data.json")

    # Load LLM models
    llm_models_path = project_root / config_section["llm_models"]
    if not llm_models_path.exists():
        raise FileNotFoundError(f"LLM models config not found: {llm_models_path}")

    models_count = load_llm_models(str(llm_models_path), conn, replace=False, force=True)
    print(f"  ✓ Loaded {models_count} LLM models")

    # Load exam configs
    exam_configs = config_section.get("exam_configs", [])
    for exam_config in exam_configs:
        exam_path = project_root / exam_config["path"]
        if not exam_path.exists():
            print(f"⚠️  Exam config not found: {exam_path}")
            continue

        load_exam_config(str(exam_path), conn, replace=False, force=True)
        print(
            f"  ✓ Loaded exam config: {exam_config['board']} "
            f"{exam_config['level']} {exam_config['subject']}"
        )


def _load_sample_papers(conn: sqlite3.Connection, project_root: Path) -> None:
    """Load sample paper and mark scheme data from configuration."""
    from paperlab.loading.marks_loader import load_mark_scheme
    from paperlab.loading.paper_loader import load_paper

    # Check if sample data loading is enabled
    if not settings.sample_data_enabled:
        print("⚠️  Sample data loading disabled in configuration")
        return

    # Load sample data configuration
    config_path = settings.sample_config_path

    if not config_path.exists():
        print(f"⚠️  Sample data configuration not found: {config_path}")
        print("  Skipping sample data load.")
        return

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON in sample data config: {e}")
        return

    samples = config.get("default_samples", [])
    if not samples:
        print("⚠️  No samples defined in configuration")
        return

    # Load each sample
    for sample in samples:
        sample_name = sample.get("name", "Unknown")
        paper_path = project_root / sample["paper"]
        markscheme_path = project_root / sample["mark_scheme"]

        if not paper_path.exists():
            print(f"⚠️  Sample paper not found: {paper_path}")
            continue
        if not markscheme_path.exists():
            print(f"⚠️  Sample mark scheme not found: {markscheme_path}")
            continue

        # Load paper
        print(f"  ✓ Loading sample: {sample_name}")
        paper_id = load_paper(str(paper_path), conn)
        print(f"    - Paper loaded with ID: {paper_id}")

        # Load mark scheme
        load_mark_scheme(str(markscheme_path), conn)
        print("    - Mark scheme loaded")


def init(force: bool = False, backup: bool = False) -> int:
    """Initialize database from schema and load config + sample data from JSON.

    Args:
        force: Skip confirmation prompt (for CI/testing)
        backup: Create backup before deletion

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Paths
    project_root = settings.project_root
    db_path = settings.db_path
    schema_file = project_root / settings.db_dir / "schema.sql"

    # Safety checks
    _check_environment()

    # Confirm deletion if database exists
    if not _confirm_deletion(db_path, force, backup):
        print("Aborted.")
        return 1

    # Delete existing database
    if db_path.exists():
        db_path.unlink()
        print("\n✓ Deleted existing database")

    # Create new database
    print(f"✓ Creating new database: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        # Execute schema
        print(f"✓ Executing schema: {schema_file}")
        _execute_sql_file(conn, schema_file)

        # Load config data from JSON
        print("\n✓ Loading configuration from JSON")
        _load_config_data(conn, project_root)

        # Verify
        _verify_database(conn)

        # Load sample papers
        print("\n✓ Loading sample papers")
        _load_sample_papers(conn, project_root)

        # Commit all changes
        conn.commit()

        print(f"\n✅ Database initialized successfully: {db_path}")
        return 0

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        conn.close()
        # Clean up failed database
        if db_path.exists():
            db_path.unlink()
        return 1

    finally:
        conn.close()
