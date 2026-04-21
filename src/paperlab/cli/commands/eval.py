"""Evaluation commands for test case and test suite management."""

import sqlite3
from pathlib import Path

from paperlab.cli.loading_utils import run_loader_command
from paperlab.config import settings
from paperlab.data.database import connection
from paperlab.data.repositories.evaluation import test_cases, test_suites
from paperlab.evaluation.execution.test_executor import (
    build_submissions_phase,
    cleanup_test_database,
    execute_marking_phase,
    extract_results_phase,
    get_test_student_id,
    load_test_data_phase,
    rebuild_correlation_data,
    setup_test_database,
    validate_test_suite_exists,
)
from paperlab.evaluation.loading.test_case_loader import load_test_case
from paperlab.evaluation.loading.test_suite_loader import load_test_suite
from paperlab.evaluation.messages import CLICommands, SuccessMessages
from paperlab.loaders.path_utils import to_logical_path
from paperlab.marking.exceptions import ExtractionError
from paperlab.utils.database import validate_databases_exist


def load_case(test_case_json_path: str, replace: bool = False, force: bool = False) -> int:
    """Load test case from JSON into evaluation_results.db.

    Args:
        test_case_json_path: Path to test case JSON file
        replace: If True, replace existing test case with same image path
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    project_root = settings.project_root
    production_db = settings.db_path
    evaluation_db = settings.evaluation_db_path

    # Wrapper to call load_test_case with connections
    def load_with_connections(prod_conn: sqlite3.Connection, eval_conn: sqlite3.Connection) -> int:
        return load_test_case(
            test_case_json_path,
            prod_conn,
            eval_conn,
            project_root,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    success_message = (
        SuccessMessages.TEST_CASE_UPDATED if replace else SuccessMessages.TEST_CASE_LOADED
    ).replace("{test_case_id}", "{result}")

    return run_loader_command(
        load_with_connections,
        db_paths=[production_db, evaluation_db],
        db_schema_paths={
            production_db: None,
            evaluation_db: settings.evaluation_schema_path,
        },
        success_message=success_message,
    )


def load_folder(folder_path: str) -> int:
    """Load all test case JSONs from a folder sequentially.

    Efficiently loads multiple test cases by checking which cases are already
    loaded with a single query, then only loading new cases.

    Args:
        folder_path: Path to folder containing test case JSON files

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval load-folder \\
            data/evaluation/test_cases/pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08
    """
    production_db = settings.db_path
    evaluation_db = settings.evaluation_db_path

    # Validate databases exist
    if not validate_databases_exist(
        [
            (production_db, CLICommands.DB_INIT),
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    try:
        folder = Path(folder_path)
        # Resolve to absolute path if relative
        if not folder.is_absolute():
            folder = settings.project_root / folder

        if not folder.exists():
            print(f"❌ Folder not found: {folder_path}")
            return 1

        if not folder.is_dir():
            print(f"❌ Path is not a directory: {folder_path}")
            return 1

        # 1. Find all JSON files in folder
        json_files = sorted(folder.glob("*.json"))
        if not json_files:
            print(f"⚠️  No JSON files found in: {folder_path}")
            return 0

        print(f"Found {len(json_files)} JSON files in folder")

        # 2. Query DB for already-loaded cases from this folder
        with connection(evaluation_db) as eval_conn:
            # Convert folder path to logical path and create LIKE pattern
            logical_folder = to_logical_path(folder)
            folder_pattern = f"{logical_folder}/%"

            loaded_paths = test_cases.get_json_paths_by_folder(folder_pattern, eval_conn)
            loaded_paths_set = set(loaded_paths)

        # 3. Calculate which files need loading
        files_to_load = []
        for json_file in json_files:
            logical_path = to_logical_path(json_file)
            if logical_path not in loaded_paths_set:
                files_to_load.append(json_file)

        skipped_count = len(json_files) - len(files_to_load)
        if skipped_count > 0:
            print(f"Skipping {skipped_count} already-loaded test cases")

        if not files_to_load:
            print("✓ All test cases already loaded")
            return 0

        print(f"Loading {len(files_to_load)} new test cases...")

        # 4. Load each new test case
        successful = 0
        failed = []

        for json_file in files_to_load:
            try:
                # Reuse existing load_case logic
                exit_code = load_case(str(json_file), replace=False, force=False)
                if exit_code == 0:
                    successful += 1
                    print(f"  ✓ {json_file.name}")
                else:
                    failed.append((json_file.name, "Load returned error code"))
            except Exception as e:
                failed.append((json_file.name, str(e)))
                print(f"  ❌ {json_file.name}: {e}")

        # 5. Print summary
        print(f"\n{'=' * 60}")
        print(f"Folder: {folder_path}")
        print(f"Total JSON files: {len(json_files)}")
        print(f"Already loaded: {skipped_count}")
        print(f"Newly loaded: {successful}")
        if failed:
            print(f"Failed: {len(failed)}")
            print("\nFailure details:")
            for filename, error in failed:
                print(f"  - {filename}: {error}")
        print(f"{'=' * 60}")

        return 0 if not failed else 1

    except Exception as e:
        print(f"❌ Folder loading failed: {e}")
        return 1


def load_suite(test_suite_json_path: str, replace: bool = False, force: bool = False) -> int:
    """Load test suite from JSON into evaluation_results.db.

    Args:
        test_suite_json_path: Path to test suite JSON file
        replace: If True, replace existing suite with same name
        force: If True, skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    evaluation_db = settings.evaluation_db_path

    # Wrapper to call load_test_suite with connection
    def load_with_connection(eval_conn: sqlite3.Connection) -> int:
        return load_test_suite(
            test_suite_json_path,
            eval_conn,
            replace=replace,
            force=force,
        )

    # Determine success message based on replace flag
    success_message = (
        SuccessMessages.TEST_SUITE_UPDATED if replace else SuccessMessages.TEST_SUITE_LOADED
    ).replace("{test_suite_id}", "{result}")

    return run_loader_command(
        load_with_connection,
        db_paths=[evaluation_db],
        db_schema_paths={evaluation_db: settings.evaluation_schema_path},
        success_message=success_message,
    )


def run_suite(
    suite_name: str,
    model_identifier: str | None = None,
    notes: str | None = None,
) -> int:
    """Run test suite with specified model.

    Executes marking for all test cases in suite using production code path.
    Results are extracted to evaluation_results.db for analysis.

    This function orchestrates all phases of test execution and manages
    database connections following Pattern A (CLI opens connections).

    Args:
        suite_name: Name of test suite to run
        model_identifier: LLM model identifier (e.g., "claude-sonnet-4-5-20250929").
                         If None, uses default from config.
        notes: Optional notes for this test run

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval run-suite "GCSE Baseline"
        uv run paperlab eval run-suite "GCSE Baseline" --model claude-sonnet-4-5-20250929
        uv run paperlab eval run-suite "GCSE Baseline" --model gpt-4o --notes "Testing GPT-4o"
    """
    # Use default model if not specified
    if model_identifier is None:
        model_identifier = settings.default_model

    # Check databases exist
    production_db = settings.db_path
    evaluation_db = settings.evaluation_db_path

    if not validate_databases_exist(
        [
            (production_db, CLICommands.DB_INIT),
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    test_db_path: Path | None = None  # Track for cleanup and error reporting

    try:
        # ====================================================================
        # Phase 1: Validate test suite exists and get metadata
        # ====================================================================
        with connection(evaluation_db) as eval_conn:
            suite = test_suites.get_by_name(suite_name, eval_conn)
            if suite is None:
                print(f"❌ Test suite not found: {suite_name}")
                print("\nAvailable suites:")
                all_suite_names = test_suites.list_all_names(eval_conn)
                for name in all_suite_names:
                    print(f"  - {name}")
                return 1

            # Type narrowing: suite["id"] is int (from get_by_name implementation)
            suite_id = suite["id"]
            if not isinstance(suite_id, int):
                raise ValueError(f"Invalid suite ID type: {type(suite_id)}")
            test_suite_id = suite_id
            test_suite_name = validate_test_suite_exists(test_suite_id, eval_conn)

        print(f"Running test suite: {test_suite_name}")
        print(f"Model: {model_identifier}")

        # ====================================================================
        # Phase 2: Create ephemeral test database
        # ====================================================================
        test_db_path = settings.db_path.parent / "test_execution.db"
        print(f"\nCreating test database: {test_db_path}")

        student_id = setup_test_database(test_db_path)
        print(f"✓ Test database created (student_id: {student_id})")

        # ====================================================================
        # Phase 3: Load test data (papers, marks, configs)
        # ====================================================================
        print("\nLoading test data...")
        with (
            connection(test_db_path) as test_conn,
            connection(evaluation_db) as eval_conn,
        ):
            load_test_data_phase(
                test_suite_id=test_suite_id,
                eval_conn=eval_conn,
                test_conn=test_conn,
            )
        print("✓ Test data loaded (papers, marks, configs)")

        # ====================================================================
        # Phase 4: Build submissions and correlation data (Phase A)
        # ====================================================================
        print("\nCreating submissions...")
        with (
            connection(test_db_path) as test_conn,
            connection(evaluation_db) as eval_conn,
        ):
            submission_ids, correlation_data, model_id, provider = build_submissions_phase(
                test_suite_id=test_suite_id,
                model_identifier=model_identifier,
                student_id=student_id,
                eval_conn=eval_conn,
                test_conn=test_conn,
            )

        print(f"✓ Created {len(submission_ids)} submissions")

        # ====================================================================
        # Phase 5: Execute marking (Phase B - $$$ EXPENSIVE - results written to test_execution.db)
        # ====================================================================
        print(f"\nMarking {len(submission_ids)} submissions...")
        print("(This may take several minutes depending on batch size and API tier)")

        # Progress callback for user feedback
        def progress_callback(completed: int, total: int) -> None:
            print(f"  Progress: {completed}/{total} submissions marked")

        # Execute marking (BatchMarker manages its own connections per worker thread)
        result = execute_marking_phase(
            submission_ids=submission_ids,
            model_id=model_id,
            model_identifier=model_identifier,
            provider=provider,
            test_db_path=test_db_path,
            progress_callback=progress_callback,
        )

        # Report marking results
        total = len(submission_ids)
        successful = len(result.successful)
        failed = len(result.failed)
        duration_sec = result.total_duration_ms / 1000

        print(f"\n✓ Marking completed in {duration_sec:.1f}s")
        print(f"  Successful: {successful}/{total}")

        if failed > 0:
            print(f"  Failed: {failed}/{total}")
            print("\nFailure details:")
            for idx, (submission_id, exc) in enumerate(result.failed, 1):
                print(f"  {idx}. Submission {submission_id}: {type(exc).__name__}: {exc}")
            print("\n  (Partial results will be extracted)")

        # ====================================================================
        # Validation: Ensure we have results to extract
        # ====================================================================
        if successful == 0:
            raise ValueError(
                f"Cannot extract results - all {total} markings failed.\n"
                "\n"
                "Test database preserved for debugging at: {test_db_path}\n"
                "\n"
                "Check the failure details above and:\n"
                "  - Verify API key is configured correctly\n"
                "  - Check network connectivity\n"
                "  - Review error messages for specific issues"
            )

        # ====================================================================
        # Phase 6: Extract artifacts to evaluation_results.db
        # CRITICAL: If this fails, test_execution.db is preserved for retry
        # ====================================================================
        print("\nExtracting results to evaluation database...")

        try:
            # Open only eval_conn (test_execution.db opened/closed internally by extractor)
            # CRITICAL: Cannot have test_execution.db connection open during ATTACH
            with connection(evaluation_db) as eval_conn:
                test_run_id = extract_results_phase(
                    test_suite_id=test_suite_id,
                    model_identifier=model_identifier,
                    correlation_data=correlation_data,
                    test_db_path=test_db_path,
                    eval_conn=eval_conn,
                    notes=notes,
                )

        except Exception as e:
            # Extraction failed - preserve test_execution.db for retry
            error_msg = (
                f"Extraction failed: {e}\n"
                f"\n"
                f"Test results preserved at: {test_db_path}\n"
                f"Marking results NOT lost - you can retry extraction without re-marking.\n"
                f"\n"
                f"Retry with:\n"
                f"  uv run paperlab eval retry-extraction {test_db_path} "
                f'"{test_suite_name}" {model_identifier}'
            )
            print(f"\n❌ {error_msg}")
            raise ExtractionError(error_msg) from e

        print(f"✓ Extraction completed (test_run_id: {test_run_id})")

        # ====================================================================
        # Phase 7: Delete test_execution.db ONLY after successful extraction
        # ====================================================================
        print("\nCleaning up...")
        cleanup_test_database(test_db_path)
        test_db_path = None  # Mark as deleted for exception handler
        print("✓ Test database deleted")

        # Success summary
        print(f"\n✅ Test run {test_run_id} completed successfully")
        print(f"   Suite: {test_suite_name}")
        print(f"   Model: {model_identifier}")
        print(f"   Questions: {successful}/{total} marked")
        if notes:
            print(f"   Notes: {notes}")

        return 0

    except ExtractionError:
        # Re-raise extraction errors (already formatted with retry instructions)
        return 1

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1

    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return 1

    except Exception as e:
        # Any other failure - preserve test_execution.db for debugging
        if test_db_path and test_db_path.exists():
            print(
                f"\n❌ Test execution failed: {e}\n"
                f"\n"
                f"Test database preserved at: {test_db_path}\n"
                f"Inspect with: sqlite3 {test_db_path}\n"
                f"\n"
                f"Common issues:\n"
                f"  - Missing test data files (papers/marks JSONs)\n"
                f"  - API key not configured\n"
                f"  - Network connectivity issues\n"
                f"  - Invalid test suite or model identifier"
            )
        return 1


def retry_extraction_cmd(
    test_db_path_str: str,
    suite_name: str,
    model_identifier: str,
    notes: str | None = None,
) -> int:
    """Retry extraction from preserved test_execution.db after failure.

    Use this when extraction failed but marking succeeded. Avoids expensive
    re-marking by reusing preserved LLM results.

    This function manages database connections following Pattern A (CLI opens connections).

    Args:
        test_db_path_str: Path to preserved test_execution.db
        suite_name: Original test suite name
        model_identifier: Original model identifier
        notes: Optional notes for retry attempt

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval retry-extraction \\
            data/db/test_execution.db "GCSE Baseline" claude-sonnet-4-5-20250929
    """
    from paperlab.utils.database import ensure_database_exists, validate_databases_exist

    test_db_path = Path(test_db_path_str)
    evaluation_db = settings.evaluation_db_path

    # Validate test database exists (with custom context for this workflow)
    test_db_context = (
        "Cannot retry extraction without preserved results.\n"
        "\n"
        "Possible causes:\n"
        "  - Database was already deleted (check path)\n"
        "  - Original test execution never ran\n"
        "  - Previous retry succeeded and cleaned up database"
    )
    if not ensure_database_exists(
        test_db_path,
        "uv run paperlab eval run --suite <suite_name> --llm <llm_name>",
        error_context=test_db_context,
    ):
        return 1

    # Check evaluation database exists
    if not validate_databases_exist(
        [
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    try:
        # Look up test suite by name and get ID
        with connection(evaluation_db) as eval_conn:
            suite = test_suites.get_by_name(suite_name, eval_conn)
            if suite is None:
                print(f"❌ Test suite not found: {suite_name}")
                return 1

            # Type narrowing: suite["id"] is int (from get_by_name implementation)
            suite_id = suite["id"]
            if not isinstance(suite_id, int):
                raise ValueError(f"Invalid suite ID type: {type(suite_id)}")
            test_suite_id = suite_id
            test_suite_name = str(suite["name"])

        print(f"Retrying extraction for test suite: {test_suite_name}")
        print(f"Test database: {test_db_path}")

        # ====================================================================
        # Phase 1: Rebuild correlation data from preserved test database
        # ====================================================================
        print("\nRebuilding correlation data...")
        with (
            connection(test_db_path) as test_conn,
            connection(evaluation_db) as eval_conn,
        ):
            # Get test student ID from preserved database
            student_id = get_test_student_id(test_conn)

            # Rebuild correlation (doesn't re-mark, just rebuilds mapping)
            correlation_data = rebuild_correlation_data(
                test_suite_id=test_suite_id,
                student_id=student_id,
                eval_conn=eval_conn,
                test_conn=test_conn,
            )

        print(f"✓ Correlation data rebuilt ({len(correlation_data)} mappings)")

        # ====================================================================
        # Phase 2: Retry extraction
        # ====================================================================
        print("\nExtracting results to evaluation database...")
        with connection(evaluation_db) as eval_conn:
            # Prepend "RETRY:" to notes
            retry_notes = f"RETRY: {notes}" if notes else "RETRY"

            test_run_id = extract_results_phase(
                test_suite_id=test_suite_id,
                model_identifier=model_identifier,
                correlation_data=correlation_data,
                test_db_path=test_db_path,
                eval_conn=eval_conn,
                notes=retry_notes,
            )

        print(f"✓ Extraction completed (test_run_id: {test_run_id})")

        # ====================================================================
        # Phase 3: Delete test_execution.db after successful retry
        # ====================================================================
        print("\nCleaning up...")
        cleanup_test_database(test_db_path)
        print("✓ Test database deleted")

        print(f"\n✅ Retry successful: test_run_id={test_run_id}")
        return 0

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1

    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return 1

    except Exception as e:
        # Extraction failed again - keep database for further debugging
        print(
            f"\n❌ Retry failed: {e}\n"
            f"\n"
            f"Test database still preserved at: {test_db_path}\n"
            f"\n"
            f"Actions:\n"
            f"  - Check disk space\n"
            f"  - Verify evaluation_results.db is writable\n"
            f"  - Inspect test_execution.db: sqlite3 {test_db_path}\n"
            f"  - Contact support if issue persists"
        )
        return 1


def audit_sanity_cases() -> int:
    """Audit questions for missing mark_scheme_sanity test cases.

    Reports which questions in the production database don't have
    corresponding sanity check test cases in the evaluation database.

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval audit-sanity-cases
    """
    from paperlab.cli.commands.eval_formatters import format_audit_report
    from paperlab.evaluation.services.sanity_case_auditor import audit_sanity_cases as run_audit
    from paperlab.utils.database import validate_databases_exist

    production_db = settings.db_path
    evaluation_db = settings.evaluation_db_path

    # Validate databases exist
    if not validate_databases_exist(
        [
            (production_db, CLICommands.DB_INIT),
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    try:
        # Run audit (business logic in service layer)
        with connection(production_db) as prod_conn, connection(evaluation_db) as eval_conn:
            report = run_audit(prod_conn, eval_conn)

        # Format and display results
        print(format_audit_report(report))

        return 0

    except ValueError as e:
        print(f"❌ {e}")
        print("Load validation types with:")
        print("  uv run paperlab load validation-types")
        return 1

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1

    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return 1


def generate_sanity_cases() -> int:
    """Generate sanity test case JSONs for all questions missing them.

    Creates JSON files (with relative paths) for each question in production
    that doesn't have a corresponding sanity test case in evaluation.

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval generate-sanity-cases
    """
    from paperlab.cli.commands.eval_formatters import format_generation_report
    from paperlab.evaluation.generation.sanity_case_generator import generate_sanity_test_cases
    from paperlab.utils.database import validate_databases_exist

    production_db = settings.db_path
    evaluation_db = settings.evaluation_db_path

    # Validate databases exist
    if not validate_databases_exist(
        [
            (production_db, CLICommands.DB_INIT),
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    try:
        # Generate test cases (uses repositories internally)
        with connection(production_db) as prod_conn, connection(evaluation_db) as eval_conn:
            result = generate_sanity_test_cases(prod_conn, eval_conn)

        # Format and print report
        report = format_generation_report(result)
        print(f"\n{report}")

        # Return error code if any errors occurred
        return 1 if result.errors else 0

    except ValueError as e:
        print(f"❌ Generation failed: {e}")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def list_suites() -> int:
    """List all available test suites.

    Returns:
        Exit code (0 for success, 1 for error)

    Example:
        uv run paperlab eval list-suites
    """
    evaluation_db = settings.evaluation_db_path

    # Check database exists
    if not validate_databases_exist(
        [
            (evaluation_db, f"sqlite3 {evaluation_db} < {settings.evaluation_schema_path}"),
        ]
    ):
        return 1

    try:
        with connection(evaluation_db) as eval_conn:
            suite_names = test_suites.list_all_names(eval_conn)

        if not suite_names:
            print("No test suites found.")
            print("\nLoad test suites with:")
            print("  uv run paperlab eval load-suite <path_to_suite.json>")
            return 0

        print(f"Available test suites ({len(suite_names)}):\n")
        for name in suite_names:
            print(f"  - {name}")

        return 0

    except Exception as e:
        print(f"❌ Error listing suites: {e}")
        return 1
