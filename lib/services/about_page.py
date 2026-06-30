"""Reads the About-page content from the committed ABOUT.md file.

ABOUT.md lives at the repository root so a deployment can customise the About
page by editing that file in its fork — no database or app-settings involved.
"""

from pathlib import Path

# lib/services/about_page.py -> parents[2] is the repository root.
ABOUT_MD_PATH = Path(__file__).resolve().parents[2] / "ABOUT.md"


def read_about_content() -> str:
    """Return the markdown content shown on the About page."""
    return ABOUT_MD_PATH.read_text(encoding="utf-8")
