"""Test case diff calculator.

Calculates and formats differences between JSON test case definitions and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.evaluation import test_case_marks
from paperlab.evaluation.models import TestCaseInput
from paperlab.loaders.update_framework import EntityDiff


@dataclass
class TestCaseDiff(EntityDiff[TestCaseInput]):
    """Diff for test case changes.

    Attributes:
        exists: Whether test case exists in database
        has_changes: Whether any changes detected
        image_paths: Student work image paths (for display)
        paper_identifier: Paper identifier
        question_number: Question number
        marks_changed: Whether expected marks changed
        notes_changed: Whether notes changed
        old_notes: Current notes in database
        new_notes: New notes from JSON
    """

    image_paths: list[str]
    paper_identifier: str
    question_number: int
    marks_changed: bool
    notes_changed: bool
    old_notes: str | None
    new_notes: str | None

    @property
    def has_destructive_changes(self) -> bool:
        """Test case updates are always destructive (full replacement)."""
        return True

    def format_diff(self) -> str:
        """Format test case diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        lines = [
            f"\n⚠️  Replacing test case for '{self.paper_identifier}' Q{self.question_number}:\n"
        ]

        if len(self.image_paths) == 1:
            lines.append(f"  Image: {self.image_paths[0]}")
        else:
            lines.append(f"  Images: {len(self.image_paths)} files")
            for idx, img in enumerate(self.image_paths, start=1):
                lines.append(f"    {idx}. {img}")

        if self.marks_changed:
            lines.append("  Expected marks will be updated")

        if self.notes_changed:
            lines.append("  Notes changed:")
            if self.old_notes:
                lines.append(f'    - "{self.old_notes}"')
            else:
                lines.append("    - (no notes)")
            if self.new_notes:
                lines.append(f'    + "{self.new_notes}"')
            else:
                lines.append("    + (no notes)")

        lines.append("")
        lines.append(
            "⚠️  WARNING: Replacing test cases is destructive.\n"
            "This will delete and recreate the test case and all expected marks.\n"
            "Any test run results using this test case will still reference it.\n"
        )

        return "\n".join(lines)


class TestCaseDiffCalculator:
    """Calculate diffs for test cases."""

    def calculate_diff(
        self,
        json_test_case: TestCaseInput,
        db_test_case: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> TestCaseDiff:
        """Calculate test case differences.

        Args:
            json_test_case: Test case from JSON
            db_test_case: Existing test case record from database (None if doesn't exist)
            conn: Database connection for additional queries

        Returns:
            TestCaseDiff with changes
        """
        image_paths = json_test_case.student_work_image_paths
        paper_identifier = json_test_case.paper_identifier
        question_number = json_test_case.question_number
        new_notes = json_test_case.notes

        # Check if test case exists
        if db_test_case is None:
            return TestCaseDiff(
                exists=False,
                has_changes=False,
                image_paths=image_paths,
                paper_identifier=paper_identifier,
                question_number=question_number,
                marks_changed=False,
                notes_changed=False,
                old_notes=None,
                new_notes=new_notes,
            )

        # Get existing data
        test_case_id = db_test_case["id"]
        if not isinstance(test_case_id, int):
            raise TypeError(f"Test case ID must be an integer, got {type(test_case_id)}")
        old_notes = db_test_case["notes"]

        # Check if notes changed
        notes_changed = old_notes != new_notes

        # Get current marks and compare with new marks
        current_marks = test_case_marks.get_marks(test_case_id, conn)
        # Convert JSON string keys to int for comparison
        new_marks = {int(k): v for k, v in json_test_case.expected_marks.items()}

        # Compare marks (both count and values)
        marks_changed = current_marks != new_marks

        has_changes = marks_changed or notes_changed

        return TestCaseDiff(
            exists=True,
            has_changes=has_changes,
            image_paths=image_paths,
            paper_identifier=paper_identifier,
            question_number=question_number,
            marks_changed=marks_changed,
            notes_changed=notes_changed,
            old_notes=str(old_notes) if old_notes else None,
            new_notes=new_notes,
        )
