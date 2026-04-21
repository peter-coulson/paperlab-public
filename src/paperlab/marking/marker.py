"""Question marking orchestrator.

Coordinates the complete marking pipeline: prompt building, LLM calling,
response parsing, validation, and storage.

Architecture:
- Orchestration only - no provider-specific logic
- Delegates prompt building to PromptBuilder (returns MarkingRequest)
- Delegates formatting to LLM clients (each owns its format strategy)
- Clear data flow: submission → request → LLM → parse → validate → store

Design principles:
- Orchestration only - delegates all operations to specialized modules
- Connection provided by caller (dependency injection)
- Provider-agnostic - doesn't know about Claude/OpenAI differences
- Comprehensive error handling and verification
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from paperlab.config import ErrorMessages
from paperlab.data.repositories.marking import (
    llm_models,
    marking_attempts,
    question_marking_results,
    question_submissions,
    questions,
    submission_images,
)
from paperlab.data.storage import R2Storage
from paperlab.marking.exceptions import MarkingError
from paperlab.marking.parser import parse_llm_response
from paperlab.marking.prompt_builder import PromptBuilder

if TYPE_CHECKING:
    from paperlab.marking.models import MarkingRequest
    from paperlab.services.llm_client import LLMClient


@dataclass
class MarkingContext:
    """Context for tracking marking state during execution.

    Used to preserve state for error handling when exceptions occur
    at different points in the marking pipeline.
    """

    request: "MarkingRequest | None" = None
    raw_response: str | None = None


class QuestionMarker:
    """Orchestrates the marking of a single question submission.

    Architecture:
        - Provider-agnostic: doesn't know about Claude/OpenAI differences
        - Builds MarkingRequest via PromptBuilder
        - Passes request to LLM client (client handles formatting)
        - Parses and stores response

    Responsibilities:
    - Coordinate request building, LLM calling, parsing, storage
    - Track timing and metadata
    - Verify successful storage
    - Handle errors with clear messages

    Does NOT own:
    - Database connections (provided by caller)
    - LLM API calls (delegated to llm_client)
    - Prompt formatting (delegated to llm_client - each owns its format)
    - Response parsing (delegated to parser)
    - Data storage (delegated to repositories)

    Example:
        >>> from paperlab.data.database import connection
        >>> from paperlab.services.claude_client import ClaudeClient
        >>> llm_client = ClaudeClient(api_key="...")
        >>> marker = QuestionMarker(llm_client)
        >>> with connection() as conn:
        ...     attempt_id = marker.mark_submission(
        ...         submission_id=42,
        ...         llm_model_id=1,
        ...         conn=conn
        ...     )
        >>> print(f"Stored as attempt ID: {attempt_id}")
    """

    def __init__(self, llm_client: "LLMClient", r2_storage: R2Storage | None = None) -> None:
        """Initialize with LLM client dependency.

        Args:
            llm_client: Client for calling LLM API (injected for testing)
                       Must implement LLMClient Protocol
            r2_storage: R2 storage client (injected for testing, created if None)
        """
        self.llm_client = llm_client
        self.r2_storage = r2_storage or R2Storage()

    def mark_submission(
        self, submission_id: int, llm_model_id: int, conn: sqlite3.Connection
    ) -> int:
        """Mark an existing submission using LLM.

        This is PHASE B of the upload workflow: mark existing submission.
        Submission must already exist (created via submissions pipeline).

        Flow:
            1. Validate inputs (submission, model exist)
            2. Load submission images
            3. Build MarkingRequest (provider-agnostic)
            4. Call LLM client (client handles formatting)
            5. Parse and store response

        Args:
            submission_id: Database ID of submission to mark
            llm_model_id: Database ID of LLM model to use
            conn: Database connection (transaction managed by caller)

        Returns:
            marking_attempt_id: Database ID of marking attempt

        Raises:
            ValueError: If submission or model not found
            RuntimeError: If storage verification fails
        """
        # Validate inputs
        question_id = self._validate_marking_inputs(submission_id, llm_model_id, conn)

        # Load images
        image_paths = self._load_submission_images(submission_id, conn)

        # Start timer for error tracking (before any operations that might fail)
        start_time = perf_counter()

        # Create context for error handling
        ctx = MarkingContext()

        try:
            # Build marking request (provider-agnostic)
            ctx.request = self._build_marking_request(question_id, conn)

            # Call LLM (client handles formatting internally)
            ctx.raw_response = self.llm_client.mark_question(
                request=ctx.request,
                image_paths=image_paths,
            )
            elapsed_ms = int((perf_counter() - start_time) * 1000)

            # Parse and store success
            return self._handle_success(
                submission_id=submission_id,
                llm_model_id=llm_model_id,
                question_id=question_id,
                raw_response=ctx.raw_response,
                request=ctx.request,
                elapsed_ms=elapsed_ms,
                conn=conn,
            )

        except ClientError as e:
            return self._handle_r2_error(e, submission_id, llm_model_id, ctx, start_time, conn)
        except (ValueError, json.JSONDecodeError) as e:
            return self._handle_parse_error(e, submission_id, llm_model_id, ctx, start_time, conn)
        except Exception as e:
            return self._handle_llm_error(e, submission_id, llm_model_id, ctx, start_time, conn)

    def _validate_marking_inputs(
        self, submission_id: int, llm_model_id: int, conn: sqlite3.Connection
    ) -> int:
        """Validate submission, question, and model exist.

        Args:
            submission_id: Database ID of submission to mark
            llm_model_id: Database ID of LLM model to use
            conn: Database connection

        Returns:
            question_id: Database ID of question being marked

        Raises:
            ValueError: If submission, question, or model not found, or duplicate marking detected
        """
        # Validation: Submission exists
        submission = question_submissions.get_by_id(submission_id, conn)
        if not submission:
            raise ValueError(ErrorMessages.SUBMISSION_NOT_FOUND.format(submission_id=submission_id))

        question_id: int = submission["question_id"]

        # Validation: Question exists
        try:
            questions.get_question_structure(question_id, conn)
        except ValueError as e:
            raise ValueError(
                ErrorMessages.QUESTION_NOT_FOUND.format(question_id=question_id)
            ) from e

        # Validation: Model exists
        try:
            llm_models.get_by_id(llm_model_id, conn)
        except ValueError as e:
            raise ValueError(f"LLM model ID {llm_model_id} not found") from e

        # Check for existing successful marking (prevent duplicate API calls)
        if marking_attempts.has_successful_attempt(submission_id, conn):
            raise ValueError(
                f"Submission {submission_id} already has successful marking. "
                f"Duplicate marking not allowed."
            )

        return question_id

    def _load_submission_images(
        self, submission_id: int, conn: sqlite3.Connection
    ) -> list[Path | str]:
        """Load and resolve submission images to LLM-compatible format.

        Args:
            submission_id: Database ID of submission
            conn: Database connection

        Returns:
            List of image paths (Path for local, str for URLs)

        Raises:
            ValueError: If submission has no images
            FileNotFoundError: If local image file not found
            ClientError: If R2 presigned URL generation fails
        """
        # Load images from submission
        images = submission_images.get_images_for_submission(submission_id, conn)
        if not images:
            raise ValueError(f"Submission {submission_id} has no images")

        # Convert logical paths to LLM-compatible format (Path or URL)
        image_paths: list[Path | str] = []
        for img in images:
            logical_path = img["image_path"]
            resolved_path = self._resolve_image_path(logical_path)  # May raise ClientError

            # CRITICAL: Validate file exists (skip for URLs)
            if isinstance(resolved_path, Path) and not resolved_path.exists():
                raise FileNotFoundError(
                    f"Image file not found for submission {submission_id}: "
                    f"{resolved_path} (logical path: {logical_path})"
                )

            image_paths.append(resolved_path)

        return image_paths

    def _build_marking_request(
        self, question_id: int, conn: sqlite3.Connection
    ) -> "MarkingRequest":
        """Build marking request for question (provider-agnostic).

        Args:
            question_id: Database ID of question
            conn: Database connection

        Returns:
            MarkingRequest containing all data for marking
        """
        prompt_builder = PromptBuilder(conn)
        return prompt_builder.build_marking_request(question_id=question_id)

    def _extract_token_usage(self) -> tuple[int, int]:
        """Extract token usage from last LLM response.

        Handles both Anthropic and OpenAI response formats.

        Returns:
            Tuple of (input_tokens, output_tokens) - (0, 0) if not available
        """
        if not (hasattr(self.llm_client, "last_message") and self.llm_client.last_message):
            return (0, 0)

        llm_message = self.llm_client.last_message
        if not hasattr(llm_message, "usage"):
            return (0, 0)

        usage = llm_message.usage

        # Anthropic format: usage.input_tokens, usage.output_tokens
        if hasattr(usage, "input_tokens"):
            return (usage.input_tokens, usage.output_tokens)

        # OpenAI format: usage.prompt_tokens, usage.completion_tokens
        if hasattr(usage, "prompt_tokens"):
            return (usage.prompt_tokens, usage.completion_tokens)

        return (0, 0)

    def _handle_success(
        self,
        submission_id: int,
        llm_model_id: int,
        question_id: int,
        raw_response: str,
        request: "MarkingRequest",
        elapsed_ms: int,
        conn: sqlite3.Connection,
    ) -> int:
        """Handle successful LLM marking response.

        Parses response, stores marking attempt and results, verifies storage.

        Args:
            submission_id: Database ID of submission
            llm_model_id: Database ID of LLM model
            question_id: Database ID of question
            raw_response: Raw LLM response text
            request: MarkingRequest used for marking
            elapsed_ms: Time taken for LLM call
            conn: Database connection

        Returns:
            marking_attempt_id: Database ID of marking attempt

        Raises:
            ValueError: If parsing fails
            json.JSONDecodeError: If response contains invalid JSON
            RuntimeError: If storage verification fails
        """
        # Parse response (may raise ValueError/JSONDecodeError)
        json_str, parsed_response = parse_llm_response(
            raw_response=raw_response,
            question_id=question_id,
            conn=conn,
        )

        # Extract token usage from cached LLM response object
        input_tokens, output_tokens = self._extract_token_usage()

        # Store SUCCESS marking attempt
        # Note: We store the base system instructions and abbreviated question content
        # The actual formatted prompts depend on the client, but this is sufficient for debugging
        attempt_id = marking_attempts.create(
            submission_id=submission_id,
            llm_model_id=llm_model_id,
            status="success",
            processing_time_ms=elapsed_ms,
            system_prompt=request.system_instructions,
            user_prompt=f"{request.abbreviations}\n\n{request.question_content}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw_response=raw_response,
            response_received=json_str,
            error_message=None,
            conn=conn,
        )

        # Store results
        # Convert Pydantic models to dict primitives (repository has no domain dependencies)
        from paperlab.constants.fields import CriterionFields

        results_data = [
            {
                CriterionFields.CRITERION_ID: result.criterion_id,
                CriterionFields.OBSERVATION: result.observation,
                CriterionFields.MARKS_AWARDED: result.marks_awarded,
                CriterionFields.FEEDBACK: result.feedback,
                CriterionFields.CONFIDENCE_SCORE: result.confidence_score,
            }
            for result in parsed_response.results
        ]
        question_marking_results.create_results_batch(
            marking_attempt_id=attempt_id,
            results=results_data,
            conn=conn,
        )

        # Verify storage
        if not marking_attempts.exists(attempt_id, conn):
            raise RuntimeError(
                f"Failed to verify marking attempt storage (attempt_id={attempt_id})"
            )

        result_count = question_marking_results.count_results_for_attempt(attempt_id, conn)
        expected_results = len(results_data)
        if result_count != expected_results:
            raise RuntimeError(
                f"Results storage verification failed: expected {expected_results}, "
                f"got {result_count}"
            )

        return attempt_id

    def _handle_r2_error(
        self,
        error: ClientError,
        submission_id: int,
        llm_model_id: int,
        ctx: MarkingContext,
        start_time: float,
        conn: sqlite3.Connection,
    ) -> int:
        """Handle R2 presigned URL generation error.

        This error occurs BEFORE LLM call, so no raw_response exists.

        Args:
            error: boto3 ClientError
            submission_id: Database ID of submission
            llm_model_id: Database ID of LLM model
            ctx: Marking context (tracks state)
            start_time: Start time for elapsed calculation
            conn: Database connection

        Returns:
            marking_attempt_id: Database ID of failed attempt

        Raises:
            MarkingError: Always raised after storing failed attempt
        """
        elapsed_ms = int((perf_counter() - start_time) * 1000)

        # Extract error details from boto3 ClientError
        error_code = (
            error.response.get("Error", {}).get("Code", "Unknown")
            if hasattr(error, "response")
            else "Unknown"
        )
        error_msg = str(error)

        # Extract prompts from context if available
        system_prompt = ctx.request.system_instructions if ctx.request else ""
        user_prompt = (
            f"{ctx.request.abbreviations}\n\n{ctx.request.question_content}" if ctx.request else ""
        )

        _attempt_id = marking_attempts.create(
            submission_id=submission_id,
            llm_model_id=llm_model_id,
            status="llm_error",  # Treat as retryable error (like LLM rate limits)
            processing_time_ms=elapsed_ms,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            input_tokens=0,
            output_tokens=0,
            raw_response=None,
            response_received=None,
            error_message=f"R2 presigned URL generation failed [{error_code}]: {error_msg}",
            conn=conn,
        )
        # Raise MarkingError (CLI commits failed attempt for observability)
        raise MarkingError(
            f"R2 presigned URL generation failed [{error_code}]: {error_msg}"
        ) from error

    def _handle_parse_error(
        self,
        error: ValueError | json.JSONDecodeError,
        submission_id: int,
        llm_model_id: int,
        ctx: MarkingContext,
        start_time: float,
        conn: sqlite3.Connection,
    ) -> int:
        """Handle LLM response parsing error.

        raw_response may exist if LLM call succeeded but parsing failed.

        Args:
            error: Parsing exception
            submission_id: Database ID of submission
            llm_model_id: Database ID of LLM model
            ctx: Marking context (tracks state)
            start_time: Start time for elapsed calculation
            conn: Database connection

        Returns:
            marking_attempt_id: Database ID of failed attempt

        Raises:
            MarkingError: Always raised after storing failed attempt
        """
        elapsed_ms = int((perf_counter() - start_time) * 1000)

        # Extract token usage if LLM call succeeded
        input_tokens, output_tokens = self._extract_token_usage()

        # Extract prompts from context if available
        system_prompt = ctx.request.system_instructions if ctx.request else ""
        user_prompt = (
            f"{ctx.request.abbreviations}\n\n{ctx.request.question_content}" if ctx.request else ""
        )

        _attempt_id = marking_attempts.create(
            submission_id=submission_id,
            llm_model_id=llm_model_id,
            status="parse_error",
            processing_time_ms=elapsed_ms,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw_response=ctx.raw_response,
            response_received=None,
            error_message=f"Parse error: {str(error)}",
            conn=conn,
        )
        # Raise MarkingError (CLI commits failed attempt for observability)
        raise MarkingError(f"Parse error: {str(error)}") from error

    def _handle_llm_error(
        self,
        error: Exception,
        submission_id: int,
        llm_model_id: int,
        ctx: MarkingContext,
        start_time: float,
        conn: sqlite3.Connection,
    ) -> int:
        """Handle generic LLM errors (rate limit, timeout, auth, network).

        raw_response may not exist if LLM call never completed.

        Args:
            error: Generic exception
            submission_id: Database ID of submission
            llm_model_id: Database ID of LLM model
            ctx: Marking context (tracks state)
            start_time: Start time for elapsed calculation
            conn: Database connection

        Returns:
            marking_attempt_id: Database ID of failed attempt

        Raises:
            MarkingError: Always raised after storing failed attempt
        """
        elapsed_ms = int((perf_counter() - start_time) * 1000)

        # Determine error type from exception
        error_type = "llm_error"
        if "rate" in str(error).lower() or "429" in str(error):
            error_type = "rate_limit"
        elif "timeout" in str(error).lower() or "timed out" in str(error).lower():
            error_type = "timeout"

        # Extract prompts from context if available
        system_prompt = ctx.request.system_instructions if ctx.request else ""
        user_prompt = (
            f"{ctx.request.abbreviations}\n\n{ctx.request.question_content}" if ctx.request else ""
        )

        _attempt_id = marking_attempts.create(
            submission_id=submission_id,
            llm_model_id=llm_model_id,
            status=error_type,
            processing_time_ms=elapsed_ms,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            input_tokens=0,
            output_tokens=0,
            raw_response=ctx.raw_response,
            response_received=None,
            error_message=str(error),
            conn=conn,
        )
        # Raise MarkingError (CLI commits failed attempt for observability)
        raise MarkingError(str(error)) from error

    def _resolve_image_path(self, logical_path: str) -> Path | str:
        """Resolve logical path to LLM-compatible format.

        Handles both local paths (eval) and R2 paths (production).

        Args:
            logical_path: Logical path from database (local or R2 key)

        Returns:
            - R2 path → presigned URL (str)
            - Local path → absolute Path (Path)

        Raises:
            ClientError: If R2 URL generation fails (bubbles up to caller)
            ValueError: If R2 path invalid
            FileNotFoundError: If local path doesn't exist (checked by caller)
        """
        from paperlab.loaders.path_utils import is_r2_path, to_absolute_path

        if is_r2_path(logical_path):
            # R2 path - generate presigned URL for LLM fetching
            # May raise ClientError - caller handles this
            return self.r2_storage.generate_presigned_url(
                remote_key=logical_path,
                expiry_seconds=86400,  # 24 hours - safe for batch marking + retries
            )
        else:
            # Local path - convert to absolute path (existing behavior)
            return to_absolute_path(logical_path)
