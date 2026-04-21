"""Generic update/replace framework for all loaders.

Provides consistent diff calculation, confirmation prompts, and update handling
across all entity types (papers, marks, test suites, configs).
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")


@dataclass
class EntityDiff(Generic[T]):
    """Base class for entity diffs.

    Subclasses should implement format_diff() and has_destructive_changes.

    Attributes:
        exists: Whether entity exists in database
        has_changes: Whether any changes detected
    """

    exists: bool
    has_changes: bool

    @property
    def has_destructive_changes(self) -> bool:
        """Whether changes include removals/reductions.

        Subclasses should override if they have destructive changes.
        Default: False (safe changes only).
        """
        return False

    def format_diff(self) -> str:
        """Format diff for display (implemented by subclasses).

        Returns:
            Formatted diff string ready for display to user
        """
        raise NotImplementedError


class DiffCalculator(Protocol[T]):
    """Protocol for entity-specific diff calculation.

    Each entity type (suite, paper, marks, config) should implement this protocol
    to provide custom diff logic.
    """

    def calculate_diff(
        self,
        json_entity: T,
        db_entity: dict[str, Any] | None,
        conn: sqlite3.Connection,
    ) -> EntityDiff[T]:
        """Calculate difference between JSON and database state.

        Args:
            json_entity: Validated Pydantic model from JSON
            db_entity: Existing database record (None if doesn't exist)
            conn: Database connection for additional queries

        Returns:
            EntityDiff with changes and metadata
        """
        ...


def confirm_destructive_changes() -> bool:
    """Prompt user for confirmation of destructive changes.

    Returns:
        True if user confirms (types 'y' or 'yes'), False otherwise
    """
    response = input("Continue? [y/N] ").strip().lower()
    return response in ("y", "yes")


def ensure_entity_does_not_exist(
    natural_key_lookup: Callable[[T, sqlite3.Connection], dict[str, Any] | None],
    json_entity: T,
    conn: sqlite3.Connection,
    entity_type_name: str,
) -> None:
    """Check that entity doesn't exist (for create mode).

    Args:
        natural_key_lookup: Function to find existing record by natural key
        json_entity: Entity from JSON
        conn: Database connection
        entity_type_name: Human-readable entity type (e.g., "Paper", "Mark scheme")

    Raises:
        ValueError: If entity already exists (with helpful message about --replace flag)
    """
    existing = natural_key_lookup(json_entity, conn)
    if existing is not None:
        entity_id = existing.get("id") or existing.get("paper_id")  # Handle both patterns
        raise ValueError(
            f"{entity_type_name} already exists (ID: {entity_id}). Use --replace flag to update it."
        )


def handle_update_mode(
    json_entity: T,
    natural_key_lookup: Callable[[T, sqlite3.Connection], dict[str, Any] | None],
    diff_calculator: DiffCalculator[T],
    delete_func: Callable[[int, sqlite3.Connection], None],
    conn: sqlite3.Connection,
    force: bool = False,
) -> tuple[bool, EntityDiff[T]]:
    """Generic update handler for all loaders.

    Workflow:
        1. Look up existing entity by natural key
        2. Calculate diff (entity-specific)
        3. Early return if doesn't exist (error) or no changes
        4. Display diff
        5. Prompt for confirmation if destructive changes (unless force=True)
        6. Delete existing entity (CASCADE handles children)
        7. Return (should_proceed=True, diff)

    Args:
        json_entity: Validated Pydantic model from JSON
        natural_key_lookup: Function to find existing record by natural key
                           (e.g., lookup suite by name)
        diff_calculator: Calculator for entity-specific diffs
        delete_func: Function to delete existing record by ID
        conn: Database connection
        force: Skip confirmation prompts

    Returns:
        (should_proceed, diff)
        - should_proceed: True if should continue with insert, False if cancelled/no changes
        - diff: Calculated differences

    Raises:
        ValueError: If entity doesn't exist (must use --replace only for updates)
                   or if user cancels destructive operation
    """
    # Look up existing entity
    db_entity = natural_key_lookup(json_entity, conn)

    # Calculate diff
    diff = diff_calculator.calculate_diff(json_entity, db_entity, conn)

    # Error if entity doesn't exist
    if not diff.exists:
        raise ValueError(
            "Cannot update entity - it doesn't exist. Remove --replace flag to create a new entity."
        )

    # Early return if no changes
    if not diff.has_changes:
        print("✓ Entity is already up to date (no changes)")
        return False, diff

    # Display diff
    print(diff.format_diff())

    # Prompt for confirmation if destructive changes
    if diff.has_destructive_changes and not force and not confirm_destructive_changes():
        raise ValueError("Operation cancelled by user")

    # Extract entity ID and delete existing record
    # Handle both "id" and "paper_id" key patterns
    entity_id = db_entity.get("id") or db_entity.get("paper_id")  # type: ignore
    assert isinstance(entity_id, int), "Entity ID must be an integer"
    delete_func(entity_id, conn)

    return True, diff
