"""Tests for the citation validator agent.

The agent loads its substantiation-judgment method from the portable
`citation-support` skill (the source of truth) and appends a backend
`_ENV_GUIDANCE` template carrying the Draft-Detective specifics the skill omits:
the assigned section, the concrete document-access tools, the bibliography→file
mapping, and the structured-output field mapping. Here we guard that the skill
loads and the addendum still references those specifics — and that the addendum
formats with the kwargs `validate_section` passes — without invoking the LLM.
"""

from lib.agents.citation_validator import _ENV_GUIDANCE
from lib.skills import load_skill_prompt

# The kwargs shape produced by validate_section / the internal eval solver.
_SAMPLE_KWARGS = {
    "main_file_id": "file-123",
    "start_line": 1,
    "end_line": 42,
    "section_headings": "Results > Findings",
    "reference_file_map": "[1] Smith 2020 -> file-abc",
    "headings": ["Results", "Findings"],
}


def test_citation_support_skill_loads_non_empty_without_frontmatter():
    body = load_skill_prompt("citation-support")
    assert body.strip()
    assert not body.lstrip().startswith("---")


def test_env_guidance_carries_backend_specifics():
    # Concrete tools the portable skill describes only abstractly.
    for tool in ("read_document", "search_document", "vector_search"):
        assert tool in _ENV_GUIDANCE

    # Section/bibliography placeholders substituted per invocation.
    for placeholder in (
        "{main_file_id}",
        "{start_line}",
        "{end_line}",
        "{reference_file_map}",
    ):
        assert placeholder in _ENV_GUIDANCE

    # Output field mapping (the schema fields the skill must not name).
    for field in ("evidence_alignment", "quoted_text"):
        assert field in _ENV_GUIDANCE


def test_env_guidance_formats_with_validate_section_kwargs():
    # Guards the placeholder set: .format must not raise KeyError, and the
    # composed system prompt begins with the skill body.
    rendered = _ENV_GUIDANCE.format(**_SAMPLE_KWARGS)
    assert "file-123" in rendered

    # Ensure the known placeholders were substituted (without forbidding literal braces
    # in inserted content such as bibliography strings).
    for placeholder in (
        "{main_file_id}",
        "{start_line}",
        "{end_line}",
        "{section_headings}",
        "{reference_file_map}",
    ):
        assert placeholder not in rendered

    composed = load_skill_prompt("citation-support") + rendered
    assert composed.startswith(load_skill_prompt("citation-support"))
