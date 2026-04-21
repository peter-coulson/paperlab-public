"""Central configuration package for paperlab application.

Single source of truth for all application configuration.
This package re-exports all configuration from internal modules.

Design principles:
- DRY: All configuration in one place
- Type-safe: Pydantic validation
- Environment-aware: .env file support
- Testable: Easy to override in tests

Usage:
    All imports should use `paperlab.config`, never the internal submodules:

    >>> from paperlab.config import settings
    >>> from paperlab.config import ErrorMessages, ValidationLimits
    >>> from paperlab.config import generate_paper_identifier

    Internal submodules (settings.py, constants.py, helpers.py) are
    implementation details and should not be imported directly.
"""

# Import from internal modules
from paperlab.config.constants import (
    IMAGE_DETAIL_LEVEL,
    IMAGE_MAX_DIMENSION,
    SUBJECT_ABBREVIATIONS,
    SUPPORTED_IMAGE_FORMATS,
    SYSTEM_PROMPT_BASE,
    BlockType,
    CLICommands,
    DatabaseSettings,
    DateTimeFormats,
    DisplayOrder,
    ErrorFormatting,
    ErrorMessages,
    FieldLengthLimits,
    ImageMediaType,
    ImageSequence,
    ImageValidationLimits,
    LLMProviders,
    LLMTestConfig,
    MarkingAttemptStatus,
    MarkType,
    ResponseValidationLimits,
    Tables,
    TokenEstimation,
    ValidationLimits,
    ValidationPatterns,
)
from paperlab.config.helpers import generate_paper_identifier
from paperlab.config.settings import Settings, settings

# Define public API - only these should be imported by external code
__all__ = [
    # Runtime settings
    "Settings",
    "settings",
    # Constant classes
    "BlockType",
    "CLICommands",
    "DatabaseSettings",
    "DateTimeFormats",
    "DisplayOrder",
    "ErrorFormatting",
    "ErrorMessages",
    "FieldLengthLimits",
    "ImageSequence",
    "ImageValidationLimits",
    "LLMProviders",
    "LLMTestConfig",
    "MarkingAttemptStatus",
    "MarkType",
    "ResponseValidationLimits",
    "Tables",
    "TokenEstimation",
    "ValidationLimits",
    "ValidationPatterns",
    # Module-level constants
    "IMAGE_DETAIL_LEVEL",
    "IMAGE_MAX_DIMENSION",
    "ImageMediaType",
    "SUBJECT_ABBREVIATIONS",
    "SUPPORTED_IMAGE_FORMATS",
    "SYSTEM_PROMPT_BASE",
    # Helper functions
    "generate_paper_identifier",
]
