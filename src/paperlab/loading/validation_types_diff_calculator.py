"""Validation types configuration diff calculator.

Calculates and formats differences between JSON validation type configurations and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.evaluation import validation_types
from paperlab.loaders.update_framework import EntityDiff
from paperlab.loading.models.config import ValidationTypesInput


@dataclass
class ValidationTypesDiff(EntityDiff[ValidationTypesInput]):
    """Diff for validation types configuration changes.

    Attributes:
        exists: Whether validation types exist in database
        has_changes: Whether any changes detected
        added_types: List of validation type codes being added
        removed_types: List of validation type codes being removed
        modified_types: List of (code, old_display_name, new_display_name) tuples
        old_count: Number of types currently in database
        new_count: Number of types in JSON
    """

    added_types: list[str]
    removed_types: list[str]
    modified_types: list[tuple[str, str, str]]  # (code, old_display_name, new_display_name)
    old_count: int
    new_count: int

    @property
    def has_destructive_changes(self) -> bool:
        """Types are destructive if any are removed."""
        return len(self.removed_types) > 0

    def format_diff(self) -> str:
        """Format validation types diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        lines = ["\n⚠️  Replacing validation types configuration:\n"]

        # Summary
        lines.append(f"  Types: {self.old_count} → {self.new_count}")
        lines.append("")

        # Added types
        if self.added_types:
            lines.append(f"  ✅ Adding {len(self.added_types)} type(s):")
            for code in sorted(self.added_types):
                lines.append(f"     + {code}")
            lines.append("")

        # Removed types
        if self.removed_types:
            lines.append(f"  ❌ Removing {len(self.removed_types)} type(s):")
            for code in sorted(self.removed_types):
                lines.append(f"     - {code}")
            lines.append("")

        # Modified types
        if self.modified_types:
            lines.append(f"  🔄 Modifying {len(self.modified_types)} type(s):")
            for code, old_name, new_name in sorted(self.modified_types):
                lines.append(f"     ~ {code}:")
                lines.append(f"         '{old_name}' → '{new_name}'")
            lines.append("")

        # Warning if destructive
        if self.has_destructive_changes:
            lines.append(
                "⚠️  WARNING: This operation will remove validation types from the database.\n"
                "Make sure no existing test cases depend on the removed types.\n"
            )

        return "\n".join(lines)


class ValidationTypesDiffCalculator:
    """Calculate diffs for validation types configuration."""

    def calculate_diff(
        self,
        json_types: ValidationTypesInput,
        db_entity: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> ValidationTypesDiff:
        """Calculate validation types configuration differences.

        Args:
            json_types: Validation types configuration from JSON
            db_entity: Not used (file-level natural key, not row-level)
            conn: Database connection for queries

        Returns:
            ValidationTypesDiff with changes
        """
        # Get all existing validation types from database
        existing_types = validation_types.get_all(conn)
        existing_by_code = {t.code: t for t in existing_types}

        # Get all types from JSON
        new_types_by_code = {t.code: t for t in json_types.validation_types}

        # Calculate differences
        existing_codes = set(existing_by_code.keys())
        new_codes = set(new_types_by_code.keys())

        added_types = list(new_codes - existing_codes)
        removed_types = list(existing_codes - new_codes)
        common_codes = existing_codes & new_codes

        # Check for modifications (display_name or description changes)
        modified_types = []
        for code in common_codes:
            db_type = existing_by_code[code]
            json_type = new_types_by_code[code]

            # Check if display_name or description changed
            if (
                db_type.display_name != json_type.display_name
                or db_type.description != json_type.description
            ):
                modified_types.append(
                    (
                        code,
                        db_type.display_name,
                        json_type.display_name,
                    )
                )

        # Determine if changes exist
        has_changes = bool(added_types or removed_types or modified_types)
        exists = len(existing_types) > 0

        return ValidationTypesDiff(
            exists=exists,
            has_changes=has_changes,
            added_types=added_types,
            removed_types=removed_types,
            modified_types=modified_types,
            old_count=len(existing_types),
            new_count=len(json_types.validation_types),
        )
