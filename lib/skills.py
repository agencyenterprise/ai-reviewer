"""Load a skill's markdown body for use as an agent/workflow prompt.

Skills under the repo-root `skills/` directory are the single source of truth
for the prompts and rules used by agents and deep-agent workflows. Code
references a skill by name (e.g. ``"reviewer-2"``) and loads its body here,
rather than duplicating the prompt text in Python.
"""

from pathlib import Path

# Repo root: lib/skills.py -> parents[1]
_SKILLS_DIR = Path(__file__).parents[1] / "skills"


def load_skill_prompt(skill_name: str) -> str:
    """Return the markdown body of ``skills/<skill_name>/SKILL.md``.

    The YAML frontmatter block is stripped; the remaining markdown is the
    prompt/rules used by the caller.
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
