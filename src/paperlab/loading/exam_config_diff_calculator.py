"""Exam configuration diff calculator.

Calculates and formats differences between JSON exam config and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.marking import exam_types, mark_types
from paperlab.loaders.update_framework import EntityDiff
from paperlab.loading.models.config import ExamConfigInput


@dataclass
class ExamConfigDiff(EntityDiff[ExamConfigInput]):
    """Diff for exam configuration changes.

    Attributes:
        exists: Whether config exists in database (any papers for this subject)
        has_changes: Whether any changes detected
        subject_key: (board, level, subject) tuple for display
        papers_added: List of paper codes being added
        papers_removed: List of paper codes being removed
        papers_unchanged: List of paper codes unchanged
        mark_types_changed: Summary of mark type changes
        mark_types_added_count: Count of new mark_type records
        mark_types_removed_count: Count of mark_type records being deleted
    """

    subject_key: tuple[str, str, str]  # (board, level, subject)
    papers_added: list[str]
    papers_removed: list[str]
    papers_unchanged: list[str]
    mark_types_changed: str
    mark_types_added_count: int
    mark_types_removed_count: int

    @property
    def has_destructive_changes(self) -> bool:
        """Exam config updates are destructive if removing papers or mark_types."""
        return len(self.papers_removed) > 0 or self.mark_types_removed_count > 0

    def format_diff(self) -> str:
        """Format exam config diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        board, level, subject = self.subject_key
        lines = [f"\n⚠️  Replacing exam configuration for '{board} {level} {subject}':\n"]

        # Papers changes
        if self.papers_added:
            lines.append(f"  📄 Papers added ({len(self.papers_added)}):")
            for paper_code in sorted(self.papers_added):
                lines.append(f"    + {paper_code}")
            lines.append("")

        if self.papers_removed:
            lines.append(f"  📄 Papers removed ({len(self.papers_removed)}):")
            for paper_code in sorted(self.papers_removed):
                lines.append(f"    - {paper_code}")
            lines.append("")

        if self.papers_unchanged:
            lines.append(f"  📄 Papers unchanged ({len(self.papers_unchanged)}):")
            for paper_code in sorted(self.papers_unchanged):
                lines.append(f"    = {paper_code}")
            lines.append("")

        # Mark types changes
        lines.append(f"  🏷️  Mark types: {self.mark_types_changed}")
        if self.mark_types_added_count > 0:
            lines.append(f"    + {self.mark_types_added_count} mark_type records added")
        if self.mark_types_removed_count > 0:
            lines.append(f"    - {self.mark_types_removed_count} mark_type records removed")
        lines.append("")

        # Warnings
        if self.has_destructive_changes:
            lines.append("⚠️  WARNING: This operation is destructive.\n")
            if self.papers_removed:
                lines.append(
                    "Removing papers will CASCADE delete all dependent data:\n"
                    "  - Papers (instances)\n"
                    "  - Questions and parts\n"
                    "  - Mark schemes\n"
                    "  - Student marks\n"
                )
            if self.mark_types_removed_count > 0:
                lines.append(
                    "Removing mark_types will CASCADE delete all dependent data:\n"
                    "  - Mark criteria in mark schemes\n"
                    "  - Student marks of those types\n"
                )
        else:
            lines.append("✓ No destructive changes (additions only)\n")

        return "\n".join(lines)


class ExamConfigDiffCalculator:
    """Calculate diffs for exam configurations."""

    def calculate_diff(
        self,
        json_config: ExamConfigInput,
        db_config: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> ExamConfigDiff:
        """Calculate exam configuration differences.

        Args:
            json_config: Exam configuration from JSON
            db_config: Not used for exam config (we query by natural key instead)
            conn: Database connection for additional queries

        Returns:
            ExamConfigDiff with changes
        """
        subject_key = (json_config.exam_board, json_config.exam_level, json_config.subject)

        # Get current papers from database
        current_papers = exam_types.get_all_for_subject(
            json_config.exam_board, json_config.exam_level, json_config.subject, conn
        )

        # Check if config exists
        if not current_papers:
            # New config - no existing data
            new_mark_types_count = sum(
                len(group.paper_codes) * len(group.mark_types)
                for group in json_config.mark_type_groups
            )

            return ExamConfigDiff(
                exists=False,
                has_changes=True,
                subject_key=subject_key,
                papers_added=[p.paper_code for p in json_config.papers],
                papers_removed=[],
                papers_unchanged=[],
                mark_types_changed=f"Creating {new_mark_types_count} mark_type records",
                mark_types_added_count=new_mark_types_count,
                mark_types_removed_count=0,
            )

        # Existing config - calculate diff
        current_paper_codes = {p["paper_code"] for p in current_papers}
        new_paper_codes = {p.paper_code for p in json_config.papers}

        papers_added = sorted(new_paper_codes - current_paper_codes)
        papers_removed = sorted(current_paper_codes - new_paper_codes)
        papers_unchanged = sorted(new_paper_codes & current_paper_codes)

        # Get current mark_types count
        current_mark_types_count = mark_types.count_mark_types_for_subject(
            json_config.exam_board, json_config.exam_level, json_config.subject, conn
        )

        # Calculate expected mark_types count from group structure
        # This is the cross product: sum of (papers × mark_types) per group
        # No DB lookup needed - just count from the JSON structure
        new_mark_types_count = sum(
            len(group.paper_codes) * len(group.mark_types) for group in json_config.mark_type_groups
        )

        # Mark type change summary
        if current_mark_types_count == new_mark_types_count:
            mark_types_changed = (
                f"{current_mark_types_count} → {new_mark_types_count} "
                "(unchanged count, may have different codes)"
            )
            mark_types_added_count = 0
            mark_types_removed_count = 0
        elif new_mark_types_count > current_mark_types_count:
            diff = new_mark_types_count - current_mark_types_count
            mark_types_changed = f"{current_mark_types_count} → {new_mark_types_count} (+{diff})"
            mark_types_added_count = diff
            mark_types_removed_count = 0
        else:
            diff = current_mark_types_count - new_mark_types_count
            mark_types_changed = f"{current_mark_types_count} → {new_mark_types_count} (-{diff})"
            mark_types_added_count = 0
            mark_types_removed_count = diff

        return ExamConfigDiff(
            exists=True,
            has_changes=True,  # Always has changes if we're replacing
            subject_key=subject_key,
            papers_added=papers_added,
            papers_removed=papers_removed,
            papers_unchanged=papers_unchanged,
            mark_types_changed=mark_types_changed,
            mark_types_added_count=mark_types_added_count,
            mark_types_removed_count=mark_types_removed_count,
        )
