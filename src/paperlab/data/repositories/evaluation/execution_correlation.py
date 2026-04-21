"""Execution correlation repository for artifact extraction.

Manages temporary correlation table that maps marking requests to test cases
during artifact extraction from test_execution.db to evaluation_results.db.

Design principles:
- Temporary table lifecycle management (create/drop)
- Bulk operations for performance
- Clear separation: data access logic only (no orchestration)
"""

import sqlite3

from paperlab.config.constants import Tables

# Type alias for correlation data: (question_id, test_case_id, first_image_path)
# This is the single source of truth - imported by other modules
CorrelationData = list[tuple[int, int, str]]


def create_correlation_table(
    correlation_data: CorrelationData,
    conn: sqlite3.Connection,
) -> None:
    """Create correlation table for extraction.

    Creates a table mapping (question_id, test_case_id, first_image_path).
    First image path is denormalized for performance and validation.

    DESIGN TRADE-OFF: Denormalization vs Performance
    -----------------------------------------------
    first_image_path is duplicated from test_case_images table because:
    1. Performance: Enables simple 3-way JOIN (not 5-way) during extraction
    2. Validation: Uniqueness constraints enforced at schema level
    3. Clarity: Explicit correlation anchor visible in table

    This is acceptable because:
    - Temporary table (deleted with test_execution.db after extraction)
    - Single writer (request_builder.py creates once per execution)
    - Uniqueness enforced at multiple layers (schema + application + runtime)
    - Trade-off documented and intentional (not accidental duplication)

    Uniqueness constraints:
    - (question_id, first_image_path): Prevents ambiguous correlation
    - (test_case_id): One test case per execution

    This table is used to correlate marking_attempts back to test_cases
    without complex schema JOINs.

    Design decision: Table is created in test_execution.db (not evaluation_results.db)
    because it's metadata ABOUT test execution data. This enables:
    - Same-database JOINs for better performance (no ATTACH overhead)
    - Correlation survives extraction failures (aids debugging and retry)
    - Automatic cleanup when test_execution.db is deleted after successful extraction
    - Clear semantics: "enriched source data" not "extraction state"
    - Regular table (not TEMPORARY) ensures visibility across ATTACH operations

    Table lifecycle:
    - Created at extraction start (with marking results)
    - Used during bulk extraction queries (same-DB JOINs)
    - Dropped explicitly at extraction end (or via rollback on failure)
    - Deleted with test_execution.db after successful extraction

    Args:
        correlation_data: List of (question_id, test_case_id, first_image_path) tuples
        conn: Database connection (typically test_execution.db)

    Raises:
        sqlite3.IntegrityError: If uniqueness constraint violated
        sqlite3.Error: If table creation or insertion fails

    Example:
        >>> from paperlab.data.database import connection
        >>> from pathlib import Path
        >>> correlation_data = [(1, 42, "path/to/image.png"), (2, 43, "path/to/other.png")]
        >>> test_db_path = Path("data/db/test_execution.db")
        >>> with connection(test_db_path) as conn:
        ...     create_correlation_table(correlation_data, conn)
        ...     # Table now exists in test_execution.db as regular table
        ...     # Will be deleted when test_execution.db is deleted
    """
    # Create correlation table (will be deleted when test_execution.db is deleted)
    conn.execute(f"""
        CREATE TABLE {Tables.EXECUTION_CORRELATION} (
            question_id INTEGER NOT NULL,
            test_case_id INTEGER NOT NULL,
            first_image_path TEXT NOT NULL,
            PRIMARY KEY (question_id, test_case_id),
            UNIQUE (question_id, first_image_path),
            UNIQUE (test_case_id),
            CHECK (first_image_path != '')
        )
    """)

    # Bulk insert correlation data
    conn.executemany(
        f"INSERT INTO {Tables.EXECUTION_CORRELATION} "
        "(question_id, test_case_id, first_image_path) VALUES (?, ?, ?)",
        correlation_data,
    )


def drop_correlation_table(conn: sqlite3.Connection) -> None:
    """Drop execution correlation table.

    Explicitly drops the execution_correlation table after extraction completes.
    Safe to call even if table doesn't exist (uses IF EXISTS).

    This cleanup is optional since test_execution.db is deleted after successful
    extraction anyway. However, explicit cleanup is clearer and ensures the table
    is removed before commit, making the extraction transaction atomic.

    Note: If extraction fails and rollback occurs, this DROP is also rolled back,
    leaving correlation table intact for debugging and retry attempts.

    Args:
        conn: Database connection (typically test_execution.db)

    Example:
        >>> from paperlab.data.database import connection
        >>> from pathlib import Path
        >>> test_db_path = Path("data/db/test_execution.db")
        >>> with connection(test_db_path) as conn:
        ...     # After extraction is complete
        ...     drop_correlation_table(conn)
    """
    conn.execute(f"DROP TABLE IF EXISTS {Tables.EXECUTION_CORRELATION}")
