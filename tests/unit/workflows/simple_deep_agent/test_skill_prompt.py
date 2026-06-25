"""Tests for SimpleDeepAgentManifest prompt resolution (source of truth).

The shared loader (`lib/skills.py`) is tested in tests/unit/test_skills.py;
here we cover how SimpleDeepAgentManifest resolves its prompt from a `skill`
reference or an inline `user_prompt`.
"""

import pytest

from lib.workflows.models import WorkflowRunType
from lib.workflows.registry import get_workflow_manifest
from lib.workflows.simple_deep_agent.manifest_base import SimpleDeepAgentManifest

# SimpleDeepAgent workflows whose rules live in a skill file.
_SKILL_BACKED_WORKFLOWS = [
    WorkflowRunType.FIGURES_TABLES_CHECK,
    WorkflowRunType.DOCUMENT_STRUCTURE,
    WorkflowRunType.RECOMMENDATION_CHECK,
]


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
