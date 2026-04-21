"""Repository for llm_models table.

Provides data access methods for LLM model metadata.
Used by client factory to map model identifiers to providers.
"""

import sqlite3
from typing import TypedDict


class LLMModelInfo(TypedDict):
    """Type-safe representation of LLM model data.

    Returned by all repository methods to provide clear type information
    about which fields are available and their types.
    """

    id: int
    model_identifier: str
    display_name: str
    provider: str


def get_by_identifier(model_identifier: str, conn: sqlite3.Connection) -> LLMModelInfo:
    """Look up LLM model by identifier.

    Args:
        model_identifier: Model identifier (e.g., 'claude-sonnet-4-5-20250929')
        conn: Database connection

    Returns:
        LLMModelInfo dict with keys: id, model_identifier, display_name, provider

    Raises:
        ValueError: If model not found in database

    Example:
        >>> model = get_by_identifier("claude-sonnet-4-5-20250929", conn)
        >>> print(model["provider"])  # "anthropic"
        >>> print(model["id"])  # 1
    """
    cursor = conn.execute(
        """
        SELECT id, model_identifier, display_name, provider
        FROM llm_models
        WHERE model_identifier = ?
        """,
        (model_identifier,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"LLM model not found: {model_identifier}\n"
            "Ensure the model exists in the llm_models table.\n"
            "Available models can be queried with get_all()."
        )

    return LLMModelInfo(
        id=int(row[0]),
        model_identifier=str(row[1]),
        display_name=str(row[2]),
        provider=str(row[3]),
    )


def get_by_id(llm_model_id: int, conn: sqlite3.Connection) -> LLMModelInfo:
    """Look up LLM model by database ID.

    Args:
        llm_model_id: Database ID
        conn: Database connection

    Returns:
        LLMModelInfo dict with keys: id, model_identifier, display_name, provider

    Raises:
        ValueError: If model not found

    Example:
        >>> model = get_by_id(1, conn)
        >>> print(model["model_identifier"])  # "claude-sonnet-4-5-20250929"
    """
    cursor = conn.execute(
        """
        SELECT id, model_identifier, display_name, provider
        FROM llm_models
        WHERE id = ?
        """,
        (llm_model_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(
            f"LLM model not found with id: {llm_model_id}\n"
            "Ensure the model exists in the llm_models table."
        )

    return LLMModelInfo(
        id=int(row[0]),
        model_identifier=str(row[1]),
        display_name=str(row[2]),
        provider=str(row[3]),
    )


def exists(model_identifier: str, conn: sqlite3.Connection) -> bool:
    """Check if LLM model exists.

    Args:
        model_identifier: Model identifier
        conn: Database connection

    Returns:
        True if model exists, False otherwise

    Example:
        >>> if exists("claude-sonnet-4-5-20250929", conn):
        ...     print("Model available")
    """
    cursor = conn.execute(
        """
        SELECT 1
        FROM llm_models
        WHERE model_identifier = ?
        """,
        (model_identifier,),
    )
    return cursor.fetchone() is not None


def get_all(conn: sqlite3.Connection) -> list[LLMModelInfo]:
    """Get all LLM models.

    Args:
        conn: Database connection

    Returns:
        List of LLMModelInfo dicts, each with keys: id, model_identifier, display_name, provider
        Sorted by provider, then display_name

    Example:
        >>> models = get_all(conn)
        >>> for model in models:
        ...     print(f"{model['provider']}: {model['display_name']}")
        anthropic: Claude Sonnet 4.5
        anthropic: Claude Opus 4
    """
    cursor = conn.execute(
        """
        SELECT id, model_identifier, display_name, provider
        FROM llm_models
        ORDER BY provider, display_name
        """
    )

    return [
        LLMModelInfo(
            id=int(row[0]),
            model_identifier=str(row[1]),
            display_name=str(row[2]),
            provider=str(row[3]),
        )
        for row in cursor.fetchall()
    ]


def get_all_by_provider(provider: str, conn: sqlite3.Connection) -> list[LLMModelInfo]:
    """Get all LLM models for a specific provider.

    Useful for comparing models from the same provider.

    Args:
        provider: Provider name (e.g., 'anthropic', 'openai')
        conn: Database connection

    Returns:
        List of LLMModelInfo dicts, each with keys: id, model_identifier, display_name, provider
        Sorted by display_name

    Example:
        >>> anthropic_models = get_all_by_provider("anthropic", conn)
        >>> print(f"Found {len(anthropic_models)} Anthropic models")
    """
    cursor = conn.execute(
        """
        SELECT id, model_identifier, display_name, provider
        FROM llm_models
        WHERE provider = ?
        ORDER BY display_name
        """,
        (provider,),
    )

    return [
        LLMModelInfo(
            id=int(row[0]),
            model_identifier=str(row[1]),
            display_name=str(row[2]),
            provider=str(row[3]),
        )
        for row in cursor.fetchall()
    ]


def create_models_batch(
    models: list[dict[str, str]],
    conn: sqlite3.Connection,
) -> int:
    """Create multiple LLM models in batch using single SQL operation.

    Uses executemany() for efficient batch insertion.
    Accepts list of dictionaries with primitive values (no domain model dependency).

    Does NOT commit - caller manages transaction.

    Args:
        models: List of model dictionaries with keys:
            - model_identifier: str (unique identifier)
            - display_name: str (human-readable name)
            - provider: str (provider name)
        conn: Database connection

    Returns:
        Number of rows inserted (should equal len(models))

    Raises:
        sqlite3.IntegrityError: If model_identifier already exists or constraints violated
        ValueError: If required keys missing

    Example:
        >>> models = [
        ...     {
        ...         "model_identifier": "claude-sonnet-4-5-20250929",
        ...         "display_name": "Claude Sonnet 4.5",
        ...         "provider": "anthropic"
        ...     },
        ...     {
        ...         "model_identifier": "gpt-4o",
        ...         "display_name": "GPT-4o",
        ...         "provider": "openai"
        ...     }
        ... ]
        >>> count = create_models_batch(models, conn)
        >>> conn.commit()
    """
    if not models:
        return 0

    # Prepare data tuples for executemany
    data = [
        (
            model["model_identifier"],
            model["display_name"],
            model["provider"],
        )
        for model in models
    ]

    # Single batch INSERT
    cursor = conn.executemany(
        """
        INSERT INTO llm_models (model_identifier, display_name, provider)
        VALUES (?, ?, ?)
        """,
        data,
    )

    return cursor.rowcount


def count_models(conn: sqlite3.Connection) -> int:
    """Count total number of LLM models.

    Args:
        conn: Database connection

    Returns:
        Number of models in database

    Example:
        >>> count = count_models(conn)
        >>> print(f"Database contains {count} models")
    """
    cursor = conn.execute("SELECT COUNT(*) FROM llm_models")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def delete_all(conn: sqlite3.Connection) -> None:
    """Delete all LLM models from database.

    Used by loader in replace mode to clear existing models before loading new ones.

    Args:
        conn: Database connection

    Warning:
        This is a destructive operation. Caller should handle confirmation prompts.

    Example:
        >>> delete_all(conn)
        >>> conn.commit()  # Must explicitly commit
    """
    conn.execute("DELETE FROM llm_models")
