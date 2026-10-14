"""Integration tests write to and delete from a real Postgres: make sure it is the test one."""

import subprocess
from collections.abc import Iterator
from contextlib import AbstractContextManager, ExitStack, nullcontext

import psycopg
import pytest
from sqlalchemy.engine import make_url

from lib.config.env import config as env_config
from tests.integration_db import integration_database_session, is_test_database


@pytest.fixture(scope="session", autouse=True)
def _test_database(request: pytest.FixtureRequest) -> Iterator[None]:
    """Prepare the test database, and keep it from being rebuilt while tests run."""
    url = make_url(env_config.DATABASE_URL)
    if not is_test_database(url):
        pytest.fail("Integration tests only run against a database named *_test.")
    # Uncaptured, so "Waiting for test sessions..." reaches the terminal while
    # another run holds the database.
    capture = request.config.pluginmanager.getplugin("capturemanager")
    uncaptured: AbstractContextManager[None] = (
        capture.global_and_fixture_disabled() if capture else nullcontext()
    )
    with ExitStack() as stack:
        try:
            with uncaptured:
                stack.enter_context(integration_database_session(url))
        except (
            psycopg.Error,
            RuntimeError,
            TimeoutError,
            subprocess.TimeoutExpired,
        ) as error:
            hint = ""
            if isinstance(error, psycopg.OperationalError):
                hint = " Is Postgres running? Locally: `docker compose up -d db`."
            pytest.fail(f"Could not prepare {url.database}: {error}{hint}")
        yield
