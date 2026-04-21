"""Exceptions for submission pipeline."""


class SubmissionError(Exception):
    """Base exception for submission operations."""

    pass


class InvalidImageError(SubmissionError):
    """Raised when image validation fails."""

    pass


class DuplicateSubmissionError(SubmissionError):
    """Raised when attempting to create duplicate submission."""

    pass
