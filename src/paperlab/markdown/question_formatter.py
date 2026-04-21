"""Public API for formatting questions and mark schemes as markdown."""

from typing import Any

from paperlab.constants.fields import CriterionFields
from paperlab.markdown._helpers import (
    calculate_part_totals,
    format_content_blocks,
    format_criterion_identifier,
    format_marks_annotation,
    format_part_label,
    header,
)


def format_question_only(
    question_data: dict[str, Any],
    mark_scheme_data: list[dict[str, Any]],
    base_level: int = 2,
) -> str:
    """Format question structure as markdown (no mark scheme content).

    Args:
        question_data: Question structure from questions.get_question_structure()
        mark_scheme_data: Mark scheme data (used only for calculating totals)
        base_level: Header level for question title (default: 2)

    Returns:
        Formatted question as markdown string

    Example output (base_level=2):
        ## Question 5 [8 marks]

        **(a) [2 marks]**

        Calculate the derivative of $y = x^2 + 5x$

        **(b) [3 marks]**

        Find the gradient at $x = 3$
    """
    lines = []

    # Calculate part totals
    part_totals = calculate_part_totals(mark_scheme_data)

    # Question header with total marks
    question_total = question_data["total_marks"]
    total_annotation = format_marks_annotation(question_total)
    lines.append(
        header(base_level, f"Question {question_data['question_number']} {total_annotation}")
    )

    # Format each part
    for part in question_data["parts"]:
        part_label = format_part_label(part["part_letter"], part["sub_part_letter"])

        # Part header (if not NULL part)
        if part_label:
            part_marks = part_totals.get(part["part_id"], 0)
            part_annotation = format_marks_annotation(part_marks)
            lines.append(f"**{part_label} {part_annotation}**")

        # Content blocks
        content = format_content_blocks(part["content_blocks"])
        lines.append(content)
        lines.append("")

    return "\n".join(lines).strip()


def format_mark_scheme_only(
    question_data: dict[str, Any],
    mark_scheme_data: list[dict[str, Any]],
    base_level: int = 2,
) -> str:
    """Format mark scheme as markdown (no question content).

    Args:
        question_data: Question data (used only for question number and total marks)
        mark_scheme_data: Mark scheme from mark_criteria.get_mark_scheme_for_question()
        base_level: Header level for question title (default: 2, parts at base_level+1)

    Returns:
        Formatted mark scheme as markdown string

    Example output (base_level=2):
        ## Mark Scheme - Question 5 [8 marks]

        ### Part (a) [2 marks]

        **Answer: 15.12**

        **M1 (1 mark)** - Apply power rule
        Correct application: $\frac{d}{dx}(x^n) = nx^{n-1}$

        **A1 (1 mark)** - Correct answer
        $2x + 5$
    """
    lines = []

    # Calculate part totals
    part_totals = calculate_part_totals(mark_scheme_data)

    # Header with question number and total marks
    question_total = question_data["total_marks"]
    total_annotation = format_marks_annotation(question_total)
    lines.append(
        header(
            base_level,
            f"Mark Scheme - Question {question_data['question_number']} {total_annotation}",
        )
    )

    for part_data in mark_scheme_data:
        # Part header with total marks
        part_label = format_part_label(part_data["part_letter"], part_data["sub_part_letter"])
        if part_label:
            part_marks = part_totals.get(part_data["part_id"], 0)
            part_annotation = format_marks_annotation(part_marks)
            lines.append(header(base_level + 1, f"Part {part_label} {part_annotation}"))

        # Expected answer (if present)
        if part_data.get("expected_answer"):
            lines.append(f"**Answer: {part_data['expected_answer']}**")
            lines.append("")

        # Format each criterion
        for criterion in part_data["criteria"]:
            # Criterion identifier
            criterion_id = format_criterion_identifier(
                criterion["mark_type_code"],
                criterion[CriterionFields.MARKS_AVAILABLE],
                criterion["criterion_index"],
            )
            lines.append(f"**{criterion_id}**")

            # Criterion content
            if criterion["content_blocks"]:
                content = format_content_blocks(criterion["content_blocks"])
                lines.append(content)

            lines.append("")

    return "\n".join(lines).strip()


def format_question_with_marks(
    question_data: dict[str, Any],
    mark_scheme_data: list[dict[str, Any]],
    base_level: int = 2,
) -> str:
    """Format question with mark scheme interleaved.

    Args:
        question_data: Question structure from questions.get_question_structure()
        mark_scheme_data: Mark scheme from mark_criteria.get_mark_scheme_for_question()
        base_level: Header level for question title (default: 2, parts at base_level+1,
            mark scheme at base_level+2)

    Returns:
        Formatted question + mark scheme as markdown string

    Example output (base_level=2):
        ## Question 5 [8 marks]

        ### Part (a) [2 marks]

        Calculate the derivative of $y = x^2 + 5x$

        #### Mark Scheme

        **M1 (1 mark)** - Apply power rule
        Correct application: $\frac{d}{dx}(x^n) = nx^{n-1}$

        **A1 (1 mark)** - Correct answer
        $2x + 5$
    """
    lines = []

    # Calculate part totals
    part_totals = calculate_part_totals(mark_scheme_data)

    # Question header with total marks
    question_total = question_data["total_marks"]
    total_annotation = format_marks_annotation(question_total)
    lines.append(
        header(base_level, f"Question {question_data['question_number']} {total_annotation}")
    )

    # Build part lookup for mark scheme
    mark_scheme_by_part = {p["part_id"]: p for p in mark_scheme_data}

    # Format each part with interleaved marks
    for part in question_data["parts"]:
        part_label = format_part_label(part["part_letter"], part["sub_part_letter"])

        # Part header with total marks
        if part_label:
            part_marks = part_totals.get(part["part_id"], 0)
            part_annotation = format_marks_annotation(part_marks)
            lines.append(header(base_level + 1, f"Part {part_label} {part_annotation}"))

        # Question content
        content = format_content_blocks(part["content_blocks"])
        lines.append(content)
        lines.append("")

        # Mark scheme for this part
        part_marks_data = mark_scheme_by_part.get(part["part_id"])
        if part_marks_data and part_marks_data["criteria"]:
            lines.append(header(base_level + 2, "Mark Scheme"))

            # Expected answer (if present)
            if part_marks_data.get("expected_answer"):
                lines.append(f"**Answer: {part_marks_data['expected_answer']}**")
                lines.append("")

            for criterion in part_marks_data["criteria"]:
                # Criterion identifier
                criterion_id = format_criterion_identifier(
                    criterion["mark_type_code"],
                    criterion[CriterionFields.MARKS_AVAILABLE],
                    criterion["criterion_index"],
                )
                lines.append(f"**{criterion_id}**")

                # Criterion content
                if criterion["content_blocks"]:
                    criterion_content = format_content_blocks(criterion["content_blocks"])
                    lines.append(criterion_content)

                lines.append("")

    return "\n".join(lines).strip()
