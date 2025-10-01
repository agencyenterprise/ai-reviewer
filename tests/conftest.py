"""Shared test utilities for all agent tests.

This module provides reusable utilities that work across all agent test suites:
- Path resolution
- Document loading
- Supporting documents formatting
"""

import asyncio
from pathlib import Path
from typing import Optional, Any

import pytest

from lib.services.file import create_file_document_from_path


# Root tests directory
TESTS_DIR = Path(__file__).parent


# Store test case data during test execution
_agent_test_case_data = {}


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

            def serialize_field_selector(field_selector):
                """Convert sets to lists recursively in field selectors."""
                if isinstance(field_selector, set):
                    return list(field_selector)
                elif isinstance(field_selector, dict):
                    return {
                        k: serialize_field_selector(v)
                        for k, v in field_selector.items()
                    }
                else:
                    return field_selector

            # Store in global dict for later retrieval
            _agent_test_case_data[item.nodeid] = {
                "name": case.name,
                "agent": {
                    "name": case.agent.name,
                    "version": case.agent.version,
                },
                "prompt_kwargs": {
                    # Truncate large fields for readability
                    k: (v[:200] + "..." if isinstance(v, str) and len(v) > 200 else v)
                    for k, v in case.prompt_kwargs.items()
                },
                "expected_output": case.expected_dict,
                "actual_outputs": [
                    result.model_dump() for result in (case.results or [])
                ],
                "evaluation_config": {
                    "strict_fields": serialize_field_selector(case.strict_fields),
                    "llm_fields": serialize_field_selector(case.llm_fields),
                    "evaluator_model": case.evaluator_model,
                    "run_count": case.run_count,
                },
                "evaluation_result": eval_result,
            }


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
