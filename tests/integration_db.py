"""The database the test suite runs against, and how it gets ready.

Loaded as a pytest plugin (`-p tests.integration_db` in pyproject.toml), so it
runs before any test module imports `lib.config.env`, which reads
`DATABASE_URL` once at import. On import it points `DATABASE_URL` at the test
database: `TEST_DATABASE_URL` when set, else the `.env` database's name with
`_test` appended. `load_dotenv()` never overrides a variable that is already
set, so the app, the checkpointer and Alembic all follow.

`prepare_test_database()` creates that database when missing, rebuilds it when
it carries a migration this checkout doesn't know (one from another branch),
and runs `alembic upgrade head`. The integration tests call it themselves; run
it by hand to get ready ahead of time, or with `--reset` to start from empty:

    uv run python -m tests.integration_db [--reset]
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import load_dotenv
from psycopg import sql
from sqlalchemy.engine import URL, make_url

TEST_SUFFIX = "_test"
REPO_ROOT = Path(__file__).resolve().parent.parent
# Taken on the server while preparing, so parallel test workers wait for the
# first one instead of all creating and migrating at once.
PREPARE_LOCK_KEY = 0x44445F5445


def resolve_test_database_url(environ: dict[str, str]) -> URL:
    """`TEST_DATABASE_URL` as given, else `DATABASE_URL` with `_test` on its name."""
    explicit = environ.get("TEST_DATABASE_URL")
    if explicit:
        return make_url(explicit)
    url = make_url(environ["DATABASE_URL"])
    name = url.database or ""
    return url if name.endswith(TEST_SUFFIX) else url.set(database=name + TEST_SUFFIX)


def is_test_database(url: str | URL) -> bool:
    return (make_url(url).database or "").endswith(TEST_SUFFIX)


def _point_at_test_database() -> None:
    load_dotenv()
    if "DATABASE_URL" not in os.environ and "TEST_DATABASE_URL" not in os.environ:
        return  # nothing to point at; lib.config.env reports the missing variable
    url = resolve_test_database_url(dict(os.environ))
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)


_point_at_test_database()


def _admin_connection(url: URL) -> psycopg.Connection:
    """A connection to the server's `postgres` database, for creating and dropping."""
    admin = url.set(drivername="postgresql", database="postgres")
    return psycopg.connect(admin.render_as_string(hide_password=False), autocommit=True)


def _exists(admin: psycopg.Connection, name: str) -> bool:
    query = "SELECT 1 FROM pg_database WHERE datname = %s"
    return admin.execute(query, (name,)).fetchone() is not None


def _applied_revisions(url: URL) -> set[str]:
    with psycopg.connect(url.render_as_string(hide_password=False)) as conn:
        exists = conn.execute("SELECT to_regclass('alembic_version')").fetchone()
        if not exists or exists[0] is None:
            return set()
        return {
            row[0] for row in conn.execute("SELECT version_num FROM alembic_version")
        }


def _script() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(REPO_ROOT / "alembic.ini")))


def _upgrade(url: URL) -> None:
    """Run Alembic in its own process: its env.py reconfigures logging."""
    env = {**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade head failed:\n{result.stderr}")


def prepare_test_database(url: URL, reset: bool = False) -> None:
    """Create, rebuild or migrate the test database until it is at head."""
    name = url.database
    if not name or not is_test_database(url):
        raise RuntimeError(
            f"Refusing to prepare {name}: its name must end in {TEST_SUFFIX}"
        )
    script = _script()
    known = {revision.revision for revision in script.walk_revisions()}
    identifier = sql.Identifier(name)
    with _admin_connection(url) as admin:
        admin.execute("SELECT pg_advisory_lock(%s)", (PREPARE_LOCK_KEY,))
        applied = _applied_revisions(url) if _exists(admin, name) else None
        # A revision this checkout doesn't know came from another branch: the
        # database is disposable, so rebuild it rather than ask for a downgrade.
        if applied is not None and (reset or not applied <= known):
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(identifier))
            applied = None
        if applied is None:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(identifier))
        if applied != set(script.get_heads()):
            _upgrade(url)
        admin.execute("SELECT pg_advisory_unlock(%s)", (PREPARE_LOCK_KEY,))


def main() -> None:
    url = make_url(os.environ["DATABASE_URL"])
    prepare_test_database(url, reset="--reset" in sys.argv[1:])
    print(f"{url.database} is at the latest migration")


if __name__ == "__main__":
    main()
