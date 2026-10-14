"""The database the test suite runs against, and how it gets ready.

Loaded as a pytest plugin (`-p tests.integration_db` in pyproject.toml), so it
runs before any test module imports `lib.config.env`, which reads
`DATABASE_URL` once at import. On import it points `DATABASE_URL` at the test
database: `TEST_DATABASE_URL` when set, else the `.env` database's name with
`_test` appended. `load_dotenv()` never overrides a variable that is already
set, so the app, the checkpointer and Alembic all follow. The resolved URL is
also exported as `TEST_DATABASE_URL`, so pytest-xdist workers, which inherit
the environment, take it as given instead of appending `_test` again.

The integration tests' session fixture calls `integration_database_session()`,
which creates the database when missing, rebuilds it when it carries a
migration this checkout doesn't know (one from another branch), runs
`alembic upgrade heads`, and then keeps the database from changing until the
session ends. Run it by hand to get ready ahead of time, or with `--reset` to
start from empty:

    uv run python -m tests.integration_db [--reset]

Two test databases on one server never wait on each other: the locks are keyed
by name. Two runs of the same database from branches with different migrations
take turns, each rebuilding it, which is correct but slow.
"""

import os
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import load_dotenv
from psycopg import sql
from sqlalchemy.engine import URL, make_url

TEST_SUFFIX = "_test"
REPO_ROOT = Path(__file__).resolve().parent.parent
# libpq lets these query parameters pick the database instead of the URL's
# path, which would slip past a check of the path's name.
NAME_OVERRIDES = ("dbname", "service")
# PostgreSQL truncates longer identifiers, so a longer name could reach another
# database: "<63-byte dev name>_test" would drop the dev database.
MAX_NAME_BYTES = 63
# How long a rebuild or migration waits for running sessions before giving up.
WAIT_LIMIT_SECONDS = 300
WAIT_POLL_SECONDS = 2


def resolve_test_database_url(environ: dict[str, str]) -> URL:
    """`TEST_DATABASE_URL` as given, else `DATABASE_URL` with `_test` on its name."""
    explicit = environ.get("TEST_DATABASE_URL")
    url = make_url(explicit or environ["DATABASE_URL"])
    overrides = [key for key in NAME_OVERRIDES if key in url.query]
    if overrides:
        raise ValueError(
            f"Remove {', '.join(overrides)} from the database URL: the test suite "
            "picks its database from the URL's path."
        )
    if not explicit:
        # Always appended, even to a name already ending in _test: the .env
        # database is never the test database.
        url = url.set(database=(url.database or "") + TEST_SUFFIX)
    if not is_test_database(url):
        raise ValueError(
            f"Cannot use {url.database!r} as the test database: its name must end "
            f"in {TEST_SUFFIX}, fit in {MAX_NAME_BYTES} bytes and hold no %. Set "
            "TEST_DATABASE_URL to one that does."
        )
    return url


def is_test_database(url: str | URL) -> bool:
    url = make_url(url)
    if any(key in url.query for key in NAME_OVERRIDES):
        return False
    name = url.database or ""
    fits = len(name.encode()) <= MAX_NAME_BYTES
    # SQLAlchemy keeps a %-escape in the path while libpq decodes it, so the two
    # would name different databases. Passwords are decoded by both: unaffected.
    return fits and "%" not in name and name.endswith(TEST_SUFFIX)


def libpq_url(url: URL) -> str:
    """The URL as libpq reads it: psycopg and the app's checkpointer reject a
    SQLAlchemy dialect suffix such as `postgresql+psycopg://`."""
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def _point_at_test_database() -> None:
    load_dotenv()
    if "DATABASE_URL" not in os.environ and "TEST_DATABASE_URL" not in os.environ:
        return  # nothing to point at; lib.config.env reports the missing variable
    resolved = libpq_url(resolve_test_database_url(dict(os.environ)))
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"] = resolved


_point_at_test_database()


def _admin_connection(url: URL) -> psycopg.Connection:
    """A connection to the server's `postgres` database, for creating and dropping."""
    return psycopg.connect(libpq_url(url.set(database="postgres")), autocommit=True)


def _lock_key(kind: str, url: URL) -> str:
    """Per database name, so unrelated test databases never wait on each other."""
    return f"draft-detective:{kind}:{url.database}"


def _lock(conn: psycopg.Connection, key: str) -> None:
    conn.execute("SELECT pg_advisory_lock(hashtextextended(%s, 0))", (key,))


def _lock_shared(conn: psycopg.Connection, key: str) -> None:
    conn.execute("SELECT pg_advisory_lock_shared(hashtextextended(%s, 0))", (key,))


def _unlock(conn: psycopg.Connection, key: str) -> None:
    conn.execute("SELECT pg_advisory_unlock(hashtextextended(%s, 0))", (key,))


def _try_lock(conn: psycopg.Connection, key: str) -> bool:
    row = conn.execute(
        "SELECT pg_try_advisory_lock(hashtextextended(%s, 0))", (key,)
    ).fetchone()
    return bool(row and row[0])


@contextmanager
def _locked(conn: psycopg.Connection, key: str) -> Iterator[None]:
    _lock(conn, key)
    try:
        yield
    finally:
        _unlock(conn, key)


def _exists(admin: psycopg.Connection, name: str) -> bool:
    query = "SELECT 1 FROM pg_database WHERE datname = %s"
    return admin.execute(query, (name,)).fetchone() is not None


def _applied_revisions(url: URL) -> set[str]:
    with psycopg.connect(libpq_url(url)) as conn:
        exists = conn.execute("SELECT to_regclass('alembic_version')").fetchone()
        if not exists or exists[0] is None:
            return set()
        return {
            row[0] for row in conn.execute("SELECT version_num FROM alembic_version")
        }


def _script() -> ScriptDirectory:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    # alembic.ini's script_location is relative to the working directory, and
    # pytest may be started from a subdirectory.
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def _upgrade(url: URL) -> None:
    """Run Alembic in its own process: its env.py reconfigures logging."""
    env = {**os.environ, "DATABASE_URL": libpq_url(url)}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "heads"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        # A connection left idle in a transaction on the test database blocks
        # the migration; fail like a lock wait instead of hanging.
        timeout=WAIT_LIMIT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade heads failed:\n{result.stderr}")


def _rebuild(admin: psycopg.Connection, name: str) -> None:
    identifier = sql.Identifier(name)
    # FORCE: finished runs release their lock before their workers' pools close,
    # and only idle connections can remain once the exclusive lock is held.
    admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(identifier))
    admin.execute(sql.SQL("CREATE DATABASE {}").format(identifier))


def _needed_change(admin: psycopg.Connection, url: URL, reset: bool) -> str | None:
    """ "rebuild", "upgrade", or None when the database is already at head."""
    script = _script()
    applied = _applied_revisions(url) if _exists(admin, url.database or "") else None
    known = {revision.revision for revision in script.walk_revisions()}
    # A revision this checkout doesn't know came from another branch: the
    # database is disposable, so rebuild it rather than ask for a downgrade.
    if applied is None or reset or not applied <= known:
        return "rebuild"
    return None if applied == set(script.get_heads()) else "upgrade"


def _wait_for_sessions(admin: psycopg.Connection, url: URL, deadline: float) -> None:
    """Let go of PREPARE while other sessions finish, so their workers never queue.

    When this raises (or is interrupted) PREPARE is not held, and the caller's
    `_locked` unlocks it again; Postgres answers that with false, harmlessly.
    """
    _unlock(admin, _lock_key("prepare", url))
    if time.monotonic() > deadline:
        raise TimeoutError(
            f"Gave up after {WAIT_LIMIT_SECONDS}s: another test session still uses "
            f"{url.database} (a test paused in a debugger, or a hung run, holds it)."
        )
    time.sleep(WAIT_POLL_SECONDS)
    _lock(admin, _lock_key("prepare", url))


def _prepare(admin: psycopg.Connection, url: URL, reset: bool) -> None:
    """Bring the test database to head; call with the PREPARE lock held."""
    if not url.database or not is_test_database(url):
        raise RuntimeError(f"Refusing to prepare {url.database}: not a test database")
    deadline = time.monotonic() + WAIT_LIMIT_SECONDS
    waiting = False
    while (change := _needed_change(admin, url, reset)) is not None:
        # Rebuilding or migrating changes what a running session sees.
        if _try_lock(admin, _lock_key("in_use", url)):
            try:
                if change == "rebuild":
                    _rebuild(admin, url.database)
                _upgrade(url)
            finally:
                _unlock(admin, _lock_key("in_use", url))
            return
        if not waiting:
            waiting = True
            print(f"Waiting for test sessions using {url.database}...", file=sys.stderr)
        _wait_for_sessions(admin, url, deadline)


def prepare_test_database(url: URL, reset: bool = False) -> None:
    """Create, rebuild or migrate the test database until it is at head."""
    with _admin_connection(url) as admin, _locked(admin, _lock_key("prepare", url)):
        _prepare(admin, url, reset)


@contextmanager
def integration_database_session(url: URL) -> Iterator[None]:
    """Prepare the test database, then keep it from changing until exit."""
    in_use = _admin_connection(url)
    try:
        with _admin_connection(url) as admin:
            with _locked(admin, _lock_key("prepare", url)):
                _prepare(admin, url, reset=False)
                # Never waits: an exclusive holder would also hold PREPARE.
                _lock_shared(in_use, _lock_key("in_use", url))
        yield
    finally:
        in_use.close()


def main() -> None:
    url = make_url(os.environ["DATABASE_URL"])
    prepare_test_database(url, reset="--reset" in sys.argv[1:])
    print(f"{url.database} is at the latest migration")


if __name__ == "__main__":
    main()
