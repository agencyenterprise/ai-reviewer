"""The guards that keep the test suite off any database but a *_test one."""

import pytest

from tests.integration_db import is_test_database, libpq_url, resolve_test_database_url

DEV = "postgresql://user:secret@localhost:5432/ai_reviewer"


def test_appends_test_to_the_env_database():
    url = resolve_test_database_url({"DATABASE_URL": DEV})

    assert url.database == "ai_reviewer_test"
    assert (url.host, url.port, url.username) == ("localhost", 5432, "user")


def test_never_uses_an_env_database_already_named_test():
    url = resolve_test_database_url({"DATABASE_URL": DEV + "_test"})

    assert url.database == "ai_reviewer_test_test"


def test_takes_test_database_url_as_given():
    explicit = "postgresql://user:secret@other:5433/scratch_test"

    url = resolve_test_database_url(
        {"DATABASE_URL": DEV, "TEST_DATABASE_URL": explicit}
    )

    assert (url.host, url.database) == ("other", "scratch_test")


def test_refuses_an_explicit_url_that_is_not_a_test_database():
    with pytest.raises(ValueError, match="must end in _test"):
        resolve_test_database_url({"TEST_DATABASE_URL": DEV})


@pytest.mark.parametrize("parameter", ["dbname=ai_reviewer", "service=dev"])
def test_refuses_query_parameters_that_pick_another_database(parameter):
    with pytest.raises(ValueError, match="Remove"):
        resolve_test_database_url({"DATABASE_URL": f"{DEV}?{parameter}"})

    assert not is_test_database(f"{DEV}_test?{parameter}")


def test_refuses_names_postgres_would_truncate():
    long_dev = "postgresql://user:secret@localhost/" + "a" * 59

    with pytest.raises(ValueError, match="63 bytes"):
        resolve_test_database_url({"DATABASE_URL": long_dev})


def test_counts_the_name_in_bytes_not_characters():
    assert is_test_database("postgresql://h/" + "a" * 58 + "_test")
    assert not is_test_database("postgresql://h/" + "é" * 30 + "_test")


def test_keeps_ordinary_query_parameters():
    url = resolve_test_database_url({"DATABASE_URL": f"{DEV}?sslmode=require"})

    assert url.query == {"sslmode": "require"}


def test_libpq_url_drops_the_sqlalchemy_dialect():
    url = resolve_test_database_url(
        {"TEST_DATABASE_URL": "postgresql+psycopg://user:p%21w@h/x_test"}
    )

    assert libpq_url(url) == "postgresql://user:p%21w@h/x_test"


def test_refuses_a_percent_escaped_database_name():
    with pytest.raises(ValueError, match="hold no %"):
        resolve_test_database_url({"DATABASE_URL": "postgresql://h/db%20name"})


def test_keeps_a_percent_encoded_password():
    url = resolve_test_database_url({"DATABASE_URL": "postgresql://u:p%25w@h/db"})

    assert (url.password, url.database) == ("p%w", "db_test")
