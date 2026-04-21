"""Data models package.

Contains dataclasses representing database records across different domains.
"""

from paperlab.data.models.marking import (
    GradeBoundary,
    PaperAttempt,
    PaperResult,
    QuestionAttempt,
)

__all__ = [
    "GradeBoundary",
    "PaperAttempt",
    "PaperResult",
    "QuestionAttempt",
]
