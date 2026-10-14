# Project Instructions

A Python backend (FastAPI + LangChain, under `lib/`) and a Next.js frontend (under `frontend/`). Rules marked **Always** or **Never** are strict. The rest are defaults to follow unless there's a reason not to.

## Quick Reference

```bash
# Backend (always uv)
uv run dev.py                              # Start the full dev environment
uv run pytest tests/unit                   # Unit tests (what CI runs)
uv run pytest tests/path/to/test.py -k "name"
uv run mypy .                              # Type check (CI blocks on errors)

# Frontend (always pnpm, from frontend/)
cd frontend && pnpm install
cd frontend && pnpm dev
cd frontend && pnpm test                   # Vitest
cd frontend && pnpm run lint
cd frontend && pnpm run openapi-generate   # Regenerate API types
```

## Before Handing Back Work

Run the same checks CI runs for the side you touched. A red check here means a red PR.

- **Python changes:** `uv run mypy .` and `uv run pytest tests/unit`. Also run the integration tests you touched (`uv run pytest tests/integration/...`), since CI skips them.
- **Frontend changes:** `pnpm run lint`, `pnpm test` and `pnpm run build`, from `frontend/`.
- **Backend API changes:** regenerate the frontend types (see below), then run the frontend checks.

If a check fails and you can't fix it, tell the user which one and why. Never hand the work back as finished.

---

## Python Backend Rules

### Always use `uv`, never raw `python`, `pip` or `pytest`

Dependencies are pinned in `uv.lock`. Calling `python` or `pip` directly can pick up a different interpreter or install outside the lockfile.

```bash
# ✅ Correct
uv run python script.py
uv run pytest tests/ -k "test_name"
uv add package-name

# ❌ Incorrect
python script.py
.venv/bin/python script.py
python -m pytest
pip install package-name
```

### Never create an `__init__.py` unless it has a job

The codebase uses implicit namespace packages, and pytest runs with `--import-mode=importlib` to match. Add an `__init__.py` only when it does real work, such as re-exporting members (`lib/models/__init__.py` does this for the database models). Never add an empty or marker one.

```bash
# ✅ Correct
lib/workflows/new_workflow/
├── state.py
├── graph.py
└── nodes/
    └── process.py

# ❌ Incorrect
lib/workflows/new_workflow/
├── __init__.py          # Don't create this
└── nodes/
    ├── __init__.py      # Or this
    └── process.py
```

### Never import inside a function

Always put imports at the top of the file. A lazy import hides a module's dependencies, and a broken import then fails only when that code path runs instead of at startup. The one exception is breaking a circular import, and it must carry a comment saying so.

```python
# ✅ Correct
from lib.services.users import UserService

def process(doc: Document) -> None:
    service = UserService()

# ✅ Acceptable - a circular import, explained
def process(doc: Document) -> None:
    # Imported here to avoid a circular import between lib.services.users and lib.services.documents
    from lib.services.users import UserService
    service = UserService()
```

Never use `import *` either.

### Always use Pydantic `BaseModel`, never `@dataclass`

One modeling tool across the codebase, and every model gets validation and serialization the same way.

```python
# ✅ Correct
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    title: str = Field(description="Document title")
    page_count: int
```

### Always use SQLAlchemy 2.0 `select()` with `col()`

Never use the legacy `db.query()` style. Wrap SQLModel columns in `col()` inside `.where()`, `.join()` and similar calls: without it mypy reads `File.project_id == x` as a plain `bool` and reports an error.

```python
# ✅ Correct
from sqlalchemy import select
from sqlmodel import col

stmt = select(File).where(col(File.project_id) == project_id)
stmt = select(File).where(col(File.id).in_(file_ids))

# ❌ Incorrect
db.query(File).filter(File.project_id == project_id).all()   # legacy 1.x
select(File).where(File.project_id == project_id)            # mypy error: bool
```

### Never run Alembic

When you change a model in `lib/models/`, change only the model file, then remind the user to generate and apply the migration. The user reviews migrations and applies them to their own database:

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Type hints

Always annotate function signatures. Use built-in generics and `|` unions (we're on Python 3.13). Older files still use `typing.List` and `Optional`; don't churn them, but never write that style in new code.

```python
# ✅ Correct
def process_documents(files: list[File], config: ProcessingConfig | None = None) -> DocumentResult: ...

# ❌ Incorrect in new code
from typing import List, Optional
def process_documents(files: List[File], config: Optional[ProcessingConfig] = None) -> DocumentResult: ...
```

Use `TypedDict` for workflow state.

### Always keep mypy at zero errors

The baseline is zero, so any error mypy reports came from the current work. The `backend.yml` CI workflow runs `uv run mypy .` and blocks the merge on failure.

- After editing a `.py` file (backend, tests or evals), run `uv run mypy <touched paths>`.
- Before finishing, run `uv run mypy .` once. Changes often break untouched files: union narrowing, SQLAlchemy `Select[...]` reassignments and structured-output agent return types are common sources.
- Never use a bare `# type: ignore`. When nothing else works (narrowing with `isinstance`, `cast()`, a better annotation), use `# type: ignore[specific-code]` with a short comment if the reason isn't obvious.
- If mypy misbehaves, `rm -rf .mypy_cache` and retry before assuming a real error.

---

## Frontend Rules

### Always use `pnpm`, from `frontend/`

Dependencies are pinned in `pnpm-lock.yaml`. `npm` and `yarn` ignore it.

### Never edit `frontend/lib/generated-api/`

The files are generated by Hey API (`@hey-api/openapi-ts`) from the backend's OpenAPI schema and are overwritten on every regeneration. Always run `pnpm run openapi-generate` from `frontend/` after any backend API change (endpoints, request or response types, schemas). The backend must be running for it to work.

### Never use `useEffect` for derived state or data fetching

Effects that sync state cause extra renders and stale-value bugs. Use `useEffect` only to sync with something outside React (DOM APIs, subscriptions, timers). Instead:

- **Derived state:** compute it during render (`useMemo` if it's expensive).
- **Side effects of user actions:** do them in the event handler.
- **Data fetching:** use React Query.
- **Resetting state:** change the component's `key`.

```tsx
// ❌ Incorrect
const [fullName, setFullName] = useState("");
useEffect(() => setFullName(`${firstName} ${lastName}`), [firstName, lastName]);
useEffect(() => { fetchData().then(setData); }, [id]);

// ✅ Correct
const fullName = `${firstName} ${lastName}`;
const { data } = useQuery({ queryKey: ["data", id], queryFn: fetchData });
```

### Components and types

- Always build UI from the shadcn/ui components in `frontend/components/ui/` and Tailwind utility classes. Write custom CSS only when Tailwind can't express it.
- Never use `any`. Type component props explicitly.
- Never nest ternaries in JSX. Use early returns or a small helper.

---

## Code Size

- Keep files around 100–200 lines, 300 at most. Database models, configuration and workflow definitions that need to stay together can run longer.
- Split a file when it mixes responsibilities, not just because it's long.
- Keep functions to about 20 lines. Split longer ones unless splitting would make the code harder to follow.

---

## Skill Files

Skill files under `skills/` must be **environment-agnostic**. Users install them standalone in Claude apps and other agent runtimes, not just in this repo's workflow agents.

- Never reference runtime-specific tool names (e.g. a workflow agent's `view_image`), internal URL schemes or file layouts specific to one runtime.
- Phrase capabilities conditionally: "when you have a way to view images…", "if you can search the document…".
- Runtime-specific wiring (which tool to call, what a `draftdetective://` src means) belongs in the agent's system prompt, next to where the tool is bound.

---

## Testing

### Backend Tests (pytest)

```bash
uv run pytest tests/unit                          # Unit tests (what CI runs)
uv run pytest tests/integration                   # Integration tests (need a database)
uv run pytest tests/path/to/test.py -k "name"     # One file or pattern
```

- `tests/unit/` has no external dependencies. `tests/integration/` talks to a real database, which is why CI skips it.
- Shared fixtures and helpers (`data_path`, `create_test_file_document_from_path`, `create_test_context`) are in `tests/conftest.py`. Reuse them before writing new ones.
- Never call a real LLM in a test. Use LangChain's `GenericFakeChatModel` (see `tests/unit/services/chat/test_thread_state.py`) or patch the call.
- Mark async tests with `@pytest.mark.asyncio`.

### Frontend Tests (Vitest)

Vitest runs in jsdom and needs Node 22.22.2 or newer (`frontend/.nvmrc`). CI runs it on every PR.

```bash
cd frontend && pnpm test                              # All tests
cd frontend && pnpm test lib/workflow-state.test.ts   # One file
cd frontend && pnpm test -t "name of the test"        # Tests matching a name
```

- Tests live next to the module they cover, as `*.test.ts` (e.g. `components/workflows/run-readiness.test.ts`).
- Import `describe`/`it`/`expect`/`vi` from `vitest` explicitly; globals are off.
- The `@/` path alias resolves as it does in the app.

#### Test logic and business rules, never UI

Frontend tests cover **logic and business rules**: data derivation and transformation, state transitions, validation, filtering and sorting, API response mapping, and the decisions a hook or store makes. They **never test UI**: markup, DOM structure, CSS classes, styling, layout, copy, icons or snapshots. UI assertions break on every cosmetic change without catching real bugs.

When logic is tangled inside a component, extract it into a plain function, hook or store module and test that.

```ts
// ✅ Correct - test the rule the run dialog relies on
describe('runReadiness', () => {
  it('holds a web-search assessment until consent is given', () => {
    const selectedTypes = [WorkflowRunType.ReferenceValidationV2];
    expect(readiness({ selectedTypes }).blocker).toBe('consent-missing');
    expect(readiness({ selectedTypes, webSearchConsent: true }).ready).toBe(true);
  });
});

// ❌ Incorrect - rendering the component and asserting on its markup
it('renders the run button disabled', () => {
  const html = renderToStaticMarkup(<RunWorkflowDialog selectedTypes={[WorkflowRunType.ReferenceValidationV2]} />);
  expect(html).toContain('disabled');
  expect(html).toContain('bg-muted');
});
```

### Evaluations (Inspect AI)

[Inspect AI](https://inspect.ai-safety-institute.org.uk/) evals live under `evals_inspectai/e2e/`, one directory per workflow with a dataset file (`dataset.json` or `dataset.jsonl`) and a task module. They run each workflow end to end against the API, the same way a user triggers it, so **the backend must be running** (`uv run dev.py`).

```bash
uv run inspect eval evals_inspectai/e2e/reference_validation_v2/reference_validation_v2_e2e.py              # Full suite
uv run inspect eval evals_inspectai/e2e/figures_tables_check/figures_tables_check_e2e.py --sample-id=1      # One sample (1-indexed)
uv run inspect eval evals_inspectai/e2e/figures_tables_check/figures_tables_check_e2e.py --sample-id=1 --epochs=3   # Repeat for determinism
uv run inspect eval evals_inspectai/e2e/reference_validation_v2/reference_validation_v2_e2e.py --limit=5-10 # A range
uv run inspect view                                                                                         # Results dashboard
```

---

## Git Conventions

### Never commit or open a PR unless asked

Finish the work, confirm it passes the checks above, then wait. The user reviews changes before they go into git.

### Commit messages

Always use [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <description>`. Common types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `style`, `perf`, `ci`, `build`.

```bash
# ✅ Correct
feat(revisions): add revision system for main document replacement
fix(upload): validate single main file per revision
test(revisions): add unit tests for create_new_revision

# ❌ Incorrect
update files
fix bug
WIP
```

### Pull requests

Always target `dev` unless the user names another base branch. The description has four sections: "Summary", "Motivation", "What's Changed" (split into backend and frontend, listing every changed file and why) and "Risks and Mitigations". Keep it under 1000 words.
