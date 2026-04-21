"""Parser for paper identifier format.

Handles parsing of paper identifiers in the format:
BOARD-LEVEL-SUBJECT-CODE-DATE

Examples:
- PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08
- AQA-GCSE-MATHEMATICS-8300-1F-2024-05-15
"""

import re
from dataclasses import dataclass

from paperlab.config.constants import ErrorMessages


@dataclass
class PaperIdentifierComponents:
    """Parsed components of a paper identifier.

    Attributes:
        board: Exam board (may contain hyphens, e.g., "PEARSON-EDEXCEL")
        level: Exam level (e.g., "GCSE", "A-LEVEL")
        subject: Subject name (may contain hyphens, e.g., "MATHEMATICS")
        code: Paper code (e.g., "1MA1-1H", "8300-1F")
        date: Paper date (e.g., "2023-11-08")
    """

    board: str
    level: str
    subject: str
    code: str
    date: str


# Known exam levels for parsing
KNOWN_EXAM_LEVELS = {"GCSE", "A-LEVEL", "AS-LEVEL", "ALEVEL", "ASLEVEL"}

# Pattern for paper identifier components
# Format: BOARD-LEVEL-SUBJECT-CODE-DATE
# - BOARD: One or more words separated by hyphens
# - LEVEL: Known exam level (GCSE, A-LEVEL, etc.)
# - SUBJECT: One or more words separated by hyphens
# - CODE: Alphanumeric with optional hyphens
# - DATE: YYYY-MM-DD format
PAPER_IDENTIFIER_PATTERN = re.compile(
    r"^(?P<prefix>.*?)-(?P<level>GCSE|A-LEVEL|AS-LEVEL|ALEVEL|ASLEVEL)-(?P<suffix>.+)$"
)


def parse_paper_identifier(paper_identifier: str) -> PaperIdentifierComponents:
    """Parse paper identifier into components.

    Strategy:
    1. Find the known exam level (GCSE, A-LEVEL, etc.) in the identifier
    2. Everything before the level is the board (may contain hyphens)
    3. Parse the suffix after level to extract subject, code, and date

    Args:
        paper_identifier: Full paper identifier string

    Returns:
        PaperIdentifierComponents with parsed fields

    Raises:
        ValueError: If identifier format is invalid

    Examples:
        >>> parse_paper_identifier("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
        PaperIdentifierComponents(
            board="PEARSON-EDEXCEL",
            level="GCSE",
            subject="MATHEMATICS",
            code="1MA1-1H",
            date="2023-11-08"
        )

        >>> parse_paper_identifier("AQA-GCSE-MATHEMATICS-8300-1F-2024-05-15")
        PaperIdentifierComponents(
            board="AQA",
            level="GCSE",
            subject="MATHEMATICS",
            code="8300-1F",
            date="2024-05-15"
        )
    """
    # Use regex to split on known exam level
    match = PAPER_IDENTIFIER_PATTERN.match(paper_identifier)

    if not match:
        raise ValueError(
            ErrorMessages.INVALID_PAPER_IDENTIFIER.format(paper_identifier=paper_identifier)
        )

    board = match.group("prefix")
    level = match.group("level")
    suffix = match.group("suffix")

    # Parse suffix: SUBJECT-CODE-DATE
    # Date is always last 10 characters (YYYY-MM-DD)
    # Need to find where subject ends and code begins

    # Extract date (last 10 chars: YYYY-MM-DD)
    if len(suffix) < 10:
        raise ValueError(
            ErrorMessages.INVALID_PAPER_IDENTIFIER.format(paper_identifier=paper_identifier)
        )

    # Date is last component after final hyphen before YYYY-MM-DD pattern
    suffix_parts = suffix.split("-")

    # Date is last 3 parts (YYYY-MM-DD)
    if len(suffix_parts) < 4:  # At least SUBJECT-CODE-YYYY-MM-DD
        raise ValueError(
            ErrorMessages.INVALID_PAPER_IDENTIFIER.format(paper_identifier=paper_identifier)
        )

    date = "-".join(suffix_parts[-3:])  # YYYY-MM-DD

    # Everything before date
    subject_and_code = suffix_parts[:-3]

    # Heuristic: Subject is typically one word, code is everything after
    # But subject can be multiple words (e.g., "COMBINED-SCIENCE")
    # For now, take first part as subject, rest as code
    subject = subject_and_code[0]
    code = "-".join(subject_and_code[1:]) if len(subject_and_code) > 1 else ""

    if not code:
        raise ValueError(
            ErrorMessages.INVALID_PAPER_IDENTIFIER.format(paper_identifier=paper_identifier)
        )

    return PaperIdentifierComponents(
        board=board, level=level, subject=subject, code=code, date=date
    )
