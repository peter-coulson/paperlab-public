# Repository Patterns

Data access patterns for PaperLab backend.

---

## Repository Layer Responsibility

**Principle:** Repository layer owns ALL database interaction. Domain logic never writes SQL.

**Location:** `src/paperlab/data/repositories/`

**Pattern:**
```
Domain Logic → Repository Functions → SQL Execution → Database
```

**Why:**
- Single source of truth for queries
- Domain logic stays database-agnostic
- Easy to test (mock repositories)

---

## Soft Delete Pattern

**Purpose:** Preserve data for undo/restore operations without permanent deletion.

**Implementation:**

```python
def soft_delete_attempt(
    attempt_id: int,
    deleted_by: int,
    conn: sqlite3.Connection
) -> None:
    """Soft delete by setting deleted_at timestamp."""
    cursor = conn.execute(
        """
        UPDATE paper_attempts
        SET deleted_at = CURRENT_TIMESTAMP,
            deleted_by = ?
        WHERE id = ? AND deleted_at IS NULL
        """,
        (deleted_by, attempt_id)
    )

    if cursor.rowcount == 0:
        raise ValueError(f"Attempt {attempt_id} not found or already deleted")
```

**Key characteristics:**
- Sets `deleted_at` timestamp (not actual deletion)
- Records `deleted_by` for audit trail
- Raises `ValueError` if already deleted or not found
- WHERE clause checks `deleted_at IS NULL` (prevents double-delete)

**Why soft delete:**
- Undo support (restore within time window)
- Audit trail (who deleted when)
- Data integrity (preserves foreign key relationships)

**Where:** See `src/paperlab/data/repositories/marking/paper_attempts.py` and `practice.py`

---

## Restore Pattern

**Purpose:** Reverse soft deletion by clearing deleted_at timestamp.

**Implementation:**

```python
def restore_attempt(
    attempt_id: int,
    restored_by: int,
    conn: sqlite3.Connection
) -> None:
    """Restore soft-deleted attempt."""
    cursor = conn.execute(
        """
        UPDATE paper_attempts
        SET deleted_at = NULL,
            deleted_by = NULL,
            restored_by = ?,
            restored_at = CURRENT_TIMESTAMP
        WHERE id = ? AND deleted_at IS NOT NULL
        """,
        (restored_by, attempt_id)
    )

    if cursor.rowcount == 0:
        raise ValueError(f"Attempt {attempt_id} not found or not deleted")
```

**Key characteristics:**
- Clears `deleted_at` (makes visible again)
- Records `restored_by` and `restored_at` for audit
- Raises `ValueError` if not currently deleted
- WHERE clause checks `deleted_at IS NOT NULL` (can only restore deleted items)

**Where:** See `src/paperlab/data/repositories/marking/paper_attempts.py` and `practice.py`

---

## ValueError for Not Found

**Pattern:** Repositories raise `ValueError` when record not found or invalid state.

```python
if cursor.rowcount == 0:
    raise ValueError(f"Attempt {attempt_id} not found")
```

**Why ValueError:**
- Domain-level exception (not HTTP-specific)
- API layer translates to 404 (see `api/PATTERNS.md`)
- CLI layer shows user-friendly error
- Repositories stay transport-agnostic

**Alternative approach rejected:** Custom exceptions like `NotFoundError` add complexity without benefit. ValueError is semantic and standard.

---

## List with Filtering Pattern

**Pattern:** List functions filter out soft-deleted records by default.

```python
def get_attempts_for_student(
    student_id: int,
    conn: sqlite3.Connection
) -> list[dict]:
    """Get all non-deleted attempts for student."""
    cursor = conn.execute(
        """
        SELECT id, attempt_uuid, paper_name, created_at, submitted_at, completed_at
        FROM paper_attempts
        WHERE student_id = ? AND deleted_at IS NULL
        ORDER BY created_at DESC
        """,
        (student_id,)
    )
    return [dict(row) for row in cursor.fetchall()]
```

**Key characteristics:**
- WHERE clause includes `deleted_at IS NULL`
- Orders by `created_at DESC` (newest first)
- Returns list of dicts (domain layer converts to dataclasses)

**Where:** See `src/paperlab/data/repositories/marking/paper_attempts.py`

---

## Connection Management

**Pattern:** Repository functions receive connection, never create it (Pattern A).

```python
def some_repository_function(
    param: int,
    conn: sqlite3.Connection
) -> ResultType:
    """Repository function signature."""
    cursor = conn.execute("SELECT ...", (param,))
    return process_result(cursor)
```

**Why:**
- Transaction boundaries controlled by caller (CLI or API)
- Repositories are pure data access (no transaction logic)
- Easy to compose multiple repository calls in one transaction

**See:** `backend/ARCHITECTURE.md` → Connection Management (Pattern A)

---

## Related Documentation

- `backend/ARCHITECTURE.md` → Pattern A connection management
- `backend/DATABASE.md` → Database setup and schema
- `api/PATTERNS.md` → API error handling (ValueError → 404)
- `api/WORKFLOWS.md` → Soft delete/restore API flows
