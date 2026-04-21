"""LLM models configuration diff calculator.

Calculates and formats differences between JSON model configurations and database state.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

from paperlab.data.repositories.marking import llm_models
from paperlab.loaders.update_framework import EntityDiff
from paperlab.loading.models.config import LLMModelsInput


@dataclass
class LLMModelsDiff(EntityDiff[LLMModelsInput]):
    """Diff for LLM models configuration changes.

    Attributes:
        exists: Whether models exist in database
        has_changes: Whether any changes detected
        added_models: List of model identifiers being added
        removed_models: List of model identifiers being removed
        modified_models: List of (identifier, old_display_name, new_display_name) tuples
        old_count: Number of models currently in database
        new_count: Number of models in JSON
    """

    added_models: list[str]
    removed_models: list[str]
    modified_models: list[tuple[str, str, str]]  # (identifier, old_name, new_name)
    old_count: int
    new_count: int

    @property
    def has_destructive_changes(self) -> bool:
        """Models are destructive if any are removed."""
        return len(self.removed_models) > 0

    def format_diff(self) -> str:
        """Format models diff for display.

        Returns:
            Formatted diff string ready for display to user
        """
        lines = ["\n⚠️  Replacing LLM models configuration:\n"]

        # Summary
        lines.append(f"  Models: {self.old_count} → {self.new_count}")
        lines.append("")

        # Added models
        if self.added_models:
            lines.append(f"  ✅ Adding {len(self.added_models)} model(s):")
            for identifier in sorted(self.added_models):
                lines.append(f"     + {identifier}")
            lines.append("")

        # Removed models
        if self.removed_models:
            lines.append(f"  ❌ Removing {len(self.removed_models)} model(s):")
            for identifier in sorted(self.removed_models):
                lines.append(f"     - {identifier}")
            lines.append("")

        # Modified models
        if self.modified_models:
            lines.append(f"  🔄 Modifying {len(self.modified_models)} model(s):")
            for identifier, old_name, new_name in sorted(self.modified_models):
                lines.append(f"     ~ {identifier}:")
                lines.append(f"         '{old_name}' → '{new_name}'")
            lines.append("")

        # Warning if destructive
        if self.has_destructive_changes:
            lines.append(
                "⚠️  WARNING: This operation will remove models from the database.\n"
                "Make sure no existing papers or test suites depend on the removed models.\n"
            )

        return "\n".join(lines)


class LLMModelsDiffCalculator:
    """Calculate diffs for LLM models configuration."""

    def calculate_diff(
        self,
        json_models: LLMModelsInput,
        db_entity: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> LLMModelsDiff:
        """Calculate LLM models configuration differences.

        Args:
            json_models: Models configuration from JSON
            db_entity: Not used (file-level natural key, not row-level)
            conn: Database connection for queries

        Returns:
            LLMModelsDiff with changes
        """
        # Get all existing models from database
        existing_models = llm_models.get_all(conn)
        existing_by_identifier = {m["model_identifier"]: m for m in existing_models}

        # Get all models from JSON
        new_models_by_identifier = {m.model_identifier: m for m in json_models.models}

        # Calculate differences
        existing_ids = set(existing_by_identifier.keys())
        new_ids = set(new_models_by_identifier.keys())

        added_models = list(new_ids - existing_ids)
        removed_models = list(existing_ids - new_ids)
        common_ids = existing_ids & new_ids

        # Check for modifications (display_name or provider changes)
        modified_models = []
        for identifier in common_ids:
            db_model = existing_by_identifier[identifier]
            json_model = new_models_by_identifier[identifier]

            # Check if display_name changed (most common change)
            if db_model["display_name"] != json_model.display_name:
                modified_models.append(
                    (
                        identifier,
                        db_model["display_name"],
                        json_model.display_name,
                    )
                )
            # Note: provider changes are rare and could indicate a mistake
            # but we allow them (will be shown as modified)
            elif db_model["provider"] != json_model.provider:
                modified_models.append(
                    (
                        identifier,
                        f"{db_model['display_name']} ({db_model['provider']})",
                        f"{json_model.display_name} ({json_model.provider})",
                    )
                )

        # Determine if changes exist
        has_changes = bool(added_models or removed_models or modified_models)
        exists = len(existing_models) > 0

        return LLMModelsDiff(
            exists=exists,
            has_changes=has_changes,
            added_models=added_models,
            removed_models=removed_models,
            modified_models=modified_models,
            old_count=len(existing_models),
            new_count=len(json_models.models),
        )
