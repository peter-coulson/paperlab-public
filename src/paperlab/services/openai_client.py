"""OpenAI API client implementation.

Provides OpenAI-specific implementation of the LLM client interface.

Architecture:
- Owns prompt formatting: minimal prompt + JSON schema for structured outputs
- Schema generation is internal to this client (not external dependency)
- Uses response_format param for guaranteed JSON compliance

Design principles:
- Inherits shared logic from BaseLLMClient
- Maps OpenAI SDK exceptions to our exception hierarchy
- Uses OpenAI's vision API for image-based marking
- Follows best practices from context/api-docs/openai.md
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import openai
from openai import AuthenticationError, BadRequestError, OpenAI, RateLimitError

from paperlab.config import IMAGE_DETAIL_LEVEL, LLMProviders, settings
from paperlab.marking.models import MarkingRequest
from paperlab.services.llm_client import (
    BaseLLMClient,
    LLMAPIError,
    LLMAuthenticationError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam
    from openai.types.chat.chat_completion_content_part_image_param import (
        ChatCompletionContentPartImageParam,
    )
    from openai.types.chat.chat_completion_content_part_text_param import (
        ChatCompletionContentPartTextParam,
    )


class OpenAIClient(BaseLLMClient):
    """OpenAI API client (also supports OpenAI-compatible APIs).

    Implements LLM marking using OpenAI's Chat Completions API with vision support.
    Can also be used for OpenAI-compatible providers (e.g., Google Gemini) via
    the `base_url` parameter.

    Prompt Formatting:
        OpenAI supports Structured Outputs (response_format with JSON schema).
        This client owns the formatting logic:
        - System prompt: Base instructions (no JSON example needed)
        - User prompt: Abbreviations + question + brief format note
        - API param: JSON schema generated from expected_structure

    Features:
    - Vision API for analyzing student work images
    - Structured JSON output via response_format param
    - Error mapping to standardized exception hierarchy
    - Retry logic with exponential backoff (inherited)
    - OpenAI-compatible API support via base_url parameter

    Usage:
        >>> from paperlab.services.openai_client import OpenAIClient
        >>> from paperlab.marking.prompt_builder import PromptBuilder
        >>> client = OpenAIClient(api_key="sk-...")
        >>> request = builder.build_marking_request(question_id=1)
        >>> response = client.mark_question(request, images)

    Reference:
        See context/api-docs/openai.md for implementation details
    """

    def __init__(
        self,
        api_key: str,
        model_identifier: str,
        base_url: str | None = None,
        provider_name: str = LLMProviders.OPENAI,
    ) -> None:
        """Initialize OpenAI client.

        Args:
            api_key: API key for the provider
            model_identifier: Model to use (e.g., 'gpt-4o', 'gemini-2.0-flash')
            base_url: Optional base URL for OpenAI-compatible APIs
                      (e.g., Gemini's https://generativelanguage.googleapis.com/v1beta/openai/)
            provider_name: Provider name for logging/error messages (defaults to OpenAI)

        Raises:
            ValueError: If API key invalid
        """
        # Initialize base client with settings from config
        super().__init__(
            api_key=api_key,
            model_identifier=model_identifier,
            max_retries=settings.llm_max_retries,
            timeout=settings.llm_timeout,
            provider_name=provider_name,
        )

        # Initialize OpenAI SDK client (with optional custom base_url)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # Cache for last API response (used to extract token usage)
        self.last_message: openai.types.chat.ChatCompletion | None = None

    def mark_question(
        self,
        request: MarkingRequest,
        image_paths: list[Path | str],
    ) -> str:
        """Mark a question using OpenAI API.

        Formats the MarkingRequest into OpenAI's format:
        - System prompt with base instructions
        - User prompt with abbreviations + question + brief note
        - JSON schema passed via response_format param

        Args:
            request: MarkingRequest containing all prompt data
            image_paths: Local file paths or presigned URLs

        Returns:
            Raw text response from OpenAI (pure JSON)
        """
        # Format prompts for OpenAI
        system_prompt = self._format_system_prompt(request)
        user_prompt = self._format_user_prompt(request)

        # Generate schema from expected structure
        json_schema = self._generate_json_schema(request.expected_structure)

        # Call API with retry logic
        return self._mark_with_retry(system_prompt, user_prompt, image_paths, json_schema)

    def _format_system_prompt(self, request: MarkingRequest) -> str:
        """Format system prompt for OpenAI.

        OpenAI uses schema for format enforcement, so system prompt
        doesn't need JSON-specific instructions.

        Args:
            request: MarkingRequest with base system instructions

        Returns:
            System prompt (base instructions unchanged)
        """
        return request.system_instructions

    def _format_user_prompt(self, request: MarkingRequest) -> str:
        """Format user prompt for OpenAI (no JSON example needed).

        Args:
            request: MarkingRequest with abbreviations and question content

        Returns:
            User prompt with abbreviations, question, and brief format note
        """
        return f"""{request.abbreviations}

---

# Question and Mark Scheme

{request.question_content}

---

**Note:** Response format is enforced via JSON Schema. Provide a marking result for
EVERY criterion shown above. Each result must include:
- `criterion_id`: The exact criterion ID from the mark scheme
- `observation`: Internal reasoning about the student work (not shown to students)
- `feedback`: Direct, objective feedback stating whether criterion was met (user-facing)
- `marks_awarded`: Integer within the valid range (0 to maximum marks for that criterion)
- `confidence_score`: Float between 0.0 (very uncertain) and 1.0 (completely certain)"""

    def _generate_json_schema(
        self, expected_structure: dict[str, list[dict[str, int | str]]]
    ) -> dict[str, Any]:
        """Generate OpenAI JSON Schema from expected structure.

        Args:
            expected_structure: Dict with 'results' list of criterion info

        Returns:
            OpenAI JSON Schema dict with strict validation

        Raises:
            ValueError: If no markable criteria
        """
        results = expected_structure.get("results", [])

        # Validate we have criteria to mark
        if not results:
            raise ValueError(
                "Cannot generate schema: No markable criteria in expected_structure\n"
                "Note: GENERAL criteria are excluded (guidance only, not marked)"
            )

        # Collect criterion IDs and find max marks
        criterion_ids: list[int] = []
        max_marks = 0
        for criterion_info in results:
            criterion_ids.append(int(criterion_info["criterion_id"]))
            max_marks = max(max_marks, int(criterion_info["marks_available"]))

        # Build schema
        # Note: OpenAI Structured Outputs doesn't support oneOf, so we use enum for criterion_id
        # and a global max for marks_awarded. Runtime validation catches per-criterion limits.
        return {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "criterion_id": {
                                "type": "integer",
                                "enum": criterion_ids,
                            },
                            "observation": {
                                "type": "string",
                            },
                            "feedback": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "marks_awarded": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": max_marks,
                            },
                            "confidence_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                        },
                        "required": [
                            "criterion_id",
                            "observation",
                            "feedback",
                            "marks_awarded",
                            "confidence_score",
                        ],
                        "additionalProperties": False,
                    },
                    "minItems": len(criterion_ids),
                    "maxItems": len(criterion_ids),
                }
            },
            "required": ["results"],
            "additionalProperties": False,
        }

    def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path | str],
        *args: Any,
    ) -> str:
        """Call OpenAI API to mark a question.

        This method is called by _mark_with_retry after validation.

        Args:
            system_prompt: System-level instructions for GPT
            user_prompt: Question-specific prompt
            image_paths: Local file paths or presigned URLs (already validated)
            *args: First arg is json_schema if provided

        Returns:
            Raw text response from OpenAI

        Raises:
            LLMAPIError: If API call fails
            LLMAuthenticationError: If API key invalid
            LLMRateLimitError: If rate limit exceeded
            LLMTimeoutError: If request times out
            LLMInvalidRequestError: If request parameters invalid
        """
        # Extract json_schema from args if provided
        json_schema: dict[str, Any] | None = args[0] if args else None

        try:
            # Build content array with all images followed by text prompt
            # Format: [image1, image2, ..., text]
            content_parts: list[
                ChatCompletionContentPartImageParam | ChatCompletionContentPartTextParam
            ] = []

            # Add all images first (preserves sequence order)
            for image_path in image_paths:
                # Detect if URL or local path
                if isinstance(image_path, str) and image_path.startswith("https://"):
                    # Remote URL handling differs by provider:
                    # - OpenAI: Can fetch from presigned URLs directly
                    # - Gemini: Requires base64 data URLs (doesn't support arbitrary URLs)
                    if self.provider_name == LLMProviders.GOOGLE:
                        # Gemini: Fetch image and convert to base64 data URL
                        image_data, media_type = self._fetch_remote_image(image_path)
                        image_url = f"data:{media_type};base64,{image_data}"
                        image_block: ChatCompletionContentPartImageParam = {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": IMAGE_DETAIL_LEVEL,
                            },
                        }
                    else:
                        # OpenAI: Pass URL directly (API fetches it)
                        image_block = {
                            "type": "image_url",
                            "image_url": {
                                "url": image_path,
                                "detail": IMAGE_DETAIL_LEVEL,
                            },
                        }
                else:
                    # Local file - encode to data URL (existing logic)
                    if isinstance(image_path, str):
                        image_path = Path(image_path)

                    # Encode image to base64
                    image_data = self._encode_image(image_path)

                    # Determine media type from file extension
                    media_type = self._get_media_type(image_path)

                    # Build data URL for image (OpenAI format: data:image/jpeg;base64,{data})
                    image_url = f"data:{media_type};base64,{image_data}"

                    # Build image block
                    # OpenAI format differs from Anthropic:
                    # - Uses "image_url" type instead of "image"
                    # - Supports detail level for OCR quality
                    image_block = {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": IMAGE_DETAIL_LEVEL,  # "high" for better handwriting OCR
                        },
                    }
                content_parts.append(image_block)

            # Add text prompt after all images
            text_block: ChatCompletionContentPartTextParam = {
                "type": "text",
                "text": user_prompt,
            }
            content_parts.append(text_block)

            # Build messages array
            # OpenAI API expects list of messages with roles
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ]

            # Configure response format based on schema
            response_format: dict[str, Any]
            if json_schema:
                # Use Structured Outputs (strict schema validation)
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "marking_response",
                        "schema": json_schema,
                        "strict": True,  # Enforce exact compliance
                    },
                }
            else:
                # Fallback to basic JSON object mode (when no schema provided)
                response_format = {"type": "json_object"}

            # Call OpenAI API with response format
            # Type ignore needed: OpenAI SDK types don't match runtime API for response_format
            response = self.client.chat.completions.create(  # type: ignore[call-overload]
                model=self.model_identifier,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                messages=messages,
                response_format=response_format,
                timeout=self.timeout,
            )

            # Cache response for token usage extraction
            self.last_message = response

            # Extract text from response
            # OpenAI returns response.choices[0].message.content
            if not response.choices or len(response.choices) == 0:
                raise LLMAPIError("Empty response from OpenAI API", provider=self.provider_name)

            first_choice = response.choices[0]
            if not first_choice.message or not first_choice.message.content:
                raise LLMAPIError(
                    "No content in OpenAI response message", provider=self.provider_name
                )

            # Ensure we return a string (mypy doesn't know content is str)
            content = first_choice.message.content
            if not isinstance(content, str):
                raise LLMAPIError(
                    f"Expected string content, got {type(content)}", provider=self.provider_name
                )

            return content

        except AuthenticationError as e:
            raise LLMAuthenticationError(
                f"Invalid OpenAI API key: {e}", provider=self.provider_name
            ) from e

        except RateLimitError as e:
            raise LLMRateLimitError(
                f"OpenAI rate limit exceeded: {e}",
                status_code=429,
                provider=self.provider_name,
            ) from e

        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI API timeout: {e}") from e

        except BadRequestError as e:
            raise LLMInvalidRequestError(
                f"Invalid request to OpenAI API: {e}",
                status_code=400,
                provider=self.provider_name,
            ) from e

        except openai.APIError as e:
            # Catch-all for other API errors
            raise LLMAPIError(f"OpenAI API error: {e}", provider=self.provider_name) from e

        except Exception as e:
            # Catch any unexpected errors
            raise LLMAPIError(
                f"Unexpected error calling OpenAI API: {e}", provider=self.provider_name
            ) from e
