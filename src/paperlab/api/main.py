"""FastAPI application for PaperLab.

Home screen and Flow 2 (Selection + Upload) endpoints for M6 - Backend Integration.
API is transport layer - wraps existing domain logic.

M6 Simplifications:
- Temporary JWT auth (see auth.py)
- No pagination (return all attempts)
- Filtering handled client-side
- No caching
"""

import sqlite3

from botocore.exceptions import ClientError
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from paperlab.api.auth import clear_student_cache, get_current_student_id
from paperlab.api.constants import (
    ERROR_ALREADY_SUBMITTED,
    ERROR_ATTEMPT_NOT_FOUND,
    ERROR_INVALID_STAGING_KEY,
    ERROR_NOT_A_DRAFT,
    ERROR_PAPER_ALREADY_SUBMITTED,
    ERROR_QUESTION_NOT_FOUND,
    PRESIGNED_URL_EXPIRY_SECONDS,
    STATUS_FAILED,
    STATUS_MARKING,
)
from paperlab.api.models.attempts import (
    CreateAndSubmitPracticeRequest,
    CreatePaperAttemptRequest,
    CreatePaperAttemptResponse,
    PaperDraftDetailsResponse,
    PaperListResponse,
    PaperMetadata,
    PaperQuestionResponse,
    PracticeAttemptResponse,
    QuestionListResponse,
    QuestionMetadata,
    SubmitPaperQuestionRequest,
    SubmitResponse,
)
from paperlab.api.models.responses import PaperAttemptListItem, QuestionAttemptResponse
from paperlab.api.models.results import (
    PaperResultsResponse,
    QuestionResultsResponse,
)
from paperlab.api.models.status import (
    ErrorInfo,
    FailedQuestion,
    PaperStatusResponse,
    ProgressInfo,
    QuestionErrorInfo,
    QuestionStatusResponse,
)
from paperlab.api.models.uploads import PresignedUrlRequest, PresignedUrlResponse
from paperlab.api.status import derive_paper_status, derive_question_status
from paperlab.config import MarkingAttemptStatus, settings
from paperlab.data.database import connection
from paperlab.data.repositories.marking import (
    mark_criteria,
    paper_attempts,
    paper_results,
    papers,
    practice,
    question_attempts,
    question_content,
    question_marking_results,
    question_submissions,
    questions,
    submission_images,
)
from paperlab.data.repositories.marking import (
    status as status_repo,
)
from paperlab.paper_marking.grading import grade_paper_attempt
from paperlab.paper_marking.marking import mark_paper_attempt
from paperlab.services.client_factory import get_marking_client
from paperlab.storage.storage import R2Storage
from paperlab.submissions.finalize_paper import (
    PaperSubmissionError,
    finalize_paper_attempt,
)
from paperlab.submissions.submit_question import (
    StagingKeyValidationError,
    submit_paper_question,
    submit_practice_question,
    validate_staging_keys,
)

app = FastAPI(title="PaperLab API", version="0.1.0")

# CORS configuration: localhost (dev), Cloudflare Pages, custom domain
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1)(:\d+)?"  # Local dev
        r"|https://(paperlab-app\.pages\.dev|app\.mypaperlab\.com)"  # Production
    ),
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers (including Authorization)
)


async def mark_paper_attempt_async(attempt_id: int) -> None:
    """Background task wrapper for paper marking and grading.

    Runs mark_paper_attempt followed by grade_paper_attempt (if all successful).
    Doesn't propagate exceptions (background task).

    Args:
        attempt_id: Paper attempt ID to mark and grade
    """
    try:
        # Get LLM client and model (uses default from settings)
        with connection(settings.db_path) as conn:
            llm_client, llm_model_id = get_marking_client(
                model_identifier=None,
                conn=conn,
            )

        # Step 1: Mark all questions in paper (creates own connection per thread)
        with connection(settings.db_path) as conn:
            marking_result = mark_paper_attempt(
                paper_attempt_id=attempt_id,
                llm_client=llm_client,
                llm_model_id=llm_model_id,
                conn=conn,
            )
            conn.commit()

        # Step 2: Grade paper if all questions marked successfully
        if len(marking_result.failed) == 0:
            with connection(settings.db_path) as conn:
                grade_paper_attempt(attempt_id, conn)
                conn.commit()

    except Exception:
        pass  # Background task - silently fail


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for connectivity monitoring.

    Used by Flutter app to verify API availability beyond device connectivity.
    Returns 200 OK if API is running and responsive.

    Returns:
        Simple status message
    """
    return {"status": "ok"}


@app.get(
    "/api/diagrams/{board}/{level}/{subject}/{paper_stem}/q{question_number}_{diagram_index}.png"
)
async def get_diagram(
    board: str,
    level: str,
    subject: str,
    paper_stem: str,
    question_number: int,
    diagram_index: int,
) -> FileResponse:
    """Serve diagram image from local storage (public, no auth required).

    Diagrams are from public exam papers and don't contain sensitive data.
    Path: data/papers/structured/{board}/{level}/{subject}/diagrams/{paper_stem}/q{NN}_{index}.png

    Args:
        board: Exam board (e.g., "pearson-edexcel")
        level: Exam level (e.g., "gcse")
        subject: Subject (e.g., "mathematics")
        paper_stem: Paper identifier stem (e.g., "1ma1_1h_2023_11_08")
        question_number: Question number (1-based)
        diagram_index: Diagram index within question (1-based, sequential across parts)

    Returns:
        PNG image file

    Raises:
        403: Invalid path (path traversal attempt)
        404: Diagram not found
    """
    base = settings.project_root / "data/papers/structured"
    diagram_path = base / board / level / subject / "diagrams" / paper_stem
    diagram_path = diagram_path / f"q{question_number:02d}_{diagram_index}.png"

    # Security: Prevent path traversal attacks
    if not diagram_path.resolve().is_relative_to(base.resolve()):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not diagram_path.exists():
        raise HTTPException(status_code=404, detail="Diagram not found")
    return FileResponse(path=str(diagram_path), media_type="image/png")


@app.get(
    "/api/diagrams_ms/{board}/{level}/{subject}/{paper_stem}/q{question_number}_c{criterion_index}.png"
)
async def get_mark_scheme_diagram(
    board: str,
    level: str,
    subject: str,
    paper_stem: str,
    question_number: int,
    criterion_index: int,
) -> FileResponse:
    """Serve mark scheme diagram image from local storage (public, no auth required).

    Mark scheme diagrams are from public exam papers and don't contain sensitive data.
    Path: data/papers/structured/{board}/{level}/{subject}/diagrams_ms/{paper_stem}/q{NN}_c{C}.png

    Args:
        board: Exam board (e.g., "pearson-edexcel")
        level: Exam level (e.g., "gcse")
        subject: Subject (e.g., "mathematics")
        paper_stem: Paper identifier stem (e.g., "1ma1_1h_2023_11_08")
        question_number: Question number (1-based)
        criterion_index: Criterion index (0-based)

    Returns:
        PNG image file

    Raises:
        403: Invalid path (path traversal attempt)
        404: Diagram not found
    """
    base = settings.project_root / "data/papers/structured"
    diagram_path = base / board / level / subject / "diagrams_ms" / paper_stem
    diagram_path = diagram_path / f"q{question_number:02d}_c{criterion_index}.png"

    # Security: Prevent path traversal attacks
    if not diagram_path.resolve().is_relative_to(base.resolve()):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not diagram_path.exists():
        raise HTTPException(status_code=404, detail="Mark scheme diagram not found")
    return FileResponse(path=str(diagram_path), media_type="image/png")


@app.get("/api/attempts/papers", response_model=list[PaperAttemptListItem])
async def list_paper_attempts(
    student_id: int = Depends(get_current_student_id),
) -> list[PaperAttemptListItem]:
    """List all paper attempts for the current student.

    M6: Returns all attempts (filtering handled client-side in Flutter).
    Client derives state from timestamps (draft/marking/complete).

    Returns:
        List of paper attempts with paper names and timestamps
    """
    with connection(settings.db_path) as conn:
        attempts = paper_attempts.get_attempts_for_student(student_id, conn)

    return [PaperAttemptListItem.from_domain(a) for a in attempts]


@app.get("/api/attempts/papers/{attempt_id}", response_model=PaperDraftDetailsResponse)
async def get_paper_draft_details(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> PaperDraftDetailsResponse:
    """Get draft details for resuming paper upload.

    Returns paper metadata, question count, and submitted questions map.
    Used when resuming a draft paper from home screen.

    Args:
        attempt_id: Paper attempt ID

    Returns:
        Draft details with question count and submitted questions

    Raises:
        404 Not Found: Attempt doesn't exist, not owned by student, or not a draft
        401 Unauthorized: Not authenticated
    """
    with connection(settings.db_path) as conn:
        try:
            # 1. Get attempt and verify ownership
            attempt = paper_attempts.get_attempt(attempt_id, conn)
            if attempt.student_id != student_id:
                raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

            # 2. Verify it's a draft (not submitted yet)
            if attempt.submitted_at is not None:
                raise HTTPException(
                    status_code=404,
                    detail=ERROR_NOT_A_DRAFT,
                )

            # 3. Get paper info for display name
            paper_info = papers.get_paper_full(attempt.paper_id, conn)

            # 4. Get question count for the paper
            question_count = papers.get_question_count(attempt.paper_id, conn)

            # 5. Get submitted questions with image counts
            submitted_questions = question_attempts.get_submitted_questions_with_image_counts(
                attempt_id, conn
            )

            # 6. Build response
            return PaperDraftDetailsResponse.from_domain(
                attempt_data={
                    "id": attempt.id,
                    "attempt_uuid": attempt.attempt_uuid,
                    "paper_name": str(paper_info["display_name"]),
                    "exam_date": str(paper_info["exam_date"]),
                },
                question_count=question_count,
                submitted_questions=submitted_questions,
            )

        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/attempts/questions", response_model=list[QuestionAttemptResponse])
async def list_question_attempts(
    student_id: int = Depends(get_current_student_id),
) -> list[QuestionAttemptResponse]:
    """List all practice question attempts for the current student.

    M6: Returns all attempts (filtering handled client-side in Flutter).
    Client derives state from timestamps (marking/complete).

    Returns:
        List of practice question attempts with question names and timestamps
    """
    with connection(settings.db_path) as conn:
        attempts = practice.get_attempts_for_student(student_id, conn)

    return [QuestionAttemptResponse.from_domain(a) for a in attempts]


@app.delete("/api/attempts/papers/{attempt_id}", status_code=204)
async def delete_paper_attempt(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> Response:
    """Soft delete paper attempt (preserves audit trail).

    Args:
        attempt_id: ID of paper attempt to delete

    Returns:
        204 No Content on success

    Raises:
        404 Not Found: Attempt doesn't exist or already deleted
        500 Internal Server Error: Database error
    """
    with connection(settings.db_path) as conn:
        try:
            paper_attempts.soft_delete_attempt(
                paper_attempt_id=attempt_id, deleted_by=student_id, conn=conn
            )
            conn.commit()

        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e

    return Response(status_code=204)


@app.delete("/api/attempts/questions/{attempt_id}", status_code=204)
async def delete_question_attempt(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> Response:
    """Soft delete practice question attempt (preserves audit trail).

    Args:
        attempt_id: ID of practice question attempt to delete

    Returns:
        204 No Content on success

    Raises:
        404 Not Found: Attempt doesn't exist or already deleted
        500 Internal Server Error: Database error
    """
    with connection(settings.db_path) as conn:
        try:
            practice.soft_delete_attempt(attempt_id=attempt_id, deleted_by=student_id, conn=conn)
            conn.commit()

        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e

    return Response(status_code=204)


@app.post("/api/attempts/papers/{attempt_id}/restore", status_code=204)
async def restore_paper_attempt(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> Response:
    """Restore soft-deleted paper attempt (undo delete).

    Args:
        attempt_id: ID of paper attempt to restore

    Returns:
        204 No Content on success

    Raises:
        404 Not Found: Attempt doesn't exist, not deleted, or not owned by student
        500 Internal Server Error: Database error
    """
    with connection(settings.db_path) as conn:
        try:
            paper_attempts.restore_attempt(
                paper_attempt_id=attempt_id, restored_by=student_id, conn=conn
            )
            conn.commit()

        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e

    return Response(status_code=204)


@app.post("/api/attempts/questions/{attempt_id}/restore", status_code=204)
async def restore_question_attempt(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> Response:
    """Restore soft-deleted practice question attempt (undo delete).

    Args:
        attempt_id: ID of practice question attempt to restore

    Returns:
        204 No Content on success

    Raises:
        404 Not Found: Attempt doesn't exist, not deleted, or not owned by student
        500 Internal Server Error: Database error
    """
    with connection(settings.db_path) as conn:
        try:
            practice.restore_attempt(attempt_id=attempt_id, restored_by=student_id, conn=conn)
            conn.commit()

        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e

    return Response(status_code=204)


# =============================================================================
# Flow 2: Selection + Upload Endpoints
# =============================================================================


@app.get("/api/papers", response_model=PaperListResponse)
async def list_papers(
    exam_board: str | None = None,
    exam_level: str | None = None,
    subject: str | None = None,
    _: int = Depends(get_current_student_id),  # Auth required but ID unused
) -> PaperListResponse:
    """List available papers for selection screen.

    Args:
        exam_board: Filter by board (e.g., "pearson-edexcel")
        exam_level: Filter by level (e.g., "gcse")
        subject: Filter by subject (e.g., "mathematics")

    Returns:
        List of papers with metadata
    """
    with connection(settings.db_path) as conn:
        papers_list = papers.list_papers(
            exam_board=exam_board,
            exam_level=exam_level,
            subject=subject,
            conn=conn,
        )

    return PaperListResponse(papers=[PaperMetadata.from_domain(p) for p in papers_list])


@app.get("/api/questions", response_model=QuestionListResponse)
async def list_questions_for_practice(
    exam_board: str | None = None,
    exam_level: str | None = None,
    subject: str | None = None,
    paper_id: int | None = None,
    _: int = Depends(get_current_student_id),  # Auth required but ID unused
) -> QuestionListResponse:
    """List available questions for practice selection screen.

    Args:
        exam_board: Filter by board
        exam_level: Filter by level
        subject: Filter by subject
        paper_id: Filter by specific paper

    Returns:
        List of questions with metadata
    """
    with connection(settings.db_path) as conn:
        questions_list = questions.list_questions(
            exam_board=exam_board,
            exam_level=exam_level,
            subject=subject,
            paper_id=paper_id,
            conn=conn,
        )

    return QuestionListResponse(questions=[QuestionMetadata.from_domain(q) for q in questions_list])


@app.post("/api/uploads/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    student_id: int = Depends(get_current_student_id),
) -> PresignedUrlResponse:
    """Generate presigned URL for staging bucket upload.

    Args:
        request: Contains attempt_uuid and filename

    Returns:
        Presigned PUT URL and staging key
    """
    # For paper attempts: verify ownership
    # For practice: no DB check (validated on submit)
    with connection(settings.db_path) as conn:
        attempt = paper_attempts.get_attempt_by_uuid(request.attempt_uuid, conn)
        if attempt is not None and attempt.student_id != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

    # Build staging key
    staging_key = f"staging/{request.attempt_uuid}/{request.filename}"

    # Generate presigned PUT URL
    try:
        r2 = R2Storage()
        upload_url = r2.generate_presigned_upload_url(
            remote_key=staging_key,
            bucket="staging",
            expiry_seconds=PRESIGNED_URL_EXPIRY_SECONDS,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return PresignedUrlResponse(upload_url=upload_url, staging_key=staging_key)


@app.post(
    "/api/attempts/papers",
    response_model=CreatePaperAttemptResponse,
    status_code=201,
)
async def create_paper_attempt(
    request: CreatePaperAttemptRequest,
    student_id: int = Depends(get_current_student_id),
) -> CreatePaperAttemptResponse:
    """Create draft paper attempt.

    Args:
        request: Paper metadata to look up paper ID

    Returns:
        Created paper attempt with ID
    """
    with connection(settings.db_path) as conn:
        try:
            # Look up paper ID by metadata
            paper_id = papers.get_paper_id_by_metadata(
                exam_board=request.exam_board,
                exam_level=request.exam_level,
                subject=request.subject,
                paper_code=request.paper_code,
                year=request.year,
                month=request.month,
                conn=conn,
            )

            # Create attempt
            attempt = paper_attempts.create_attempt(
                attempt_uuid=request.attempt_uuid,
                student_id=student_id,
                paper_id=paper_id,
                inherited_from_attempt=None,
                conn=conn,
            )

            # Get paper display name
            paper_info = papers.get_paper_full(paper_id, conn)

            conn.commit()

            return CreatePaperAttemptResponse.from_domain(
                {
                    "id": attempt.id,
                    "attempt_uuid": attempt.attempt_uuid,
                    "paper_name": str(paper_info["display_name"]),
                    "exam_date": str(paper_info["exam_date"]),
                    "created_at": attempt.created_at,
                    "submitted_at": attempt.submitted_at,
                    "completed_at": attempt.completed_at,
                }
            )

        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/api/attempts/papers/{attempt_id}/questions",
    response_model=PaperQuestionResponse,
)
async def submit_paper_question_endpoint(
    attempt_id: int,
    request: SubmitPaperQuestionRequest,
    student_id: int = Depends(get_current_student_id),
) -> PaperQuestionResponse:
    """Submit one question to paper attempt (atomic commit).

    Args:
        attempt_id: Paper attempt ID
        request: Question number and staging keys

    Returns:
        Question attempt ID and submission ID
    """
    with connection(settings.db_path) as conn:
        try:
            # 1. Verify ownership and draft state
            attempt = paper_attempts.get_attempt(attempt_id, conn)
            if attempt.student_id != student_id:
                raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)
            if attempt.submitted_at is not None:
                raise HTTPException(status_code=409, detail=ERROR_PAPER_ALREADY_SUBMITTED)

            # 2. Validate staging keys belong to this attempt (via orchestrator)
            validate_staging_keys(request.staging_keys, attempt.attempt_uuid)

            # 3. Atomic commit via orchestrator
            r2 = R2Storage()
            result = submit_paper_question(
                paper_attempt_id=attempt_id,
                paper_id=attempt.paper_id,
                student_id=student_id,
                question_number=request.question_number,
                staging_keys=request.staging_keys,
                r2=r2,
                conn=conn,
            )

            conn.commit()

            return PaperQuestionResponse(
                question_attempt_id=result.question_attempt_id,
                submission_id=result.submission_id,
                question_number=result.question_number,
            )

        except StagingKeyValidationError:
            conn.rollback()
            raise HTTPException(status_code=422, detail=ERROR_INVALID_STAGING_KEY) from None
        except ClientError as e:
            conn.rollback()
            raise HTTPException(status_code=502, detail=f"Storage error: {e}") from e
        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/api/attempts/papers/{attempt_id}/submit",
    response_model=SubmitResponse,
)
async def submit_paper_attempt(
    attempt_id: int,
    background_tasks: BackgroundTasks,
    student_id: int = Depends(get_current_student_id),
) -> SubmitResponse:
    """Finalize paper attempt (sets submitted_at, triggers marking queue).

    Args:
        attempt_id: Paper attempt ID
        background_tasks: FastAPI background tasks
        student_id: Current student ID from JWT

    Returns:
        Attempt ID and submitted timestamp
    """
    with connection(settings.db_path) as conn:
        try:
            # Verify ownership first
            attempt = paper_attempts.get_attempt(attempt_id, conn)
            if attempt.student_id != student_id:
                raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)
            if attempt.submitted_at is not None:
                raise HTTPException(status_code=409, detail=ERROR_ALREADY_SUBMITTED)

            # Finalize via service (validates all questions submitted)
            result = finalize_paper_attempt(attempt_id, conn)
            conn.commit()

            # Trigger background marking (after successful commit)
            background_tasks.add_task(mark_paper_attempt_async, attempt_id)

            return SubmitResponse(
                attempt_id=result.attempt_id,
                submitted_at=result.submitted_at,
            )

        except PaperSubmissionError as e:
            conn.rollback()
            raise HTTPException(status_code=422, detail=str(e)) from None
        except HTTPException:
            conn.rollback()
            raise
        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/api/attempts/questions",
    response_model=PracticeAttemptResponse,
    status_code=201,
)
async def create_and_submit_practice_attempt(
    request: CreateAndSubmitPracticeRequest,
    student_id: int = Depends(get_current_student_id),
) -> PracticeAttemptResponse:
    """Create AND submit practice attempt in single call.

    Single-phase: creates submission, images, practice attempt, and marks immediately.

    Args:
        request: Question ID, attempt UUID, and staging keys

    Returns:
        Practice attempt with marking status
    """
    with connection(settings.db_path) as conn:
        try:
            # 1. Validate staging keys match attempt_uuid (via orchestrator)
            validate_staging_keys(request.staging_keys, request.attempt_uuid)

            # 2. Validate question exists
            try:
                questions.get_question_structure(request.question_id, conn)
            except ValueError:
                raise HTTPException(status_code=404, detail=ERROR_QUESTION_NOT_FOUND) from None

            # 3. Get LLM client and model
            llm_client, llm_model_id = get_marking_client(
                model_identifier=None,  # Uses default from settings
                conn=conn,
            )

            # 4. Atomic commit via orchestrator
            r2 = R2Storage()
            result = submit_practice_question(
                attempt_uuid=request.attempt_uuid,
                student_id=student_id,
                question_id=request.question_id,
                staging_keys=request.staging_keys,
                r2=r2,
                llm_client=llm_client,
                llm_model_id=llm_model_id,
                conn=conn,
            )

            conn.commit()

            return PracticeAttemptResponse(
                id=result.practice_attempt_id,
                attempt_uuid=request.attempt_uuid,
                submission_id=result.submission_id,
                question_display=result.question_display,
                created_at=result.created_at,
                marking_status=result.marking_status,
            )

        except StagingKeyValidationError:
            conn.rollback()
            raise HTTPException(status_code=422, detail=ERROR_INVALID_STAGING_KEY) from None
        except ClientError as e:
            conn.rollback()
            raise HTTPException(status_code=502, detail=f"Storage error: {e}") from e
        except HTTPException:
            conn.rollback()
            raise
        except ValueError:
            conn.rollback()
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e


# =============================================================================
# Flow 3: Marking Progress Status Endpoints
# =============================================================================


RETRYABLE_ERRORS = {MarkingAttemptStatus.RATE_LIMIT, MarkingAttemptStatus.TIMEOUT}


@app.get("/api/attempts/papers/{attempt_id}/status", response_model=PaperStatusResponse)
async def get_paper_status(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> PaperStatusResponse:
    """Poll paper attempt marking status.

    Used by MarkingInProgressScreen to show real-time progress.
    Status is derived from database state (timestamps + marking attempts), not stored.

    Args:
        attempt_id: Paper attempt ID

    Returns:
        Status with optional progress (if marking) or error (if failed)
    """
    with connection(settings.db_path) as conn:
        # 1. Get attempt (raises ValueError if not found)
        try:
            attempt = paper_attempts.get_attempt(attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        # 2. Verify ownership
        if attempt.student_id != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 3. Get marking stats from repository
        marking_stats = status_repo.get_paper_marking_stats(attempt_id, attempt.paper_id, conn)

        # 4. Derive status
        status = derive_paper_status(attempt, marking_stats)

        # 5. Build response based on status
        progress = None
        error = None

        if status == STATUS_MARKING:
            progress = ProgressInfo(
                questions_total=marking_stats.total_questions,
                questions_completed=marking_stats.successful,
                questions_in_progress=0,
                questions_failed=marking_stats.failed,
            )
        elif status == STATUS_FAILED:
            failed_questions = status_repo.get_failed_questions(attempt_id, conn)
            error = ErrorInfo(
                message=f"{len(failed_questions)} question(s) failed to mark",
                failed_questions=[
                    FailedQuestion(
                        question_number=q["question_number"],
                        error_type=q["error_type"],
                        error_message=q["error_message"] or "Unknown error",
                    )
                    for q in failed_questions
                ],
            )

        return PaperStatusResponse(
            attempt_id=attempt_id,
            status=status,  # type: ignore[arg-type]
            progress=progress,
            error=error,
        )


@app.get("/api/attempts/questions/{attempt_id}/status", response_model=QuestionStatusResponse)
async def get_question_status(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> QuestionStatusResponse:
    """Poll practice question marking status.

    Used by MarkingInProgressScreen for practice question flow.
    Status derived from submission and marking attempt state.

    Args:
        attempt_id: Practice question attempt ID

    Returns:
        Status with optional error (if failed)
    """
    with connection(settings.db_path) as conn:
        # 1. Get attempt (raises ValueError if not found)
        try:
            attempt = practice.get_attempt(attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        # 2. Verify ownership
        if attempt["student_id"] != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 3. Get latest marking attempt from repository
        marking = status_repo.get_latest_marking_attempt(attempt["submission_id"], conn)

        # 4. Derive status
        status = derive_question_status(attempt, marking)

        # 5. Build response
        error = None

        if status == STATUS_FAILED and marking is not None:
            error = QuestionErrorInfo(
                error_type=marking["status"],
                error_message=marking["error_message"] or "Unknown error",
                can_retry=marking["status"] in RETRYABLE_ERRORS,
            )

        return QuestionStatusResponse(
            attempt_id=attempt_id,
            status=status,  # type: ignore[arg-type]
            error=error,
        )


# =============================================================================
# Flow 4: View Results Endpoints
# =============================================================================


def _build_question_results_response(
    submission_id: int,
    question_id: int,
    paper_id: int,
    r2: R2Storage,
    conn: sqlite3.Connection,
) -> QuestionResultsResponse:
    """Build question results response from submission data.

    Shared helper for paper and practice question results endpoints.
    Fetches marking results, question content, mark scheme, and images.

    Args:
        submission_id: Submission ID for marking results and images
        question_id: Question ID for content and mark scheme
        paper_id: Paper ID for paper name
        r2: R2 storage client for presigned URLs
        conn: Database connection

    Returns:
        QuestionResultsResponse with all data merged

    Raises:
        ValueError: If no successful marking results found
    """
    # Get marking results (raises ValueError if no successful marking)
    marking_results = question_marking_results.get_results_for_submission(submission_id, conn)

    # Get question structure and paper info
    question_struct = questions.get_question_structure(question_id, conn)
    paper_info = papers.get_paper_full(paper_id, conn)

    # Get mark scheme and question content
    mark_scheme = mark_criteria.get_mark_scheme_for_question(question_id, conn)
    q_content = question_content.get_content_for_question(question_id, conn)

    # Get images and generate presigned URLs
    images_data = submission_images.get_images_for_submission(submission_id, conn)
    images_with_urls = [
        {
            "url": r2.generate_presigned_download_url(img["image_path"]),
            "sequence": img["image_sequence"],
        }
        for img in images_data
    ]

    return QuestionResultsResponse.from_domain(
        question_number=question_struct["question_number"],
        paper_name=str(paper_info["display_name"]),
        exam_date=str(paper_info["exam_date"]),
        question_content=q_content,
        mark_scheme=mark_scheme,
        marking_results=marking_results,
        images=images_with_urls,
        board=str(paper_info["exam_board"]),
        level=str(paper_info["exam_level"]),
        subject=str(paper_info["subject"]),
        paper_code=str(paper_info["paper_code"]),
    )


@app.get("/api/attempts/papers/{attempt_id}/results", response_model=PaperResultsResponse)
async def get_paper_results(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> PaperResultsResponse:
    """Get paper results summary for completed paper attempt.

    Returns overall marks, grade, and per-question breakdown.
    Used by PaperResultsScreen.

    Args:
        attempt_id: Paper attempt ID

    Returns:
        Paper results with question scores

    Raises:
        404: Attempt not found, not owned by student, or not completed
        401: Not authenticated
    """
    with connection(settings.db_path) as conn:
        # 1. Get attempt
        try:
            attempt = paper_attempts.get_attempt(attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        # 2. Verify ownership
        if attempt.student_id != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 3. Check completion (404 for incomplete - prevents info leak)
        if attempt.completed_at is None:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 4. Get paper result
        result = paper_results.get_result(attempt_id, conn)
        if result is None:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 5. Get paper name
        paper_info = papers.get_paper_full(attempt.paper_id, conn)

        # 6. Get per-question scores
        question_scores = question_marking_results.get_scores_for_paper_attempt(attempt_id, conn)

        return PaperResultsResponse.from_domain(
            attempt_id=attempt_id,
            paper_name=str(paper_info["display_name"]),
            exam_date=str(paper_info["exam_date"]),
            total_awarded=result.total_marks_awarded,
            total_available=result.total_marks_available,
            percentage=result.percentage,
            grade=result.indicative_grade,
            question_scores=question_scores,
        )


@app.get(
    "/api/attempts/papers/{paper_attempt_id}/questions/{question_attempt_id}/results",
    response_model=QuestionResultsResponse,
)
async def get_paper_question_results(
    paper_attempt_id: int,
    question_attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> QuestionResultsResponse:
    """Get detailed question results for paper flow.

    Returns question content, mark scheme criteria, marks awarded,
    feedback, and student work images with presigned URLs.

    Args:
        paper_attempt_id: Paper attempt ID (for ownership validation)
        question_attempt_id: Question attempt ID

    Returns:
        Question results with parts, criteria, feedback, and images

    Raises:
        404: Paper/question attempt not found, not owned, or not marked
        401: Not authenticated
    """
    with connection(settings.db_path) as conn:
        # 1. Verify paper attempt ownership
        try:
            paper_attempt = paper_attempts.get_attempt(paper_attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        if paper_attempt.student_id != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 2. Get question attempt and verify it belongs to paper attempt
        try:
            qa = question_attempts.get_attempt(question_attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        if qa.paper_attempt_id != paper_attempt_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 3. Get submission details
        submission = question_submissions.get_by_id(qa.submission_id, conn)
        if submission is None:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        # 4. Build response (validates marking exists)
        r2 = R2Storage()
        try:
            return _build_question_results_response(
                submission_id=qa.submission_id,
                question_id=submission["question_id"],
                paper_id=paper_attempt.paper_id,
                r2=r2,
                conn=conn,
            )
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None


@app.get(
    "/api/attempts/practice/{attempt_id}/results",
    response_model=QuestionResultsResponse,
)
async def get_practice_results(
    attempt_id: int,
    student_id: int = Depends(get_current_student_id),
) -> QuestionResultsResponse:
    """Get detailed question results for practice flow.

    Same response format as paper question results, but starts from
    practice_question_attempts table.

    Args:
        attempt_id: Practice question attempt ID

    Returns:
        Question results with parts, criteria, feedback, and images

    Raises:
        404: Attempt not found, not owned, or not marked
        401: Not authenticated
    """
    with connection(settings.db_path) as conn:
        # 1. Get practice attempt
        try:
            attempt = practice.get_attempt(attempt_id, conn)
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None

        # 2. Verify ownership
        if attempt["student_id"] != student_id:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        submission_id = attempt["submission_id"]

        # 3. Get submission details
        submission = question_submissions.get_by_id(submission_id, conn)
        if submission is None:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND)

        question_id = submission["question_id"]
        paper_id = questions.get_paper_id_for_question(question_id, conn)

        # 4. Build response (validates marking exists)
        r2 = R2Storage()
        try:
            return _build_question_results_response(
                submission_id=submission_id,
                question_id=question_id,
                paper_id=paper_id,
                r2=r2,
                conn=conn,
            )
        except ValueError:
            raise HTTPException(status_code=404, detail=ERROR_ATTEMPT_NOT_FOUND) from None


# =============================================================================
# Account Management Endpoints
# =============================================================================


@app.delete("/api/account", status_code=204)
async def delete_account(
    background_tasks: BackgroundTasks,
    student_id: int = Depends(get_current_student_id),
) -> Response:
    """Delete user account and all associated data.

    Required for Apple App Store compliance (Guideline 5.1.1(v)).

    Deletion order (designed for safety):
    1. Delete Supabase auth user (FIRST - prevents re-login if later steps fail)
    2. Delete all user data from database (in transaction)
    3. Queue R2 image cleanup (background task - orphaned files are harmless)

    If Supabase deletion succeeds but DB deletion fails:
    - User is locked out (can't log in)
    - Data remains (can be cleaned up manually)
    - This is safer than the reverse (deleted data + active account)

    Args:
        background_tasks: FastAPI background tasks for R2 cleanup
        student_id: Current student ID from JWT

    Returns:
        204 No Content on success

    Raises:
        500 Internal Server Error: If Supabase deletion fails
        500 Internal Server Error: If database deletion fails
    """
    import httpx

    # Pre-flight check: Ensure Supabase credentials are configured
    # This prevents orphaned auth users if DB deletion succeeds but Supabase doesn't
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=503,
            detail="Account deletion temporarily unavailable. Please contact support.",
        )

    # Step 1: Get Supabase user UUID from JWT (we need it for admin API)
    # The student_id dependency already validated the JWT, but we need the UUID
    with connection(settings.db_path) as conn:
        # Get supabase_uid from students table
        cursor = conn.execute("SELECT supabase_uid FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Student not found")
        supabase_uid = row[0]

    # Step 1.5: Clear auth cache BEFORE any deletions
    # Prevents stale cache entries if user re-authenticates during deletion
    clear_student_cache(supabase_uid)

    # Step 2: Delete Supabase auth user (FIRST - prevents re-login)
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{settings.supabase_url}/auth/v1/admin/users/{supabase_uid}",
                    headers={
                        "Authorization": f"Bearer {settings.supabase_service_role_key}",
                        "apikey": settings.supabase_service_role_key,
                    },
                )
                if response.status_code not in (200, 204, 404):
                    # Log but continue - user may have been deleted already
                    # 404 is OK - user doesn't exist in Supabase
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to delete Supabase user: {response.text}",
                    )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Supabase: {e}",
            ) from e

    # Step 3: Collect R2 image paths before deleting DB records
    r2_paths_to_delete: list[str] = []
    with connection(settings.db_path) as conn:
        try:
            # Get all image paths for this student's submissions
            # From paper attempts
            cursor = conn.execute(
                """
                SELECT DISTINCT si.image_path
                FROM submission_images si
                JOIN question_submissions qs ON si.submission_id = qs.id
                JOIN question_attempts qa ON qs.id = qa.submission_id
                JOIN paper_attempts pa ON qa.paper_attempt_id = pa.id
                WHERE pa.student_id = ?
                """,
                (student_id,),
            )
            r2_paths_to_delete.extend([row[0] for row in cursor.fetchall()])

            # From practice attempts
            cursor = conn.execute(
                """
                SELECT DISTINCT si.image_path
                FROM submission_images si
                JOIN question_submissions qs ON si.submission_id = qs.id
                JOIN practice_question_attempts pqa ON qs.id = pqa.submission_id
                WHERE pqa.student_id = ?
                """,
                (student_id,),
            )
            r2_paths_to_delete.extend([row[0] for row in cursor.fetchall()])
        except Exception:
            pass  # If we can't get paths, we'll just skip R2 cleanup

    # Step 4: Delete all user data from database (in transaction)
    with connection(settings.db_path) as conn:
        try:
            # Delete in order respecting foreign key constraints
            # Order: children first, then parents
            # marking_attempts -> submission_images -> question_submissions ->
            # question_attempts/practice_question_attempts -> paper_results ->
            # paper_attempts -> students

            # 4a. Delete marking attempts for paper questions
            conn.execute(
                """
                DELETE FROM marking_attempts
                WHERE submission_id IN (
                    SELECT qs.id FROM question_submissions qs
                    JOIN question_attempts qa ON qs.id = qa.submission_id
                    JOIN paper_attempts pa ON qa.paper_attempt_id = pa.id
                    WHERE pa.student_id = ?
                )
                """,
                (student_id,),
            )

            # 4b. Delete marking attempts for practice questions
            conn.execute(
                """
                DELETE FROM marking_attempts
                WHERE submission_id IN (
                    SELECT qs.id FROM question_submissions qs
                    JOIN practice_question_attempts pqa ON qs.id = pqa.submission_id
                    WHERE pqa.student_id = ?
                )
                """,
                (student_id,),
            )

            # 4c. Delete submission images for paper questions
            conn.execute(
                """
                DELETE FROM submission_images
                WHERE submission_id IN (
                    SELECT qs.id FROM question_submissions qs
                    JOIN question_attempts qa ON qs.id = qa.submission_id
                    JOIN paper_attempts pa ON qa.paper_attempt_id = pa.id
                    WHERE pa.student_id = ?
                )
                """,
                (student_id,),
            )

            # 4d. Delete submission images for practice questions
            conn.execute(
                """
                DELETE FROM submission_images
                WHERE submission_id IN (
                    SELECT qs.id FROM question_submissions qs
                    JOIN practice_question_attempts pqa ON qs.id = pqa.submission_id
                    WHERE pqa.student_id = ?
                )
                """,
                (student_id,),
            )

            # 4e. Delete question submissions for paper flow
            # (MUST be before question_attempts deletion - query references question_attempts)
            conn.execute(
                """
                DELETE FROM question_submissions
                WHERE id IN (
                    SELECT qa.submission_id FROM question_attempts qa
                    JOIN paper_attempts pa ON qa.paper_attempt_id = pa.id
                    WHERE pa.student_id = ?
                )
                """,
                (student_id,),
            )

            # 4f. Delete question attempts (paper flow)
            conn.execute(
                """
                DELETE FROM question_attempts
                WHERE paper_attempt_id IN (
                    SELECT id FROM paper_attempts WHERE student_id = ?
                )
                """,
                (student_id,),
            )

            # 4g. Delete question submissions for practice flow
            # (MUST be before practice_question_attempts deletion)
            conn.execute(
                """
                DELETE FROM question_submissions
                WHERE id IN (
                    SELECT submission_id FROM practice_question_attempts
                    WHERE student_id = ?
                )
                """,
                (student_id,),
            )

            # 4h. Delete practice question attempts
            conn.execute(
                "DELETE FROM practice_question_attempts WHERE student_id = ?",
                (student_id,),
            )

            # 4i. Delete paper results
            conn.execute(
                """
                DELETE FROM paper_results
                WHERE paper_attempt_id IN (
                    SELECT id FROM paper_attempts WHERE student_id = ?
                )
                """,
                (student_id,),
            )

            # 4j. Delete paper attempts
            conn.execute("DELETE FROM paper_attempts WHERE student_id = ?", (student_id,))

            # 4k. Delete student record
            conn.execute("DELETE FROM students WHERE id = ?", (student_id,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to delete user data",
            ) from e

    # Step 5: Queue R2 cleanup (background task - best effort)
    if r2_paths_to_delete:
        background_tasks.add_task(_cleanup_r2_images, r2_paths_to_delete)

    return Response(status_code=204)


async def _cleanup_r2_images(paths: list[str]) -> None:
    """Background task to delete images from R2 storage.

    Best-effort cleanup - failures are logged but don't affect the response.
    Orphaned images in R2 are harmless and can be cleaned up later.

    Args:
        paths: List of R2 object keys to delete
    """
    import contextlib

    with contextlib.suppress(Exception):
        r2 = R2Storage()
        # Batch delete all images at once (more efficient)
        r2.delete_permanent_images(paths)
