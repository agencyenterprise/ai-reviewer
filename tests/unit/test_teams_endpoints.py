"""Tests for the Teams messaging endpoint's own logic.

What is worth pinning here is the answer that arrives *after* the turn has ended. The
person has already been told "I will follow up here shortly", so a failure that is
merely logged leaves them waiting forever -- and a detached task whose result is never
read does not even reliably log. That combination is how a lost reply becomes silent.

The endpoint's authentication boundary is covered in ``test_teams_bot.py``, where the
token validation lives.
"""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from lib.api.routers.microsoft import teams


class TestWhenAnsweringFails:
    """Every way out of ``_answer_into_thread`` has to end in something being said."""

    @pytest.mark.asyncio
    async def test_a_reported_failure_is_apologised_for(self) -> None:
        failed = AsyncMock(
            return_value=type("Answer", (), {"failed": True, "error": "boom", "text": ""})()
        )
        posted = AsyncMock()
        with patch.object(teams, "answer_question", failed), patch.object(
            teams.bot, "post_later", posted
        ):
            await teams._answer_into_thread(
                "ref", "does this overclaim?", "Carlos", "19:x", None, "token"
            )

        posted.assert_awaited_once()
        assert posted.await_args is not None
        assert posted.await_args[0][1] == teams.APOLOGY

    @pytest.mark.asyncio
    async def test_a_raise_is_apologised_for_too(self) -> None:
        """``answer_question`` reports rather than raises, so this is the gap past it.

        Its own guard does not cover prompt formatting or the run config, and an
        ``except Exception`` never covers a future edit.
        """

        posted = AsyncMock()
        with patch.object(
            teams, "answer_question", AsyncMock(side_effect=RuntimeError("upstream"))
        ), patch.object(teams.bot, "post_later", posted):
            await teams._answer_into_thread(
                "ref", "does this overclaim?", "Carlos", "19:x", None, "token"
            )

        posted.assert_awaited_once()
        assert posted.await_args is not None
        assert posted.await_args[0][1] == teams.APOLOGY

    @pytest.mark.asyncio
    async def test_a_raise_does_not_escape_to_the_task(self) -> None:
        """Because the caller is detached, an escape would only be a warning."""

        with patch.object(
            teams, "answer_question", AsyncMock(side_effect=RuntimeError("upstream"))
        ), patch.object(teams.bot, "post_later", AsyncMock()):
            await teams._answer_into_thread("ref", "q", "Carlos", "19:x", None, "t")

    @pytest.mark.asyncio
    async def test_the_question_is_truncated_in_the_log(self) -> None:
        """A question can quote the document, and these are confidential."""

        question = "x" * 500
        with patch.object(
            teams, "answer_question", AsyncMock(side_effect=RuntimeError("upstream"))
        ), patch.object(teams.bot, "post_later", AsyncMock()), patch.object(
            teams.logger, "exception"
        ) as logged:
            await teams._answer_into_thread("ref", question, "C", "19:x", None, "t")

        assert logged.call_args is not None
        assert len(logged.call_args[0][1]) == 120


class TestRetiringADetachedTask:
    """``_finished`` is the backstop for anything the coroutine's own guard misses."""

    async def _task(self, coroutine: Any) -> "asyncio.Task[None]":
        task = asyncio.create_task(coroutine)
        teams._running.add(task)
        task.add_done_callback(teams._finished)
        await asyncio.sleep(0)
        return task

    @pytest.mark.asyncio
    async def test_a_completed_task_is_released(self) -> None:
        """Otherwise the set grows for the life of the process."""

        async def fine() -> None:
            return None

        task = await self._task(fine())
        await task
        await asyncio.sleep(0)
        assert task not in teams._running

    @pytest.mark.asyncio
    async def test_a_failure_is_logged_rather_than_left_unretrieved(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The bug this replaced: ``add_done_callback(_running.discard)`` alone.

        It dropped the reference without reading the result, so asyncio had an
        exception nobody retrieved -- a shutdown warning at best.
        """

        async def broken() -> None:
            raise RuntimeError("something outside the guard")

        with caplog.at_level(logging.ERROR, logger=teams.logger.name):
            task = await self._task(broken())
            with pytest.raises(RuntimeError):
                await task
            await asyncio.sleep(0)

        assert "detached answer task failed" in caplog.text
        assert "something outside the guard" in caplog.text
        assert task not in teams._running

    @pytest.mark.asyncio
    async def test_cancellation_is_not_reported_as_a_fault(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Shutdown cancels in-flight work; that is not an error worth paging over."""

        async def slow() -> None:
            await asyncio.sleep(10)

        with caplog.at_level(logging.ERROR, logger=teams.logger.name):
            task = await self._task(slow())
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await asyncio.sleep(0)

        assert "failed" not in caplog.text
        assert task not in teams._running


class TestAnsweringAnInvoke:
    """A `signin/*` invoke's reply is protocol, not a formality.

    The endpoint used to return an empty 200 for every activity. For an ordinary
    message that is right. For an invoke it discards what the SDK produced -- and a
    token exchange that needs consent comes back as 412 with a
    TokenExchangeInvokeResponse, which is how Teams learns to fall back to the sign-in
    card. Reporting 200 instead tells Teams the exchange worked, and sign-in stalls.
    """

    def response_for(self, status: int, body: Any) -> Any:
        from microsoft_agents.activity.invoke_response import InvokeResponse

        return InvokeResponse(status=status, body=body)

    def test_a_consent_required_exchange_keeps_its_412_and_body(self) -> None:
        body = {
            "id": "x",
            "connectionName": "graph-user",
            "failureDetail": "Proceed with regular login.",
        }
        response = teams._invoke_response(self.response_for(412, body))

        assert response.status_code == 412
        assert b"Proceed with regular login." in response.body
        assert response.media_type == "application/json"

    def test_a_successful_exchange_keeps_its_status_and_needs_no_body(self) -> None:
        response = teams._invoke_response(self.response_for(200, None))

        assert response.status_code == 200
        assert not response.body

    def test_a_model_body_is_serialised_rather_than_crashing(self) -> None:
        """``body`` is typed ``object``; a 500 here would hide the status it carries."""

        from microsoft_agents.activity import TokenExchangeInvokeResponse

        response = teams._invoke_response(
            self.response_for(
                412,
                TokenExchangeInvokeResponse(
                    id="x", connection_name="graph-user", failure_detail="nope"
                ),
            )
        )

        assert response.status_code == 412
        assert b"nope" in response.body

    def client(self) -> Any:
        """Just this router, not the whole application.

        Importing ``lib.api.main`` here builds every route and reads module-level
        config, which made this test depend on which other test had run first.
        """

        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(teams.router, prefix="/api/microsoft")
        return TestClient(app, raise_server_exceptions=False)

    def test_an_ordinary_message_still_gets_an_empty_200(self) -> None:
        """The Connector treats a body on a normal activity as a payload."""

        with patch.object(teams.bot, "handle", AsyncMock(return_value=None)):
            result = self.client().post(
                "/api/microsoft/teams/messages",
                json={"type": "message", "text": "hi", "conversation": {"id": "19:x"}},
                headers={"Authorization": "Bearer ok"},
            )

        assert result.status_code == 200
        assert result.content == b""

    def test_an_invoke_reply_reaches_the_channel_over_http(self) -> None:
        """End to end through the route, since the discarded value was the bug."""

        from microsoft_agents.activity.invoke_response import InvokeResponse

        refused = InvokeResponse(status=412, body={"failureDetail": "needs consent"})
        with patch.object(teams.bot, "handle", AsyncMock(return_value=refused)):
            result = self.client().post(
                "/api/microsoft/teams/messages",
                json={"type": "invoke", "name": "signin/tokenExchange"},
                headers={"Authorization": "Bearer ok"},
            )

        assert result.status_code == 412
        assert result.json()["failureDetail"] == "needs consent"
