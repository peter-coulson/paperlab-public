"""Marking database repositories.

All repositories in this module operate on marking.db (main marking database).

This module re-exports all repository modules to provide a clean import interface:

    >>> from paperlab.data.repositories.marking import questions, students
    >>> student = students.get_by_id(student_id, conn)
    >>> question = questions.get_by_id(question_id, conn)

The __all__ list ensures consistent exports and enables static analysis tools
to track repository usage across the codebase. When adding a new repository
module, add it to both the import statement and __all__ list.
"""

from paperlab.data.repositories.marking import (
    criteria_content,
    exam_types,
    grade_boundaries,
    llm_models,
    mark_criteria,
    mark_types,
    marking_attempts,
    paper_attempts,
    paper_results,
    papers,
    practice,
    question_attempts,
    question_content,
    question_marking_results,
    question_parts,
    question_submissions,
    questions,
    status,
    students,
    submission_contexts,
    submission_images,
)

__all__ = [
    "criteria_content",
    "exam_types",
    "grade_boundaries",
    "llm_models",
    "mark_criteria",
    "mark_types",
    "marking_attempts",
    "paper_attempts",
    "paper_results",
    "papers",
    "practice",
    "question_attempts",
    "question_content",
    "question_marking_results",
    "question_parts",
    "question_submissions",
    "questions",
    "status",
    "students",
    "submission_contexts",
    "submission_images",
]
