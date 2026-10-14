"""Integration tests write to and delete from a real Postgres: make sure it is the test one."""

import psycopg
import pytest
from sqlalchemy.engine import make_url

from lib.config.env import config as env_config
from tests.integration_db import is_test_database, prepare_test_database


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> None:
    """Create or migrate the test database before the first integration test."""
    url = make_url(env_config.DATABASE_URL)
    if not is_test_database(url):
        pytest.fail("Integration tests only run against a database named *_test.")
    try:
        prepare_test_database(url)
    except psycopg.OperationalError as error:
        pytest.fail(
            f"Cannot reach Postgres for {url.database} ({error}). "
            "Start it with `docker compose up -d db`."
        )
