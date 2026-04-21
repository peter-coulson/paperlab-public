"""Anthropic Claude API client implementation.

Provides Claude-specific implementation of the LLM client interface.

Architecture:
- Owns prompt formatting: embeds JSON example in user prompt
- Claude doesn't support structured outputs, so format is in prompt text
- Inherits shared retry/validation logic from BaseLLMClient

Design principles:
- Inherits shared logic from BaseLLMClient
- Maps Anthropic SDK exceptions to our exception hierarchy
- Uses Claude's vision API for image-based marking
- Follows best practices from context/api-docs/anthropic.md
"""

from pathlib import Path

import anthropic
from anthropic.types import ImageBlockParam, MessageParam, TextBlock, TextBlockParam

from paperlab.config import LLMProviders, settings
from paperlab.marking.models import MarkingRequest
from paperlab.services.llm_client import (
    BaseLLMClient,
    LLMAPIError,
    LLMAuthenticationError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client.

    Implements LLM marking using Claude's Messages API with vision support.

    Prompt Formatting:
        Claude doesn't support structured outputs API, so we embed the
        expected JSON format directly in the user prompt. This client
        owns the formatting logic:
        - System prompt: Base instructions + JSON-only requirement
        - User prompt: Abbreviations + question + JSON example

    Features:
    - Vision API for analyzing student work images
    - Structured JSON output via prompt formatting
    - Error mapping to standardized exception hierarchy
    - Retry logic with exponential backoff (inherited)

    Usage:
        >>> from paperlab.services.claude_client import ClaudeClient
        >>> from paperlab.marking.prompt_builder import PromptBuilder
        >>> client = ClaudeClient(api_key="sk-ant-...")
        >>> request = builder.build_marking_request(question_id=1)
        >>> response = client.mark_question(request, images)

    Reference:
        See context/api-docs/anthropic.md for implementation details
    """

    # Claude-specific system prompt addition (JSON format requirement)
    _SYSTEM_FORMAT_INSTRUCTION = (
        "\n**Response format: JSON ONLY** - Your response must ONLY be valid JSON. "
        "Never use plain text, explanations, apologies, or refusals under any circumstances."
    )

    def __init__(self, api_key: str, model_identifier: str) -> None:
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key (format: sk-ant-...)
            model_identifier: Model to use (e.g., 'claude-sonnet-4-5-20250929')

        Raises:
            ValueError: If API key invalid
        """
        # Initialize base client with settings from config
        super().__init__(
            api_key=api_key,
            model_identifier=model_identifier,
            max_retries=settings.llm_max_retries,
            timeout=settings.llm_timeout,
            provider_name=LLMProviders.ANTHROPIC,
        )

        # Initialize Anthropic SDK client
        self.client = anthropic.Anthropic(api_key=api_key)

        # Cache for last API response (used to extract token usage)
        self.last_message: anthropic.types.Message | None = None

    def mark_question(
        self,
        request: MarkingRequest,
        image_paths: list[Path | str],
    ) -> str:
        """Mark a question using Claude API.

        Formats the MarkingRequest into Claude's prompt format:
        - System prompt with JSON-only requirement
        - User prompt with embedded JSON example structure

        Args:
            request: MarkingRequest containing all prompt data
            image_paths: Local file paths or presigned URLs

        Returns:
            Raw text response from Claude (JSON)
        """
        # Format prompts for Claude
        system_prompt = self._format_system_prompt(request)
        user_prompt = self._format_user_prompt(request)

        # Call API with retry logic
        return self._mark_with_retry(system_prompt, user_prompt, image_paths)

    def _format_system_prompt(self, request: MarkingRequest) -> str:
        """Format system prompt with Claude-specific JSON requirement.

        Args:
            request: MarkingRequest with base system instructions

        Returns:
            System prompt with JSON-only format instruction appended
        """
        # Append JSON-only instruction to system prompt
        # Position doesn't matter - Claude reads entire system prompt
        return f"{request.system_instructions}\n{self._SYSTEM_FORMAT_INSTRUCTION}"

    def _format_user_prompt(self, request: MarkingRequest) -> str:
        """Format user prompt with embedded JSON example.

        Args:
            request: MarkingRequest with abbreviations, question, and expected structure

        Returns:
            User prompt with abbreviations, question, and JSON example
        """
        # Build JSON example from expected structure
        json_example = self._format_json_example(request.expected_structure)

        # Assemble user prompt: abbreviations + question + format instructions
        return f"""{request.abbreviations}

---

# Question and Mark Scheme

{request.question_content}

---

# Output Format

Your response must be ONLY this JSON structure (no other text):

```json
{json_example}
```

**Field Requirements:**
- `criterion_id`: Must exactly match the IDs shown above (do not skip any criterion)
- `observation`: Internal reasoning about the student work (not shown to students)
- `feedback`: Direct, objective feedback stating whether criterion was met (user-facing)
- `marks_awarded`: Must be within the valid range (0 to maximum marks for that criterion)
- `confidence_score`: Float between 0.0 (very uncertain) and 1.0 (completely certain)

**Critical:** Provide a result entry for EVERY criterion, even if 0 marks. If you cannot
assess the work for any reason, return JSON with 0 marks and explain in feedback."""

    def _format_json_example(
        self, expected_structure: dict[str, list[dict[str, int | str]]]
    ) -> str:
        """Format expected structure as JSON example with comments.

        Args:
            expected_structure: Dict with 'results' list of criterion info

        Returns:
            JSON string with placeholder values and range comments
        """
        criterion_entries = []
        for criterion_info in expected_structure.get("results", []):
            criterion_id = int(criterion_info["criterion_id"])
            marks_available = int(criterion_info["marks_available"])
            mark_type_code = criterion_info.get("mark_type_code", "?")

            # Build marks range comment
            marks_range = f"0-{marks_available}" if marks_available > 0 else "0"

            entry = f"""    {{
      "criterion_id": {criterion_id},
      "observation": "<string>",
      "feedback": "<string>",
      "marks_awarded": <integer>,  // {marks_range} ({mark_type_code})
      "confidence_score": <float>  // 0.0-1.0
    }}"""
            criterion_entries.append(entry)

        return (
            """{
  "results": [
"""
            + ",\n".join(criterion_entries)
            + """
  ]
}"""
        )

    def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path | str],
        *_args: object,  # Ignored - Claude doesn't use extra args
    ) -> str:
        """Call Claude API to mark a question.

        This method is called by _mark_with_retry after validation.

        Args:
            system_prompt: System-level instructions for Claude
            user_prompt: Question-specific prompt
            image_paths: Local file paths or presigned URLs (already validated)
            *_args: Ignored (for base class compatibility)

        Returns:
            Raw text response from Claude

        Raises:
            LLMAPIError: If API call fails
            LLMAuthenticationError: If API key invalid
            LLMRateLimitError: If rate limit exceeded
            LLMTimeoutError: If request times out
            LLMInvalidRequestError: If request parameters invalid
        """
        try:
            # Build content array with all images followed by text prompt
            # Format: [image1, image2, ..., text]
            content: list[ImageBlockParam | TextBlockParam] = []

            # Add all images first (preserves sequence order)
            for image_path in image_paths:
                # Detect if URL or local path
                if isinstance(image_path, str) and image_path.startswith("https://"):
                    # Remote URL - pass to Claude directly
                    image_block: ImageBlockParam = {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_path,
                        },
                    }
                else:
                    # Local file - encode to base64 (existing logic)
                    if isinstance(image_path, str):
                        image_path = Path(image_path)

                    # Encode image to base64
                    image_data = self._encode_image(image_path)

                    # Determine media type from file extension
                    media_type = self._get_media_type(image_path)

                    # Build image block
                    image_block = {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    }
                content.append(image_block)

            # Add text prompt after all images
            text_block: TextBlockParam = {"type": "text", "text": user_prompt}
            content.append(text_block)

            # Build user message with all content blocks
            user_message: MessageParam = {
                "role": "user",
                "content": content,
            }

            # Call Claude API
            message = self.client.messages.create(
                model=self.model_identifier,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                system=system_prompt,
                messages=[user_message],
            )

            # Cache message for token usage extraction
            self.last_message = message

            # Extract text from response
            # Claude returns content as a list, we need the first text block
            if not message.content or len(message.content) == 0:
                raise LLMAPIError("Empty response from Claude API", provider=self.provider_name)

            # Get first content block and ensure it's a text block
            first_block = message.content[0]
            if not isinstance(first_block, TextBlock):
                raise LLMAPIError(
                    f"Expected TextBlock in response, got {type(first_block).__name__}",
                    provider=self.provider_name,
                )

            return first_block.text

        except anthropic.AuthenticationError as e:
            raise LLMAuthenticationError(
                f"Invalid Anthropic API key: {e}", provider=self.provider_name
            ) from e

        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(
                f"Anthropic rate limit exceeded: {e}",
                status_code=429,
                provider=self.provider_name,
            ) from e

        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic API timeout: {e}") from e

        except anthropic.BadRequestError as e:
            raise LLMInvalidRequestError(
                f"Invalid request to Anthropic API: {e}",
                status_code=400,
                provider=self.provider_name,
            ) from e

        except anthropic.APIError as e:
            # Catch-all for other API errors
            raise LLMAPIError(f"Anthropic API error: {e}", provider=self.provider_name) from e

        except Exception as e:
            # Catch any unexpected errors
            raise LLMAPIError(
                f"Unexpected error calling Anthropic API: {e}", provider=self.provider_name
            ) from e
