"""Load a skill's markdown body for use as a deep-agent workflow prompt.

Skills under the repo-root `skills/` directory are the single source of truth
for the rules a deep-agent workflow checks. A workflow references a skill by
name (e.g. ``"figures-tables-check"``) and the rules live only in
``skills/<name>/SKILL.md`` — never duplicated in the manifest.
"""

from pathlib import Path

# Repo root: lib/workflows/simple_deep_agent/skill_prompt.py -> parents[3]
_SKILLS_DIR = Path(__file__).parents[3] / "skills"


def load_skill_prompt(skill_name: str) -> str:
    """Return the markdown body of ``skills/<skill_name>/SKILL.md``.

    The YAML frontmatter block is stripped; the remaining markdown is the
    rules/criteria used as the deep agent's user prompt.
    """
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.is_file():
        raise FileNotFoundError(f"Skill '{skill_name}' not found at {skill_path}")
    return _strip_frontmatter(skill_path.read_text())


def _strip_frontmatter(content: str) -> str:
    """Remove a leading YAML frontmatter block (``--- ... ---``) if present."""
    if not content.startswith("---"):
        return content

    lines = content.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1 :]).lstrip("\n")

    # No closing delimiter found — return content unchanged.
    return content
