"""Paper commands (export only - marking now via API)."""

from pathlib import Path
from typing import Literal

from paperlab.config import settings
from paperlab.data.database import connection
from paperlab.data.repositories.marking import (
    mark_criteria,
    papers,
    questions,
)
from paperlab.loading.paper_file_paths import _parse_paper_identifier, get_hierarchical_subject_dir
from paperlab.markdown.paper_formatter import format_paper_header
from paperlab.markdown.question_formatter import (
    format_mark_scheme_only,
    format_question_only,
    format_question_with_marks,
)


def create(
    paper_id: int,
    format_type: Literal["questions", "markscheme", "full"],
    output_dir: Path | None = None,
) -> Path:
    """Generate markdown file for paper.

    Args:
        paper_id: Database ID of paper to export
        format_type: Type of output ('questions', 'markscheme', or 'full')
        output_dir: Where to write markdown file (default: from config)

    Returns:
        Path to created file

    Raises:
        ValueError: If paper not found or no questions exist
    """
    if output_dir is None:
        output_dir = settings.exports_markdown_path

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    with connection() as conn:
        # Fetch paper data
        paper_data = papers.get_paper_full(paper_id, conn)

        # Fetch all questions
        question_list = questions.get_all_with_marks(paper_id, conn)
        if not question_list:
            raise ValueError(f"No questions found for paper_id={paper_id}")

        # Build output
        output_lines = []

        # Paper header
        output_lines.append(format_paper_header(paper_data, base_level=1))

        # Format each question
        for question_id, _, _ in question_list:
            question_structure = questions.get_question_structure(question_id, conn)
            mark_scheme_data = mark_criteria.get_mark_scheme_for_question(question_id, conn)

            if format_type == "questions":
                formatted = format_question_only(
                    question_structure,
                    mark_scheme_data,
                    base_level=settings.markdown_base_heading_level,
                )
            elif format_type == "markscheme":
                formatted = format_mark_scheme_only(
                    question_structure,
                    mark_scheme_data,
                    base_level=settings.markdown_base_heading_level,
                )
            else:  # full
                formatted = format_question_with_marks(
                    question_structure,
                    mark_scheme_data,
                    base_level=settings.markdown_base_heading_level,
                )

            output_lines.append(formatted)
            output_lines.append("")

        # Generate hierarchical output path
        exam_identifier = str(paper_data["exam_identifier"])

        # Get hierarchical directory (board/level/subject)
        subject_dir = get_hierarchical_subject_dir(exam_identifier, output_dir)
        subject_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename using same convention as structured papers
        _, _, _, base_filename = _parse_paper_identifier(exam_identifier)
        filename = f"{base_filename}_{format_type}.md"
        output_path = subject_dir / filename

        # Write to file
        content = "\n".join(output_lines).strip() + "\n"
        output_path.write_text(content, encoding="utf-8")

        return output_path
