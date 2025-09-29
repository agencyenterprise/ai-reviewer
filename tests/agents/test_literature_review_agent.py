from __future__ import annotations

import textwrap

import pytest

from lib.agents.literature_review import (
    LiteratureReviewResponse,
    Reference,
    ReferenceType,
    RecommendedAction,
    literature_review_agent,
)


class _FakeStructuredLLM:
    def __init__(self, schema):
        self._schema = schema

    def invoke(self, messages, config=None):
        content = "\n".join(
            getattr(message, "content", str(message)) for message in messages
        )
        if "transformer" not in content.lower():
            raise AssertionError("Expected transformer discussion in prompt")

        reference = Reference(
            title="Attention Is All You Need",
            type=ReferenceType.ARTICLE,
            link="https://doi.org/10.48550/arXiv.1706.03762",
            bibliography_info=(
                "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). "
                "Attention Is All You Need. Advances in Neural Information Processing Systems, 30."
            ),
            related_excerpt="Transformer models rely on self-attention but this paragraph omits the seminal citation.",
            rationale=(
                "The foundational transformer paper should be cited to ground the discussion of multi-head "
                "self-attention and positional encoding."
            ),
            recommended_action=RecommendedAction.ADD_CITATION,
            explanation_for_recommended_action="Add the citation after the sentence introducing self-attention mechanisms.",
        )

        return LiteratureReviewResponse(
            relevant_references=[reference],
            rationale="Ground the transformer overview in the canonical Vaswani et al. publication.",
        )


class _FakeLLM:
    def with_structured_output(self, schema):
        return _FakeStructuredLLM(schema)


@pytest.fixture(autouse=True)
def _stub_llm(monkeypatch):
    monkeypatch.setattr("lib.models.agent.init_chat_model", lambda *_, **__: _FakeLLM())


def test_attention_paragraph_suggests_attention_is_all_you_need(monkeypatch):
    original_tools = literature_review_agent.tools
    literature_review_agent.tools = []

    full_document = textwrap.dedent(
        """
        ## Transformer Architectures

        Transformer-based models have defined state-of-the-art performance across language and vision tasks. The
        architecture depends heavily on self-attention to capture token interactions without recurrence. Despite
        widespread adoption, the foundational paper that introduced multi-head attention is not cited in this
        paragraph.
        """
    ).strip()

    paragraph = "Transformer designs stack self-attention blocks with positional encodings to model context efficiently."

    try:
        response = literature_review_agent.apply_sync(
            {
                "full_document": full_document,
                "bibliography": "",
                "paragraph": paragraph,
            }
        )
    finally:
        literature_review_agent.tools = original_tools

    assert isinstance(response, LiteratureReviewResponse)
    titles = {ref.title for ref in response.relevant_references}
    assert "Attention Is All You Need" in titles

    vaswani_reference = next(
        ref
        for ref in response.relevant_references
        if ref.title == "Attention Is All You Need"
    )
    assert vaswani_reference.recommended_action is RecommendedAction.ADD_CITATION
    assert (
        "self-attention" in vaswani_reference.explanation_for_recommended_action.lower()
    )

