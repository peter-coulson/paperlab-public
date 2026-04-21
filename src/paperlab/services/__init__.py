"""Services layer for external integrations.

Handles communication with external APIs and services:
- LLM providers (Anthropic, OpenAI, etc.)
- Future: Storage services, external APIs, etc.

Design principles:
- Provider-agnostic interfaces
- Dependency injection
- Proper error handling with retries
- API key security (environment variables only)
"""

from paperlab.services import client_factory, llm_client

__all__ = [
    "client_factory",
    "llm_client",
]
