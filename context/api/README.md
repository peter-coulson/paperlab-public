# API Layer Context

FastAPI transport layer connecting Flutter/web clients to Python backend.

---

## Overview

**Role:** HTTP bridge between clients and domain logic. API is transport, not transformation.

**Architecture:**
```
Flutter → FastAPI → Domain Logic → Repository → Database
```

**Fundamental constraint:** Backend domain logic is complete. API wraps existing operations, adds zero new business logic.

---

## Design Principles

**See:** [`CLAUDE.md`](../../CLAUDE.md) → API Development Principles section

**Core principle:** API is plumbing, not engineering.

**Key principles:**
1. **API is transport** - Wrap existing orchestrators, no new business logic
2. **Mirror the domain** - Request/response models mirror domain dataclasses
3. **Preserve architecture** - API replaces CLI layer (same transaction management)
4. **Return timestamps** - Clients derive state (immutability preservation)
5. **Accept UUIDs** - Clients generate UUIDs (idempotent operations)
6. **Validate at boundary** - Pydantic structure, domain business rules
7. **Subject-agnostic** - No subject-specific endpoints
8. **Resource-oriented** - Model entities, not verbs
9. **Screen-by-screen** - Build incrementally per screen needs
10. **Framework defaults** - Use FastAPI defaults

---

## Context Files

| File | Purpose |
|------|---------|
| `PATTERNS.md` | Implementation patterns (from_domain, transaction management, error handling, directory structure) |
| `AUTHENTICATION.md` | Authentication (JWT for users) |
| `WORKFLOWS.md` | API call sequences (paper flow, practice flow, soft delete, retry) |

---

## Implementation Strategy

**Screen-by-Screen Approach:**

Build endpoints incrementally per screen needs rather than all upfront.

**Process:**
1. Choose screen (e.g., Home)
2. Create spec for planning (optional)
3. Build Pydantic models + endpoints
4. Test with curl/Postman
5. Integrate Flutter screen
6. Delete spec after implementation

**Why:** Fast feedback loop, discover real requirements, validates approach early.

---

## Async Marking (M6)

**Decision:** Marking auto-triggers on submit. No separate "start marking" step.

**Paper flow:** Triggers on `POST /attempts/papers/{id}/submit` (whole paper finalized) → marks ALL questions as async batch via BackgroundTasks. Individual questions are NOT marked during upload phase.

**Practice flow:** Triggers on `POST /attempts/questions` (single question) → marks immediately (synchronous, ~5-15s).

**No middle ground:** Paper flow marks the whole paper at once. Practice flow marks the single question. Never partial marking during paper upload.

**Why BackgroundTasks (paper):** Simple, no extra infrastructure (vs Celery+Redis). Sufficient for M6 volume.

**Why synchronous (practice):** Single question is fast enough. Simpler than polling for one question.

**Where:** See `WORKFLOWS.md` → Status Polling Flow for client-server interaction.

---

## CORS Configuration

**Required for:** Flutter web platform (browser Same-Origin Policy)

**Location:** `src/paperlab/api/main.py` - Add middleware after app initialization

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why needed:**
- Browser blocks cross-origin requests without CORS headers
- Flutter web runs on different port than API (e.g., :53XX vs :8000)
- OPTIONS preflight requests must succeed before actual requests

**Production:** Replace `allow_origin_regex` with specific domain(s):
```python
allow_origins=["https://paperlab.yourdomain.com"]
```

**Debug symptom:** `ClientException: Failed to fetch` despite backend showing 200 OK responses.

---

## Environment Configuration

**Environment naming:** Reflects infrastructure (local vs deployed), not release stage.

- **`development`** - Local backend (localhost:8000)
- **`production`** - Railway backend (https://paperlab-production.up.railway.app)

**Key insight:** M7 (Professional Beta), M8, and M9 (Public Launch) all use `production` environment. Environment is infrastructure choice, not release stage.

**Configuration:**
- Backend: `PAPERLAB_ENVIRONMENT` environment variable
- Frontend: `--dart-define=ENVIRONMENT=production` build flag
- Default: `development` (local)

---

## Deployment (Railway)

**Essential commands:**
```bash
railway logs --deployment                    # View deployment logs
railway logs --deployment --filter "@level:error"  # Filter errors only
railway status                               # Check project/service/environment linkage
railway ssh                                  # SSH into production container
```

**See:** `context/backend/PATH-CONFIGURATION.md` for volume architecture and database initialization.

---

## Size Target

**Target range:** 1,500-2,500 lines total

**Current:**
- `README.md` - This file (~150 lines)
- `PATTERNS.md` - Implementation patterns (~260 lines)
- `AUTHENTICATION.md` - Auth patterns (~180 lines)
- `WORKFLOWS.md` - API workflows (~215 lines)

**Total:** ~805 lines (well under 2,500 target, room for M7+ additions)

---

## Related Documentation

**CLAUDE.md** → API Development Principles (must follow for all API work)

**Backend:**
- `backend/ARCHITECTURE.md` → Transaction management patterns
- `backend/DATABASE.md` → Repository patterns
- `backend/STORAGE.md` → R2 storage patterns and presigned URLs
- `backend/SUBMISSIONS.md` → Submission domain logic

**Frontend:**
- `frontend/STATE-MANAGEMENT.md` → Provider setup for API integration

**Shared:**
- `shared/ROADMAP.md` → Milestone scope and success criteria

---

## Content Principles

**This context documents:**
- WHY API layer exists (role in architecture)
- WHERE to find implementation details (code, other context files)
- KEY patterns to follow (via PATTERNS.md)
- STRATEGIC decisions (screen-by-screen, temporary auth)

**This context does NOT document:**
- Complete endpoint implementations (see `src/paperlab/api/`)
- Full Pydantic model definitions (see `src/paperlab/api/models/`)
- Detailed FastAPI tutorials (see official docs)

**Follow:** WHY/WHERE, not WHAT/HOW (see `GOVERNANCE.md`)
