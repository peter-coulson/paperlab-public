"""Test suite diff calculator.

Calculates and formats differences between JSON suite definitions and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.evaluation import test_suite_cases
from paperlab.evaluation.models import TestSuiteInput
from paperlab.loaders.update_framework import EntityDiff


@dataclass
class SuiteDiff(EntityDiff[TestSuiteInput]):
    """Diff for test suite changes.

    Attributes:
        exists: Whether suite exists in database
        has_changes: Whether any changes detected
        added_paths: Test case paths being added
        removed_paths: Test case paths being removed
        description_changed: Whether description changed
        old_description: Current description in database
        new_description: New description from JSON
        suite_name: Name of the suite (for display)
    """

    added_paths: list[str]
    removed_paths: list[str]
    description_changed: bool
    old_description: str | None
    new_description: str | None
    suite_name: str

    @property
    def has_destructive_changes(self) -> bool:
        """Check if diff includes removals (destructive)."""
        return len(self.removed_paths) > 0

    def format_diff(self) -> str:
        """Format suite diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        # If only additions (no removals), show simple info
        if not self.has_destructive_changes:
            lines = []
            if self.added_paths:
                lines.append(
                    f"✓ Adding {len(self.added_paths)} test case(s) to suite '{self.suite_name}':"
                )
                for path in self.added_paths:
                    lines.append(f"  + {path}")
            if self.description_changed:
                lines.append("\n✓ Description updated")
            lines.append("")
            return "\n".join(lines)

        # Removals detected - show full diff with warning
        lines = [f"\n⚠️  Changes to test suite '{self.suite_name}':\n"]

        if self.removed_paths:
            lines.append(f"  Removing {len(self.removed_paths)} test case(s):")
            for path in self.removed_paths:
                lines.append(f"    - {path}")
            lines.append("")

        if self.added_paths:
            lines.append(f"  Adding {len(self.added_paths)} test case(s):")
            for path in self.added_paths:
                lines.append(f"    + {path}")
            lines.append("")

        if self.description_changed:
            lines.append("  Description updated:")
            if self.old_description:
                lines.append(f'    - "{self.old_description}"')
            if self.new_description:
                lines.append(f'    + "{self.new_description}"')
            lines.append("")

        lines.append(
            "⚠️  WARNING: Removing test cases from suites affects historical test runs.\n"
            "Test run results reference test cases that may no longer be in this suite.\n"
        )

        return "\n".join(lines)


class SuiteDiffCalculator:
    """Calculate diffs for test suites."""

    def calculate_diff(
        self,
        json_suite: TestSuiteInput,
        db_suite: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> SuiteDiff:
        """Calculate suite differences.

        Args:
            json_suite: Test suite from JSON
            db_suite: Existing suite record from database (None if doesn't exist)
            conn: Database connection for additional queries

        Returns:
            SuiteDiff with changes
        """
        # Check if suite exists
        if db_suite is None:
            return SuiteDiff(
                exists=False,
                has_changes=False,
                added_paths=[],
                removed_paths=[],
                description_changed=False,
                old_description=None,
                new_description=json_suite.description,
                suite_name=json_suite.name,
            )

        # Get current test cases for this suite
        suite_id = db_suite["id"]
        if not isinstance(suite_id, int):
            raise TypeError(f"Suite ID must be an integer, got {type(suite_id)}")
        current_test_cases = test_suite_cases.get_test_cases_for_suite(suite_id, conn)
        current_paths = [str(tc["test_case_json_path"]) for tc in current_test_cases]
        current_description = (
            str(db_suite["description"]) if db_suite["description"] is not None else None
        )

        # Calculate path changes
        json_paths_set = set(json_suite.test_case_json_paths)
        current_paths_set = set(current_paths)

        added = sorted(json_paths_set - current_paths_set)
        removed = sorted(current_paths_set - json_paths_set)

        # Check description change
        description_changed = json_suite.description != current_description

        # Determine if there are changes
        has_changes = bool(added or removed or description_changed)

        return SuiteDiff(
            exists=True,
            has_changes=has_changes,
            added_paths=added,
            removed_paths=removed,
            description_changed=description_changed,
            old_description=current_description,
            new_description=json_suite.description,
            suite_name=json_suite.name,
        )
