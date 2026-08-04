"""Tests for the agent that answers Teams questions.

It differs from the Word agent in one structural way: it is not given a document.
Opening one is its own job, so what is asserted here is that it gets the tool to do
that and mounts only the skills up front -- the skills middleware reads those once
before the run, so a tool cannot supply them later.

The prompt assertions are narrow on purpose. A link is the only way to reach a
document, and the failure they guard against is the model filling that gap itself:
answering from a file name, or guessing at a URL.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.agents.teams_agent import QuestionReply, answer_question


def agent_returning(answer: str) -> MagicMock:
    """A deep agent that produces one structured answer."""

    fake = MagicMock()
    fake.ainvoke = AsyncMock(
        return_value={
            "messages": [],
            "structured_response": QuestionReply(answer=answer),
        }
    )
    return fake


class TestWhatTheAgentIsGiven:
    @pytest.mark.asyncio
    async def test_it_gets_the_tool_to_open_a_document(self) -> None:
        """Opening from a link, and nothing that searches by name."""

        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("an answer"),
        ) as build:
            await answer_question("does this overclaim?")

        tools = build.call_args.kwargs["tools"]
        assert {tool.name for tool in tools} == {"open_document"}

    @pytest.mark.asyncio
    async def test_no_document_is_mounted_up_front(self) -> None:
        """The document arrives through the tool; only skills are mounted."""

        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question("does this overclaim?")

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
            await answer_question("is this right?", document_hint=url)

        prompt = agent.ainvoke.call_args[0][0]["messages"][1].content
        assert url in prompt

    @pytest.mark.asyncio
    async def test_without_a_link_the_prompt_says_nothing_about_one(self) -> None:
        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question("check the CERN paper")

        prompt = agent.ainvoke.call_args[0][0]["messages"][1].content
        assert "They linked to this document" not in prompt

    @pytest.mark.asyncio
    async def test_the_asker_is_named_in_the_prompt(self) -> None:
        agent = agent_returning("an answer")
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=agent
        ):
            await answer_question("hello?", asked_by="Carlos Bonetti")

        assert "Carlos Bonetti" in agent.ainvoke.call_args[0][0]["messages"][1].content


class TestTheAnswer:
    @pytest.mark.asyncio
    async def test_a_normal_answer_comes_back(self) -> None:
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("It overclaims in two places."),
        ):
            answer = await answer_question("does this overclaim?")

        assert answer.failed is False
        assert answer.text == "It overclaims in two places."

    @pytest.mark.asyncio
    async def test_an_empty_answer_is_a_failure_rather_than_a_blank_post(self) -> None:
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent",
            return_value=agent_returning("   "),
        ):
            answer = await answer_question("does this overclaim?")

        assert answer.failed is True and answer.text == ""

    @pytest.mark.asyncio
    async def test_a_crash_is_reported_rather_than_raised(self) -> None:
        """The caller is a background task with nobody to hand an exception to."""

        broken = MagicMock()
        broken.ainvoke = AsyncMock(side_effect=RuntimeError("upstream timeout"))
        with patch("lib.agents.teams_agent.build_llm"), patch(
            "lib.agents.teams_agent.create_deep_agent", return_value=broken
        ):
            answer = await answer_question("does this overclaim?")

        assert answer.failed is True and "upstream timeout" in (answer.error or "")


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
