"""Mark scheme diff calculator.

Calculates and formats differences between JSON mark scheme definitions and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.marking import mark_criteria
from paperlab.loaders.update_framework import EntityDiff
from paperlab.loading.models.marks import MarkSchemeInput


@dataclass
class MarksDiff(EntityDiff[MarkSchemeInput]):
    """Diff for mark scheme changes.

    Attributes:
        exists: Whether paper (and mark scheme) exists in database
        has_changes: Whether any changes detected
        paper_identifier: Paper identifier (for display)
        criteria_changes: Summary of criteria-level changes
        total_marks_changed: Whether total marks changed (indicates mismatch)
        old_criteria_count: Current criteria count in database
        new_criteria_count: New criteria count from JSON
    """

    paper_identifier: str
    criteria_changes: str
    total_marks_changed: bool
    old_criteria_count: int | None
    new_criteria_count: int

    @property
    def has_destructive_changes(self) -> bool:
        """Mark scheme updates are always destructive (full replacement)."""
        return True

    def format_diff(self) -> str:
        """Format mark scheme diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        lines = [f"\n⚠️  Replacing mark scheme for '{self.paper_identifier}':\n"]

        lines.append(f"  {self.criteria_changes}")
        lines.append("")

        lines.append(
            "⚠️  WARNING: Replacing mark schemes is destructive.\n"
            "This will delete and recreate all mark criteria and content.\n"
            "Any existing marking results using this scheme may be affected.\n"
        )

        return "\n".join(lines)


class MarksDiffCalculator:
    """Calculate diffs for mark schemes."""

    def calculate_diff(
        self,
        json_marks: MarkSchemeInput,
        db_paper: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> MarksDiff:
        """Calculate mark scheme differences.

        Args:
            json_marks: Mark scheme from JSON
            db_paper: Existing paper record from database (None if doesn't exist)
            conn: Database connection for additional queries

        Returns:
            MarksDiff with changes
        """
        paper_identifier = json_marks.paper_identifier

        # Calculate new criteria count (excluding structural NULL criteria)
        new_criteria_count = sum(
            sum(
                1 for p in q.question_parts for c in p.mark_criteria if c.mark_type_code is not None
            )
            for q in json_marks.questions
        )

        # Check if paper exists
        if db_paper is None:
            return MarksDiff(
                exists=False,
                has_changes=False,
                paper_identifier=paper_identifier,
                criteria_changes="No existing paper found",
                total_marks_changed=False,
                old_criteria_count=None,
                new_criteria_count=new_criteria_count,
            )

        # Get current criteria data
        paper_id = db_paper["paper_id"]
        assert isinstance(paper_id, int), "Paper ID must be an integer"

        old_criteria_count = mark_criteria.count_criteria(paper_id, conn)

        # Build change summary
        if old_criteria_count != new_criteria_count:
            criteria_changes = f"Mark criteria: {old_criteria_count} → {new_criteria_count}"
        else:
            criteria_changes = "Mark criteria will be recreated (count unchanged)"

        return MarksDiff(
            exists=True,
            has_changes=True,  # Always has changes if we're replacing
            paper_identifier=paper_identifier,
            criteria_changes=criteria_changes,
            total_marks_changed=False,
            old_criteria_count=old_criteria_count,
            new_criteria_count=new_criteria_count,
        )
