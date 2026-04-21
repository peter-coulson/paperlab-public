"""Formatter for mark type definitions for use in prompts."""

from typing import Any


def format_mark_types_for_prompt(mark_types: list[dict[str, Any]]) -> str:
    """Format mark types as natural language for LLM prompts.

    Args:
        mark_types: List of mark type dicts from mark_types.get_mark_types_for_exam_type()

    Returns:
        Formatted mark types as markdown string

    Example output:
        ## Mark Types

        - **M (Method)**: Awarded for correct mathematical method, even if numerical errors occur
        - **A (Accuracy)**: Awarded for correct answer, typically dependent on M mark
        - **B (Independent)**: Awarded independently, not dependent on other marks
    """
    lines = []
    lines.append("## Mark Types")
    lines.append("")

    for mark_type in mark_types:
        code = mark_type["code"]
        name = mark_type["display_name"]
        description = mark_type["description"]

        # Format: "- **CODE (Name)**: Description"
        if description:
            lines.append(f"- **{code} ({name})**: {description}")
        else:
            lines.append(f"- **{code} ({name})**")

    return "\n".join(lines)
