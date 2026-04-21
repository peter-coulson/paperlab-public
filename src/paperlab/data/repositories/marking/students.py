"""Repository for students table.

Minimal students table: maps Supabase UID to local student_id.
User metadata (email, display_name) comes from Supabase JWT, not local DB.
"""

import sqlite3


def exists(student_id: int, conn: sqlite3.Connection) -> bool:
    """Check if student exists in database.

    Args:
        student_id: Database ID of student
        conn: Database connection

    Returns:
        True if student exists, False otherwise

    Example:
        >>> if students.exists(student_id=1, conn):
        ...     print("Student found")
    """
    cursor = conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,))
    return cursor.fetchone() is not None


def get_by_supabase_uid(supabase_uid: str, conn: sqlite3.Connection) -> int | None:
    """Get student ID by Supabase user UUID.

    Args:
        supabase_uid: Supabase auth.users UUID (from JWT 'sub' claim)
        conn: Database connection

    Returns:
        student_id if found, None otherwise

    Example:
        >>> with connection() as conn:
        ...     student_id = students.get_by_supabase_uid("550e8400-...", conn)
        ...     if student_id is None:
        ...         # Auto-create via get_or_create_by_supabase_uid
    """
    cursor = conn.execute(
        "SELECT id FROM students WHERE supabase_uid = ?",
        (supabase_uid,),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else None


def get_or_create_by_supabase_uid(supabase_uid: str, conn: sqlite3.Connection) -> int:
    """Get or create student by Supabase user UUID.

    Called on every authenticated API request. Creates student record if
    not found (auto-registration on first request).

    Handles race condition: if two requests try to create simultaneously,
    the second will catch IntegrityError and retry the SELECT.

    Does NOT commit - caller manages transaction.

    Args:
        supabase_uid: Supabase auth.users UUID (from JWT 'sub' claim)
        conn: Database connection

    Returns:
        student_id (existing or newly created)

    Raises:
        ValueError: If failed to create student record

    Example:
        >>> with connection() as conn:
        ...     student_id = students.get_or_create_by_supabase_uid("550e8400-...", conn)
        ...     conn.commit()
    """
    # Try to get existing student first
    existing_id = get_by_supabase_uid(supabase_uid, conn)
    if existing_id is not None:
        return existing_id

    # Create new student record
    try:
        cursor = conn.execute(
            "INSERT INTO students (supabase_uid) VALUES (?)",
            (supabase_uid,),
        )
        student_id = cursor.lastrowid
        if student_id is None:
            raise ValueError("Failed to create student record")
        return student_id
    except sqlite3.IntegrityError:
        # Race condition: another request created the record between our SELECT and INSERT
        # Retry the SELECT - record must exist now
        existing_id = get_by_supabase_uid(supabase_uid, conn)
        if existing_id is not None:
            return existing_id
        # Should never happen, but be defensive
        raise ValueError("Failed to create or find student record") from None
