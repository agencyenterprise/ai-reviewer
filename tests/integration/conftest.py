"""Integration tests write to and delete from a real Postgres: make sure it is the test one."""

from collections.abc import Iterator
from contextlib import ExitStack

import psycopg
import pytest
from sqlalchemy.engine import make_url

from lib.config.env import config as env_config
from tests.integration_db import integration_database_session, is_test_database


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> Iterator[None]:
    """Prepare the test database, and keep it from being rebuilt while tests run."""
    url = make_url(env_config.DATABASE_URL)
    if not is_test_database(url):
        pytest.fail("Integration tests only run against a database named *_test.")
    with ExitStack() as stack:
        try:
            stack.enter_context(integration_database_session(url))
        except psycopg.OperationalError as error:
            pytest.fail(
                f"Cannot reach Postgres for {url.database} ({error}). "
                "Start it with `docker compose up -d db`."
            )
        yield
