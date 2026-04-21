"""CLI commands for LLM operations.

Commands:
- llm test: Test API connection for providers
- llm models: List available models
"""

import sys

from paperlab.config import LLMTestConfig, settings
from paperlab.config.constants import CLIMessages
from paperlab.data.database import connection
from paperlab.data.repositories.marking import llm_models
from paperlab.services.client_factory import list_available_providers


def test(provider: str | None = None, all_providers: bool = False) -> int:
    """Test LLM provider API connection.

    Args:
        provider: Specific provider to test (e.g., 'anthropic', 'openai')
        all_providers: Test all configured providers

    Returns:
        Exit code (0 if all tests pass, 1 if any fail)
    """
    providers_to_test: list[str] = []

    if all_providers:
        providers_to_test = list_available_providers()
    elif provider:
        providers_to_test = [provider]
    else:
        print(CLIMessages.LLM_MUST_SPECIFY_PROVIDER, file=sys.stderr)
        return 1

    print(CLIMessages.LLM_TEST_HEADER)

    all_passed = True

    for provider_name in providers_to_test:
        try:
            # Try to get API key (validates it exists and has correct format)
            api_key = settings.get_api_key_for_provider(provider_name)

            # Get a model for this provider to test
            with connection() as conn:
                models = llm_models.get_all_by_provider(provider_name, conn)

            if not models:
                _print_test_result(provider_name, False, CLIMessages.LLM_NO_MODELS_CONFIGURED)
                all_passed = False
                continue

            # Get model identifier for testing
            model_identifier = str(models[0]["model_identifier"])

            # Make minimal text-only API call directly to test connection
            # This doesn't save anything - just validates auth and connectivity
            try:
                _test_provider_connection(provider_name, api_key, model_identifier)
                _print_test_result(
                    provider_name,
                    True,
                    CLIMessages.LLM_TEST_SUCCESS.format(display_name=models[0]["display_name"]),
                )

            except Exception as e:
                _print_test_result(
                    provider_name, False, CLIMessages.LLM_TEST_FAILED.format(error=e)
                )
                all_passed = False

        except ValueError as e:
            # API key not configured
            _print_test_result(provider_name, False, str(e))
            all_passed = False
        except Exception as e:
            _print_test_result(
                provider_name, False, CLIMessages.LLM_UNEXPECTED_ERROR.format(error=e)
            )
            all_passed = False

    print()
    return 0 if all_passed else 1


def _print_test_result(provider: str, success: bool, message: str) -> None:
    """Format and print test result with consistent prefix.

    Args:
        provider: Provider name (e.g., 'anthropic', 'openai')
        success: Whether the test passed
        message: Result message to display
    """
    prefix = "✓" if success else "✗"
    print(f"{prefix} {provider}: {message}")


def _test_provider_connection(provider_name: str, api_key: str, model_identifier: str) -> None:
    """Make minimal text-only API call to test provider connection.

    This function makes a direct API call to validate authentication and connectivity.
    The response is NOT saved - it's only used to verify the connection works.

    Args:
        provider_name: Provider name (e.g., 'anthropic', 'openai')
        api_key: API key for the provider
        model_identifier: Model identifier to test with

    Raises:
        Exception: If connection test fails
    """
    from paperlab.config import LLMProviders

    if provider_name == LLMProviders.ANTHROPIC:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        # Minimal API call - just text, no image
        message = client.messages.create(
            model=model_identifier,
            max_tokens=LLMTestConfig.TEST_MAX_TOKENS,
            messages=[{"role": "user", "content": LLMTestConfig.TEST_MESSAGE}],
        )
        if not message.content:
            raise ValueError("Empty response from API")

    elif provider_name == LLMProviders.OPENAI:
        import openai

        openai_client = openai.OpenAI(api_key=api_key)
        # Minimal API call - just text, no image
        response = openai_client.chat.completions.create(
            model=model_identifier,
            max_tokens=LLMTestConfig.TEST_MAX_TOKENS,
            messages=[{"role": "user", "content": LLMTestConfig.TEST_MESSAGE}],
        )
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from API")

    elif provider_name == LLMProviders.GOOGLE:
        import openai

        # Google Gemini via OpenAI-compatible API
        google_client = openai.OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        # Minimal API call - just text, no image
        response = google_client.chat.completions.create(
            model=model_identifier,
            max_tokens=LLMTestConfig.TEST_MAX_TOKENS,
            messages=[{"role": "user", "content": LLMTestConfig.TEST_MESSAGE}],
        )
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from API")

    else:
        raise ValueError(f"Unsupported provider for testing: {provider_name}")


def models_list(provider: str | None = None) -> int:
    """List available LLM models.

    Args:
        provider: Filter by provider (e.g., 'anthropic', 'openai')

    Returns:
        Exit code (0 for success)
    """
    try:
        with connection() as conn:
            if provider:
                model_list = llm_models.get_all_by_provider(provider, conn)
                if not model_list:
                    print(CLIMessages.LLM_NO_MODELS_FOUND.format(provider=provider))
                    return 1
            else:
                model_list = llm_models.get_all(conn)

        if not model_list:
            print(CLIMessages.LLM_NO_MODELS_IN_DB)
            print(CLIMessages.LLM_RUN_DB_INIT)
            return 1

        print(CLIMessages.LLM_MODELS_HEADER)

        # Group by provider for better readability
        current_provider = None
        for model in model_list:
            provider = str(model["provider"])
            if provider != current_provider:
                current_provider = provider
                print(f"\n{current_provider.upper()}:")

            model_id = model["model_identifier"]
            display_name = model["display_name"]
            is_default = model_id == settings.default_model

            default_marker = " (default)" if is_default else ""
            print(f"  - {model_id}")
            print(f"    {display_name}{default_marker}")

        print()
        return 0

    except Exception as e:
        print(f"Error listing models: {e}", file=sys.stderr)
        return 1
