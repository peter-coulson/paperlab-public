"""Parser for LLM marking responses.

Handles extraction of JSON from LLM responses (which may include markdown
wrappers or preambles) and validation against mark scheme.

Design principles:
- Robust JSON extraction (handles markdown, preambles, pure JSON)
- Two-layer validation: Pydantic (structure) + business rules (database)
- Returns both raw JSON (for storage) and parsed object (for processing)
- Clear error messages for debugging
"""

import json
import re
import sqlite3

from paperlab.config import ErrorFormatting
from paperlab.marking.models import LLMMarkingResponse
from paperlab.marking.validators import validate_marking_response


def parse_llm_response(
    raw_response: str,
    question_id: int,
    conn: sqlite3.Connection,
) -> tuple[str, LLMMarkingResponse]:
    """Parse and validate LLM marking response.

    Orchestrates the complete parsing pipeline:
    1. Extract JSON from markdown wrappers/preambles
    2. Parse with Pydantic (Layer 1: types and basic constraints)
    3. Validate business rules (Layer 2: cross-validation with database)

    Args:
        raw_response: Raw LLM response (may include markdown, preambles, etc.)
        question_id: Database ID of question being marked
        conn: Database connection (for cross-validation)

    Returns:
        Tuple of (json_string, validated_response):
        - json_string: Clean JSON for storage in marking_attempts.response_received
        - validated_response: Parsed and validated LLMMarkingResponse object

    Raises:
        ValueError: If JSON extraction fails, parsing fails, or validation fails
        json.JSONDecodeError: If extracted text is not valid JSON
        pydantic.ValidationError: If JSON structure doesn't match schema

    Example:
        >>> raw = '''Here are the results:
        ... ```json
        ... {"results": [{"criterion_id": 1, ...}]}
        ... ```
        ... '''
        >>> json_str, response = parse_llm_response(raw, question_id=1, conn)
        >>> # json_str ready for database storage
        >>> # response ready for processing
    """
    # Step 1: Extract JSON from markdown wrappers
    json_str = extract_json_from_response(raw_response)

    # Step 2: Parse with Pydantic (Layer 1 validation)
    response = LLMMarkingResponse.model_validate_json(json_str)

    # Step 3: Business validation (Layer 2)
    validate_marking_response(response, question_id, conn)

    return json_str, response


def extract_json_from_response(raw_response: str) -> str:
    """Extract JSON from LLM response, handling markdown wrappers and preambles.

    LLMs often wrap JSON in markdown code blocks or include explanatory text.
    This function robustly extracts the JSON using multiple strategies.

    Strategies (tried in order):
    1. Pure JSON (try parsing directly)
    2. Markdown code block (```json...``` or ```...```)
    3. Brace pattern (find {...} in text)

    Args:
        raw_response: Raw LLM response text

    Returns:
        Clean JSON string ready for parsing

    Raises:
        ValueError: If no valid JSON found in response

    Examples:
        >>> # Pure JSON
        >>> extract_json_from_response('{"results": []}')
        '{"results": []}'

        >>> # Markdown wrapped
        >>> extract_json_from_response('```json\\n{"results": []}\\n```')
        '{"results": []}'

        >>> # With preamble
        >>> extract_json_from_response('Here are results:\\n```json\\n{"results": []}\\n```')
        '{"results": []}'
    """
    # Strategy 1: Try direct parse (pure JSON)
    try:
        json.loads(raw_response)
        return raw_response.strip()
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code block
    # Match ```json...``` or ```...```
    code_block_pattern = r"```(?:json)?\s*\n(.*?)\n```"
    matches = re.findall(code_block_pattern, raw_response, re.DOTALL)

    if matches:
        # Take first JSON block that parses successfully
        for match in matches:
            json_str = match.strip()
            try:
                json.loads(json_str)  # Validate
                return str(json_str)
            except json.JSONDecodeError:
                continue

    # Strategy 3: Look for {...} pattern (last resort)
    # Find outermost braces
    brace_pattern = r"\{.*\}"
    matches = re.findall(brace_pattern, raw_response, re.DOTALL)

    if matches:
        # Try each match until one parses (prefer longer matches first)
        for match in sorted(matches, key=len, reverse=True):
            try:
                json.loads(match)
                return str(match.strip())
            except json.JSONDecodeError:
                continue

    # No valid JSON found
    preview = raw_response[: ErrorFormatting.PREVIEW_LENGTH]
    if len(raw_response) > ErrorFormatting.PREVIEW_LENGTH:
        preview += "..."

    raise ValueError(
        "Could not extract valid JSON from LLM response.\n"
        f"Response preview (first {ErrorFormatting.PREVIEW_LENGTH} chars):\n{preview}\n\n"
        "Expected JSON format:\n"
        '{\n  "results": [\n    {\n      "criterion_id": <int>,\n      '
        '"marks_awarded": <int>,\n      "feedback": "<string>",\n      '
        '"confidence_score": <float>\n    }\n  ]\n}'
    )
