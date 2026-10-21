"""Service modules import on their own, in a fresh interpreter.

The app loads lib.workflows.registry first, which hides import cycles that
only show when something else is imported first: a script, a worker or a test
run on its own. lib.services.projects.service had one through the registry (#906).
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_project_service_imports_first() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import lib.services.projects.service"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
