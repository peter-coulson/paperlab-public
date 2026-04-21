"""Application startup validation.

Validates environment configuration after config loads but before app executes.
Provides fail-fast behavior without creating circular imports.

Design:
- Runs early in CLI lifecycle (before command dispatch)
- Validates cross-module dependencies (config + database + services)
- Config module stays import-free; validation lives here instead
"""

from paperlab.config import settings


def validate_environment(require_llm: bool = True) -> None:
    """Validate environment before app starts.

    Runs after config loads but before CLI commands execute.
    Fails fast with clear errors if environment is misconfigured.

    Args:
        require_llm: If True, validates LLM model and API key configuration.
                     Set to False for commands that don't use LLM functionality.

    Validates:
    1. Default LLM model exists in database (if require_llm=True)
    2. API key is configured for the model's provider (if require_llm=True)

    Raises:
        ValueError: If environment is misconfigured

    Note:
        Skips LLM validation if default_model is not set (allows startup without LLM config).
        Uses late imports to avoid circular dependencies.
    """
    # Skip LLM validation if not required or if default_model not set
    if not require_llm or not settings.default_model:
        return

    try:
        # Late import to avoid circular dependency
        from paperlab.data.database import connection
        from paperlab.data.repositories.marking import llm_models

        with connection() as conn:
            # Check model exists in database
            model = llm_models.get_by_identifier(settings.default_model, conn)
            provider = model["provider"]

            # Check provider has API key configured
            settings.get_api_key_for_provider(provider)

    except Exception as e:
        raise ValueError(
            f"Invalid default_model configuration '{settings.default_model}': {e}\n"
            "Ensure:\n"
            "  1. Model exists in llm_models table (check with: paperlab llm models)\n"
            "  2. Provider API key is configured in .env file\n"
            "  3. Database is initialized (run: paperlab db init)"
        ) from e
