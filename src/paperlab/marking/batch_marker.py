"""Batch question marking with parallel execution.

Coordinates marking of multiple submissions in parallel using thread pools.
Each worker creates its own database connection for thread safety.

This module implements Phase B of the two-phase marking workflow:
- Phase A: Create submissions (request_builder.py)
- Phase B: Mark submissions (this module)

Design principles:
- Simple orchestration - delegates to QuestionMarker for each submission
- Parallel execution - uses ThreadPoolExecutor for concurrent API calls
- Error isolation - one submission failure doesn't stop the batch
- Thread-safe - each worker gets its own database connection
- Rate-limit aware - configurable max_workers to stay within API limits
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from paperlab.config import settings
from paperlab.config.constants import LLMProviders
from paperlab.data.database import connection
from paperlab.marking.marker import QuestionMarker

if TYPE_CHECKING:
    from paperlab.services.llm_client import LLMClient


@dataclass
class BatchMarkingResult:
    """Results from batch marking operation.

    Provides summary of successful and failed marking attempts,
    along with timing information for performance analysis.

    Attributes:
        successful: List of marking_attempt_id for successful markings
        failed: List of (submission_id, exception) tuples for failed markings
        total_duration_ms: Total wall-clock time for batch (milliseconds)
    """

    successful: list[int]  # marking_attempt_ids
    failed: list[tuple[int, Exception]]  # (submission_id, exception) pairs
    total_duration_ms: int


class BatchMarker:
    """Marks multiple submissions in parallel using thread pool.

    Orchestrates parallel marking of multiple submissions by:
    1. Creating thread pool with configurable worker count
    2. Each worker creates its own database connection (thread-safe)
    3. Each worker calls QuestionMarker.mark_submission() independently
    4. Results collected as they complete (non-blocking)
    5. Errors isolated (one failure doesn't stop batch)

    Thread safety:
    - Each worker creates its own database connection
    - No shared mutable state between workers
    - QuestionMarker is stateless (safe for parallel use)

    Rate limiting:
    - Provider-specific defaults optimize for each API's limits:
      * Anthropic: 5 workers (Tier 1: 50 req/min)
      * OpenAI: 50 workers (Tier 1: 500 req/min)
    - Automatic provider detection from llm_client
    - Exponential backoff with jitter prevents thundering herd
    - Each provider's rate limits enforced via retry logic in LLMClient

    Example:
        >>> from paperlab.services.claude_client import ClaudeClient
        >>> llm_client = ClaudeClient(api_key="...")
        >>> batch_marker = BatchMarker(llm_client)
        >>> submission_ids = [1, 2, 3]  # Created in Phase A
        >>> result = batch_marker.mark_batch(
        ...     submission_ids=submission_ids,
        ...     llm_model_id=1,
        ...     max_workers=5
        ... )
        >>> print(f"Marked {len(result.successful)} submissions successfully")
        >>> print(f"Failed {len(result.failed)} submissions")
    """

    def __init__(self, llm_client: "LLMClient") -> None:
        """Initialize with LLM client dependency.

        Args:
            llm_client: Client for calling LLM API (injected for testing)
                       Must implement LLMClient Protocol
        """
        self.llm_client = llm_client

    def mark_batch(
        self,
        submission_ids: list[int],
        llm_model_id: int,
        max_workers: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        db_path: Path | None = None,
    ) -> BatchMarkingResult:
        """Mark multiple submissions in parallel.

        Each worker:
        1. Creates its own database connection
        2. Calls QuestionMarker.mark_submission()
        3. Closes connection when done

        Execution:
        - Submissions marked in parallel (up to max_workers concurrent)
        - Results collected as they complete (non-blocking)
        - Errors isolated (continue marking remaining submissions)

        Args:
            submission_ids: List of submission IDs to mark (from test_execution.db)
            llm_model_id: Database ID of LLM model to use for marking
            max_workers: Maximum parallel workers (default: provider-specific from settings)
                        None = auto-detect provider and use optimal default:
                          - Anthropic: settings.batch_max_workers_anthropic (default: 5)
                          - OpenAI: settings.batch_max_workers_openai (default: 50)
                        Override with integer for manual tuning based on API tier
            progress_callback: Optional callback(completed, total) called after each completion
            db_path: Path to database (default: settings.db_path for production,
                    or specify test_execution.db path for test execution)

        Returns:
            BatchMarkingResult with success/failure breakdown and timing

        Raises:
            ValueError: If submission_ids empty or max_workers invalid

        Example:
            >>> def progress(completed, total):
            ...     print(f"Progress: {completed}/{total}")
            >>> result = batch_marker.mark_batch(
            ...     submission_ids=[1, 2, 3],
            ...     llm_model_id=1,
            ...     max_workers=5,
            ...     progress_callback=progress
            ... )
        """
        # Validate inputs
        if not submission_ids:
            raise ValueError("Cannot mark empty batch - submission_ids list is empty")

        # Use provider-specific settings default if not specified
        if max_workers is None:
            # Detect provider from LLM client and use provider-specific limits
            provider = self.llm_client.provider_name.lower()

            if provider == LLMProviders.ANTHROPIC:
                max_workers = settings.batch_max_workers_anthropic
            elif provider == LLMProviders.OPENAI:
                max_workers = settings.batch_max_workers_openai
            else:
                # Fallback for unknown providers (conservative default)
                max_workers = settings.batch_max_workers

        if max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {max_workers}")

        # Track results
        successful: list[int] = []  # marking_attempt_ids
        failed: list[tuple[int, Exception]] = []  # (submission_id, exception) pairs
        completed = 0
        start_time = perf_counter()

        # Create marker (stateless, safe to share reference across threads)
        marker = QuestionMarker(self.llm_client)

        def mark_with_connection(submission_id: int) -> int:
            """Worker function: create connection, mark submission, cleanup.

            Each thread calls this function independently.
            Creates its own database connection for thread safety.

            Args:
                submission_id: Submission ID to mark

            Returns:
                marking_attempt_id from successful marking

            Raises:
                Any exception from marking pipeline (caught by executor)
            """
            # Each worker gets its own connection (thread-safe)
            with connection(db_path) as conn:
                marking_attempt_id = marker.mark_submission(submission_id, llm_model_id, conn)
                conn.commit()  # CRITICAL: Commit transaction before connection closes
                return marking_attempt_id

        # Execute in parallel using thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks to thread pool
            future_to_submission_id = {
                executor.submit(mark_with_connection, sub_id): sub_id for sub_id in submission_ids
            }

            # Collect results as they complete (non-blocking)
            for future in as_completed(future_to_submission_id):
                submission_id = future_to_submission_id[future]
                completed += 1

                try:
                    # Get result from completed future
                    marking_attempt_id = future.result()
                    successful.append(marking_attempt_id)

                except Exception as e:
                    # Isolate errors - continue marking remaining submissions
                    failed.append((submission_id, e))

                # Notify progress if callback provided
                if progress_callback:
                    progress_callback(completed, len(submission_ids))

        # Calculate total duration
        total_duration_ms = int((perf_counter() - start_time) * 1000)

        return BatchMarkingResult(
            successful=successful,
            failed=failed,
            total_duration_ms=total_duration_ms,
        )
