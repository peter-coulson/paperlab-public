# API Workflows

Client-server interaction patterns for key user journeys.

---

## Discovery Flow (Selection Phase)

**Purpose:** Fetch available papers and questions for selection screens.

**Endpoints:**
- `GET /api/papers` - List all papers (optional filters: exam_board, exam_level, subject)
- `GET /api/questions` - List all questions (optional filters: exam_board, exam_level, subject, paper_id)

**Paper Flow:**
1. User taps "Add Paper" on HomeScreen
2. Frontend calls `GET /api/papers` (with optional filters)
3. Frontend transforms API data to SelectionField format
4. User selects paper from cascading dropdowns
5. User confirms → proceeds to Paper Attempt Workflow

**Practice Flow:**
1. User taps "Add Question" on HomeScreen
2. Frontend calls `GET /api/questions` (with optional filters)
3. Frontend transforms API data to SelectionField format
4. User selects question from cascading dropdowns
5. User confirms → proceeds to Practice Attempt Workflow

**Caching:** Frontend caches discovery responses for session duration. No re-fetch unless user pulls to refresh.

**Where:** See `frontend/STATE-MANAGEMENT.md` → Selection State Pattern for cascading dropdown implementation.

---

## Paper Attempt Workflow (Two-Phase)

**Pattern:** User uploads ONE question at a time, building up a complete paper attempt.

**Flow:**
1. User selects paper on Selection Screen
2. User taps "Confirm" → Backend creates `paper_attempts` row with `submitted_at = NULL` (draft)
3. User selects question number, navigates to Question Upload Screen
4. User uploads photos for that ONE question
5. User taps "Confirm" → Backend creates `question_submissions`, `submission_images`, `question_attempts`
6. Repeat steps 3-5 for each question
7. When all questions complete → Backend sets `submitted_at`, triggers marking queue

**Why two-phase:**
- Paper is container for 1-20 questions
- User may upload Q1 today, Q7 tomorrow
- Draft paper attempt tracks progress across sessions
- Visible on Home Screen for resume

**Endpoints:**
- `POST /api/attempts/papers` - Create draft paper attempt
- `GET /api/attempts/papers/{id}` - Fetch draft details (for resume)
- `POST /api/attempts/papers/{id}/questions` - Submit one question
- `POST /api/attempts/papers/{id}/submit` - Finalize paper

### Resuming Draft Papers

**Pattern:** User can leave draft paper and return later to continue uploading questions.

**Flow:**
1. User taps draft paper on Home Screen
2. Frontend calls `GET /api/attempts/papers/{id}` to fetch draft state
3. Endpoint returns: paper name, question count, submitted questions map
4. Frontend loads state into provider → navigates to Paper Upload Screen
5. Screen displays which questions already submitted, allows uploading remaining questions

**Why separate endpoint:**
- Draft resume needs more context than list endpoint provides (submitted questions map)
- List endpoint optimized for display (paper name, timestamps only)
- Resume needs full draft state (question count, per-question submission status)

**Load before navigate:** Frontend must load draft state BEFORE navigation (Riverpod best practice). See `frontend/STATE-MANAGEMENT.md` → Navigation with Async Data.

**Where:**
- API implementation: `src/paperlab/api/main.py` - `get_paper_draft_details()`
- Backend query: `src/paperlab/data/repositories/marking/question_attempts.py` - `get_submitted_questions_with_image_counts()`
- Frontend provider: `lib/providers/upload_provider.dart` - `loadDraft()`

---

## Practice Attempt Workflow (Single-Phase)

**Pattern:** Single API call creates everything on submit.

**Flow:**
1. User selects question on Selection Screen
2. User taps "Confirm" → Navigate to Question Upload Screen (no backend call yet)
3. User uploads photos to staging bucket
4. User taps "Confirm" → Single backend call creates ALL records + marks immediately

**Why single-phase:**
- Practice is one question, 1-3 photos
- Typically completed in < 2 minutes
- No need to track "in-progress practice" on Home Screen
- If abandoned, staging TTL cleans up (no orphan DB records)
- Immediate marking provides instant feedback (core value proposition)

**Endpoint:**
- `POST /api/attempts/questions` - Create and submit practice attempt

---

## Retry with Inheritance

**Problem:** Student wants to fix specific questions in completed paper without re-marking unchanged questions.

**Solution:** Create new attempt that inherits marks from previous attempt, only re-marks changed questions.

**Flow:**
1. User taps "Edit Photo Submissions" on Paper Results Screen
2. Backend creates new `paper_attempts` row:
   - Sets `inherited_from_attempt = old_attempt_id`
   - Copies all `question_attempts` from source (all marked as inherited)
   - New attempt has `submitted_at = NULL` (draft state)
3. User re-uploads specific questions through Question Upload Screen
4. On final submit → Marking pipeline runs (only overridden questions re-marked)
5. **Old attempt soft-deleted ONLY when new attempt completes**

**Critical visibility rule:**
- Both old (complete) and new (draft/submitted) attempts visible on Home Screen during retry
- Old attempt deleted only after new attempt marking succeeds
- Purpose: Student can compare old grade with draft, prevents losing access until replacement ready

**Why inheritance:**
- Cost optimization: Reuses existing marks for unchanged questions
- Prevents re-marking identical submissions (waste of API credits)
- Faster completion (only changed questions need marking)

---

## Soft Delete + Restore Pattern

**Purpose:** Support 5-second undo window for deletions without complex state tracking.

**Implementation:**
- Soft delete happens immediately when user taps [Delete] (sets `deleted_at`)
- Frontend shows undo toast with 5-second countdown
- If user taps [Undo], call restore endpoint (clears `deleted_at`)
- If timeout expires, `deleted_at` remains set
- Backend does NOT track "pending deletion" state

**Benefits:**
- Simple implementation (no state machine, no timers in backend)
- Immediate soft delete (appears deleted instantly)
- Optional restore (user-controlled undo)
- Acceptable trade-offs for MVP

**Edge cases (acceptable for MVP):**
- User deletes multiple items quickly → Only latest undo available
- User closes app during undo window → Deletion persists
- User navigates away → Toast persists until timeout

**Endpoints:**
- `DELETE /api/attempts/papers/{id}` - Soft delete paper attempt
- `POST /api/attempts/papers/{id}/restore` - Restore deleted attempt
- `DELETE /api/attempts/questions/{id}` - Soft delete practice attempt
- `POST /api/attempts/questions/{id}/restore` - Restore practice attempt

---

## Error Message Mapping

**Purpose:** Translate technical marking status codes to user-friendly messages.

**Mapping:**

| Database Status | User-Facing Message |
|----------------|---------------------|
| `rate_limit` | Rate limit exceeded |
| `timeout` | Request timeout |
| `llm_error` | LLM error |
| `parse_error` | Response parsing failed |
| `NULL` (no attempt) | Not attempted |

**Display context:** Failure list on Marking in Progress Screen

**Why this matters:**
- Students need clear error messages to understand failures
- Generic "marking failed" is not helpful
- Specific messages help with debugging
- User-facing language (not technical database codes)

---

## Status Polling Flow

**Pattern:** Client polls status endpoint during marking, navigates on completion/failure.

**User journey:**
1. User submits paper/question (Flow 2) → navigates to MarkingInProgressScreen
2. Screen polls status endpoint every 3 seconds
3. When status = `completed` → navigate to results screen
4. When status = `failed` → show retry option

**Endpoints:**
- `GET /api/attempts/papers/{id}/status` - Paper marking progress
- `GET /api/attempts/questions/{id}/status` - Practice question status

**Status values:**

| Paper Status | Meaning |
|--------------|---------|
| `draft` | Not yet submitted (`submitted_at IS NULL`) |
| `submitted` | Just submitted, marking not started |
| `marking` | Some questions marked, in progress |
| `ready_for_grading` | All questions marked, grade pending |
| `completed` | Grading complete (`completed_at IS NOT NULL`) |
| `failed` | All questions attempted, some failed |

| Question Status | Meaning |
|-----------------|---------|
| `draft` | Not yet submitted |
| `submitted` | Submitted, not yet marked |
| `completed` | Successfully marked |
| `failed` | Marking failed |

**Why derived status:**
- Single source of truth (timestamps + marking_attempts table)
- No stale status flags to synchronize
- See `PATTERNS.md` → Status Derivation Pattern

---

## View Results Flow

**Purpose:** Fetch marking results after paper/practice marking completes.

**Precondition:** Marking must be complete (paper has `completed_at`, or practice attempt has successful marking).

**User journey:**
1. User sees "completed" status on MarkingInProgressScreen
2. User navigates to PaperResultsScreen or QuestionResultsScreen
3. Screen fetches results from appropriate endpoint
4. Results display grades, per-question scores, feedback, and student work images

### Paper Results (Summary)

**Endpoint:** `GET /api/attempts/papers/{id}/results`

**Returns:** Paper-level summary (total marks, grade, per-question scores with navigation IDs)

**Why this endpoint exists:** PaperResultsScreen needs overview with clickable questions. Returns `question_attempt_id` for each question to enable navigation to detail screen.

### Question Results (Detail)

**Paper flow:** `GET /api/attempts/papers/{paper_id}/questions/{question_id}/results`

**Practice flow:** `GET /api/attempts/practice/{id}/results`

**Returns:** Detailed per-part results (marks, feedback, mark scheme criteria, student work images)

**Why separate endpoints:** See `PATTERNS.md` → Separate ID Namespaces

**Student work images:** Results include presigned download URLs for submission images. See `backend/STORAGE.md` → Presigned URL Security → Download for URL generation pattern.

---

## Related Documentation

- `PATTERNS.md` → General API patterns (from_domain, error handling, status derivation)
- `AUTHENTICATION.md` → JWT patterns
- `backend/STORAGE.md` → R2 upload flow, staging bucket patterns
- `backend/SUBMISSIONS.md` → Domain logic for submissions
