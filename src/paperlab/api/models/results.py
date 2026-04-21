"""API response models for results endpoints (Flow 4: View Results).

These models transform domain data into API responses for:
- Paper results summary (PaperResultsScreen)
- Question results detail (QuestionResultsScreen)

Uses from_domain() pattern to filter internal fields.
"""

import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from paperlab.config import settings

if TYPE_CHECKING:
    from pathlib import Path

# Default content block type when not specified
DEFAULT_BLOCK_TYPE = "text"

# =============================================================================
# Paper Results Response (GET /api/attempts/papers/{id}/results)
# =============================================================================


class QuestionScore(BaseModel):
    """Per-question score in paper results."""

    question_number: int
    question_attempt_id: int
    awarded: int
    available: int

    model_config = ConfigDict(populate_by_name=True)


class PaperResultsResponse(BaseModel):
    """Response model for paper results summary.

    Used by PaperResultsScreen to show overall paper performance.
    """

    attempt_id: int
    paper_name: str
    exam_date: str
    total_awarded: int
    total_available: int
    percentage: float
    grade: str | None
    questions: list[QuestionScore]

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_domain(
        cls,
        attempt_id: int,
        paper_name: str,
        exam_date: str,
        total_awarded: int,
        total_available: int,
        percentage: float,
        grade: str | None,
        question_scores: list[dict[str, int]],
    ) -> "PaperResultsResponse":
        """Convert domain data to API response.

        Args:
            attempt_id: Paper attempt ID
            paper_name: Display name of paper
            exam_date: Exam date for the paper
            total_awarded: Sum of marks awarded
            total_available: Total marks available
            percentage: Percentage score
            grade: Indicative grade (e.g., '9', '8', 'U')
            question_scores: List from get_scores_for_paper_attempt()

        Returns:
            PaperResultsResponse
        """
        return cls(
            attempt_id=attempt_id,
            paper_name=paper_name,
            exam_date=exam_date,
            total_awarded=total_awarded,
            total_available=total_available,
            percentage=percentage,
            grade=grade,
            questions=[
                QuestionScore(
                    question_number=q["question_number"],
                    question_attempt_id=q["question_attempt_id"],
                    awarded=q["awarded"],
                    available=q["available"],
                )
                for q in question_scores
            ],
        )


# =============================================================================
# Question Results Response (shared by paper and practice flows)
# =============================================================================


class ContentBlock(BaseModel):
    """Content block (text or diagram).

    Matches Flutter ContentBlock model field names:
    - Text blocks: block_type='text', text set, diagram_description=None
    - Diagram blocks: block_type='diagram', text=None, diagram_description set
    """

    block_type: str
    text: str | None = None
    diagram_description: str | None = None
    diagram_image_path: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CriterionResult(BaseModel):
    """Single marking criterion result with feedback."""

    mark_type_code: str
    display_name: str
    sequence_number: int
    marks_awarded: int
    marks_available: int
    content_blocks: list[ContentBlock]
    feedback: str

    model_config = ConfigDict(populate_by_name=True)


class PartResult(BaseModel):
    """Question part with content and marking results."""

    part_letter: str | None
    sub_part_letter: str | None
    expected_answer: str | None
    content_blocks: list[ContentBlock]
    criteria: list[CriterionResult]

    model_config = ConfigDict(populate_by_name=True)


class ImageInfo(BaseModel):
    """Submission image with presigned URL."""

    url: str
    sequence: int

    model_config = ConfigDict(populate_by_name=True)


class QuestionResultsResponse(BaseModel):
    """Response model for question results detail.

    Used by QuestionResultsScreen for both paper and practice flows.
    Shows question content, marking criteria, feedback, and student work images.
    """

    question_number: int
    paper_name: str
    exam_date: str
    total_awarded: int
    total_available: int
    parts: list[PartResult]
    images: list[ImageInfo]

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_domain(
        cls,
        question_number: int,
        paper_name: str,
        exam_date: str,
        question_content: list[dict[str, Any]],
        mark_scheme: list[dict[str, Any]],
        marking_results: list[dict[str, Any]],
        images: list[dict[str, str | int]],
        board: str | None = None,
        level: str | None = None,
        subject: str | None = None,
        paper_code: str | None = None,
    ) -> "QuestionResultsResponse":
        """Convert domain data to API response.

        Merges question content, mark scheme, and marking results into
        a single hierarchical response grouped by part.

        Args:
            question_number: Question number
            paper_name: Display name of paper
            exam_date: Exam date for the paper (YYYY-MM-DD format)
            question_content: From get_content_for_question()
            mark_scheme: From get_mark_scheme_for_question()
            marking_results: From get_results_for_submission()
            images: List of {url, sequence} dicts (presigned URLs)
            board: Exam board for diagram URL derivation (e.g., "pearson-edexcel")
            level: Exam level for diagram URL derivation (e.g., "gcse")
            subject: Subject for diagram URL derivation (e.g., "mathematics")
            paper_code: Paper code for diagram URL derivation (e.g., "1MA1/1H")

        Returns:
            QuestionResultsResponse
        """
        # Compute diagram URL base path and file system path if all paper metadata provided
        diagram_url_base: str | None = None
        diagram_dir: Path | None = None
        if board and level and subject and paper_code and exam_date:
            # Normalize paper metadata for URL path
            board_slug = board.lower().replace(" ", "-")
            level_slug = level.lower()
            subject_slug = subject.lower()
            # Build paper_stem: paper_code (normalized) + exam_date (underscored)
            # e.g., "1MA1/1H" -> "1ma1_1h", "2023-11-08" -> "2023_11_08"
            paper_code_slug = re.sub(r"[/\s]+", "_", paper_code.lower())
            exam_date_slug = exam_date.replace("-", "_")
            paper_stem = f"{paper_code_slug}_{exam_date_slug}"
            diagram_url_base = (
                f"/api/diagrams/{board_slug}/{level_slug}/{subject_slug}/{paper_stem}"
            )
            # File system path for existence checks
            diagram_dir = (
                settings.project_root
                / "data/papers/structured"
                / board_slug
                / level_slug
                / subject_slug
            )

        # Counter for question diagrams (supports multiple diagrams per question)
        question_diagram_index = 0

        def build_content_block(
            b: dict[str, str | None], criterion_index: int | None = None
        ) -> ContentBlock:
            """Build ContentBlock, deriving diagram_image_path from convention.

            Args:
                b: Content block dict with block_type, content_text, diagram_description
                criterion_index: If provided, this is a mark scheme criterion block.
                                 Used to build MS diagram path (q{NN}_c{C}.png).
                                 If None, this is a question content block (q{NN}_{D}.png).
            """
            nonlocal question_diagram_index
            diagram_path: str | None = None
            # Derive diagram path from convention if diagram block and metadata available
            if b.get("diagram_description") is not None and diagram_url_base and diagram_dir:
                if criterion_index is not None:
                    # Mark scheme diagram: check diagrams_ms/{paper_stem}/q{NN}_c{C}.png
                    filename = f"q{question_number:02d}_c{criterion_index}.png"
                    file_path = diagram_dir / "diagrams_ms" / paper_stem / filename
                    if file_path.exists():
                        ms_url_base = diagram_url_base.replace("/diagrams/", "/diagrams_ms/")
                        diagram_path = f"{ms_url_base}/q{question_number}_c{criterion_index}.png"
                else:
                    # Question diagram: check diagrams/{paper_stem}/q{NN}_{D}.png
                    question_diagram_index += 1
                    filename = f"q{question_number:02d}_{question_diagram_index}.png"
                    file_path = diagram_dir / "diagrams" / paper_stem / filename
                    if file_path.exists():
                        diagram_path = (
                            f"{diagram_url_base}/q{question_number}_{question_diagram_index}.png"
                        )
            return ContentBlock(
                block_type=b.get("block_type") or DEFAULT_BLOCK_TYPE,
                text=b.get("content_text"),
                diagram_description=b.get("diagram_description"),
                diagram_image_path=diagram_path,
            )

        # Build lookup for marking results by criterion_id
        results_by_criterion: dict[int, dict[str, Any]] = {
            r["mark_criteria_id"]: r for r in marking_results
        }

        # Build lookup for question content by part_id
        content_by_part: dict[int, list[dict[str, str | None]]] = {}
        for part in question_content:
            part_id = part["part_id"]
            blocks = part.get("content_blocks", [])
            if isinstance(blocks, list):
                content_by_part[part_id] = blocks

        # Calculate totals
        total_awarded = sum(r.get("marks_awarded", 0) for r in marking_results)
        total_available = sum(
            c.get("marks_available", 0) for p in mark_scheme for c in p.get("criteria", [])
        )

        # Build parts from mark scheme, merging in question content and results
        parts: list[PartResult] = []
        for ms_part in mark_scheme:
            part_id = ms_part["part_id"]

            # Get question content blocks for this part
            q_content = content_by_part.get(part_id, [])
            part_content_blocks = [build_content_block(b) for b in q_content]

            # Build criteria with results merged in
            criteria: list[CriterionResult] = []
            for i, criterion in enumerate(ms_part.get("criteria", [])):
                criterion_id = criterion.get("criterion_id")
                result = results_by_criterion.get(criterion_id, {})

                # Mark scheme content blocks (pass criterion_index for MS diagram paths)
                ms_content = criterion.get("content_blocks", [])
                criterion_content = [build_content_block(b, criterion_index=i) for b in ms_content]

                criteria.append(
                    CriterionResult(
                        mark_type_code=criterion.get("mark_type_code", ""),
                        display_name=criterion.get("mark_type_name", ""),
                        sequence_number=i + 1,
                        marks_awarded=result.get("marks_awarded", 0),
                        marks_available=criterion.get("marks_available", 0),
                        content_blocks=criterion_content,
                        feedback=result.get("feedback", ""),
                    )
                )

            parts.append(
                PartResult(
                    part_letter=ms_part.get("part_letter"),
                    sub_part_letter=ms_part.get("sub_part_letter"),
                    expected_answer=ms_part.get("expected_answer"),
                    content_blocks=part_content_blocks,
                    criteria=criteria,
                )
            )

        # Build images list
        image_list = [
            ImageInfo(url=str(img["url"]), sequence=int(img["sequence"])) for img in images
        ]

        return cls(
            question_number=question_number,
            paper_name=paper_name,
            exam_date=exam_date,
            total_awarded=total_awarded,
            total_available=total_available,
            parts=parts,
            images=image_list,
        )
