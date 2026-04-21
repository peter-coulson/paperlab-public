"""Formatting utilities for eval CLI commands.

Presentation logic for evaluation command outputs.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from paperlab.evaluation.generation.sanity_case_generator import GenerationResult
    from paperlab.evaluation.services.sanity_case_auditor import AuditReport


def format_generation_report(result: GenerationResult) -> str:
    """Format generation result as user-friendly report.

    Args:
        result: Generation result to format

    Returns:
        Formatted report string
    """
    if not result.files_created and not result.errors:
        return "✅ All questions already have sanity test cases!"

    lines = []
    lines.append(f"{'=' * 80}")
    lines.append("Sanity Test Case Generation Report")
    lines.append(f"{'=' * 80}")
    lines.append(f"\nGenerated {len(result.files_created)} JSON file(s)")

    if result.files_skipped:
        lines.append(f"Skipped {len(result.files_skipped)} existing file(s)")

    if result.errors:
        lines.append(f"\n⚠️  {len(result.errors)} error(s) occurred:")
        for error in result.errors:
            lines.append(f"  - {error}")

    if result.files_created:
        # Group by paper for cleaner output
        by_paper: dict[str, list[tuple[Path, str | list[str]]]] = defaultdict(list)

        for json_path, img_name in result.files_created:
            # Extract paper identifier from path
            # Path format: .../pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08/q01_...
            paper_dir = json_path.parent
            by_paper[str(paper_dir)].append((json_path, img_name))

        lines.append(f"\n{'=' * 80}")
        lines.append("Files Created")
        lines.append(f"{'=' * 80}")

        for paper_dir_str in sorted(by_paper.keys()):
            files = by_paper[paper_dir_str]
            lines.append(f"\n📁 {paper_dir_str}")
            lines.append(f"   Created {len(files)} file(s):")

            for json_path, img_name in files:
                lines.append(f"     ✓ {json_path.name} → needs {img_name}")

    lines.append(f"\n{'=' * 80}")
    lines.append("Next Steps")
    lines.append(f"{'=' * 80}")
    lines.append("1. Add PNG images to the directories shown above")
    lines.append("2. Images should show perfect answers with full marks")
    lines.append("3. Load test cases with: uv run paperlab eval load-case <json_path>")
    lines.append("4. Verify with: uv run paperlab eval audit-sanity-cases")

    return "\n".join(lines)


def format_audit_report(report: AuditReport) -> str:
    """Format audit report as user-friendly output.

    Args:
        report: Audit report to format

    Returns:
        Formatted report string
    """
    lines = []
    lines.append(f"\n{'=' * 80}")
    lines.append("Sanity Test Case Audit Report")
    lines.append(f"{'=' * 80}")
    lines.append(f"\nTotal questions in production DB: {report.total_questions}")
    lines.append(f"Questions with sanity test cases:  {report.with_cases}")
    lines.append(f"Questions missing sanity cases:    {len(report.missing_cases)}")

    if len(report.missing_cases) == 0:
        lines.append("\n✅ All questions have sanity test cases!")
        return "\n".join(lines)

    # Group missing by paper for cleaner output
    by_paper: dict[str, list[tuple[int, Path, str, str | list[str]]]] = defaultdict(list)

    for case in report.missing_cases:
        by_paper[case.paper_identifier].append(
            (case.question_number, case.case_dir, case.json_filename, case.image_filename)
        )

    lines.append(f"\n{'=' * 80}")
    lines.append("Missing Sanity Test Cases")
    lines.append(f"{'=' * 80}")

    for paper_id in sorted(by_paper.keys()):
        paper_questions = by_paper[paper_id]
        lines.append(f"\n📄 {paper_id}")
        lines.append(f"   Missing: {len(paper_questions)} question(s)")

        # Show first case's directory as example
        first_case_dir = paper_questions[0][1]
        lines.append(f"   Directory: {first_case_dir}")
        lines.append("   Files needed:")

        for qnum, _, json_file, img_file in sorted(paper_questions):
            lines.append(f"     • Q{qnum:02d}: {json_file} + {img_file}")

    lines.append(f"\n{'=' * 80}")
    lines.append("Next Steps")
    lines.append(f"{'=' * 80}")
    lines.append("1. Create JSON files in the directories shown above")
    lines.append("2. Add corresponding PNG images (perfect answers with full marks)")
    lines.append("3. Load test cases with: uv run paperlab eval load-case <json_path>")
    lines.append("4. Re-run this audit to verify: uv run paperlab eval audit-sanity-cases")

    return "\n".join(lines)
