# Storage Architecture

Cloudflare R2 object storage patterns for student photo submissions.

---

## Overview

**Storage strategy:** Two-bucket architecture separating temporary uploads (staging) from permanent submissions.

**Why R2:** Cost-effective object storage ($0.015/GB/month) with presigned URL support for direct client uploads (no backend bandwidth bottleneck).

**Critical constraint:** All submission images are immutable after creation (audit trail, marking reproducibility).

---

## Two-Bucket Pattern

### Staging Bucket (Temporary)

**Purpose:** Hold student photos during selection and preview phase (before submission).

**Characteristics:**
- Temporary storage (auto-deleted after confirmation or timeout)
- Student can upload/delete freely via presigned URLs
- No marking triggered, no cost commitment
- Client-writable (via presigned PUT URLs)

**Path format:** `staging/{session_id}/{image_id}.{ext}`

**Lifecycle:**
1. Created: Student starts photo selection
2. Active: During selection/preview (1-24 hours)
3. Deleted: After confirmation (moved to permanent) OR timeout (abandoned)

**Cleanup strategies:**
- Primary: Session-based (delete when session expires)
- Fallback: 24-hour TTL via R2 lifecycle rule
- Why hybrid: Precise cleanup when possible, guaranteed cleanup on failure

### Permanent Bucket (Immutable)

**Purpose:** Store confirmed submissions for marking (never auto-delete).

**Characteristics:**
- Permanent storage (audit trail, marking reproducibility)
- Immutable after creation (no updates, no deletes)
- Backend-only writes (students cannot write directly)
- Triggers marking pipeline on creation

**Path format:** `submissions/{submission_uuid}_page{NN}.{ext}`

**Example:**
```
submissions/a7b3c4d5-e6f7-8901-2345-6789abcdef01_page01.jpg
submissions/a7b3c4d5-e6f7-8901-2345-6789abcdef01_page02.jpg
```

**Why immutable:** Enables marking reproducibility (re-run exact same images), audit trail (investigate disputes), cost protection (prevent accidental re-marks).

---

## Atomic Commit Pattern

**Critical guarantee:** Staging → permanent + database happens atomically (all-or-nothing).

**Flow:**
1. Client confirms submission
2. Backend copies staging images → permanent storage
3. Backend creates `question_submissions` + `submission_images` rows
4. Backend deletes staging images
5. Backend commits transaction
6. Backend triggers marking pipeline

**Why atomic:** Ensures images and database are always in sync. If any step fails, entire operation rolls back (staging preserved for retry).

**See:** `src/paperlab/storage/storage.py` (R2Storage class) and `src/paperlab/submissions/submit_question.py` (orchestration).

---

## Presigned URL Security

**Pattern:** Backend generates time-limited presigned URLs, client uploads/downloads directly to/from R2.

**Why:** No backend bandwidth bottleneck, reduces latency, enables parallel uploads, matches M3 architecture (presigned URLs for LLM reads).

### Upload (Staging)

**Flow:**
1. Client requests presigned upload URL from backend
2. Backend generates presigned PUT URL (1-hour expiry)
3. Client uploads directly to R2 staging bucket
4. Client notifies backend of upload completion

**Permissions:** PUT only, staging bucket only, 1-hour expiry

**Security:**
- Short expiry prevents URL reuse
- Limited to staging bucket (cannot write to permanent)
- Session-scoped (cannot access other students' staging)

### Download (Permanent)

**Flow:**
1. Client requests presigned download URL for submission image
2. Backend validates student owns submission
3. Backend generates presigned GET URL (1-hour expiry)
4. Client downloads directly from R2

**Permissions:** GET only, specific object only, 1-hour expiry

**Security:**
- Ownership validation (student can only access own submissions)
- Object-scoped (cannot list bucket or access other submissions)
- Short expiry (cannot bookmark or share URLs)

---

## Public Image Access (LLM Marking)

**Purpose:** Enable LLM APIs (OpenAI, Anthropic) to fetch student work images directly from R2.

**Why needed:** LLMs mark submissions by analyzing images. Direct R2→LLM fetching avoids backend bandwidth bottleneck and base64 encoding overhead.

### M7 Implementation: r2.dev Public URLs

**Current approach (M7 beta):** Use Cloudflare-managed r2.dev subdomain for public read access.

**Format:** `https://pub-{hash}.r2.dev/submissions/{uuid}_page{NN}.{ext}`

**Configuration:** Enable r2.dev public URL in Cloudflare Dashboard, set `PAPERLAB_R2_PUBLIC_URL` environment variable.

**Trade-off:** Simple (zero config) vs Production-grade (rate limits, no security controls)

**Why safe for beta:** Rate limit headroom (10-20x), CDN caching, limited exposure (5-10 testers), UUIDs prevent enumeration, no student PII in filenames.

**Security:** ⚠️ All bucket contents publicly readable. Acceptable for M7 beta, **not acceptable for production**.

### M9 Migration: Custom Domain

**Target (M9 production launch):** Replace r2.dev with custom domain (e.g., `images.paperlab.app`)

**Why migrate:**
- **Remove rate limits** - Custom domains have no r2.dev throttling
- **Security controls** - Add Cloudflare WAF, bot protection, access rules
- **Professional branding** - Custom domain vs cloudflare subdomain
- **Disable r2.dev** - Prevent public bypass after adding WAF

**Implementation:** Connect custom subdomain in Cloudflare, update `PAPERLAB_R2_PUBLIC_URL`, disable r2.dev access, add WAF rules.

**Code location:** `src/paperlab/data/storage.py` → `generate_presigned_url()` contains TODO comments

**See also:** `ROADMAP.md` → M9 → "R2 custom domain setup"

---

## CORS Configuration

**Why needed:** Direct browser uploads/downloads are cross-origin requests (app domain ≠ R2 domain). Browsers block these without explicit CORS policy.

**Required for:**
- **Staging bucket:** Browser PUT uploads via presigned URLs (critical for upload flow)
- **Permanent bucket:** Browser GET downloads via presigned URLs (for displaying marked work in app)

**Configuration:** Cloudflare Dashboard → R2 → Bucket Settings → CORS Policy

**Key principle:** Development uses wildcard origins (varying ports/schemes), production restricts to app domain.

**Without CORS:** Browser rejects presigned URL uploads with CORS error, upload flow fails.

---

## Bucket Security Configuration

**Public access:** DISABLED on both buckets (default). Access only via presigned URLs with ownership validation.

**Why disabled:** Student work contains private data. Public access would expose all submissions without authentication.

**Encryption:** R2 encrypts all objects at rest by default (AES-256). No additional configuration needed.

**Access control:** Managed via presigned URLs with time expiry and ownership validation in backend.

---

## Copy-on-Edit Strategy

**Problem:** Student wants to edit photos for individual questions without re-uploading unchanged photos.

**Solution:** Copy unchanged photos to staging, allow modifications, create new submission with all photos.

**Trade-off:** Storage duplication (cheap) vs schema complexity (expensive). Chose duplication for simplicity.

**Flow:**
1. Client requests edit for submission
2. Backend copies permanent → staging
3. Client modifies photos in staging
4. Standard atomic commit creates new submission
5. Old submission preserved (immutable audit trail)

**Implementation:** Standard R2 copy operations, discovered during M6 API development.

---

## Cleanup Strategies

### Session-Based (Primary)

**Trigger:** Session expires (user logout, timeout, explicit end)

**Implementation:**
- Backend tracks active sessions in database
- On session end: Delete all staging images for session
- Immediate cleanup (no waiting for TTL)

**Benefits:** Precise, immediate, no orphaned staging images

### TTL-Based (Fallback)

**Trigger:** R2 lifecycle rule deletes objects older than 24 hours

**Implementation:**
- R2 bucket lifecycle policy (configured once)
- Automatic, no backend logic required

**Benefits:** Guaranteed cleanup if session tracking fails, handles crashed sessions

### Hybrid (Recommended)

**Use session-based when possible, rely on TTL as safety net.**

**Why:** Best of both worlds - precise cleanup with guaranteed fallback.

---

## Orphaned Submissions

**Definition:** Submission in permanent storage not referenced by any `question_attempts` or `practice_question_attempts`.

**Cause:** Photo edit workflow creates new submission, old submission becomes orphaned.

**Current behavior:** Preserved indefinitely (immutable audit trail).

**Future enhancement (post-M6):**
- Soft-delete orphaned submissions after 30 days
- Periodically purge from R2 storage (cron job)
- Maintains immutability during active use, cleans up obsolete data

---

## Error Handling

**Upload failures:** Client retries with exponential backoff (idempotent operations)

**Confirmation failures:** Rollback transaction, staging preserved for retry

**Cleanup failures:** Fallback from session-based to TTL-based (24-hour guarantee)

---

## Privacy Protection

**Why staging protects privacy:**
- Accidental uploads never reach permanent storage (deleted from staging)
- Abandoned uploads auto-deleted (no permanent record)
- Access control: Students can only access own images (session-scoped presigned URLs)

---

## Related Documentation

**Backend context:**
- `SUBMISSIONS.md` - Submission creation pipeline, attempt lifecycle, draft/retry/soft-delete patterns
- `ARCHITECTURE.md` - Connection management, transaction patterns

**API context:**
- `api/README.md` - R2 upload flow, presigned URL endpoints, error handling

**Implementation:**
- `src/paperlab/storage/storage.py` - R2Storage class (presigned URLs, copy, delete)
- `src/paperlab/submissions/submit_question.py` - Atomic commit orchestrator
- `src/paperlab/api/main.py` - Upload and submission endpoints

---

## Content Principles

**This context documents:**
- WHY two buckets (protects against accidental uploads, enables editing)
- WHERE patterns are used (atomic commit, presigned URLs, copy-on-edit)
- KEY architectural decisions (trade storage for simplicity, hybrid cleanup)
- STRATEGIC trade-offs (cost vs complexity analysis)

**This context does NOT document:**
- Complete R2 client implementations (see `src/paperlab/storage/storage.py`)
- Presigned URL generation code (see R2Storage class)
- Complete API endpoint specs (see `src/paperlab/api/main.py`)
- Step-by-step upload workflows (implementation details in code)
