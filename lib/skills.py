"""Load a skill's markdown body for use as an agent/workflow prompt.

Skills under the repo-root `skills/` directory are the single source of truth
for the prompts and rules used by agents and deep-agent workflows. Code
references a skill by name (e.g. ``"reviewer-2"``) and loads its body here,
rather than duplicating the prompt text in Python.

A skill may carry sections that only make sense when the skill is driven by an
agent talking to a user (e.g. asking for web-search consent). Those are wrapped
in a ``<!-- interactive-only:start -->`` / ``<!-- interactive-only:end -->``
pair and stripped here: on the backend the same gate is already enforced before
the run starts, by the UI or by the MCP consent gate, and there is nobody for
the agent to ask mid-run. Both markers are required — an unclosed section is
left in place, which `tests/unit/test_skills.py` fails on.
"""

import re
from pathlib import Path

# Repo root: lib/skills.py -> parents[1]
_SKILLS_DIR = Path(__file__).parents[1] / "skills"

# Sections addressed to an interactive agent, not to a backend workflow run.
INTERACTIVE_ONLY_START = "<!-- interactive-only:start -->"
INTERACTIVE_ONLY_END = "<!-- interactive-only:end -->"

# Consumes the blank line after the block too, so removing a section that sat
# between two others doesn't leave a gap behind.
_INTERACTIVE_ONLY_RE = re.compile(
    rf"[ \t]*{re.escape(INTERACTIVE_ONLY_START)}.*?{re.escape(INTERACTIVE_ONLY_END)}[ \t]*\n*",
    re.DOTALL,
)


def load_skill_prompt(skill_name: str) -> str:
    """Return the markdown body of ``skills/<skill_name>/SKILL.md``.

    The YAML frontmatter block and any interactive-only sections are stripped;
    the remaining markdown is the prompt/rules used by the caller.
    """
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.is_file():
        raise FileNotFoundError(f"Skill '{skill_name}' not found at {skill_path}")
    return strip_interactive_only(_strip_frontmatter(skill_path.read_text()))


def strip_interactive_only(content: str) -> str:
    """Remove any interactive-only sections from a skill's markdown.

    Frontmatter (when present) is left in place, so this is also what mounts a
    raw SKILL.md into a deep agent's filesystem for the agent to read itself.
    """
    if INTERACTIVE_ONLY_START not in content:
        return content
    return _INTERACTIVE_ONLY_RE.sub("", content)


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
