"""Tests for the shared skill-prompt loader (`lib/skills.py`).

Covers frontmatter stripping, interactive-only stripping, the missing-skill
error, and that the skills backing non-SimpleDeepAgent agents load cleanly.
SimpleDeepAgentManifest prompt resolution is covered in
tests/unit/workflows/simple_deep_agent/test_skill_prompt.py.
"""

import re
from pathlib import Path

import pytest

from lib.api.mcp.serialization import WEB_SEARCH_CONSENT_QUESTION
from lib.skills import (
    _SKILLS_DIR,
    INTERACTIVE_ONLY_END,
    INTERACTIVE_ONLY_START,
    _strip_frontmatter,
    load_skill_prompt,
    strip_interactive_only,
)


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


def test_strip_interactive_only_removes_the_marked_section():
    content = (
        "# Title\n\n"
        "<!-- interactive-only:start -->\n"
        "## Ask first\n\nSay the thing.\n"
        "<!-- interactive-only:end -->\n\n"
        "## Step 1\n"
    )
    assert strip_interactive_only(content) == "# Title\n\n## Step 1\n"


def test_strip_interactive_only_removes_every_section():
    content = (
        "a\n<!-- interactive-only:start -->\nx\n<!-- interactive-only:end -->\n"
        "b\n<!-- interactive-only:start -->\ny\n<!-- interactive-only:end -->\nc\n"
    )
    assert strip_interactive_only(content) == "a\nb\nc\n"


def test_strip_interactive_only_without_markers_is_unchanged():
    content = "# Title\n\nBody\n"
    assert strip_interactive_only(content) == content


# Skills whose workflow declares `needs_web_search`, so the portable skill has
# to gate itself on the user's consent when no app collected it first.
_WEB_SEARCH_SKILLS = [
    "reference-validation",
    "reference-download",
    "methodology-comparison",
    "literature-review",
    "live-reports",
]


@pytest.mark.parametrize("skill", _WEB_SEARCH_SKILLS)
def test_web_search_skill_asks_for_consent(skill: str):
    """The consent step must be present, and marked interactive-only."""
    raw = (_SKILLS_DIR / skill / "SKILL.md").read_text()
    assert INTERACTIVE_ONLY_START in raw
    assert INTERACTIVE_ONLY_END in raw
    assert WEB_SEARCH_CONSENT_QUESTION in raw, (
        f"{skill} must quote the MCP gate's consent question verbatim, so a "
        "user meets the same wording whichever surface they came through"
    )


@pytest.mark.parametrize(
    "skill_file", sorted(_SKILLS_DIR.glob("*/SKILL.md")), ids=lambda p: p.parent.name
)
def test_interactive_only_markers_are_balanced(skill_file: Path):
    """An unclosed section is not stripped, so it would leak into a prompt.

    Stripping is deliberately lenient at runtime — a markdown typo shouldn't
    break a workflow run — so the marker convention is enforced here instead.
    """
    markers = re.findall(
        f"{re.escape(INTERACTIVE_ONLY_START)}|{re.escape(INTERACTIVE_ONLY_END)}",
        skill_file.read_text(),
    )
    expected = [INTERACTIVE_ONLY_START, INTERACTIVE_ONLY_END] * (len(markers) // 2)
    assert markers == expected, (
        f"{skill_file.parent.name}: interactive-only markers must come in "
        f"start/end pairs, got {markers}"
    )


@pytest.mark.parametrize("skill", _WEB_SEARCH_SKILLS)
def test_backend_prompt_drops_the_consent_step(skill: str):
    """A backend run has its consent already and nobody to ask mid-run."""
    body = load_skill_prompt(skill)
    assert "interactive-only" not in body
    assert "Do you consent" not in body
    assert body.strip()
