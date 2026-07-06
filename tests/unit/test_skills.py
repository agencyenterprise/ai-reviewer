"""Tests for the shared skill-prompt loader (`lib/skills.py`).

Covers frontmatter stripping, the missing-skill error, and that the skills
backing non-SimpleDeepAgent agents load cleanly. SimpleDeepAgentManifest
prompt resolution is covered in
tests/unit/workflows/simple_deep_agent/test_skill_prompt.py.
"""

import pytest

from lib.skills import _strip_frontmatter, load_skill_prompt


def test_strip_frontmatter_removes_leading_yaml_block():
    content = "---\nname: foo\ndescription: bar\n---\n\n# Title\n\nBody"
    assert _strip_frontmatter(content) == "# Title\n\nBody"


def test_strip_frontmatter_no_frontmatter_is_unchanged():
    content = "# Title\n\nBody text"
    assert _strip_frontmatter(content) == content


def test_strip_frontmatter_unterminated_block_is_unchanged():
    content = "---\nname: foo\nno closing delimiter"
    assert _strip_frontmatter(content) == content


def test_load_skill_prompt_missing_skill_raises():
    with pytest.raises(FileNotFoundError):
        load_skill_prompt("does-not-exist")


# Agents that load their system prompt verbatim from a skill (the single source
# of truth). Guards against a renamed/missing skill file.
_SKILL_BACKED_AGENTS = [
    "reviewer-2",
    "inference-validation",
    "reference-download",
    "literature-review",
    "live-reports",
    "methodology-extraction",
    "methodology-comparison",
    "reproducibility-check",
    "reference-extraction",
    "advocacy-tone",
    "about-this-preface",
    "about-this-authors",
    "abbreviation-extraction",
    "abbreviation-scan",
    "citation-support",
]


@pytest.mark.parametrize("skill", _SKILL_BACKED_AGENTS)
def test_skill_loads_non_empty_without_frontmatter(skill: str):
    body = load_skill_prompt(skill)
    assert body.strip()
    assert not body.lstrip().startswith("---")
