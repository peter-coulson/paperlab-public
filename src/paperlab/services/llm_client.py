"""LLM client interface and shared implementation.

Provides:
- LLMClient Protocol: Interface contract for all LLM providers
- BaseLLMClient: Shared implementation (retry logic, validation, error handling)
- Exception hierarchy: Typed errors for different failure modes

Architecture:
- Each client accepts MarkingRequest (provider-agnostic domain object)
- Each client formats the request for its specific API (prompt + schema/params)
- Marker orchestrator doesn't know about provider differences

Design principles:
- Protocol for interface (duck typing, no coupling between providers)
- Base class for code reuse (DRY)
- Provider-specific logic in subclasses (claude_client.py, openai_client.py)
- Fail fast with clear errors
"""

from __future__ import annotations

import base64
import random
import time
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlparse

import httpx

from paperlab.config import (
    SUPPORTED_IMAGE_FORMATS,
    ErrorMessages,
    ImageMediaType,
    ImageSequence,
    ImageValidationLimits,
    ResponseValidationLimits,
    settings,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from paperlab.marking.models import MarkingRequest

# ============================================================================
# Exception Hierarchy
# ============================================================================


class LLMError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMAPIError(LLMError):
    """API returned an error response.

    Attributes:
        status_code: HTTP status code if available
        provider: Name of the provider that failed
    """

    def __init__(
        self, message: str, status_code: int | None = None, provider: str | None = None
    ) -> None:
        self.status_code = status_code
        self.provider = provider
        super().__init__(message)


class LLMRateLimitError(LLMAPIError):
    """Rate limit exceeded (retryable with backoff)."""

    pass


class LLMTimeoutError(LLMError):
    """Request timed out (retryable)."""

    pass


class LLMAuthenticationError(LLMAPIError):
    """Invalid API key (not retryable)."""

    pass


class LLMInvalidRequestError(LLMAPIError):
    """Invalid request parameters (not retryable)."""

    pass


# ============================================================================
# Helper Functions
# ============================================================================


def _format_image_error(idx: int, total: int, message: str) -> str:
    """Format image validation error with sequence context.

    Args:
        idx: Current image index (1-indexed)
        total: Total number of images
        message: Error message to append

    Returns:
        Formatted error string: "Image {idx}/{total} - {message}"

    Example:
        >>> _format_image_error(2, 5, "file not found")
        'Image 2/5 - file not found'
    """
    return f"Image {idx}/{total} - {message}"


# ============================================================================
# Protocol (Interface Contract)
# ============================================================================


class LLMClient(Protocol):
    """Interface for LLM providers.

    All LLM clients must implement mark_question() method and expose provider_name.
    No inheritance required - structural typing (duck typing with type hints).

    Architecture:
        - Each client accepts MarkingRequest (provider-agnostic domain object)
        - Each client is responsible for formatting into its API format
        - Marker orchestrator doesn't need to know about provider differences

    Usage:
        >>> from paperlab.services.claude_client import ClaudeClient
        >>> from paperlab.marking.prompt_builder import PromptBuilder
        >>> client = ClaudeClient(api_key="sk-ant-...")
        >>> request = builder.build_marking_request(question_id=1)
        >>> response = client.mark_question(request, [Path("work.jpg")])
        >>> print(client.provider_name)  # "anthropic"
    """

    provider_name: str

    def mark_question(
        self,
        request: MarkingRequest,
        image_paths: list[Path | str],
    ) -> str:
        """Mark a question using the LLM.

        Each provider implements this differently:
        - Claude: Formats prompt with embedded JSON example
        - OpenAI: Formats prompt with schema in response_format param

        Args:
            request: MarkingRequest containing all prompt data (provider-agnostic)
            image_paths: Local file paths (Path) OR presigned URLs (str)

        Returns:
            Raw text response from LLM (JSON extraction handled by parser)

        Raises:
            LLMError: If API call fails (see exception hierarchy for specifics)
        """
        ...


# ============================================================================
# Base Implementation (Shared Logic)
# ============================================================================


class BaseLLMClient:
    """Shared implementation for LLM clients.

    Provides:
    - Retry logic with exponential backoff
    - Response validation
    - Image encoding and validation
    - Error classification

    Subclasses implement:
    - mark_question(): Format request and call API
    - _call_api(): Provider-specific API call

    Architecture:
        Each subclass owns its prompt formatting strategy:
        - ClaudeClient: Embeds JSON example in user prompt
        - OpenAIClient: Uses response_format param with schema

    Example:
        >>> class ClaudeClient(BaseLLMClient):
        ...     def mark_question(self, request, images):
        ...         # Format prompt with JSON example
        ...         user_prompt = self._format_prompt(request)
        ...         return self._mark_with_retry(system, user_prompt, images)
    """

    def __init__(
        self,
        api_key: str,
        model_identifier: str,
        max_retries: int = 3,
        timeout: int = 120,
        provider_name: str = "unknown",
    ) -> None:
        """Initialize LLM client.

        Args:
            api_key: API key for the provider
            model_identifier: Model to use (e.g., 'claude-sonnet-4-5', 'gpt-4o')
            max_retries: Maximum retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 120)
            provider_name: Name of provider for error messages

        Raises:
            ValueError: If parameters invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        if not model_identifier:
            raise ValueError("Model identifier cannot be empty")

        if max_retries < 0 or max_retries > 10:
            raise ValueError(f"max_retries must be between 0 and 10, got {max_retries}")

        if timeout < 10 or timeout > 600:
            raise ValueError(f"timeout must be between 10 and 600 seconds, got {timeout}")

        self.api_key = api_key
        self.model_identifier = model_identifier
        self.max_retries = max_retries
        self.timeout = timeout
        self.provider_name = provider_name

    def mark_question(
        self,
        request: MarkingRequest,
        image_paths: list[Path | str],
    ) -> str:
        """Mark a question using LLM.

        Default implementation - subclasses SHOULD override to add formatting.

        Args:
            request: MarkingRequest containing all prompt data
            image_paths: Local file paths (Path) OR presigned URLs (str)

        Returns:
            Raw response text from LLM

        Raises:
            LLMError: If API call fails after retries
            ValueError: If no images provided or images invalid
            NotImplementedError: If subclass doesn't override
        """
        raise NotImplementedError(
            "Subclasses must implement mark_question() with provider-specific formatting"
        )

    def _mark_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: list[Path | str],
        *extra_args: Any,
    ) -> str:
        """Execute marking with validation and retry logic.

        Common implementation used by all providers. Validates images,
        calls API with retry, and validates response.

        Args:
            system_prompt: System-level instructions
            user_prompt: Question-specific prompt (already formatted by client)
            image_paths: Local file paths or presigned URLs
            *extra_args: Additional arguments passed to _call_api (e.g., schema)

        Returns:
            Raw response text from LLM

        Raises:
            LLMError: If API call fails after retries
            ValueError: If images invalid
        """
        # Validate all images before any API calls
        self._validate_images(image_paths)

        # Call API with retry logic
        response = self._retry_with_backoff(
            self._call_api, system_prompt, user_prompt, image_paths, *extra_args
        )

        # Validate and return response
        return self._validate_response(response)

    def _call_api(
        self, system_prompt: str, user_prompt: str, image_paths: list[Path | str], *args: Any
    ) -> str:
        """Provider-specific API call implementation.

        Subclasses MUST override this method.

        Args:
            system_prompt: System-level instructions
            user_prompt: Question-specific prompt
            image_paths: Local file paths or presigned URLs (already validated)
            *args: Additional provider-specific arguments (e.g., schema for OpenAI)

        Returns:
            Raw response text from provider API

        Raises:
            NotImplementedError: If subclass doesn't override
            LLMAPIError: If API call fails
        """
        raise NotImplementedError("Subclasses must implement _call_api()")

    def _retry_with_backoff(self, fn: Callable[..., str], *args: Any) -> str:
        """Execute function with exponential backoff retry logic with jitter.

        Retries on:
        - LLMRateLimitError (rate limits)
        - LLMTimeoutError (timeouts)

        Does NOT retry on:
        - LLMAuthenticationError (invalid API key)
        - LLMInvalidRequestError (bad parameters)

        Backoff strategy:
        - Exponential base: 1s, 2s, 4s, 8s, ...
        - Random jitter: ±50% of base delay
        - Prevents thundering herd (workers retry at different times)

        Example delays:
        - Attempt 2: 0.5-1.5s (1s ± 50%)
        - Attempt 3: 1.0-3.0s (2s ± 50%)
        - Attempt 4: 2.0-6.0s (4s ± 50%)

        Args:
            fn: Function to call
            *args: Arguments to pass to function

        Returns:
            Result from function

        Raises:
            LLMError: If all retries exhausted or non-retryable error
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return fn(*args)

            except (LLMRateLimitError, LLMTimeoutError) as e:
                last_error = e

                # Don't sleep after last attempt
                if attempt < self.max_retries:
                    # Exponential backoff with random jitter
                    # Base: 2^attempt (1s, 2s, 4s, ...)
                    # Jitter: ±50% of base (prevents thundering herd)
                    base_sleep = 2**attempt
                    jitter = random.uniform(-base_sleep * 0.5, base_sleep * 0.5)
                    sleep_time = base_sleep + jitter

                    # Ensure non-negative sleep time
                    sleep_time = max(0.1, sleep_time)

                    time.sleep(sleep_time)

            except (LLMAuthenticationError, LLMInvalidRequestError) as e:
                # Don't retry on non-retryable errors
                # Add context about which attempt failed for debugging
                raise LLMError(
                    f"Non-retryable error on attempt {attempt + 1}/{self.max_retries + 1}: {e}"
                ) from e

        # All retries exhausted
        if last_error:
            raise LLMError(
                f"Failed after {self.max_retries + 1} attempts: {last_error}"
            ) from last_error

        # Should never reach here, but satisfy type checker
        raise LLMError("Unknown error in retry logic")

    def _validate_images(self, image_paths: list[Path | str]) -> None:
        """Validate image files before API call.

        For local paths (Path): Validates existence, size, security
        For URLs (str): Validates URL format and domain (security)

        Args:
            image_paths: Local file paths (Path) OR presigned URLs (str) - minimum 1 required

        Raises:
            ValueError: If no images provided or any image invalid
            FileNotFoundError: If any local image doesn't exist
        """
        # Minimum image requirement
        if not image_paths:
            raise ValueError(ErrorMessages.MIN_IMAGE_REQUIRED)

        # Validate each image
        for idx, image_path in enumerate(image_paths, start=ImageSequence.START):
            if isinstance(image_path, str):
                # Validate HTTPS URL
                self._validate_image_url(image_path, idx)
            else:
                # Validate local path
                self._validate_local_image(image_path, idx, len(image_paths))

    def _validate_image_url(self, image_url: str, idx: int) -> None:
        """Validate HTTPS image URL (comprehensive security validation).

        Args:
            image_url: URL to validate
            idx: Image index for error messages

        Raises:
            ValueError: If URL is invalid or insecure
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(image_url)

            # Validate scheme is HTTPS
            if parsed.scheme != "https":
                raise ValueError(
                    f"Image URL must use HTTPS protocol for image {idx}\n"
                    f"Got: {parsed.scheme}:// in {image_url}\n"
                    f"Security: Only HTTPS URLs accepted"
                )

            # Validate domain matches R2 pattern (presigned or public)
            # Two valid patterns:
            # 1. Presigned: *.r2.cloudflarestorage.com (M9 production)
            # 2. Public: pub-*.r2.dev (M7 beta)
            is_presigned = parsed.netloc.endswith(".r2.cloudflarestorage.com")
            is_public_dev = parsed.netloc.endswith(".r2.dev")

            if not parsed.netloc or not (is_presigned or is_public_dev):
                raise ValueError(
                    f"Untrusted image URL domain for image {idx}: {parsed.netloc}\n"
                    f"Only R2 URLs are allowed:\n"
                    f"  - *.r2.cloudflarestorage.com (presigned)\n"
                    f"  - pub-*.r2.dev (public dev)"
                )

            # Validate domain structure based on type
            domain_parts = parsed.netloc.split(".")

            if is_presigned:
                # Presigned URL: <bucket>.<account-id>.r2.cloudflarestorage.com (5 parts)
                if len(domain_parts) != 5:
                    raise ValueError(
                        f"Invalid R2 presigned domain structure for image {idx}: {parsed.netloc}\n"
                        f"Expected: <bucket>.<account-id>.r2.cloudflarestorage.com (5 parts)\n"
                        f"Got {len(domain_parts)} parts"
                    )

                # Validate last 3 parts are exactly "r2.cloudflarestorage.com"
                if domain_parts[-3:] != ["r2", "cloudflarestorage", "com"]:
                    raise ValueError(
                        f"Invalid R2 presigned domain for image {idx}: {parsed.netloc}\n"
                        f"Domain must end with r2.cloudflarestorage.com"
                    )

                # Presigned URLs must have query parameters (signatures)
                if not parsed.query:
                    url_preview = image_url[:100] + "..." if len(image_url) > 100 else image_url
                    raise ValueError(
                        f"Missing presigned URL signature for image {idx}\n"
                        f"URL appears to be missing authentication parameters: {url_preview}"
                    )

            elif is_public_dev:
                # Public dev URL: pub-<hash>.r2.dev (3 parts)
                if len(domain_parts) != 3:
                    raise ValueError(
                        f"Invalid R2 public dev domain structure for image {idx}: {parsed.netloc}\n"
                        f"Expected: pub-<hash>.r2.dev (3 parts)\n"
                        f"Got {len(domain_parts)} parts"
                    )

                # Validate last 2 parts are exactly "r2.dev"
                if domain_parts[-2:] != ["r2", "dev"]:
                    raise ValueError(
                        f"Invalid R2 public dev domain for image {idx}: {parsed.netloc}\n"
                        f"Domain must end with r2.dev"
                    )

                # Validate first part starts with "pub-"
                if not domain_parts[0].startswith("pub-"):
                    raise ValueError(
                        f"Invalid R2 public dev subdomain for image {idx}: {domain_parts[0]}\n"
                        f"Must start with 'pub-'"
                    )

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse URL for image {idx}: {e}") from e

    def _validate_local_image(self, image_path: Path, idx: int, total: int) -> None:
        """Validate local image file (existence, size, security).

        Args:
            image_path: Local file path
            idx: Image index for error messages
            total: Total number of images for error messages

        Raises:
            ValueError: If path is invalid or file has invalid size
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Security: Validate path is within allowed directories
            resolved_path = image_path.resolve()
            allowed_roots = [
                settings.project_root / "data",
                settings.project_root / "tmp",
            ]
            if not any(resolved_path.is_relative_to(root) for root in allowed_roots):
                raise ValueError(
                    f"Security: Image path outside allowed directories: {image_path}\n"
                    f"Allowed directories: {', '.join(str(r) for r in allowed_roots)}"
                )
        except (ValueError, OSError) as e:
            raise ValueError(
                _format_image_error(idx, total, f"Invalid path: {image_path}: {e}")
            ) from e

        if not image_path.exists():
            raise FileNotFoundError(_format_image_error(idx, total, f"not found: {image_path}"))

        if not image_path.is_file():
            raise ValueError(_format_image_error(idx, total, f"is not a file: {image_path}"))

        # Check file size
        file_size = image_path.stat().st_size
        min_size = ImageValidationLimits.MIN_SIZE_BYTES
        max_size = ImageValidationLimits.MAX_SIZE_BYTES

        if file_size < min_size:
            msg = f"too small ({file_size} bytes, minimum {min_size}): {image_path}"
            raise ValueError(_format_image_error(idx, total, msg))

        if file_size > max_size:
            msg = f"too large ({file_size} bytes, maximum {max_size}): {image_path}"
            raise ValueError(_format_image_error(idx, total, msg))

    def _validate_response(self, response: str) -> str:
        """Validate LLM response before returning.

        Args:
            response: Raw response from LLM

        Returns:
            Validated and cleaned response

        Raises:
            LLMError: If response invalid
        """
        if not response:
            raise LLMError(ErrorMessages.LLM_EMPTY_RESPONSE.format(provider=self.provider_name))

        # Strip whitespace
        response = response.strip()
        min_len = ResponseValidationLimits.MIN_LENGTH
        max_len = ResponseValidationLimits.MAX_LENGTH

        if len(response) < min_len:
            raise LLMError(
                ErrorMessages.LLM_RESPONSE_TOO_SHORT.format(
                    length=len(response),
                    min_len=min_len,
                    provider=self.provider_name,
                    preview=response[:100],
                )
            )

        if len(response) > max_len:
            raise LLMError(
                ErrorMessages.LLM_RESPONSE_TOO_LONG.format(
                    length=len(response),
                    max_len=max_len,
                    provider=self.provider_name,
                )
            )

        # Basic sanity check - response should contain JSON
        if "{" not in response and "[" not in response:
            raise LLMError(
                ErrorMessages.LLM_RESPONSE_NOT_JSON.format(
                    provider=self.provider_name,
                    preview=response[:200],
                )
            )

        return response

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string, preserving original format.

        Reads the image file directly without resizing or format conversion.
        This preserves full resolution for better accuracy on detailed content
        like hand-drawn diagrams.

        Args:
            image_path: Path to image file

        Returns:
            Base64-encoded string in original format

        Raises:
            ValueError: If image cannot be read or encoded
        """
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        except Exception as e:
            raise ValueError(f"Failed to encode image {image_path}: {e}") from e

    def _get_media_type(self, image_path: Path) -> ImageMediaType:
        """Determine media type from image file extension.

        Uses SUPPORTED_IMAGE_FORMATS from config for validation.

        Args:
            image_path: Path to image file

        Returns:
            Media type literal for LLM APIs

        Raises:
            ValueError: If file extension unsupported
        """
        extension = image_path.suffix.lower()

        if extension in SUPPORTED_IMAGE_FORMATS:
            return SUPPORTED_IMAGE_FORMATS[extension]
        else:
            supported_formats = ", ".join(sorted(SUPPORTED_IMAGE_FORMATS.keys()))
            raise ValueError(
                f"Unsupported image format: {extension}\nSupported formats: {supported_formats}"
            )

    def _fetch_remote_image(self, url: str) -> tuple[str, ImageMediaType]:
        """Fetch remote image and encode to base64.

        Used by providers that don't support fetching from arbitrary URLs
        (e.g., Gemini via OpenAI compatibility API).

        Args:
            url: Remote image URL (presigned or public)

        Returns:
            Tuple of (base64_data, media_type)

        Raises:
            LLMAPIError: If fetch fails or content type unsupported
        """
        try:
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()

            # Determine media type from Content-Type header or URL
            content_type = response.headers.get("content-type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                media_type: ImageMediaType = "image/jpeg"
            elif "png" in content_type:
                media_type = "image/png"
            elif "webp" in content_type:
                media_type = "image/webp"
            else:
                # Fallback: infer from URL path
                parsed = urlparse(url)
                path_lower = parsed.path.lower()
                if path_lower.endswith(".jpg") or path_lower.endswith(".jpeg"):
                    media_type = "image/jpeg"
                elif path_lower.endswith(".png"):
                    media_type = "image/png"
                elif path_lower.endswith(".webp"):
                    media_type = "image/webp"
                else:
                    raise LLMAPIError(
                        f"Cannot determine image type from URL: {url}",
                        provider=self.provider_name,
                    )

            # Encode to base64
            image_data = base64.b64encode(response.content).decode("utf-8")
            return image_data, media_type

        except httpx.HTTPStatusError as e:
            raise LLMAPIError(
                f"Failed to fetch image from {url}: HTTP {e.response.status_code}",
                provider=self.provider_name,
            ) from e
        except httpx.RequestError as e:
            raise LLMAPIError(
                f"Failed to fetch image from {url}: {e}",
                provider=self.provider_name,
            ) from e
