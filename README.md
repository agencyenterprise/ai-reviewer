## rand-ai-reviewer

Minimal Python project managed with uv.

### Prerequisites

- **uv**: Fast Python package/dependency manager. Official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- Verify:

```bash
uv --version
```

Python 3.13 is required and will be handled by uv (it can auto-install it if missing).

### Setup

From the project root:

```bash
# Sync env from lockfile (reproducible)
uv sync --frozen

# If you don't want to enforce the lockfile, use:
# uv sync
```

This creates a local virtual environment at `.venv/` and installs dependencies from `pyproject.toml` / `uv.lock`.

If Python 3.13 is not present, install it via uv:

```bash
uv python install 3.13
```

### Run

Execute the app using uv (no manual activation needed):

```bash
uv run python main.py
```

Streamlit (temporary UI for PoC)

```
streamlit run streamlit/main.py
```

### Optional: activate the virtual environment

```bash
source .venv/bin/activate
python main.py
```

### Managing dependencies

- **Add a dependency**:

```bash
uv add <package>
```

- **Remove a dependency**:

```bash
uv remove <package>
```

- **Upgrade using the lockfile**:

```bash
uv lock --upgrade && uv sync --frozen
```

### Notes

- Python version is pinned to 3.13 via `.python-version` and `pyproject.toml`.
- Use `uv sync --reinstall` if your environment becomes inconsistent.
