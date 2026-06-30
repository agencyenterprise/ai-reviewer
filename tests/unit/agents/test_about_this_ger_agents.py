"""Tests for the About This (GER) validator agents.

These agents load their rules from a portable skill (the source of truth) and
append a backend `_ENV_GUIDANCE` addendum carrying the Draft-Detective specifics
the skill omits (document location, issues output contract). Here we guard that
the skill loads and the addendum still references those specifics, without
invoking the LLM.
"""

import pytest

from lib.agents.authors_validator import _ENV_GUIDANCE as AUTHORS_ENV_GUIDANCE
from lib.agents.preface_validator import _ENV_GUIDANCE as PREFACE_ENV_GUIDANCE
from lib.skills import load_skill_prompt

_CASES = [
    ("about-this-preface", PREFACE_ENV_GUIDANCE),
    ("about-this-authors", AUTHORS_ENV_GUIDANCE),
]


@pytest.mark.parametrize("skill, env_guidance", _CASES)
def test_agent_composes_skill_with_env_guidance(skill: str, env_guidance: str):
    body = load_skill_prompt(skill)
    assert body.strip()

    # The backend addendum carries the specifics the portable skill omits.
    assert "/main.md" in env_guidance
    assert "/skills/issues/SKILL.md" in env_guidance
    assert "start_line" in env_guidance and "end_line" in env_guidance
    assert "report_markdown" in env_guidance

    composed = body + env_guidance
    assert composed.startswith(body)
    assert composed.endswith(env_guidance)
