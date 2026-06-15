"""Tests for resolving deep-agent prompts from skill files (source of truth)."""

import pytest

from lib.workflows.models import WorkflowRunType
from lib.workflows.registry import get_workflow_manifest
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest
from lib.workflows.simple_deep_agent.skill_prompt import (
    _strip_frontmatter,
    load_skill_prompt,
)

# The Tier 1 workflows whose rules live in a skill file.
_SKILL_BACKED_WORKFLOWS = [
    WorkflowRunType.FIGURES_TABLES_CHECK,
    WorkflowRunType.DOCUMENT_STRUCTURE,
    WorkflowRunType.RECOMMENDATION_CHECK,
]


def test_strip_frontmatter_removes_leading_yaml_block():
    content = "---\nname: foo\ndescription: bar\n---\n\n# Title\n\nBody text"
    assert _strip_frontmatter(content) == "# Title\n\nBody text"


def test_strip_frontmatter_no_frontmatter_is_unchanged():
    content = "# Title\n\nBody text"
    assert _strip_frontmatter(content) == content


def test_strip_frontmatter_unterminated_block_is_unchanged():
    content = "---\nname: foo\nno closing delimiter"
    assert _strip_frontmatter(content) == content


def test_load_skill_prompt_missing_skill_raises():
    with pytest.raises(FileNotFoundError):
        load_skill_prompt("does-not-exist")


@pytest.mark.parametrize("workflow_type", _SKILL_BACKED_WORKFLOWS)
def test_skill_backed_manifest_resolves_prompt(workflow_type: WorkflowRunType):
    manifest = get_workflow_manifest(workflow_type)
    assert isinstance(manifest, SimpleDeepAgentManifest)
    assert manifest.skill is not None
    assert manifest.user_prompt is None

    prompt = manifest.resolve_user_prompt()
    assert prompt.strip()
    # Frontmatter must be stripped — the prompt is markdown, not YAML.
    assert not prompt.lstrip().startswith("---")


def test_resolve_user_prompt_requires_a_source():
    class _Bare(SimpleDeepAgentManifest):
        type = WorkflowRunType.FIGURES_TABLES_CHECK
        name = "bare"
        description = "no prompt source"

    with pytest.raises(ValueError, match="skill.*user_prompt"):
        _Bare().resolve_user_prompt()


def test_inline_user_prompt_still_supported():
    class _Inline(SimpleDeepAgentManifest):
        type = WorkflowRunType.FIGURES_TABLES_CHECK
        name = "inline"
        description = "inline prompt"
        user_prompt = "Check the thing."

    assert _Inline().resolve_user_prompt() == "Check the thing."
