"""Prompt assembly for LLM marking requests.

Orchestrates the assembly of complete prompts by:
1. Loading static templates (markdown files)
2. Fetching dynamic data (questions, mark schemes) via repositories
3. Formatting data for presentation (via formatting layer)
4. Returning provider-agnostic MarkingRequest objects

Architecture:
    - PromptBuilder is 100% provider-agnostic (no Claude/OpenAI logic)
    - Returns MarkingRequest domain object with all content
    - Each LLM client is responsible for formatting MarkingRequest into its API format

Connection Management:
    This module uses dependency injection - caller owns connection lifecycle.
    Always use the connection context manager pattern:

    ✅ Correct usage:
        from paperlab.data.database import connection
        from paperlab.marking.prompt_builder import PromptBuilder

        with connection() as conn:
            builder = PromptBuilder(conn)
            request = builder.build_marking_request(question_id=1)
        # Connection automatically closed here

    ❌ Incorrect usage:
        from paperlab.data.database import get_connection

        conn = get_connection()
        builder = PromptBuilder(conn)
        # ... Connection never closed! Memory leak!
"""

from pathlib import Path
from sqlite3 import Connection

from paperlab.config import (
    SUBJECT_ABBREVIATIONS,
    SYSTEM_PROMPT_BASE,
    MarkType,
    settings,
)
from paperlab.constants.fields import CriterionFields
from paperlab.data.repositories.marking import mark_criteria, questions
from paperlab.markdown._helpers import (
    format_content_blocks,
    format_criterion_identifier,
    format_part_label,
)
from paperlab.marking.models import MarkingRequest


class PromptBuilder:
    """Assembles marking requests for LLM consumption (provider-agnostic).

    Responsibilities:
    - Template loading (system prompt, abbreviations)
    - Orchestrating data fetching from repositories
    - Delegating presentation formatting to formatting layer
    - Returning MarkingRequest domain object

    Does NOT:
    - Know about specific LLM providers (Claude, OpenAI)
    - Format output instructions (each client does this)
    - Generate JSON schemas (OpenAI client does this)

    Connection Lifecycle:
    - This class does NOT own the connection
    - Caller must manage connection lifecycle using context manager
    - See module docstring for correct usage pattern
    """

    def __init__(self, conn: Connection):
        """Initialize with database connection (dependency injection).

        Args:
            conn: Active database connection for repository access

        Note:
            Caller is responsible for closing the connection.
            Use context manager: with connection() as conn: ...
        """
        self.conn = conn

    def build_marking_request(self, question_id: int) -> MarkingRequest:
        """Build provider-agnostic marking request for a question.

        Returns a MarkingRequest containing all data needed for marking.
        Each LLM client is responsible for formatting this into its API format.

        Args:
            question_id: Database ID of question to mark

        Returns:
            MarkingRequest with system instructions, question content,
            abbreviations, and expected response structure

        Raises:
            FileNotFoundError: If template files don't exist
            ValueError: If question not found in database

        Example:
            >>> builder = PromptBuilder(conn)
            >>> request = builder.build_marking_request(question_id=1)
            >>> # Pass to LLM client:
            >>> response = client.mark_question(request, images)
        """
        # Load base system instructions (format-agnostic)
        system_path = settings.project_root / SYSTEM_PROMPT_BASE
        system_instructions = self._load_template(system_path)

        # Get subject and load abbreviations
        subject = self._get_subject_for_question(question_id)
        abbreviations_path = self._get_abbreviations_path(subject)
        abbreviations = self._load_template(abbreviations_path)

        # Generate question + mark scheme content
        question_content = self._format_question_with_markscheme(question_id)

        # Get expected response structure for validation/schema
        expected_structure = self.get_expected_response_structure(question_id)

        return MarkingRequest(
            system_instructions=system_instructions,
            question_content=question_content,
            abbreviations=abbreviations,
            expected_structure=expected_structure,
        )

    def _get_abbreviations_path(self, subject: str) -> Path:
        """Get abbreviations template path for subject.

        Args:
            subject: Subject name (e.g., 'Mathematics')

        Returns:
            Path to abbreviations template

        Raises:
            ValueError: If subject not found in SUBJECT_ABBREVIATIONS
        """
        if subject not in SUBJECT_ABBREVIATIONS:
            raise ValueError(
                f"No abbreviations template configured for subject: {subject}\n"
                f"Available subjects: {', '.join(SUBJECT_ABBREVIATIONS.keys())}"
            )
        return settings.project_root / SUBJECT_ABBREVIATIONS[subject]

    def get_expected_response_structure(
        self, question_id: int
    ) -> dict[str, list[dict[str, int | str]]]:
        """Get expected JSON structure template for LLM response validation.

        Returns schema showing all criterion IDs that must be present in the response,
        enabling validation that LLM marked every criterion.

        IMPORTANT: Excludes GENERAL criteria - these are guidance only, not marking criteria.

        Args:
            question_id: Database ID of question

        Returns:
            Dictionary with response structure template:
            {
                'results': [
                    {
                        'criterion_id': int,  # Expected criterion ID
                        'marks_available': int,  # Max marks for validation
                        'mark_type_code': str,  # For reference
                    },
                    ...
                ]
            }

        Raises:
            ValueError: If question not found

        Example:
            >>> builder = PromptBuilder(conn)
            >>> expected = builder.get_expected_response_structure(question_id=1)
            >>> # Use for validation:
            >>> # - Check all criterion_ids present in LLM response
            >>> # - Validate marks_awarded <= marks_available per criterion
            >>> # - Ensure no extra criteria in response
        """
        mark_scheme_data = mark_criteria.get_mark_scheme_for_question(question_id, self.conn)

        criteria_list = []
        for part_data in mark_scheme_data:
            for criterion in part_data["criteria"]:
                # Skip GENERAL criteria - guidance only, not marking criteria
                if criterion["mark_type_code"] == MarkType.GENERAL:
                    continue

                criteria_list.append(
                    {
                        CriterionFields.CRITERION_ID: criterion[CriterionFields.CRITERION_ID],
                        CriterionFields.MARKS_AVAILABLE: criterion[CriterionFields.MARKS_AVAILABLE],
                        "mark_type_code": criterion["mark_type_code"],
                    }
                )

        return {"results": criteria_list}

    def _format_question_with_markscheme(self, question_id: int) -> str:
        """Format question and mark scheme in interleaved structure for prompt.

        Creates optimized prompt format:
        - Question number with total marks
        - For each part:
          - Part label with marks
          - Question content
          - All mark criteria for that part (inline, not separate section)

        This format makes criterion-to-question mapping crystal clear for the LLM.

        Args:
            question_id: Database ID of question

        Returns:
            Formatted markdown string with question and mark scheme interleaved

        Raises:
            ValueError: If question not found

        Example output:
            # Question 5 [8 marks]

            ## Part (a) [2 marks]

            Calculate the derivative of $y = x^2 + 5x$

            ### Mark Scheme

            **Criterion ID: 1 | M1 (1 mark)**
            Correct application of power rule

            **Criterion ID: 2 | A1 (1 mark)**
            Correct answer: $2x + 5$
        """
        # Fetch data via repositories
        question_structure = questions.get_question_structure(question_id, self.conn)
        mark_scheme_data = mark_criteria.get_mark_scheme_for_question(question_id, self.conn)

        lines = []

        # Question header
        question_number = question_structure["question_number"]
        total_marks = question_structure["total_marks"]
        lines.append(f"# Question {question_number} [{total_marks} marks]\n")

        # Build part lookup for mark scheme
        mark_scheme_by_part = {p["part_id"]: p for p in mark_scheme_data}

        # Calculate part totals
        part_totals = {
            part_id: sum(c[CriterionFields.MARKS_AVAILABLE] for c in part_data["criteria"])
            for part_id, part_data in mark_scheme_by_part.items()
        }

        # Format each part with interleaved marks
        for part in question_structure["parts"]:
            part_label = format_part_label(part["part_letter"], part["sub_part_letter"])

            # Part header with total marks
            if part_label:
                part_marks = part_totals.get(part["part_id"], 0)
                mark_word = "mark" if part_marks == 1 else "marks"
                lines.append(f"## Part {part_label} [{part_marks} {mark_word}]\n")

            # Question content
            if part["content_blocks"]:
                content = format_content_blocks(part["content_blocks"])
                lines.append(content)
                lines.append("")

            # Mark scheme for this part
            part_marks_data = mark_scheme_by_part.get(part["part_id"])
            if part_marks_data and part_marks_data["criteria"]:
                lines.append("### Mark Scheme\n")

                # Expected answer (if present)
                if part_marks_data.get("expected_answer"):
                    lines.append(f"**Answer: {part_marks_data['expected_answer']}**\n")

                # Format each criterion with ID prominently displayed
                for criterion in part_marks_data["criteria"]:
                    # Criterion header with ID and identifier
                    criterion_id = criterion[CriterionFields.CRITERION_ID]
                    criterion_identifier = format_criterion_identifier(
                        criterion["mark_type_code"],
                        criterion[CriterionFields.MARKS_AVAILABLE],
                        criterion["criterion_index"],
                    )
                    lines.append(f"**Criterion ID: {criterion_id} | {criterion_identifier}**")

                    # Criterion description/content
                    if criterion["content_blocks"]:
                        criterion_content = format_content_blocks(criterion["content_blocks"])
                        lines.append(criterion_content)

                    lines.append("")

        return "\n".join(lines).strip()

    def _get_subject_for_question(self, question_id: int) -> str:
        """Get subject name for a given question.

        Delegates to repository for data access (no SQL in domain layer).

        Args:
            question_id: Database ID of question

        Returns:
            Subject name (e.g., 'Mathematics', 'English Language')

        Raises:
            ValueError: If question not found or subject not found (from repository)

        Example:
            >>> builder = PromptBuilder(conn)
            >>> subject = builder._get_subject_for_question(question_id=1)
            >>> # Returns: 'Mathematics'
        """
        return questions.get_subject_for_question(question_id, self.conn)

    def _load_template(self, path: Path) -> str:
        """Load prompt template from file.

        Args:
            path: Path to template file

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {path}\n"
                f"Expected location: {path.absolute()}\n"
                "Ensure template files exist in prompts/marking/ directory."
            )
        return path.read_text(encoding="utf-8")
