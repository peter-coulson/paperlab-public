"""Import smoke test for all paperlab modules.

Validates that all modules can be imported without errors.
Catches:
- Broken imports
- Circular dependencies
- Missing dependencies
- Syntax errors
"""

import importlib

import pytest

MODULES_TO_TEST = [
    # Top-level packages
    "paperlab.api",
    "paperlab.cli",
    "paperlab.config",
    "paperlab.constants",
    "paperlab.data",
    "paperlab.evaluation",
    "paperlab.loaders",
    "paperlab.loading",
    "paperlab.markdown",
    "paperlab.marking",
    "paperlab.paper_marking",
    "paperlab.services",
    "paperlab.startup",
    "paperlab.storage",
    "paperlab.submissions",
    "paperlab.utils",
    # API layer
    "paperlab.api.main",
    "paperlab.api.auth",
    "paperlab.api.models",
    # CLI layer
    "paperlab.cli.main",
    "paperlab.cli.commands",
    # Data layer
    "paperlab.data.database",
    "paperlab.data.models",
    "paperlab.data.repositories",
    "paperlab.data.repositories.marking",
    "paperlab.data.repositories.evaluation",
    # Evaluation layer
    "paperlab.evaluation.execution",
    "paperlab.evaluation.generation",
    "paperlab.evaluation.loading",
    "paperlab.evaluation.services",
    # Loading layer
    "paperlab.loading.models",
    "paperlab.loading.validators",
    # Services layer
    "paperlab.services.client_factory",
    "paperlab.services.llm_client",
]


@pytest.mark.parametrize("module_name", MODULES_TO_TEST)
def test_module_imports(module_name: str) -> None:
    """Test that module can be imported without errors."""
    try:
        importlib.import_module(module_name)
    except ImportError as e:
        pytest.fail(
            f"Failed to import {module_name}\n"
            f"Error: {e}\n"
            f"This usually indicates:\n"
            f"  - Missing dependency in pyproject.toml\n"
            f"  - Circular import dependency\n"
            f"  - Syntax error in the module"
        )
    except Exception as e:
        pytest.fail(
            f"Unexpected error importing {module_name}\n"
            f"Error type: {type(e).__name__}\n"
            f"Error: {e}"
        )
