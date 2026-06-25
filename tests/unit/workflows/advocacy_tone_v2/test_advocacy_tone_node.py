"""Tests for advocacy_tone_v2 prompt composition and config registration."""

from lib.services.app_configs import _collect_all_defaults
from lib.skills import load_skill_prompt
from lib.workflows.advocacy_tone_v2.config_keys import (
    ADVOCACY_TONE_V2_CONFIG_KEY,
    ADVOCACY_TONE_V2_DEFAULTS,
)
from lib.workflows.advocacy_tone_v2.nodes.advocacy_tone import build_user_prompt


def test_build_user_prompt_without_config_is_just_the_skill():
    skill = load_skill_prompt("advocacy-tone")
    assert build_user_prompt(None) == skill
    assert build_user_prompt("   ") == skill  # blank config ignored


def test_build_user_prompt_appends_config_block():
    cfg = "Trigger words:\nfoo, bar, baz"
    prompt = build_user_prompt(cfg)
    assert prompt.startswith(load_skill_prompt("advocacy-tone"))
    assert "## Configuration for this deployment" in prompt
    assert cfg in prompt
    # the injected config supersedes the skill defaults
    assert "supersede" in prompt.lower()


def test_default_config_is_registered_for_seeding():
    keys = {d.key for d in _collect_all_defaults()}
    assert ADVOCACY_TONE_V2_CONFIG_KEY in keys
    # the bundled defaults entry carries a non-empty default value
    (entry,) = [
        d for d in ADVOCACY_TONE_V2_DEFAULTS if d.key == ADVOCACY_TONE_V2_CONFIG_KEY
    ]
    assert entry.default_value.strip()
