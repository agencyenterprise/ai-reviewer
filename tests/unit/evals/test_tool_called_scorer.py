"""The local-image plumbing and the behavioural scorer behind the figure samples."""

import base64
from pathlib import Path

import pytest
from inspect_ai.model import ChatMessageAssistant, ChatMessageUser, ModelName
from inspect_ai.scorer import CORRECT, INCORRECT, SampleScore, Score, Target
from inspect_ai.solver import TaskState
from inspect_ai.tool import ToolCall

from evals_inspectai.common import loaders
from evals_inspectai.common.loaders import inline_local_images, references_local_images
from evals_inspectai.common.scorers import applicable_mean, tool_called

FIGURE_DOC = (
    "# Report\n\nFigure 1 shows it.\n\n![](files/figures/x.png)\n\n**Figure 1**\n"
)


def _state(messages, input_text) -> TaskState:
    return TaskState(
        model=ModelName("mockllm/model"),
        sample_id=1,
        epoch=1,
        input=input_text,
        messages=messages,
        metadata={},
    )


def _call(name: str) -> ChatMessageAssistant:
    return ChatMessageAssistant(
        content="",
        tool_calls=[
            ToolCall(id="c1", function=name, arguments={"image_reference": "x"})
        ],
    )


class TestLocalImages:
    def test_local_paths_are_recognised_and_remote_or_inlined_ones_are_not(self):
        assert references_local_images(FIGURE_DOC)
        assert not references_local_images("![](https://example.org/a.png)")
        assert not references_local_images("![](data:image/png;base64,QUJD)")
        assert not references_local_images("![](draftdetective://abc)")
        assert not references_local_images("# Plain text only\n")

    def test_inlining_replaces_the_path_with_a_data_uri_and_keeps_lines(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "files").mkdir()
        (tmp_path / "files" / "chart.png").write_bytes(b"\x89PNGfake")
        monkeypatch.setattr(loaders, "_PROJECT_ROOT", tmp_path)
        doc = "a\n\n![Chart](files/chart.png)\n\nb\n"

        inlined = inline_local_images(doc)

        encoded = base64.b64encode(b"\x89PNGfake").decode()
        assert inlined == f"a\n\n![Chart](data:image/png;base64,{encoded})\n\nb\n"
        assert inlined.count("\n") == doc.count("\n")
        assert not references_local_images(inlined)

    def test_inlining_rejects_unknown_image_types(self, tmp_path, monkeypatch):
        (tmp_path / "f.svg").write_text("<svg/>")
        monkeypatch.setattr(loaders, "_PROJECT_ROOT", tmp_path)
        with pytest.raises(ValueError):
            inline_local_images("![](f.svg)")

    def test_every_figure_referenced_by_a_dataset_exists(self):
        """A record that names a missing PNG would fail only at upload time."""
        root = Path(loaders._PROJECT_ROOT)
        missing = []
        for dataset in root.glob("e2e/*/dataset.*"):
            for match in loaders._LOCAL_IMAGE_RE.finditer(dataset.read_text()):
                if not (root / match.group("path")).exists():
                    missing.append((dataset.name, match.group("path")))
        assert missing == []


@pytest.mark.asyncio
async def test_a_call_to_the_tool_scores_correct_and_applicable():
    score = await tool_called("view_image")(
        _state([_call("view_image")], FIGURE_DOC), Target("")
    )
    assert score.value == CORRECT
    assert score.metadata == {"applicable": True}
    assert "image_reference" in (score.explanation or "")


@pytest.mark.asyncio
async def test_no_call_scores_incorrect_when_the_document_has_figures():
    score = await tool_called("view_image")(
        _state([_call("report_issue"), ChatMessageUser(content="hi")], FIGURE_DOC),
        Target(""),
    )
    assert score.value == INCORRECT
    assert score.metadata == {"applicable": True}


@pytest.mark.asyncio
async def test_text_only_documents_are_not_judged():
    """A sample without figures neither passes nor fails the check."""
    score = await tool_called("view_image")(_state([], "# Plain text\n"), Target(""))
    assert score.value == CORRECT
    assert score.metadata == {"applicable": False}


def test_applicable_mean_ignores_not_applicable_samples():
    def sample(value, applicable):
        return SampleScore(
            score=Score(value=value, metadata={"applicable": applicable})
        )

    scores = [sample(CORRECT, False), sample(CORRECT, True), sample(INCORRECT, True)]
    assert applicable_mean()(scores) == 0.5
    assert applicable_mean()([sample(CORRECT, False)]) == 0.0
