"""Paper structure diff calculator.

Calculates and formats differences between JSON paper definitions and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.marking import question_parts, questions
from paperlab.loaders.update_framework import EntityDiff
from paperlab.loading.models.papers import PaperStructureInput


@dataclass
class PaperDiff(EntityDiff[PaperStructureInput]):
    """Diff for paper structure changes.

    Attributes:
        exists: Whether paper exists in database
        has_changes: Whether any changes detected
        paper_identifier: Paper identifier (for display)
        question_changes: Summary of question-level changes
        total_marks_changed: Whether total marks changed
        old_total_marks: Current total marks in database
        new_total_marks: New total marks from JSON
    """

    paper_identifier: str
    question_changes: str
    total_marks_changed: bool
    old_total_marks: int | None
    new_total_marks: int

    @property
    def has_destructive_changes(self) -> bool:
        """Paper updates are always destructive (full replacement)."""
        return True

    def format_diff(self) -> str:
        """Format paper diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        lines = [f"\n⚠️  Replacing paper structure for '{self.paper_identifier}':\n"]

        if self.total_marks_changed and self.old_total_marks is not None:
            lines.append(f"  Total marks: {self.old_total_marks} → {self.new_total_marks}")
            lines.append("")

        lines.append(f"  {self.question_changes}")
        lines.append("")

        lines.append(
            "⚠️  WARNING: Replacing paper structure is destructive.\n"
            "This will delete and recreate all questions, parts, and content blocks.\n"
            "Any mark schemes for this paper will be preserved.\n"
        )

        return "\n".join(lines)


class PaperDiffCalculator:
    """Calculate diffs for paper structures."""

    def calculate_diff(
        self,
        json_paper: PaperStructureInput,
        db_paper: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> PaperDiff:
        """Calculate paper differences.

        Args:
            json_paper: Paper structure from JSON
            db_paper: Existing paper record from database (None if doesn't exist)
            conn: Database connection for additional queries

        Returns:
            PaperDiff with changes
        """
        paper_identifier = json_paper.paper_identifier

        # Check if paper exists
        if db_paper is None:
            return PaperDiff(
                exists=False,
                has_changes=False,
                paper_identifier=paper_identifier,
                question_changes="No existing paper",
                total_marks_changed=False,
                old_total_marks=None,
                new_total_marks=json_paper.paper_instance.total_marks,
            )

        # Get current paper data
        paper_id = db_paper["paper_id"]
        assert isinstance(paper_id, int), "Paper ID must be an integer"
        old_total_marks = int(db_paper["total_marks"])
        new_total_marks = json_paper.paper_instance.total_marks

        # Get current question structure
        current_questions = questions.get_all_with_marks(paper_id, conn)
        current_question_count = len(current_questions)
        new_question_count = len(json_paper.questions)

        # Get current parts count
        current_parts_count = question_parts.count_parts(paper_id, conn)
        new_parts_count = sum(len(q.parts) for q in json_paper.questions)

        # Build change summary
        changes = []
        if current_question_count != new_question_count:
            changes.append(f"Questions: {current_question_count} → {new_question_count}")
        if current_parts_count != new_parts_count:
            changes.append(f"Parts: {current_parts_count} → {new_parts_count}")

        if not changes:
            question_changes = "Structure will be recreated (questions/parts counts unchanged)"
        else:
            question_changes = ", ".join(changes)

        total_marks_changed = old_total_marks != new_total_marks

        return PaperDiff(
            exists=True,
            has_changes=True,  # Always has changes if we're replacing
            paper_identifier=paper_identifier,
            question_changes=question_changes,
            total_marks_changed=total_marks_changed,
            old_total_marks=old_total_marks,
            new_total_marks=new_total_marks,
        )
