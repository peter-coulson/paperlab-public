"""Factory for creating LLM clients based on provider information.

Provides centralized logic for:
- Provider → Client class mapping
- API key retrieval and validation
- Client instantiation
- Model resolution and client creation for marking (with database lookup)

Design principles:
- Single source of truth for provider-client mapping
- Fail fast with clear errors
- Easy to extend (add new provider = update PROVIDER_CLIENTS dict)
- No database dependencies in low-level factory (services layer parallel to domain logic)
- High-level convenience functions use database for model resolution
- Follows "expand through data, not code" principle
"""

import sqlite3
from typing import TYPE_CHECKING

from paperlab.config import LLMProviders, settings

if TYPE_CHECKING:
    from paperlab.services.llm_client import BaseLLMClient


# ============================================================================
# Provider → Client Class Mapping
# ============================================================================
# NOTE: Actual imports happen lazily in factory functions
# to avoid circular imports and unnecessary SDK loads


def _get_anthropic_client(api_key: str, model_identifier: str) -> "BaseLLMClient":
    """Lazy import and instantiate Anthropic client."""
    from paperlab.services.claude_client import ClaudeClient

    return ClaudeClient(api_key=api_key, model_identifier=model_identifier)


def _get_openai_client(api_key: str, model_identifier: str) -> "BaseLLMClient":
    """Lazy import and instantiate OpenAI client."""
    from paperlab.services.openai_client import OpenAIClient

    return OpenAIClient(api_key=api_key, model_identifier=model_identifier)


def _get_google_client(api_key: str, model_identifier: str) -> "BaseLLMClient":
    """Lazy import and instantiate Google Gemini client via OpenAI compatibility."""
    from paperlab.services.openai_client import OpenAIClient

    return OpenAIClient(
        api_key=api_key,
        model_identifier=model_identifier,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        provider_name=LLMProviders.GOOGLE,
    )


# Map provider name → client factory function
# Uses LLMProviders constants for consistency (single source of truth)
PROVIDER_CLIENTS = {
    LLMProviders.ANTHROPIC: _get_anthropic_client,
    LLMProviders.OPENAI: _get_openai_client,
    LLMProviders.GOOGLE: _get_google_client,
}


# ============================================================================
# Public API
# ============================================================================


def get_client_for_provider(provider: str, model_identifier: str) -> "BaseLLMClient":
    """Get LLM client for specified provider (no database dependency).

    Factory method that:
    1. Validates provider has client implementation
    2. Retrieves API key from config (environment variables)
    3. Instantiates and returns appropriate client

    Args:
        provider: Provider name (e.g., 'anthropic', 'openai')
        model_identifier: Model identifier for API calls (e.g., 'claude-sonnet-4-5-20250929')

    Returns:
        Instantiated LLM client ready for use

    Raises:
        ValueError: If provider unsupported or API key missing

    Example:
        >>> # Caller does database lookup
        >>> model_info = llm_models.get_by_identifier("claude-sonnet-4-5-20250929", conn)
        >>> # Factory creates client from provider info
        >>> client = get_client_for_provider(model_info["provider"], "claude-sonnet-4-5-20250929")
        >>> response = client.mark_question(system, user, image_path)
    """
    # Step 1: Validate provider has client implementation
    if provider not in PROVIDER_CLIENTS:
        raise ValueError(
            f"No client implementation for provider: {provider}\n"
            f"Supported providers: {', '.join(PROVIDER_CLIENTS.keys())}\n"
            "To add support: implement new client in services/ and update PROVIDER_CLIENTS"
        )

    # Step 2: Get API key from config (fails if not configured)
    try:
        api_key = settings.get_api_key_for_provider(provider)
    except ValueError as e:
        raise ValueError(
            f"Cannot create client for {provider}: {e}\n"
            f"Provider '{provider}' requires API key.\n"
            "See .env.example for configuration details."
        ) from e

    # Step 3: Instantiate client using factory function
    client_factory_fn = PROVIDER_CLIENTS[provider]
    return client_factory_fn(api_key, model_identifier)


def list_available_providers() -> list[str]:
    """List all providers with client implementations.

    Returns:
        List of provider names (e.g., ['anthropic', 'openai', 'google'])

    Example:
        >>> providers = list_available_providers()
        >>> print(f"Supported providers: {', '.join(providers)}")
    """
    return list(PROVIDER_CLIENTS.keys())


def get_marking_client(
    model_identifier: str | None,
    conn: sqlite3.Connection,
) -> tuple["BaseLLMClient", int]:
    """Resolve model identifier and create LLM client for marking.

    This is a high-level convenience function that combines:
    1. Model identifier resolution (None → default from settings)
    2. Database lookup (identifier → provider + model_id)
    3. Client creation (provider → configured LLM client)

    Designed to eliminate duplication in CLI commands and prepare for frontend usage.
    Single source of truth for "model identifier → ready-to-use client" logic.

    Args:
        model_identifier: Model identifier (e.g., 'claude-sonnet-4-5-20250929')
                         If None, uses settings.default_model
        conn: Database connection (for model lookup)

    Returns:
        Tuple of (client, llm_model_id):
        - client: Configured LLM client ready for marking
        - llm_model_id: Database ID of the model (for recording attempts)

    Raises:
        ValueError: If model not found in database or provider unsupported

    Example:
        >>> # CLI usage
        >>> with connection() as conn:
        ...     client, model_id = get_marking_client(model_arg, conn)
        ...     attempt_id = marker.mark_submission(submission_id, model_id, conn)

        >>> # Frontend API usage (same function)
        >>> client, model_id = get_marking_client(request.model, conn)
    """
    # Import here to avoid circular dependency (repositories import from services)
    from paperlab.data.repositories.marking import llm_models

    # Step 1: Resolve model identifier (None → default)
    resolved_model = model_identifier or settings.default_model

    # Step 2: Database lookup (raises ValueError if not found)
    model_info = llm_models.get_by_identifier(resolved_model, conn)
    llm_model_id = int(model_info["id"])
    provider = model_info["provider"]

    # Step 3: Create client (raises ValueError if provider unsupported or API key missing)
    client = get_client_for_provider(provider, resolved_model)

    return (client, llm_model_id)
