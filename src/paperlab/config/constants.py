"""Application constants (compile-time values).

This module contains all constant classes and module-level constants:

Constant Classes:
- BlockType: Content block type constants
- MarkType: Mark type constants
- DisplayOrder: Display order constants
- ValidationLimits: Maximum collection sizes
- Tables: Database table names
- DatabaseSettings: Database configuration constants
- SecurityRules: Security validation rules
- ValidationPatterns: Regex patterns for validation
- FieldLengthLimits: Maximum field lengths
- DateTimeFormats: Date/time format strings
- TimeConversions: Time unit conversion constants
- GitSettings: Git repository configuration constants
- TokenEstimation: LLM token estimation constants
- ErrorFormatting: Error message formatting constants
- ErrorMessages: Standard error message templates
- LLMProviders: LLM provider configuration
- ImageSequence: Image sequence constants for multi-image support
- MarkingAttemptStatus: Marking attempt status constants

Module-level Constants:
- SUBJECT_ABBREVIATIONS: Subject-specific abbreviations template paths
- SYSTEM_PROMPT_BASE: Base system prompt path
- SUPPORTED_IMAGE_FORMATS: Image format mappings
- IMAGE_DETAIL_LEVEL: LLM image detail setting
"""

from typing import Final, Literal

# Type alias for image media types (used by all LLM clients)
ImageMediaType = Literal["image/jpeg", "image/png", "image/webp"]


# ============================================================================
# Constants (not configurable via environment)
# ============================================================================

# Configuration Guidelines:
# ------------------------
# This file contains TWO types of configuration:
#
# 1. **Settings class** (environment-configurable):
#    - Database paths, API keys, feature flags
#    - Can be overridden via environment variables (PAPERLAB_*)
#    - Can be set in .env file
#    - Used for deployment-specific values
#
# 2. **Constant classes** (static configuration):
#    - Application constants (field limits, validation rules)
#    - Subject/provider mappings (SUBJECT_PROMPTS, PROVIDER_CLIENTS)
#    - Never change at runtime
#    - Require code update to modify
#
# When to use code vs database:
# -----------------------------
# - Static config (never changes at runtime) → Constants below
# - Dynamic reference data (exam boards, mark types) → Database tables
# - Subject mappings (expand per-subject) → SUBJECT_ABBREVIATIONS dict
# - Feature flags & environment settings → Settings class
# - Adding new subjects: Add to SUBJECT_ABBREVIATIONS + create abbreviations template
# - Adding new exam boards: INSERT into exam_types table (no code change)
# - Adding new mark types: INSERT into mark_types table (no code change)


# LLM Provider names (single source of truth)
class LLMProviders:
    """LLM provider name constants.

    Single source of truth for provider names across the application.
    Used in config (API keys), client_factory (provider mapping), and database.
    """

    ANTHROPIC: Final[str] = "anthropic"
    OPENAI: Final[str] = "openai"
    GOOGLE: Final[str] = "google"

    @classmethod
    def all(cls) -> list[str]:
        """Get list of all supported providers."""
        return [cls.ANTHROPIC, cls.OPENAI, cls.GOOGLE]


# Subject-to-abbreviations mapping
# Contains ONLY the abbreviations table - format instructions handled by LLM clients
SUBJECT_ABBREVIATIONS: Final[dict[str, str]] = {
    "Mathematics": "prompts/marking/maths_abbreviations.md",
}

# Base system prompt path (format-agnostic instructions)
SYSTEM_PROMPT_BASE: Final[str] = "prompts/marking/system_base.md"


class BlockType:
    """Content block type constants.

    Used in question_content_blocks and mark_criteria_content_blocks tables.
    """

    TEXT: Final[str] = "text"
    DIAGRAM: Final[str] = "diagram"


class MarkType:
    """Mark type constants."""

    GENERAL: Final[str] = "GENERAL"


class DisplayOrder:
    """Display order constants for clarity and consistency.

    These constants make code more readable and ensure consistency
    across validation logic and error messages.
    """

    NULL_PART: Final[int] = 0  # NULL part/criterion always at index 0
    FIRST_CONTENT_BLOCK: Final[int] = 1  # Content blocks start at 1
    FIRST_LETTERED_PART: Final[int] = 1  # Lettered parts start at 1 (after NULL part at 0)


class ValidationLimits:
    """Maximum collection sizes to prevent memory issues and ensure reasonable data.

    These limits protect against malformed or malicious JSON that could
    cause performance problems or resource exhaustion.
    """

    MAX_QUESTIONS_PER_PAPER: Final[int] = 100  # Reasonable maximum for any exam paper
    MAX_PARTS_PER_QUESTION: Final[int] = 50  # Should be enough for any question structure
    MAX_CONTENT_BLOCKS_PER_PART: Final[int] = 100  # Prevents excessive content blocks
    MAX_CRITERIA_PER_QUESTION: Final[int] = 200  # Mark criteria can be numerous


class Tables:
    """Database table name constants.

    Centralized table names for schema management and validation.
    Single source of truth for all table names - prevents magic strings.
    """

    # Reference tables (configuration data)
    EXAM_TYPES: Final[str] = "exam_types"
    MARK_TYPES: Final[str] = "mark_types"
    LLM_MODELS: Final[str] = "llm_models"

    REFERENCE_TABLES: Final[list[str]] = [EXAM_TYPES, MARK_TYPES, LLM_MODELS]

    # Operational tables (user/exam data)
    STUDENTS: Final[str] = "students"
    PAPERS: Final[str] = "papers"
    QUESTIONS: Final[str] = "questions"
    QUESTION_PARTS: Final[str] = "question_parts"
    QUESTION_CONTENT_BLOCKS: Final[str] = "question_content_blocks"
    MARK_CRITERIA: Final[str] = "mark_criteria"
    MARK_CRITERIA_CONTENT_BLOCKS: Final[str] = "mark_criteria_content_blocks"
    QUESTION_SUBMISSIONS: Final[str] = "question_submissions"
    SUBMISSION_IMAGES: Final[str] = "submission_images"
    MARKING_ATTEMPTS: Final[str] = "marking_attempts"
    QUESTION_MARKING_RESULTS: Final[str] = "question_marking_results"

    # M4 tables (paper marking and practice questions)
    PRACTICE_QUESTION_ATTEMPTS: Final[str] = "practice_question_attempts"
    PAPER_ATTEMPTS: Final[str] = "paper_attempts"
    QUESTION_ATTEMPTS: Final[str] = "question_attempts"
    PAPER_RESULTS: Final[str] = "paper_results"
    GRADE_BOUNDARIES: Final[str] = "grade_boundaries"

    OPERATIONAL_TABLES: Final[list[str]] = [
        STUDENTS,
        PAPERS,
        QUESTIONS,
        QUESTION_PARTS,
        QUESTION_CONTENT_BLOCKS,
        MARK_CRITERIA,
        MARK_CRITERIA_CONTENT_BLOCKS,
        QUESTION_SUBMISSIONS,
        SUBMISSION_IMAGES,
        MARKING_ATTEMPTS,
        QUESTION_MARKING_RESULTS,
        PRACTICE_QUESTION_ATTEMPTS,
        PAPER_ATTEMPTS,
        QUESTION_ATTEMPTS,
        PAPER_RESULTS,
        GRADE_BOUNDARIES,
    ]

    # Temporary tables (ephemeral - used during test execution)
    EXECUTION_CORRELATION: Final[str] = "execution_correlation"

    @classmethod
    def all_tables(cls) -> list[str]:
        """Get all table names in sorted order."""
        return sorted(cls.REFERENCE_TABLES + cls.OPERATIONAL_TABLES)


class DatabaseSettings:
    """Database configuration constants."""

    FOREIGN_KEYS_PRAGMA: Final[str] = "PRAGMA foreign_keys = ON"
    BACKUP_PREFIX: Final[str] = "marking_backup_"
    ATTACHED_TEST_DB_ALIAS: Final[str] = "test_exec"
    # Synthetic Supabase UID for test execution (not a real Supabase account)
    TEST_STUDENT_SUPABASE_UID: Final[str] = "00000000-0000-0000-0000-000000000001"


class ValidationPatterns:
    """Regex patterns for validation."""

    ISO_DATE_REGEX: Final[str] = r"^\d{4}-\d{2}-\d{2}$"
    ROMAN_NUMERAL_I_TO_X: Final[str] = r"^(i{1,3}|iv|v|vi{0,3}|ix|x)$"
    VALIDATION_TYPE_CODE_REGEX: Final[str] = r"^[a-z][a-z0-9_]*$"


class FieldLengthLimits:
    """Maximum field lengths for database columns and validation.

    These limits must match the database schema constraints.
    """

    EXAM_BOARD_MAX: Final[int] = 100
    EXAM_LEVEL_MAX: Final[int] = 50
    SUBJECT_MAX: Final[int] = 100
    PAPER_CODE_MAX: Final[int] = 50
    DISPLAY_NAME_MAX: Final[int] = 200
    EXAM_IDENTIFIER_MAX: Final[int] = 200
    CONTENT_TEXT_MAX: Final[int] = 10000
    DIAGRAM_DESCRIPTION_MAX: Final[int] = 5000
    DIAGRAM_IMAGE_PATH_MAX: Final[int] = 500
    MARK_TYPE_CODE_MAX: Final[int] = 20
    VALIDATION_TYPE_CODE_MAX: Final[int] = 50
    VALIDATION_TYPE_DESCRIPTION_MAX: Final[int] = 1000


class DateTimeFormats:
    """Date and time format strings."""

    BACKUP_TIMESTAMP: Final[str] = "%Y%m%d_%H%M%S"


class TimeConversions:
    """Time unit conversion constants."""

    MS_TO_SECONDS: Final[float] = 1000.0


class GitSettings:
    """Git repository configuration constants."""

    SHA1_HASH_LENGTH: Final[int] = 40
    HEX_DIGITS: Final[str] = "0123456789abcdef"


class TokenEstimation:
    """Constants for LLM token estimation.

    Used when calculating approximate token counts from text before sending to LLM.
    """

    CHARS_PER_TOKEN: Final[int] = 4
    # Rationale: Conservative estimate based on OpenAI/Anthropic tokenization
    # 1 token ≈ 4 characters for English text
    # Source: https://help.openai.com/en/articles/4936856


class ErrorFormatting:
    """Constants for error message formatting."""

    PREVIEW_LENGTH: Final[int] = 200
    # Rationale: Enough context for debugging without overwhelming logs
    # Fits in typical terminal width when formatted


class ErrorMessages:
    """Standard error message templates.

    Using templates ensures consistent error messaging across the application.
    """

    INSERT_FAILED: Final[str] = "Failed to get {entity}_id after INSERT"
    MIN_IMAGE_REQUIRED: Final[str] = (
        "At least one image is required for marking. "
        "The current system architecture requires image-based marking."
    )
    STUDENT_NOT_FOUND: Final[str] = "Student ID {student_id} not found"
    QUESTION_NOT_FOUND: Final[str] = "Question ID {question_id} not found"
    SUBMISSION_NOT_FOUND: Final[str] = "Submission ID {submission_id} not found"
    INVALID_PAPER_IDENTIFIER: Final[str] = (
        "Cannot parse paper identifier: {paper_identifier}\n"
        "Expected format: BOARD-LEVEL-SUBJECT-CODE-DATE\n"
        "Example: PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"
    )

    # LLM Response Validation Messages
    LLM_EMPTY_RESPONSE: Final[str] = (
        "Empty response from {provider} API. This may indicate an API error or timeout."
    )
    LLM_RESPONSE_TOO_SHORT: Final[str] = (
        "Response too short ({length} chars, minimum {min_len}) from {provider}. "
        "Expected JSON marking response. Got: {preview}"
    )
    LLM_RESPONSE_TOO_LONG: Final[str] = (
        "Response too long ({length} chars, maximum {max_len}) from {provider}. "
        "This may indicate an API error."
    )
    LLM_RESPONSE_NOT_JSON: Final[str] = (
        "Response from {provider} does not appear to contain JSON. " "First 200 chars: {preview}"
    )

    # Paper validation errors (M4)
    PAPER_INCOMPLETE: Final[str] = (
        "Cannot submit paper - not all questions submitted\n"
        "Expected: {expected} questions, found: {found} questions submitted"
    )
    PAPER_ALREADY_COMPLETE: Final[str] = (
        "Paper attempt {attempt_id} is already complete (immutable)\n"
        "Completed at: {completed_at}\n"
        "To retry, create new attempt: paperlab paper attempt create --inherit-from {attempt_id}"
    )
    NO_NEW_SUBMISSIONS: Final[str] = (
        "Cannot submit retry attempt with zero new submissions\n"
        "All {count} questions inherited from Attempt #{source_id}\n"
        "Please re-upload at least one question before submitting"
    )
    PAPER_ATTEMPT_NOT_FOUND: Final[str] = "Paper attempt {attempt_id} not found"
    CANNOT_MODIFY_SUBMITTED_ATTEMPT: Final[str] = (
        "Cannot modify submitted paper attempt {attempt_id}\n"
        "Paper was submitted at {submitted_at} and photos are now locked.\n"
        "Create a new retry attempt to change photos:\n"
        "  paperlab paper attempt create --student {student_id} "
        "--paper {paper_id} --inherit-from {attempt_id}"
    )
    PAPER_ATTEMPT_WRONG_STUDENT: Final[str] = (
        "Cannot submit to another student's paper attempt\n"
        "Paper attempt {attempt_id} belongs to student {owner_id}, not student {submitter_id}"
    )


# ============================================================================
# CLI Output Messages
# ============================================================================


class CLIMessages:
    """User-facing CLI output messages for paper marking workflow (M4)."""

    # Paper attempt creation
    PAPER_ATTEMPT_CREATED: Final[str] = "Paper attempt created:"
    ATTEMPT_UUID: Final[str] = "  Attempt UUID: {uuid}"
    ATTEMPT_ID: Final[str] = "  Attempt ID: {id}"
    STUDENT_ID: Final[str] = "  Student ID: {id}"
    PAPER_ID: Final[str] = "  Paper ID: {id}"
    INHERITED_FROM: Final[str] = "  Inherited from: Attempt #{id}"
    INHERITED_COUNT: Final[str] = "Inherited {count} questions from attempt {attempt_id}"

    # Question submission
    QUESTION_SUBMITTED: Final[str] = "Question submitted to paper attempt:"
    SUBMISSION_UUID: Final[str] = "  Submission UUID: {uuid}"
    SUBMISSION_ID: Final[str] = "  Submission ID: {id}"
    QUESTION_ATTEMPT_ID: Final[str] = "  Question Attempt ID: {id}"
    PAPER_ATTEMPT_ID: Final[str] = "  Paper Attempt ID: {id}"

    # Practice question submission
    PRACTICE_SUBMITTED: Final[str] = "Practice question submitted and marked!"
    MARKING_ATTEMPT_ID: Final[str] = "  Marking Attempt: {id}"

    # Paper submission
    PAPER_SUBMITTED: Final[str] = "Paper attempt {attempt_id} submitted for marking..."
    MARKING_COMPLETE: Final[str] = "\nMarking complete:"
    SUCCESSFUL_COUNT: Final[str] = "  Successful: {count}"
    FAILED_COUNT: Final[str] = "  Failed: {count}"
    TOTAL_DURATION: Final[str] = "  Total duration: {duration}ms"
    FAILED_SUBMISSIONS: Final[str] = "\nFailed submissions:"
    FAILED_SUBMISSION_DETAIL: Final[str] = "  Submission {id}: {error}"

    # Grading (Stage 6)
    CALCULATING_GRADE: Final[str] = "\nCalculating grade..."
    GRADING_SUCCESS: Final[str] = "\n✓ Paper graded successfully!"
    GRADE_TOTAL_MARKS: Final[str] = "   Total Marks: {awarded}/{available}"
    GRADE_PERCENTAGE: Final[str] = "   Percentage: {percentage}%"
    GRADE_INDICATIVE: Final[str] = "   Indicative Grade: {grade}"
    ATTEMPT_COMPLETE: Final[str] = "\nAttempt #{attempt_id} now complete (immutable)."

    # LLM test messages
    LLM_TEST_HEADER: Final[str] = "Testing LLM provider connections...\n"
    LLM_MUST_SPECIFY_PROVIDER: Final[str] = "Error: Must specify --provider or --all"
    LLM_NO_MODELS_CONFIGURED: Final[str] = "No models configured in database"
    LLM_TEST_SUCCESS: Final[str] = "Connection successful (tested with {display_name})"
    LLM_TEST_FAILED: Final[str] = "Connection failed - {error}"
    LLM_UNEXPECTED_ERROR: Final[str] = "Unexpected error - {error}"
    LLM_MODELS_HEADER: Final[str] = "Available LLM models:\n"
    LLM_NO_MODELS_FOUND: Final[str] = "No models found for provider: {provider}"
    LLM_NO_MODELS_IN_DB: Final[str] = "No models configured in database."
    LLM_RUN_DB_INIT: Final[str] = "Run 'paperlab db init' to load seed data."

    # Database messages
    DB_NOT_FOUND: Final[str] = "Database not found: {path}"
    DB_INIT_HINT: Final[str] = "Initialize it with: uv run paperlab db init"
    DB_MANUAL_INIT_HINT: Final[str] = (
        "Create it manually with:\n  sqlite3 {db_path} < {schema_path}"
    )


# ============================================================================
# LLM Image Processing Configuration
# ============================================================================

# Supported image formats and their MIME types for LLM APIs
# Formats optimized for document/photo capture (excludes GIF - not suitable for exam work)
SUPPORTED_IMAGE_FORMATS: Final[dict[str, ImageMediaType]] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# Image detail level for vision APIs
# "high" provides better OCR for handwriting recognition
# Currently used by OpenAI; Anthropic may add similar parameter in future
IMAGE_DETAIL_LEVEL: Final[Literal["low", "high", "auto"]] = "high"

# Maximum image dimension (longest edge) for LLM requests
# Images are resized to this dimension before encoding, maintaining aspect ratio.
# 512px validated to achieve 99.1% accuracy (vs 96.1% at ~1200px original).
# See analysis/sessions/2026-01-15-image-resolution-test.md
IMAGE_MAX_DIMENSION: Final[int] = 512


class ImageSequence:
    """Image sequence constants for multi-image support.

    Image sequences are 1-indexed per database constraint (CHECK image_sequence > 0).
    First image is used as correlation anchor for test case matching.
    """

    FIRST: Final[int] = 1  # First image in sequence (correlation anchor)
    START: Final[int] = 1  # Starting sequence number for iteration

    @classmethod
    def is_first(cls, sequence: int) -> bool:
        """Check if sequence number is the first image."""
        return sequence == cls.FIRST


class MarkingAttemptStatus:
    """Marking attempt status constants.

    Status values for marking_attempts table.
    Used to track success/failure of marking operations.
    """

    SUCCESS: Final[str] = "success"  # Marking completed successfully
    PARSE_ERROR: Final[str] = "parse_error"  # LLM response couldn't be parsed
    RATE_LIMIT: Final[str] = "rate_limit"  # API rate limit exceeded
    TIMEOUT: Final[str] = "timeout"  # API request timed out
    LLM_ERROR: Final[str] = "llm_error"  # LLM API returned error

    @classmethod
    def all(cls) -> list[str]:
        """Get list of all valid status values."""
        return [cls.SUCCESS, cls.PARSE_ERROR, cls.RATE_LIMIT, cls.TIMEOUT, cls.LLM_ERROR]


class CLICommands:
    """CLI command and subcommand name constants.

    Centralizes all CLI command strings to ensure consistency and prevent typos.
    Used by argparse setup and command detection logic.
    """

    # Top-level commands
    DB: Final[str] = "db"
    PAPER: Final[str] = "paper"
    LLM: Final[str] = "llm"
    EVAL: Final[str] = "eval"
    STORAGE: Final[str] = "storage"
    LOAD: Final[str] = "load"

    # Common subcommands (used by remaining CLI commands)
    CREATE: Final[str] = "create"
    INIT: Final[str] = "init"
    TEST: Final[str] = "test"
    MODELS: Final[str] = "models"

    # Storage subcommands
    PRESIGNED_URL: Final[str] = "presigned-url"
    DOWNLOAD: Final[str] = "download"

    # Load subcommands
    MARKS: Final[str] = "marks"
    LLM_MODELS: Final[str] = "llm-models"
    VALIDATION_TYPES: Final[str] = "validation-types"
    EXAM_CONFIG: Final[str] = "exam-config"

    # Eval subcommands
    LOAD_CASE: Final[str] = "load-case"
    LOAD_FOLDER: Final[str] = "load-folder"
    LOAD_SUITE: Final[str] = "load-suite"
    AUDIT_SANITY_CASES: Final[str] = "audit-sanity-cases"
    GENERATE_SANITY_CASES: Final[str] = "generate-sanity-cases"
    RUN_SUITE: Final[str] = "run-suite"
    LIST_SUITES: Final[str] = "list-suites"


class LLMTestConfig:
    """Configuration constants for LLM API testing.

    Used by CLI 'llm test' command to validate API connectivity.
    """

    TEST_MESSAGE: Final[str] = "Reply with OK"
    TEST_MAX_TOKENS: Final[int] = 10


class ImageValidationLimits:
    """Image validation size limits for LLM client.

    Used to validate images before sending to LLM APIs.
    """

    MIN_SIZE_BYTES: Final[int] = 10_000  # 10KB - Minimum reasonable image size
    MAX_SIZE_BYTES: Final[int] = 20_000_000  # 20MB - Maximum for most LLM APIs


class ResponseValidationLimits:
    """Response validation limits for LLM client.

    Used to validate LLM API responses for sanity checks.
    """

    MIN_LENGTH: Final[int] = 10  # Minimum characters for valid JSON response
    MAX_LENGTH: Final[int] = 1_000_000  # 1MB - Maximum reasonable response size
