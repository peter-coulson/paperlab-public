"""Status derivation for attempts.

Thin logic layer - takes repository results, returns status strings.
All database queries in repository layer (status.py).
"""

from typing import Any

from paperlab.api.constants import (
    STATUS_COMPLETED,
    STATUS_DRAFT,
    STATUS_FAILED,
    STATUS_MARKING,
    STATUS_READY_FOR_GRADING,
    STATUS_SUBMITTED,
)
from paperlab.config.constants import MarkingAttemptStatus
from paperlab.data.models.marking import PaperAttempt
from paperlab.data.repositories.marking.status import MarkingStats


def derive_paper_status(attempt: PaperAttempt, stats: MarkingStats) -> str:
    """Derive paper attempt status from timestamps and marking stats.

    Status flow:
        draft -> submitted -> marking -> ready_for_grading -> completed
                              |
                              v
                           failed
    """
    if attempt.completed_at is not None:
        return STATUS_COMPLETED

    if attempt.submitted_at is None:
        return STATUS_DRAFT

    # All questions attempted with failures
    if stats.failed > 0 and stats.total_marked == stats.total_questions:
        return STATUS_FAILED

    # All questions successfully marked
    if stats.successful == stats.total_questions:
        return STATUS_READY_FOR_GRADING

    # Not yet started marking
    if stats.total_marked == 0:
        return STATUS_SUBMITTED

    return STATUS_MARKING


def derive_question_status(
    attempt: dict[str, Any],
    marking: dict[str, Any] | None,
) -> str:
    """Derive practice question status from marking attempt.

    Status flow: draft -> submitted -> completed/failed
    """
    if attempt["submission_id"] is None:
        return STATUS_DRAFT

    if marking is None:
        return STATUS_SUBMITTED

    if marking["status"] == MarkingAttemptStatus.SUCCESS:
        return STATUS_COMPLETED

    return STATUS_FAILED
