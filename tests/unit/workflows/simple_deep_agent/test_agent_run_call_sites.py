"""Every caller of `SimpleDeepAgent.ainvoke` reads the `DeepAgentRun` it returns.

`ainvoke` used to hand back `(output, messages)` and now returns a single
`DeepAgentRun`. Two subclasses outside the manifest inherit it -- the
literature-review and live-reports nodes -- and both were still writing
`result, messages = await agent.ainvoke({})`, which raises
`ValueError: too many values to unpack` the moment either workflow runs.

Neither mypy nor the rest of the suite caught that. Pydantic models define
`__iter__`, so mypy sees `DeepAgentRun` as an iterable of unknown length and
accepts unpacking it into any number of names; the arity only fails at
runtime. That is the gap these tests cover, and why they check the call sites
rather than the return type: a type annotation cannot express this.
"""

import ast
import inspect
import warnings
from pathlib import Path

import pytest

from lib.workflows.simple_deep_agent.agent import SimpleDeepAgent
from lib.workflows.simple_deep_agent.agent_types import DeepAgentRun

_LIB = Path(__file__).resolve().parents[4] / "lib"


def _subclass_modules() -> list[Path]:
    """Modules defining a `SimpleDeepAgent` subclass, found by parsing, not import.

    Importing every module under `lib/` to walk `__subclasses__` would pull in
    database and service wiring for a question the source already answers.
    """
    found = []
    for path in _LIB.rglob("*.py"):
        with warnings.catch_warnings():
            # lib/services/converters/markitdown.py has a pre-existing invalid
            # escape in a docstring. Parsing every module surfaces it on every
            # run; it is not this test's business and not this PR's to fix.
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(b, ast.Name) and b.id == "SimpleDeepAgent"
                for b in node.bases
            ):
                found.append(path)
                break
    return found


def test_the_subclasses_are_the_ones_we_think():
    """A new subclass should fail this and make its author read the file."""
    names = sorted(p.name for p in _subclass_modules())
    assert names == ["literature_review.py", "live_reports.py"]


@pytest.mark.parametrize(
    "path", _subclass_modules(), ids=lambda p: p.name  # type: ignore[misc]
)
def test_no_call_site_unpacks_ainvoke(path: Path):
    """`x, y = await agent.ainvoke(...)` is the shape that breaks at runtime."""
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not (isinstance(value, ast.Await) and isinstance(value.value, ast.Call)):
            continue
        func = value.value.func
        if not (isinstance(func, ast.Attribute) and func.attr == "ainvoke"):
            continue
        for target in node.targets:
            assert not isinstance(target, ast.Tuple), (
                f"{path.name}:{node.lineno} unpacks ainvoke() into a tuple. "
                f"It returns a DeepAgentRun; read its delivery fields and "
                f".messages off it instead."
            )


def test_ainvoke_returns_a_deep_agent_run():
    """The contract the call sites above are held to."""
    assert inspect.signature(SimpleDeepAgent.ainvoke).return_annotation is DeepAgentRun


def test_unpacking_a_run_is_an_error_not_a_silent_mismatch():
    """Documents why this needs a test at all rather than a type annotation."""
    run = DeepAgentRun(files={"/report.html": "<html></html>"})
    with pytest.raises(ValueError, match="too many values to unpack"):
        _first, _second = run  # type: ignore[misc]
