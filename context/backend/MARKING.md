# Marking Pipeline

Marking execution patterns for LLM-based assessment.

---

## Overview

The marking pipeline marks existing submissions using LLM. Submissions must exist first (see `SUBMISSIONS.md`).

**Key characteristics:**
- Operates on existing submissions (requires submission_id)
- Multi-phase: build prompt → call LLM → parse → store
- Validation at every boundary
- Connection released during LLM calls (long-running)

---

## Pipeline Flow

```
Input: submission_id, llm_model_id
    ↓
Load submission + resolve image paths (R2 → presigned URLs)
    ↓
Build prompts (read connection, then release)
    ↓
Resize images (512px max) + encode to base64
    ↓
Call LLM (no connection held - may take 5-30 seconds)
    ↓
Parse JSON + validate (multi-strategy extraction)
    ↓
Store attempt + results (write connection, commit)
    ↓
Output: marking_attempt_id
```

---

## Key Decisions

### Image Preprocessing

**Resize images to 512px before LLM encoding.**

**Why:**
- 99.1% accuracy at 512px vs 96.1% at original ~1200px (validated across 4 runs)
- Lower resolution reduces noise that confuses the model
- Faster response times (7.9s → 5.0s average)
- ~87% reduction in payload size

**Where:** `services/llm_client.py` `_encode_image()` method. Config: `IMAGE_MAX_DIMENSION`.

### Connection Management

**Don't hold database connections during LLM calls.**

**Why:** LLM API calls take 5-30 seconds. Holding connections wastes resources and risks timeouts.

**Pattern:**
1. Build prompts (read, close)
2. Call LLM (no connection)
3. Store results (write, commit)

### Three-Layer Validation

| Layer | Where | What |
|-------|-------|------|
| **1. Structure** | `models.py` (Pydantic) | Field types, basic constraints |
| **2. Business** | `validators.py` | Cross-validation against database |
| **3. Integrity** | Database schema | Foreign keys, CHECK constraints |

**Why:** Fail fast with clear errors. Don't rely on constraint violations for business rules.

### GENERAL Criteria

**Rule:** GENERAL criteria are guidance only, NOT marking criteria.

**Why:**
- Excluded from expected JSON structure (LLM never sees them)
- Validation rejects if LLM includes them
- Saves tokens, prevents confusion

### Expected JSON Structure

**Principle:** Pre-fill all criterion IDs in prompt.

**Why:** LLM fills in values, not structure. Reduces parsing errors 20-40x.

---

## Failure Modes

**All marking attempts are recorded for observability.**

| Status | Meaning | Retryable |
|--------|---------|-----------|
| `success` | Marking completed | No (already done) |
| `parse_error` | Malformed JSON | Yes |
| `rate_limit` | API rate limit | Yes |
| `timeout` | Request timeout | Yes |
| `llm_error` | Other API error | Yes |

**Failed attempt storage includes:** prompts, error message, token usage, timing.

**Why:** Debugging, cost tracking, retry intelligence.

---

## Duplicate Prevention

**Policy:** One successful marking per submission.

**Implementation:** `has_successful_attempt()` check before marking.

**Rationale:**
- Prevents accidental duplicate API calls (cost control)
- Failed attempts can retry indefinitely

---

## Batch Marking

**Purpose:** Mark multiple submissions in parallel.

**Module:** `src/paperlab/marking/batch_marker.py`

**Key patterns:**
- Thread-safe: One connection per worker thread
- Idempotent: Skips already-marked submissions
- Error isolation: Failures don't affect other submissions

**Parallelism:**
- Anthropic: 5 workers (50 RPM limit)
- OpenAI: 50 workers (500 RPM limit)

---

## Module Structure

| Module | Responsibility |
|--------|----------------|
| `marker.py` | Marking orchestration, connection lifecycle |
| `batch_marker.py` | Parallel batch processing |
| `prompt_builder.py` | Build MarkingRequest from templates + database |
| `parser.py` | Multi-strategy JSON extraction |
| `validators.py` | Business rule validation |
| `models.py` | MarkingRequest + Pydantic models for LLM responses |
| `exceptions.py` | Error hierarchy |

---

## Related Docs

- `SUBMISSIONS.md` - Submission creation (prerequisite)
- `PAPER-MARKING.md` - Full paper workflow
- `ARCHITECTURE.md` - LLM provider abstraction
