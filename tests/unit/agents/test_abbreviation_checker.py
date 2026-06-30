"""Tests for the abbreviation checker agent.

The agent loads its extraction method from the portable `abbreviation-extraction`
skill (the source of truth) and appends a backend `_ENV_GUIDANCE` addendum
carrying the Draft-Detective specifics the skill omits (document location and the
structured-output field mapping the downstream deterministic checks depend on).
Here we guard that the skill loads and the addendum still references those
specifics, without invoking the LLM.
"""

from lib.agents.abbreviation_checker import _ENV_GUIDANCE
from lib.skills import load_skill_prompt


def test_extraction_skill_loads_non_empty_without_frontmatter():
    body = load_skill_prompt("abbreviation-extraction")
    assert body.strip()
    assert not body.lstrip().startswith("---")


def test_agent_composes_skill_with_env_guidance():
    body = load_skill_prompt("abbreviation-extraction")

    # The backend addendum carries the specifics the portable skill omits:
    # document location and the exact structured-output field mapping.
    assert "/main.md" in _ENV_GUIDANCE
    for field in (
        "inline_definition",
        "occurrence_number",
        "line_start",
        "line_end",
        "abbreviations_section_definition",
        "ignored",
        "abbreviations_section_found",
    ):
        assert field in _ENV_GUIDANCE

    composed = body + _ENV_GUIDANCE
    assert composed.startswith(body)
    assert composed.endswith(_ENV_GUIDANCE)
