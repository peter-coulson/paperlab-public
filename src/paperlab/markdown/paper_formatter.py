"""Format paper metadata as markdown."""

from typing import Any

from paperlab.markdown._helpers import header


def format_paper_header(paper_data: dict[str, Any], base_level: int = 1) -> str:
    """Format paper title/header with metadata.

    Args:
        paper_data: Paper data from papers.get_paper_full()
        base_level: Header level for paper title (default: 1)

    Returns:
        Formatted paper header as markdown string

    Example output (base_level=1):
        # Pearson Edexcel GCSE Mathematics - Paper 1 (Non-Calculator)

        **Exam Board:** Pearson Edexcel
        **Level:** GCSE
        **Subject:** Mathematics
        **Paper:** Paper 1 (Non-Calculator)
        **Paper Code:** 1MA1/1H
        **Date:** 2023-06-05
        **Total Marks:** 80
    """
    lines = []

    lines.append(header(base_level, paper_data["exam_identifier"]))
    lines.append("")

    # Exam metadata
    lines.append(f"**Exam Board:** {paper_data['exam_board']}")
    lines.append(f"**Level:** {paper_data['exam_level']}")
    lines.append(f"**Subject:** {paper_data['subject']}")
    lines.append(f"**Paper:** {paper_data['display_name']}")
    lines.append(f"**Paper Code:** {paper_data['paper_code']}")
    lines.append(f"**Date:** {paper_data['exam_date']}")
    lines.append(f"**Total Marks:** {paper_data['total_marks']}")
    lines.append("")

    return "\n".join(lines)
