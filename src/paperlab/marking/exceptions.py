"""Exception classes for marking engine.

Design: Specific exception types for different failure modes.
Fail fast with clear error messages.
"""


class MarkingError(Exception):
    """Base exception for marking engine errors."""

    pass


class ValidationError(MarkingError):
    """Data validation failure (business rule violation)."""

    pass


class DataNotFoundError(MarkingError):
    """Required data not found in database."""

    pass


class ExtractionError(MarkingError):
    """Failed to extract test execution artifacts to evaluation database.

    This error is raised when the extraction phase fails after successful marking.
    The test_execution.db should be preserved for retry to avoid losing expensive
    LLM API call results.
    """

    pass
