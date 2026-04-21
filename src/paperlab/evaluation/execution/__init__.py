"""Test execution modules for running and extracting marking tests.

Connection management: CLI opens connections and passes them to orchestration
functions as parameters. See context/ARCHITECTURE.md for details.
"""

from paperlab.data.repositories.evaluation.execution_correlation import CorrelationData
from paperlab.evaluation.execution.artifact_extractor import (
    extract_test_execution_artifacts,
)
from paperlab.evaluation.execution.request_builder import build_submissions_and_correlation
from paperlab.evaluation.execution.test_database import (
    create_test_execution_db,
    delete_test_execution_db,
)
from paperlab.evaluation.execution.test_execution_loader import load_test_execution_data

__all__ = [
    "CorrelationData",
    "build_submissions_and_correlation",
    "create_test_execution_db",
    "delete_test_execution_db",
    "extract_test_execution_artifacts",
    "load_test_execution_data",
]
