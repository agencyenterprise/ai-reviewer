"""Shared test utilities for all agent tests.

This module provides reusable utilities that work across all agent test suites:
- Path resolution
- Document loading
- Supporting documents formatting
"""
import asyncio
from pathlib import Path
from typing import Optional

from lib.services.file import create_file_document_from_path


# Root tests directory
TESTS_DIR = Path(__file__).parent


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
