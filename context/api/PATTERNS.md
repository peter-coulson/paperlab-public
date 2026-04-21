# API Patterns

FastAPI implementation patterns for the transport layer.

---

## from_domain() Pattern

**Why:** Explicit transformation from domain models to API responses. Filters internal fields.

```python
class PaperAttemptResponse(BaseModel):
    id: int
    paper_name: str
    created_at: datetime

    @classmethod
    def from_domain(cls, attempt: PaperAttempt):
        return cls(id=attempt.id, ...)
```

**Where:** All response models use this pattern. See `src/paperlab/api/models/`.

---

## Transaction Management

**Pattern:** API layer owns transaction lifecycle (same as CLI Pattern A).

```python
@app.post("/api/submissions")
async def create_submission(request: SubmissionRequest):
    with connection() as conn:
        try:
            result = orchestrator.create(request, conn)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
```

**Where:** All endpoints follow this pattern. See `backend/ARCHITECTURE.md` → Connection Management.

---

## Two-Layer Validation

**Layer 1 (API):** Pydantic validates structure (types, formats, required fields)

**Layer 2 (Domain):** Orchestrators validate business rules (same as CLI)

```python
# Layer 1: Pydantic (API boundary)
class SubmissionRequest(BaseModel):
    submission_uuid: str
    question_id: int

# Layer 2: Business rules (orchestrator)
def create(request, conn):
    if not question_exists(request.question_id, conn):
        raise ValueError("Question not found")
```

**Why:** API doesn't duplicate validation. Business rules in one place.

---

## Error Handling

**Strategy:** Use FastAPI defaults + custom exception handlers for backend exceptions.

**HTTP Status Codes:**
- 200 OK, 201 Created, 204 No Content
- 400 Bad Request, 404 Not Found, 422 Validation Error
- 500 Internal Server Error

**Error Response Format:**
```json
{
  "error": {
    "message": "Question not found",
    "code": "QUESTION_NOT_FOUND"
  }
}
```

**Repository ValueError → 404 Pattern:**

Repositories raise `ValueError` when record not found or invalid state. API translates to 404.

```python
# Repository
def soft_delete_attempt(attempt_id: int, ...) -> None:
    if not exists_and_not_deleted(attempt_id):
        raise ValueError(f"Attempt {attempt_id} not found")

# API endpoint
except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

**Why:** Enables proper HTTP semantics without coupling repositories to HTTP concepts.

---

## Endpoint Naming

**Resource-Oriented (not verb-oriented):**

| Good | Bad |
|------|-----|
| `GET /api/attempts/papers` | `GET /api/list-papers` |
| `POST /api/submissions` | `POST /api/mark` |
| `DELETE /api/attempts/{id}` | `POST /api/delete-attempt` |

**Pattern:** `/api/{resource}` or `/api/{resource}/{id}` or `/api/{resource}/{id}/{sub-resource}`

### Nested Routes for Sub-Resources

**Pattern:** `/api/{parent}/{parent_id}/{child}/{child_id}`

**Example:** `GET /api/attempts/papers/{paper_id}/questions/{question_id}/results`

**Why nested:** Question attempts belong to paper attempts. Expresses ownership in URL structure. Enables ownership validation at route level.

### Separate ID Namespaces

**Problem:** Paper attempts and practice attempts live in different tables (`question_attempts`, `practice_question_attempts`) with overlapping auto-increment IDs.

**Solution:** Separate endpoints for paper flow vs practice flow.

```
Paper question results:   GET /api/attempts/papers/{paper_id}/questions/{question_id}/results
Practice results:         GET /api/attempts/practice/{practice_id}/results
```

**Why:** Prevents ID collision. Both tables have id=1, id=2, etc. Shared endpoint would be ambiguous.

---

## Directory Structure

```
src/paperlab/api/
├── __init__.py
├── main.py                      # App factory, router registration
├── auth.py                      # Authentication (JWT)
├── dependencies.py              # Shared dependencies (DB, auth)
├── exception_handlers.py        # Custom exception handlers
├── models/                      # Pydantic models (domain-organized)
│   ├── attempts.py             # Attempt request/response models
│   ├── papers.py               # Paper selection models
│   ├── questions.py            # Question selection models
│   ├── uploads.py              # Presigned URL models
│   ├── submissions.py          # Submission models
│   └── results.py              # Results response models
└── routers/                     # Endpoint routers (resource-based)
    └── (future: split from main.py)
```

**Key decisions:**
- **Resource-based routers:** Each router handles one resource type
- **Domain-organized models:** Models grouped by domain, not request/response
- **Thin main.py:** App factory, router registration, no business logic

---

## Router Pattern

**Each router uses FastAPI's APIRouter:**

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/attempts/papers", response_model=list[PaperAttemptResponse])
async def list_paper_attempts(
    student_id: int = Depends(get_current_student_id),
):
    # Implementation calls domain logic
```

**See:** `src/paperlab/api/main.py` for endpoint implementations.

---

## Dependencies Pattern

**Shared dependencies for all endpoints:**

```python
def get_db_connection():
    """Pattern A transaction management."""
    with connection(settings.db_path) as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
```

---

## App Factory Pattern

**main.py registers routers and middleware:**

```python
def create_app() -> FastAPI:
    app = FastAPI(title="PaperLab API", version="0.1.0")
    app.include_router(attempts.router, prefix="/api")
    exception_handlers.register(app)
    return app

app = create_app()
```

**Benefit:** Testable (can create app with different config), follows FastAPI best practices.

---

## Status Derivation Pattern

**Why:** Status computed from database state, never stored. Prevents stale status flags.

**Principle:** Derive from timestamps + marking attempts, return via API.

```python
# API layer derives status (thin logic, no DB access)
def derive_paper_status(attempt: PaperAttempt, stats: MarkingStats) -> str:
    if attempt.completed_at is not None:
        return "completed"
    if attempt.submitted_at is None:
        return "draft"
    if stats.failed > 0 and stats.total_marked == stats.total_questions:
        return "failed"
    # ... (see src/paperlab/api/status.py for full logic)
```

**Where:**
- Status derivation logic: `src/paperlab/api/status.py`
- Status repository queries: `src/paperlab/data/repositories/marking/status.py`
- API models: `src/paperlab/api/models/status.py`

**Benefits:**
- Single source of truth (timestamps, not status enum)
- Matches frontend derivation (consistent behavior)
- No status synchronization bugs

**Related:** See `WORKFLOWS.md` → Status Polling Flow for client-side usage.

---

## Related Documentation

- `AUTHENTICATION.md` → JWT patterns, token management
- `WORKFLOWS.md` → API call sequences (paper, practice, status polling flows)
- `backend/ARCHITECTURE.md` → Connection management patterns
- `backend/STORAGE.md` → R2 presigned URL patterns
