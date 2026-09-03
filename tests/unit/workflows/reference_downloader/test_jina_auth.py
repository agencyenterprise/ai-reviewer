"""JINA_API_KEY is optional: absent means anonymous, present means bearer auth."""

from unittest.mock import patch

from lib.workflows.reference_downloader.tools import download_file_from_url as dl


def test_no_key_means_anonymous_and_low_rate_limit():
    with patch.object(dl.config, "JINA_API_KEY", None):
        assert dl._jina_headers() == {}
        assert dl._jina_rpm() == dl.JINA_ANONYMOUS_RPM


def test_empty_key_is_treated_as_absent():
    with patch.object(dl.config, "JINA_API_KEY", ""):
        assert dl._jina_headers() == {}
        assert dl._jina_rpm() == dl.JINA_ANONYMOUS_RPM


def test_key_becomes_bearer_header_and_raises_rate_limit():
    with patch.object(dl.config, "JINA_API_KEY", "jina_secret"):
        assert dl._jina_headers() == {"Authorization": "Bearer jina_secret"}
        assert dl._jina_rpm() == dl.JINA_AUTHENTICATED_RPM
