"""Tests for the allowlist that decides which documents the service will read.

This is the whole of the boundary. The app-only Graph grant is tenant-wide, so
without these checks the service would read any file in the organisation --
including ones the person asking cannot open themselves. Both directions matter: a
document outside the sites must be refused, and a link someone legitimately pasted
from Word must not be.

The ordering in ``resolve`` is the subtle part, and it is asserted here rather than
left to the docstring: the host is checked before Graph is called, and the site is
checked afterwards against the item's own ``webUrl``, because a sharing link carries
an opaque identifier where the path would be.

``check_host`` and ``check_site`` are therefore exercised separately, as they are
called. There is deliberately no helper that runs both against one URL -- that is the
shape which put the site check back on the pasted link.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.services.microsoft.graph import client
from lib.services.microsoft.graph.client import (
    DocumentNotAllowed,
    check_host,
    check_site,
)


@pytest.fixture
def allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    from lib.config.env import config

    monkeypatch.setattr(config, "GRAPH_ALLOWED_HOSTS", "contoso.sharepoint.com")
    monkeypatch.setattr(config, "GRAPH_ALLOWED_SITE_PATHS", "/sites/Reviews")


class TestWhatIsRefused:
    def test_an_unset_host_list_refuses_everything(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fail closed: an unconfigured deployment must read nothing, not anything."""

        from lib.config.env import config

        monkeypatch.setattr(config, "GRAPH_ALLOWED_HOSTS", None)
        with pytest.raises(DocumentNotAllowed, match="GRAPH_ALLOWED_HOSTS"):
            check_host("https://contoso.sharepoint.com/sites/Reviews/a.docx")

    def test_another_host_is_refused(self, allowlist: None) -> None:
        with pytest.raises(DocumentNotAllowed, match="not an allowed SharePoint host"):
            check_host("https://evil.sharepoint.com/sites/Reviews/a.docx")

    def test_another_site_on_the_allowed_host_is_refused(self, allowlist: None) -> None:
        """The host alone is far too wide -- a tenant is one host."""

        with pytest.raises(DocumentNotAllowed, match="outside the site paths"):
            check_site("https://contoso.sharepoint.com/sites/Finance/salaries.docx")

    def test_a_sharing_prefix_does_not_smuggle_another_site_through(
        self, allowlist: None
    ) -> None:
        """Stripping the prefix must not widen what passes, only normalise it."""

        with pytest.raises(DocumentNotAllowed, match="outside the site paths"):
            check_site("https://contoso.sharepoint.com/:w:/r/sites/Finance/pay.docx")


class TestWhatIsAllowed:
    def test_a_plain_path_in_the_allowed_site(self, allowlist: None) -> None:
        check_site(
            "https://contoso.sharepoint.com/sites/Reviews/Drafts/a.docx"
        )

    def test_a_copy_link_url_from_word(self, allowlist: None) -> None:
        """What "Copy link" actually produces, and what someone pastes into Teams.

        ``/:w:/r/`` in front of an otherwise ordinary path. Comparing the raw path
        against ``/sites/Reviews`` refused the very link the feature depends on.
        """

        check_site(
            "https://contoso.sharepoint.com/:w:/r/sites/Reviews/Drafts/a.docx"
            "?d=w123&csf=1&web=1&e=abc"
        )

    def test_the_host_check_is_case_insensitive(self, allowlist: None) -> None:
        check_host("https://Contoso.SharePoint.com/sites/Reviews/a.docx")

    def test_no_site_paths_configured_allows_the_whole_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Documented behaviour: the host list is the only required narrowing."""

        from lib.config.env import config

        monkeypatch.setattr(config, "GRAPH_ALLOWED_HOSTS", "contoso.sharepoint.com")
        monkeypatch.setattr(config, "GRAPH_ALLOWED_SITE_PATHS", None)

        check_site("https://contoso.sharepoint.com/sites/Anything/a.docx")


class TestResolvingASharingLink:
    """A sharing link has no path to check, so the site check moves after the resolve.

    This is what the Teams path actually receives: "Copy link" in Word produces
    ``/:w:/s/Site/EWabc...``, where the site is an opaque identifier. Checking the
    pasted string refused it; checking the resolved ``webUrl`` authorises the document
    that was really found.
    """

    SHARING_LINK = "https://contoso.sharepoint.com/:w:/s/Reviews/EWabc123?e=xyz"

    def graph(self, web_url: str) -> Any:
        """A Graph client whose ``/shares`` lookup returns one item."""

        response = MagicMock(status_code=200)
        response.json.return_value = {"name": "a.docx", "webUrl": web_url}

        transport = MagicMock()
        transport.get = AsyncMock(return_value=response)
        transport.__aenter__ = AsyncMock(return_value=transport)
        transport.__aexit__ = AsyncMock(return_value=False)
        return transport

    @pytest.mark.asyncio
    async def test_an_opaque_link_to_an_allowed_site_resolves(
        self, allowlist: None
    ) -> None:
        graph = self.graph(
            "https://contoso.sharepoint.com/sites/Reviews/Drafts/a.docx"
        )
        with patch.object(client, "access_token", AsyncMock(return_value="t")), patch(
            "httpx.AsyncClient", return_value=graph
        ):
            item = await client.resolve(self.SHARING_LINK)

        assert item["name"] == "a.docx"

    @pytest.mark.asyncio
    async def test_an_opaque_link_to_another_site_is_still_refused(
        self, allowlist: None
    ) -> None:
        """The point of moving the check, and the thing it must not give away."""

        graph = self.graph(
            "https://contoso.sharepoint.com/sites/Finance/Payroll/salaries.docx"
        )
        with patch.object(client, "access_token", AsyncMock(return_value="t")), patch(
            "httpx.AsyncClient", return_value=graph
        ):
            with pytest.raises(DocumentNotAllowed, match="outside the site paths"):
                await client.resolve(self.SHARING_LINK)

    @pytest.mark.asyncio
    async def test_a_disallowed_host_never_reaches_graph(self, allowlist: None) -> None:
        """The host check is before the call, so a stranger's host costs nothing."""

        graph = self.graph("https://elsewhere.sharepoint.com/sites/X/a.docx")
        with patch.object(client, "access_token", AsyncMock(return_value="t")), patch(
            "httpx.AsyncClient", return_value=graph
        ):
            with pytest.raises(DocumentNotAllowed, match="not an allowed"):
                await client.resolve("https://elsewhere.sharepoint.com/:w:/s/X/EW1")

        graph.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_an_item_whose_web_url_left_the_host_is_refused(
        self, allowlist: None
    ) -> None:
        """A redirect off the allowed host must not survive by having resolved."""

        graph = self.graph("https://elsewhere.sharepoint.com/sites/Reviews/a.docx")
        with patch.object(client, "access_token", AsyncMock(return_value="t")), patch(
            "httpx.AsyncClient", return_value=graph
        ):
            with pytest.raises(DocumentNotAllowed, match="not an allowed"):
                await client.resolve(self.SHARING_LINK)
