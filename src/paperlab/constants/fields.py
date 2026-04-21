"""Database field name constants.

This module centralizes all database field names used throughout the application
to prevent typos and enable safe refactoring. All string literals for database
field names should be replaced with these constants.

Usage:
    from paperlab.constants.fields import CriterionFields, QuestionFields

    # Instead of: criterion["marks_available"]
    # Use: criterion[CriterionFields.MARKS_AVAILABLE]
"""

from typing import Final


class CriterionFields:
    """Database field names for mark_criteria and marking results tables."""

    CRITERION_ID: Final[str] = "criterion_id"
    MARKS_AVAILABLE: Final[str] = "marks_available"
    MARKS_AWARDED: Final[str] = "marks_awarded"
    OBSERVATION: Final[str] = "observation"
    FEEDBACK: Final[str] = "feedback"
    CONFIDENCE_SCORE: Final[str] = "confidence_score"
    ASSESSMENT_REASON: Final[str] = "assessment_reason"


class QuestionFields:
    """Database field names for questions table."""

    QUESTION_ID: Final[str] = "question_id"
    PAPER_ID: Final[str] = "paper_id"
    QUESTION_NUMBER: Final[str] = "question_number"


class PaperFields:
    """Database field names for papers table."""

    PAPER_ID: Final[str] = "paper_id"
    EXAM_BOARD: Final[str] = "exam_board"
    EXAM_LEVEL: Final[str] = "exam_level"
    SUBJECT: Final[str] = "subject"
    PAPER_CODE: Final[str] = "paper_code"


class StudentFields:
    """Database field names for students table."""

    STUDENT_ID: Final[str] = "student_id"
    STUDENT_NAME: Final[str] = "student_name"


class EntityFields:
    """Generic field names used across multiple tables."""

    ID: Final[str] = "id"
    NAME: Final[str] = "name"
    DESCRIPTION: Final[str] = "description"
