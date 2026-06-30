"""Tests for the About-page content reader (`lib/services/about_page.py`).

The About page is served from the committed ABOUT.md at the repo root; these
guard that the file exists and is read verbatim.
"""

from lib.services.about_page import ABOUT_MD_PATH, read_about_content


def test_about_md_file_exists_at_repo_root():
    assert ABOUT_MD_PATH.name == "ABOUT.md"
    assert ABOUT_MD_PATH.is_file()


def test_read_about_content_returns_markdown():
    content = read_about_content()
    assert content.strip()
    # Sanity check it's the About page markdown, not an empty/placeholder file.
    assert content.lstrip().startswith("# About This Tool")
    assert content == ABOUT_MD_PATH.read_text(encoding="utf-8")
