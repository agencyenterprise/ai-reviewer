"""Shared test utilities for all agent tests.

This module provides reusable utilities that work across all agent test suites:
- Path resolution
- Document loading
- Supporting documents formatting
"""

import asyncio
import os
import uuid
from enum import Enum
from pathlib import Path
from typing import Optional, Any

import pytest

from lib.config.env import config
from lib.services.file import create_file_document_from_path
from lib.models.agent_test_case import AgentTestCase


# Root tests directory
TESTS_DIR = Path(__file__).parent


# Store test case data during test execution
_agent_test_case_data = {}

# Environment variable key for sharing session_id across workers
_SESSION_ID_ENV_VAR = "PYTEST_LANGFUSE_SESSION_ID"


def pytest_configure(config):
    """Generate and set a single session ID for the entire test run.

    For pytest-xdist parallel execution, the controller process generates
    the session_id and shares it with workers via environment variable.
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")

    if worker_id:
        session_id = os.environ.get(_SESSION_ID_ENV_VAR)
        if not session_id:
            session_id = str(uuid.uuid4())
    else:
        session_id = str(uuid.uuid4())
        os.environ[_SESSION_ID_ENV_VAR] = session_id

    AgentTestCase.set_shared_session_id(session_id)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store AgentTestCase metadata during test execution."""
    outcome = yield
    report = outcome.get_result()

    # Only process the call phase (actual test execution)
    if call.when == "call":
        # Try to extract AgentTestCase from test parameters
        if hasattr(item, "callspec") and "case" in item.callspec.params:
            case = item.callspec.params["case"]

            # Get evaluation result if test was run
            eval_result = None
            if hasattr(case, "_eval_result") and case._eval_result is not None:
                eval_result = case._eval_result.model_dump()

            def serialize_for_xdist(obj):
                """Convert enums and sets to serializable types for pytest-xdist.

                This recursively processes dictionaries, lists, and other structures
                to convert enums to their string values and sets to lists.
                """
                if isinstance(obj, Enum):
                    return obj.value
                elif isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: serialize_for_xdist(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [serialize_for_xdist(item) for item in obj]
                else:
                    return obj

            session_id = getattr(case, "session_id", None)

            # Serialize all data for xdist compatibility
            report.agent_test_case_data = serialize_for_xdist(
                {
                    "name": case.name,
                    "agent": {
                        "name": case.agent.name,
                        "version": case.agent.version,
                    },
                    "prompt_kwargs": {
                        # Truncate large fields for readability
                        k: (
                            v[:200] + "..."
                            if isinstance(v, str) and len(v) > 200
                            else v
                        )
                        for k, v in case.prompt_kwargs.items()
                    },
                    "expected_output": case.expected_dict,
                    "actual_outputs": [
                        result.model_dump() for result in (case.results or [])
                    ],
                    "evaluation_config": {
                        "strict_fields": serialize_for_xdist(case.strict_fields),
                        "llm_fields": serialize_for_xdist(case.llm_fields),
                        "evaluator_model": case.evaluator_model,
                        "run_count": case.run_count,
                    },
                    "evaluation_result": eval_result,
                    "session_id": session_id,
                }
            )


@pytest.hookimpl()
def pytest_runtest_logreport(report):
    """Collect AgentTestCase data from worker processes into main process dict.

    This hook runs in the main process and receives reports from all workers,
    making it compatible with pytest-xdist parallel execution.
    """
    if hasattr(report, "agent_test_case_data"):
        _agent_test_case_data[report.nodeid] = report.agent_test_case_data


@pytest.hookimpl()
def pytest_json_modifyreport(json_report):
    """Modify the JSON report to include AgentTestCase metadata."""
    # Add agent_test_case data to each test
    for test in json_report.get("tests", []):
        nodeid = test.get("nodeid")
        if nodeid in _agent_test_case_data:
            test["agent_test_case"] = _agent_test_case_data[nodeid]


def data_path(path: str) -> str:
    """
    Convert relative test data path to absolute path.

    Args:
        path: Relative path from tests/ directory (e.g., "data/common_knowledge/main.md")

    Returns:
        Absolute path to the file
    """
    return str(TESTS_DIR / path)


async def load_document(path: str):
    """
    Load a single document from test data.

    Args:
        path: Relative path from tests/ directory

    Returns:
        FileDocument object with markdown content
    """
    return await create_file_document_from_path(data_path(path))


async def load_document_markdown(path: str) -> str:
    """
    Load document and return only the markdown content.

    Args:
        path: Relative path from tests/ directory

    Returns:
        Markdown string content
    """
    doc = await load_document(path)
    return doc.markdown


async def build_supporting_documents_block(paths: list[str]) -> str:
    """
    Build supporting documents block from file paths.

    Loads multiple documents and concatenates them with separators,
    suitable for passing to agent prompts.

    Args:
        paths: List of relative paths from tests/ directory

    Returns:
        Concatenated markdown with "---" separators, or empty string if no paths
    """
    if not paths:
        return ""

    docs = []
    for path in paths:
        doc = await load_document(path)
        docs.append(doc.markdown)

    return "\n\n---\n\n".join(docs)
