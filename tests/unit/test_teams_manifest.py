"""Tests for the generated Teams app manifest.

Two of its fields have already cost a debugging session each, and both fail in ways
that name something else entirely:

- ``validDomains`` without ``token.botframework.com`` makes Teams refuse to open the
  sign-in link, reporting "this action can't be performed since the app does not exist
  or has been uninstalled".
- ``webApplicationInfo`` is deliberately absent. Present, Teams attempts a silent token
  exchange, and unbacked by Azure configuration that fails and falls back to the card --
  looking exactly like the field was never there, only slower.

So the manifest is asserted rather than eyeballed.
"""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2] / "microsoft" / "teams-app" / "build_package.py"
)


def build_package() -> Any:
    """The script, imported by path: it is tooling rather than an importable package."""

    spec = importlib.util.spec_from_file_location("build_package", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def builder() -> Any:
    return build_package()


class TestSignInCanOpenAtAll:
    def test_the_token_service_domain_is_trusted(self, builder: Any) -> None:
        """Teams will not open a link on a domain the manifest has not declared.

        This app has no tabs, so an empty ``validDomains`` looks right -- and it was,
        which is what broke sign-in in every scope.
        """

        document = builder.manifest(app_id="a", bot_id="b", version="1.0.0")

        assert "token.botframework.com" in document["validDomains"]


class TestSSOIsNotDeclared:
    """Sign-in is a deliberate click, so ``webApplicationInfo`` must stay absent.

    It was implemented and removed. Declaring it makes Teams attempt a silent
    ``signin/tokenExchange``, which needs an Application ID URI, an exposed scope and
    the Teams client ids pre-authorised on a registration -- and buys only the removal
    of one click, once per person, since Teams cannot acquire a token in a channel
    either way. Unbacked, the exchange fails and falls back to the card, which is
    indistinguishable from this being absent except slower.
    """

    def test_the_manifest_declares_no_sso(self, builder: Any) -> None:
        document = builder.manifest(app_id="a", bot_id="b", version="1.0.0")

        assert "webApplicationInfo" not in document

    def test_nothing_builds_one(self, builder: Any) -> None:
        """Guards the removal, so it does not come back unnoticed."""

        assert not hasattr(builder, "sso_declaration")


class TestTheRestOfTheManifest:
    def test_the_bot_is_offered_in_every_scope_it_supports(self, builder: Any) -> None:
        document = builder.manifest(app_id="a", bot_id="b", version="1.0.0")

        assert set(document["bots"][0]["scopes"]) == {"personal", "team", "groupChat"}

    def test_personal_scope_is_present_because_sign_in_needs_it(
        self, builder: Any
    ) -> None:
        """Teams cannot acquire a token in a channel, so 1:1 has to be installable."""

        assert "personal" in builder.manifest(
            app_id="a", bot_id="b", version="1.0.0"
        )["bots"][0]["scopes"]

    def test_the_version_is_what_was_asked_for(self, builder: Any) -> None:
        """Teams refuses an update that does not raise the version."""

        assert (
            builder.manifest(app_id="a", bot_id="b", version="9.9.9")["version"]
            == "9.9.9"
        )
