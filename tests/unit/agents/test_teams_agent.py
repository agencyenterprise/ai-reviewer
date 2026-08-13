"""Tests for the agent that answers Teams questions.

It differs from the Word agent in one structural way: it is not given a document.
Opening one is its own job, so what is asserted here is that it gets the tool to do
that and mounts only the skills up front -- the skills middleware reads those once
before the run, so a tool cannot supply them later.

The prompt assertions are narrow on purpose. A link is the only way to reach a
document, and the failure they guard against is the model filling that gap itself:
answering from a file name, or guessing at a URL.

The persistence tests carry the most weight: a document is re-read every turn, because it
may have been edited and because the next asker may not be allowed to open it. Both
failures are silent -- a stale or unauthorised answer reads perfectly well.
"""

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from lib.agents import teams_agent
from lib.agents.teams_agent import answer_question, answer_text
from lib.agents.tools.sharepoint import (
    COMMENTS_DOCUMENT,
    DOCUMENT_SOURCE,
    MAIN_DOCUMENT,
)
from lib.services.microsoft.graph.client import DocumentNotAllowed, GraphError
from lib.services.microsoft.graph.documents import LoadedDocument

# Every run reads as somebody; the tests do not care who.
TOKEN = "a-user-token"
THREAD = "19:abc@thread.tacv2;messageid=1754"
DOCUMENT_URL = "https://x.sharepoint.com/sites/X/a.docx"


def agent_returning(answer: str, state: Optional[dict[str, Any]] = None) -> MagicMock:
    """A deep agent whose last message is the answer.

    Returns the whole history the way a checkpointed run does -- the question and then
    the reply -- because what is read back out is now the messages rather than a
    structured field.

    ``state`` is what a checkpointer would restore for this thread, which is how the
    tests stand in for an earlier turn without running one.
    """

    fake = MagicMock()
    fake.ainvoke = AsyncMock(
        return_value={
            "messages": [HumanMessage(content="a question"), AIMessage(content=answer)],
        }
    )
    snapshot = MagicMock()
    snapshot.values = state if state is not None else {}
    fake.aget_state = AsyncMock(return_value=snapshot)
    return fake


def loaded_document(markdown: str = "## A heading\n\nA paragraph.") -> LoadedDocument:
    """What Graph hands back when the document is re-read."""

    return LoadedDocument(
        name="a.docx",
        url=DOCUMENT_URL,
        markdown=markdown,
        comments=[],
        last_modified="2026-08-11T13:31:28Z",
        size_bytes=1024,
    )


def thread_with_document(url: str = DOCUMENT_URL) -> dict[str, Any]:
    """State as it stands after some earlier turn opened a document."""

    return {
        "files": {
            MAIN_DOCUMENT: {"content": ["## A heading", "", "A paragraph."]},
            DOCUMENT_SOURCE: {"content": [url]},
        },
        "messages": [],
    }


@pytest.fixture(autouse=True)
def checkpointer() -> Any:
    """Stand in for the saver, since every answer now belongs to a thread.

    Nothing here is about the pool -- ``test_checkpointer.py`` covers that -- but every
    call opens one, so it is patched for the whole module rather than per test.
    """

    saver = MagicMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=saver)
    context.__aexit__ = AsyncMock(return_value=False)
    with patch(
        "lib.agents.teams_agent.get_checkpointer", MagicMock(return_value=context)
    ) as opened:
        yield opened


class TestWhatTheAgentIsGiven:
    @pytest.mark.asyncio
    async def test_it_gets_the_tool_to_open_a_document(self) -> None:
        """Opening from a link, and nothing that searches by name."""

        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("an answer"),
        ) as build:
            await answer_question(
                "does this overclaim?", graph_token=TOKEN, thread_id=THREAD
            )

        tools = build.call_args.kwargs["tools"]
        assert {tool.name for tool in tools} == {"open_document"}

    @pytest.mark.asyncio
    async def test_no_document_is_mounted_up_front(self) -> None:
        """The document arrives through the tool; only skills are mounted."""

        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "does this overclaim?", graph_token=TOKEN, thread_id=THREAD
            )

        files = agent.ainvoke.call_args[0][0]["files"]
        assert "/main.md" not in files, "the agent opens its own document"
        assert any(path.startswith("/skills/") for path in files), (
            "skills must be mounted before the run; a tool cannot add them"
        )

    @pytest.mark.asyncio
    async def test_a_pasted_link_is_passed_through_as_a_hint(self) -> None:
        agent = agent_returning("an answer")
        url = "https://x.sharepoint.com/sites/X/a.docx"
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "is this right?",
                graph_token=TOKEN,
                thread_id=THREAD,
                document_hint=url,
            )

        prompt = agent.ainvoke.call_args[0][0]["messages"][0].content
        assert url in prompt

    @pytest.mark.asyncio
    async def test_without_a_link_the_prompt_says_nothing_about_one(self) -> None:
        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "check the CERN paper", graph_token=TOKEN, thread_id=THREAD
            )

        prompt = agent.ainvoke.call_args[0][0]["messages"][0].content
        assert "They linked to this document" not in prompt

    @pytest.mark.asyncio
    async def test_the_asker_is_named_in_the_prompt(self) -> None:
        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "hello?",
                graph_token=TOKEN,
                thread_id=THREAD,
                asked_by="Carlos Bonetti",
            )

        assert "Carlos Bonetti" in agent.ainvoke.call_args[0][0]["messages"][0].content


class TestReadingTheAnswerOutOfTheMessages:
    """No ``response_format``: the answer is the last thing the model said.

    Which puts the burden on reading it back correctly, and a persisted thread makes one
    of those cases dangerous rather than merely wrong.
    """

    def test_the_last_thing_said_is_the_answer(self) -> None:
        assert (
            answer_text(
                [
                    HumanMessage(content="first?"),
                    AIMessage(content="an old answer"),
                    HumanMessage(content="second?"),
                    AIMessage(content="the new answer"),
                ]
            )
            == "the new answer"
        )

    def test_markdown_survives_intact(self) -> None:
        """The reason for dropping the JSON wrapper, so it is worth asserting."""

        markdown = '## Findings\n\n1. **GDP** is undefined at "the total GDP" [70]\n'

        assert answer_text([HumanMessage(content="?"), AIMessage(content=markdown)]) == (
            markdown.strip()
        )

    def test_reasoning_blocks_are_not_part_of_the_answer(self) -> None:
        """Reasoning-model output arrives as blocks beside the text."""

        message = AIMessage(
            content=[
                {"type": "reasoning", "summary": "let me think about the abbreviations"},
                {"type": "text", "text": "GDP is never defined."},
            ]
        )

        assert answer_text([HumanMessage(content="?"), message]) == "GDP is never defined."

    def test_a_turn_ending_in_a_tool_call_is_not_an_answer(self) -> None:
        """It reached the recursion limit mid-work, so there is nothing to post."""

        working = AIMessage(
            content="",
            tool_calls=[{"name": "open_document", "args": {"url": "u"}, "id": "1"}],
        )

        assert answer_text([HumanMessage(content="?"), working]) == ""

    def test_it_never_reaches_back_into_an_earlier_turn(self) -> None:
        """The dangerous case, and only possible because the thread is persisted.

        A turn that produces no text must come back empty rather than re-posting the
        previous turn's answer as though it were a reply to the new question.
        """

        history = [
            HumanMessage(content="what does paragraph 12 say?"),
            AIMessage(content="Paragraph 12 says the budget tripled."),
            HumanMessage(content="and paragraph 13?"),
            AIMessage(
                content="",
                tool_calls=[{"name": "read_file", "args": {}, "id": "2"}],
            ),
            ToolMessage(content="…", tool_call_id="2"),
        ]

        assert answer_text(history) == ""

    def test_nothing_at_all_is_empty_rather_than_an_error(self) -> None:
        assert answer_text([]) == ""


class TestTheAnswer:
    @pytest.mark.asyncio
    async def test_a_normal_answer_comes_back(self) -> None:
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("It overclaims in two places."),
        ):
            answer = await answer_question(
                "does this overclaim?",
                graph_token=TOKEN,
                thread_id=THREAD,
            )

        assert answer.failed is False
        assert answer.text == "It overclaims in two places."

    @pytest.mark.asyncio
    async def test_an_empty_answer_is_a_failure_rather_than_a_blank_post(self) -> None:
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("   "),
        ):
            answer = await answer_question(
                "does this overclaim?",
                graph_token=TOKEN,
                thread_id=THREAD,
            )

        assert answer.failed is True and answer.text == ""

    @pytest.mark.asyncio
    async def test_a_crash_is_reported_rather_than_raised(self) -> None:
        """The caller is a background task with nobody to hand an exception to."""

        broken = agent_returning("never gets this far")
        broken.ainvoke = AsyncMock(side_effect=RuntimeError("upstream timeout"))
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=broken
        ):
            answer = await answer_question(
                "does this overclaim?",
                graph_token=TOKEN,
                thread_id=THREAD,
            )

        assert answer.failed is True and "upstream timeout" in (answer.error or "")


class TestContinuingAConversation:
    """One Teams thread is one LangGraph thread, which is the whole feature."""

    @pytest.mark.asyncio
    async def test_one_id_keys_the_checkpoint_and_the_langfuse_session(self) -> None:
        """Both, from one parameter: a conversation is findable in the trace view under
        the same id it is stored under."""

        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "and the second one?", graph_token=TOKEN, thread_id=THREAD
            )

        config = agent.ainvoke.call_args.kwargs["config"]
        assert config["configurable"]["thread_id"] == THREAD
        assert config["metadata"]["langfuse_session_id"] == THREAD

    @pytest.mark.asyncio
    async def test_a_checkpointer_is_given_to_the_agent(self) -> None:
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("an answer"),
        ) as build:
            await answer_question(
                "and the second one?", graph_token=TOKEN, thread_id=THREAD
            )

        assert build.call_args.kwargs["checkpointer"] is not None

    @pytest.mark.asyncio
    async def test_a_thread_is_not_optional(self) -> None:
        """No opting out, so there is no second path where a document is unchecked."""

        # Loosely typed so that omitting the argument -- the thing under test -- does not
        # need a type: ignore for what mypy is right to reject.
        called: Any = answer_question

        with pytest.raises(TypeError, match="thread_id"):
            await called("does this overclaim?", graph_token=TOKEN)

    @pytest.mark.asyncio
    async def test_the_system_prompt_is_not_a_message(self) -> None:
        """It would be checkpointed, and re-appended on every single turn."""

        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ) as build:
            await answer_question(
                "does this overclaim?", graph_token=TOKEN, thread_id=THREAD
            )

        messages = agent.ainvoke.call_args[0][0]["messages"]
        assert len(messages) == 1, "only the new question belongs in a persisted thread"
        assert messages[0].type == "human"
        assert "Draft Detective" in build.call_args.kwargs["system_prompt"]


class TestRereadingTheDocumentEachTurn:
    """A continuing thread re-reads its document instead of keeping the mounted copy.

    Two independent reasons, both covered below: it may have been edited since, and a
    checkpoint carries no memory of whose access loaded it.
    """

    @pytest.mark.asyncio
    async def test_the_document_is_read_again_as_the_person_asking(self) -> None:
        agent = agent_returning("an answer", state=thread_with_document())
        load = AsyncMock(return_value=loaded_document("Rewritten since last turn."))
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(teams_agent.documents, "load", load):
            await answer_question(
                "and the second one?", graph_token=TOKEN, thread_id=THREAD
            )

        assert load.await_args is not None
        assert load.await_args.args[0] == DOCUMENT_URL, "the thread's own document"
        assert load.await_args.kwargs["token"] == TOKEN, "read as the asker"

        files = agent.ainvoke.call_args[0][0]["files"]
        body = "\n".join(files[MAIN_DOCUMENT]["content"])
        assert "Rewritten since last turn." in body, "the fresh copy, not the old"

    @pytest.mark.asyncio
    async def test_a_stale_copy_is_replaced_rather_than_merged(self) -> None:
        """The failure this exists to prevent: answering from text since rewritten."""

        stale = thread_with_document()
        stale["files"][MAIN_DOCUMENT] = {"content": ["The old wording."]}
        agent = agent_returning("an answer", state=stale)
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(
            teams_agent.documents,
            "load",
            AsyncMock(return_value=loaded_document("The new wording.")),
        ):
            await answer_question(
                "does this overclaim?", graph_token=TOKEN, thread_id=THREAD
            )

        files = agent.ainvoke.call_args[0][0]["files"]
        body = "\n".join(files[MAIN_DOCUMENT]["content"])
        assert "The old wording." not in body
        assert "The new wording." in body

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "failure",
        [
            GraphError("could not find a.docx: 403"),
            DocumentNotAllowed("outside the site paths this service may read"),
            TimeoutError("graph took too long"),
        ],
        ids=[
            "graph refuses this person",
            "the allowlist no longer covers it",
            "a timeout",
        ],
    )
    async def test_a_document_that_cannot_be_read_is_given_up(
        self, failure: Exception
    ) -> None:
        """Fail closed. A refusal and a timeout are indistinguishable from here, and
        keeping the copy would answer someone from a document they may not open."""

        agent = agent_returning("an answer", state=thread_with_document())
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(
            teams_agent.documents, "load", AsyncMock(side_effect=failure)
        ):
            await answer_question(
                "what does paragraph 12 say?",
                graph_token="somebody-elses-token",
                thread_id=THREAD,
            )

        files = agent.ainvoke.call_args[0][0]["files"]
        assert files[MAIN_DOCUMENT] is None
        assert files[COMMENTS_DOCUMENT] is None
        assert files[DOCUMENT_SOURCE] is None

    @pytest.mark.asyncio
    async def test_the_agent_is_told_not_to_answer_from_the_history(self) -> None:
        """Dropping the file is not enough: what was quoted from it is still above."""

        agent = agent_returning("an answer", state=thread_with_document())
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(
            teams_agent.documents, "load", AsyncMock(side_effect=GraphError("403"))
        ):
            await answer_question(
                "what does paragraph 12 say?",
                graph_token="somebody-elses-token",
                thread_id=THREAD,
            )

        prompt = agent.ainvoke.call_args[0][0]["messages"][0].content
        assert "could not be opened for the person asking now" in prompt
        assert "Do not answer from what was said about it earlier" in prompt

    @pytest.mark.asyncio
    async def test_the_notice_does_not_claim_they_lack_access(self) -> None:
        """A timeout is not a permission finding, and saying so would be a falsehood."""

        agent = agent_returning("an answer", state=thread_with_document())
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(
            teams_agent.documents, "load", AsyncMock(side_effect=TimeoutError("slow"))
        ):
            await answer_question(
                "what does it say?", graph_token=TOKEN, thread_id=THREAD
            )

        prompt = agent.ainvoke.call_args[0][0]["messages"][0].content
        assert "may not have access, or it may have moved" in prompt

    @pytest.mark.asyncio
    async def test_a_new_link_closes_the_old_document(self) -> None:
        """The agent will open the new one; the old must not linger unread."""

        agent = agent_returning("an answer", state=thread_with_document())
        load = AsyncMock(return_value=loaded_document())
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(teams_agent.documents, "load", load):
            await answer_question(
                "what about this one?",
                graph_token=TOKEN,
                thread_id=THREAD,
                document_hint="https://x.sharepoint.com/sites/X/different.docx",
            )

        files = agent.ainvoke.call_args[0][0]["files"]
        assert files[MAIN_DOCUMENT] is None, "the old document goes"
        assert load.await_count == 0, "the tool opens the new one, not this"

        prompt = agent.ainvoke.call_args[0][0]["messages"][0].content
        assert "could not be opened" not in prompt, "nothing went wrong here"

    @pytest.mark.asyncio
    async def test_a_thread_with_no_document_reads_nothing(self) -> None:
        """The common case -- a first question, or a conversation about nothing yet."""

        agent = agent_returning("an answer", state={"files": {}, "messages": []})
        load = AsyncMock()
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ), patch.object(teams_agent.documents, "load", load):
            await answer_question(
                "what can you do?", graph_token=TOKEN, thread_id=THREAD
            )

        assert load.await_count == 0

    @pytest.mark.asyncio
    async def test_every_turn_reads_the_thread_before_answering(self) -> None:
        """The check cannot be skipped, so the state is always looked at first."""

        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question(
                "what can you do?", graph_token=TOKEN, thread_id=THREAD
            )

        assert agent.aget_state.await_count == 1


class TestThePrompt:
    def test_it_forbids_answering_from_a_name_alone(self) -> None:
        from lib.agents.teams_agent import SYSTEM_PROMPT

        assert "Open a document before answering" in SYSTEM_PROMPT

    def test_a_link_is_stated_as_the_only_way_to_reach_a_document(self) -> None:
        """The behaviour most likely to drift, since searching feels helpful."""

        from lib.agents.teams_agent import SYSTEM_PROMPT

        assert "A link is the only way to reach a document" in SYSTEM_PROMPT
        assert "must not guess at a URL" in SYSTEM_PROMPT

    def test_it_requires_asking_for_the_link_when_only_a_name_is_given(self) -> None:
        from lib.agents.teams_agent import SYSTEM_PROMPT

        assert "ask them to paste it" in SYSTEM_PROMPT

    def test_it_still_answers_questions_that_need_no_document(self) -> None:
        """Asking for a link to answer "what can you do?" would be a regression."""

        from lib.agents.teams_agent import SYSTEM_PROMPT

        assert "Some questions need no document at all" in SYSTEM_PROMPT
