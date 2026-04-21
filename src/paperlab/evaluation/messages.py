"""Error messages and user-facing strings for evaluation module.

Centralized location for all error messages, CLI instructions, and user-facing
strings to ensure consistency and easy maintenance.
"""


class ErrorMessages:
    """Error messages for evaluation operations."""

    # Database errors
    DB_NOT_FOUND = "❌ Database not found: {db_path}"
    DB_INIT_INSTRUCTION = "Create it with: uv run paperlab db init"

    # Paper loading errors
    LOAD_PAPER_FIRST = "Load the paper first using 'uv run paperlab load paper <json_path>'"
    LOAD_MARKSCHEME_FIRST = (
        "Load the mark scheme first using 'uv run paperlab load markscheme <json_path>'"
    )

    # Test case errors
    VALIDATION_TYPE_NOT_FOUND = "Validation type '{validation_type}' not found in database."
    QUESTION_NOT_FOUND = (
        "Question not found: {paper_identifier} Q{question_number}\n"
        "{load_paper_instruction}\n{load_markscheme_instruction}"
    )
    CRITERION_INDICES_MISMATCH = (
        "Criterion indices in test case don't match mark scheme.\n"
        "Expected (from mark scheme): {expected}\n"
        "Provided (in test case): {provided}\n"
        "Missing indices: {missing}\n"
        "Extra indices: {extra}"
    )
    MARKS_EXCEED_AVAILABLE = (
        "Test case criterion {criterion_index}: marks_awarded ({marks_awarded}) "
        "exceeds marks_available ({marks_available})"
    )
    TEST_CASE_EXISTS = (
        "Test case with image path '{image_path}' already exists (ID: {test_case_id}).\n"
        "Use --replace flag to update the existing test case."
    )

    # Test suite errors
    SUITE_NAME_EXISTS = (
        "Test suite with name '{suite_name}' already exists (ID: {suite_id}).\n"
        "Use --replace flag to update the existing suite."
    )
    DUPLICATE_PATHS_IN_SUITE = "Test suite contains duplicate image paths:\n{duplicate_paths}"
    TEST_CASE_NOT_FOUND = (
        "Referenced test case not found: {image_path}\n"
        "Load the test case first using 'uv run paperlab eval load-case <json_path>'"
    )
    SUITE_NOT_FOUND = "Test suite '{suite_name}' not found."
    SUITE_NOT_FOUND_WITH_SUGGESTIONS = (
        "Test suite '{suite_name}' not found.\n\nAvailable suites:\n{available_suites}"
    )
    TEST_SUITE_EMPTY = (
        "Test suite {test_suite_id} has no test cases. Cannot execute empty test suite."
    )

    # Test execution errors
    TEST_DB_NOT_FOUND = "Test execution database not found: {db_path}"
    EXTRACTION_FAILED = (
        "❌ Extraction failed: {error}\n\n"
        "The test execution database has been preserved at:\n"
        "  {db_path}\n\n"
        "You can retry extraction with:\n"
        '  uv run paperlab eval retry-extraction {db_path} "{suite_name}" {model_identifier}\n\n'
        "The database contains all marking results and can be safely retried without "
        "re-running expensive LLM calls."
    )
    MISSING_QUESTIONS = (
        "Cannot build marking requests: {count} question(s) not found in test database.\n"
        "Missing questions: {missing_questions}\n\n"
        "Ensure all required papers have been loaded into the test database."
    )
    MISSING_IMAGES = (
        "Cannot build marking requests: {count} student work image(s) not found.\n"
        "Missing images: {missing_images}"
    )


class CLICommands:
    """CLI command strings for instructions."""

    DB_INIT = "uv run paperlab db init"
    LOAD_PAPER = "uv run paperlab load paper <json_path>"
    LOAD_MARKSCHEME = "uv run paperlab load markscheme <json_path>"
    LOAD_TEST_CASE = "uv run paperlab eval load-case <json_path>"
    RETRY_EXTRACTION = "uv run paperlab eval retry-extraction <db_path> <suite_name> <model>"


class SuccessMessages:
    """Success messages for evaluation operations."""

    TEST_CASE_LOADED = "✅ Test case loaded successfully (ID: {test_case_id})"
    TEST_CASE_UPDATED = "✅ Test case updated successfully (ID: {test_case_id})"
    TEST_SUITE_LOADED = "✅ Test suite loaded successfully (ID: {test_suite_id})"
    TEST_SUITE_UPDATED = "✅ Test suite updated successfully (ID: {test_suite_id})"


class WarningMessages:
    """Warning messages for destructive operations."""

    DESTRUCTIVE_CHANGES_PREFIX = "⚠️  WARNING: Destructive changes detected!"
    CONFIRM_PROMPT = "Continue? (y/n): "
    OPERATION_CANCELLED = "Operation cancelled."
