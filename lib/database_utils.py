"""
Database utility functions for managing the database and running migrations.
"""

import subprocess
import sys
from sqlalchemy import text

from .config.database import engine, SessionLocal
from .config.env import config


def check_database_connection():
    """Check if we can connect to the database."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def run_migrations():
    """Run Alembic migrations to upgrade the database to the latest version."""
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Database migrations completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        return False
    except FileNotFoundError:
        print("Alembic not found. Make sure it's installed.")
        return False


def create_tables():
    """Create all tables defined in the models (alternative to migrations)."""
    from .config.database import Base

    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Failed to create tables: {e}")
        return False


def get_db_session():
    """Get a database session."""
    return SessionLocal()


def print_database_info():
    """Print database configuration info."""
    print("Database Configuration:")
    print(f"  Database URL: {config.DATABASE_URL}")
    print(f"  Host: {config.POSTGRES_HOST}")
    print(f"  Port: {config.POSTGRES_PORT}")
    print(f"  Database: {config.POSTGRES_DB}")
    print(f"  User: {config.POSTGRES_USER}")


if __name__ == "__main__":
    print_database_info()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            if check_database_connection():
                print("Database connection successful!")
            else:
                sys.exit(1)

        elif command == "migrate":
            if not run_migrations():
                sys.exit(1)

        elif command == "create-tables":
            if not create_tables():
                sys.exit(1)

        else:
            print(f"Unknown command: {command}")
            print("Available commands: check, migrate, create-tables")
            sys.exit(1)
    else:
        print("\n Available commands:")
        print("  python -m lib.database_utils check       - Check database connection")
        print("  python -m lib.database_utils migrate     - Run Alembic migrations")
        print("  python -m lib.database_utils create-tables - Create tables directly")
