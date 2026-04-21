"""Internal helper functions for formatting.

These functions are shared across formatters and not part of the public API.
"""

from typing import Any

from paperlab.config import BlockType
from paperlab.constants.fields import CriterionFields


def format_part_label(
    part_letter: str | None,
    sub_part_letter: str | None,
) -> str:
    """Format part identifier as human-readable label.

    Args:
        part_letter: Part letter (e.g., 'a', 'b') or None for NULL part
        sub_part_letter: Sub-part letter (e.g., 'i', 'ii') or None

    Returns:
        Formatted label string

    Examples:
        >>> format_part_label(None, None)
        ''
        >>> format_part_label('a', None)
        '(a)'
        >>> format_part_label('a', 'i')
        '(a)(i)'
    """
    if part_letter is None:
        return ""

    label = f"({part_letter})"
    if sub_part_letter:
        label += f"({sub_part_letter})"

    return label


def format_content_blocks(content_blocks: list[dict[str, Any]]) -> str:
    """Format content blocks as markdown.

    Args:
        content_blocks: List of content block dicts with keys:
            - block_type: 'text' or 'diagram'
            - content_text: str (for text blocks)
            - diagram_description: str (for diagram blocks)

    Returns:
        Formatted content as markdown string

    Examples:
        Text block: "Calculate the derivative of $x^2$"
        Diagram block: "> **Diagram:** Graph showing parabola"
    """
    lines = []

    for block in content_blocks:
        if block["block_type"] == BlockType.TEXT:
            lines.append(block["content_text"])
        else:  # diagram
            lines.append(f"> **Diagram:** {block['diagram_description']}")

    return "\n\n".join(lines)


def format_criterion_identifier(
    mark_type_code: str,
    marks_available: int,
    criterion_index: int,
) -> str:
    """Format criterion identifier.

    Args:
        mark_type_code: Mark type code (e.g., 'M', 'A')
        marks_available: Marks available for this criterion
        criterion_index: Index of criterion within question

    Returns:
        Formatted identifier string

    Examples:
        >>> format_criterion_identifier('M', 1, 0)
        'M1 (1 mark)'
        >>> format_criterion_identifier('A', 2, 5)
        'A2 (2 marks)'
        >>> format_criterion_identifier('GENERAL', 0, 3)
        'GENERAL (0 marks)'
    """
    # Build mark type + count (e.g., "M1", "A2")
    identifier = f"{mark_type_code}{marks_available}"

    # Add marks available
    mark_word = "mark" if marks_available == 1 else "marks"
    identifier += f" ({marks_available} {mark_word})"

    return identifier


def calculate_part_totals(mark_scheme_data: list[dict[str, Any]]) -> dict[int, int]:
    """Calculate total marks per part from mark scheme data.

    Args:
        mark_scheme_data: Mark scheme from mark_criteria.get_mark_scheme_for_question()

    Returns:
        Dictionary mapping part_id to total marks for that part

    Example:
        >>> mark_scheme_data = [
        ...     {'part_id': 1, 'criteria': [
        ...         {'marks_available': 1},
        ...         {'marks_available': 1}
        ...     ]},
        ...     {'part_id': 2, 'criteria': [
        ...         {'marks_available': 2}
        ...     ]}
        ... ]
        >>> calculate_part_totals(mark_scheme_data)
        {1: 2, 2: 2}
    """
    totals = {}
    for part in mark_scheme_data:
        total = sum(criterion[CriterionFields.MARKS_AVAILABLE] for criterion in part["criteria"])
        totals[part["part_id"]] = total
    return totals


def format_marks_annotation(total_marks: int) -> str:
    """Format marks annotation for headers.

    Args:
        total_marks: Total marks available

    Returns:
        Formatted annotation string

    Examples:
        >>> format_marks_annotation(1)
        '[1 mark]'
        >>> format_marks_annotation(3)
        '[3 marks]'
    """
    mark_word = "mark" if total_marks == 1 else "marks"
    return f"[{total_marks} {mark_word}]"


def header(level: int, text: str) -> str:
    """Generate markdown header with level validation.

    Args:
        level: Header level (1-6, clamped if outside range)
        text: Header text

    Returns:
        Formatted markdown header with newline

    Examples:
        >>> header(1, "Title")
        '# Title\\n'
        >>> header(3, "Section")
        '### Section\\n'
        >>> header(7, "Too Deep")  # Clamped to 6
        '###### Too Deep\\n'
    """
    level = max(1, min(6, level))
    return f"{'#' * level} {text}\n"
