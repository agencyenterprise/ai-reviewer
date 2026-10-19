"""Tests for the add-in chat's threads and suggestions.

Threads: found by the document whatever URL form Word reports, and only for the account
that owns them. Suggestions: the agent hears once what became of each, worded from what
was stored.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.models.microsoft_word_chat_thread import MicrosoftWordChatThread
from lib.services.microsoft.word import chat_suggestions, chat_threads, handoffs
from lib.services.microsoft.word.chat_suggestions import ChatSuggestion, news
from lib.services.microsoft.word.handoffs import (
    Account,
    HandoffComment,
    HandoffEdit,
    HandoffItems,
    HandoffOutcome,
    ItemOutcome,
)

ANA = Account(oid="oid-ana", tid="tid-contoso")
GUID = "546f3fae-d9fb-457f-a563-d25549eb3601"
PATH_URL = "https://contoso.sharepoint.com/sites/Policy/Shared%20Documents/Draft.docx"
VIEWER_URL = (
    "https://contoso.sharepoint.com/sites/Policy/_layouts/15/Doc.aspx"
    f"?sourcedoc=%7B{GUID.upper()}%7D&file=Draft.docx"
)
NOW = datetime.now(UTC)
ITEMS = HandoffItems(
    comments=[HandoffComment(quote="is the only option", comment="Overclaims.")],
    edits=[HandoffEdit(quote="recieve", replacement="receive")],
)


def thread(keys: list[str], last_turn: datetime = NOW) -> MicrosoftWordChatThread:
    return MicrosoftWordChatThread(
        id=uuid.uuid4(),
        owner_oid=ANA.oid,
        owner_tid=ANA.tid,
        document_name="Draft.docx",
        document_url=PATH_URL,
        document_keys=keys,
        created_at=last_turn,
        last_turn_at=last_turn,
    )


def session_listing(rows: list[Any]) -> Any:
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


class TestRecognisingTheDocument:
    def test_a_saved_document_is_known_by_its_path(self) -> None:
        assert chat_threads.thread_keys(PATH_URL) == sorted(
            handoffs.keys_for_url(PATH_URL)
        )

    def test_a_local_file_is_known_by_its_path(self) -> None:
        # Word desktop reports a file that is not in the cloud by its path on disk.
        assert chat_threads.thread_keys("/Users/Ana/Draft.docx") == [
            "url:/users/ana/draft.docx"
        ]

    def test_an_unsaved_document_has_one_shared_key(self) -> None:
        assert chat_threads.thread_keys("  ") == [chat_threads.UNSAVED]

    def test_each_unsaved_pane_has_its_own_key(self) -> None:
        first = chat_threads.thread_keys("unsaved:1b2c")
        second = chat_threads.thread_keys("unsaved:9f8e")

        assert first != second and chat_threads.UNSAVED not in first
        assert chat_threads.document_name("unsaved:1b2c") == "this document"

    def test_the_name_comes_from_the_url(self) -> None:
        assert chat_threads.document_name(PATH_URL) == "Draft.docx"
        assert chat_threads.document_name("") == "this document"

    def test_a_doc_aspx_link_is_named_by_its_file_not_its_page(self) -> None:
        url = (
            "https://contoso-my.sharepoint.com/:w:/r/personal/ana/_layouts/15/Doc.aspx"
            "?sourcedoc=%7B97126C1E%7D&file=v3%20CERN%20for%20AI.docx&action=default"
        )
        assert chat_threads.document_name(url) == "v3 CERN for AI.docx"


class TestFindingTheCurrentThread:
    @pytest.mark.asyncio
    async def test_it_is_found_under_any_url_form_word_reports(self) -> None:
        mine = thread([f"guid:{GUID}", *chat_threads.thread_keys(PATH_URL)])
        other = thread(["guid:00000000-0000-0000-0000-000000000000"])
        session = session_listing([other, mine])
        with patch.object(chat_threads, "get_async_db_session", return_value=session):
            found = await chat_threads.current(ANA, VIEWER_URL)

        assert found is mine
        sql = str(session.execute.await_args.args[0]).lower()
        assert "owner_oid" in sql and "owner_tid" in sql and "cleared_at is null" in sql

    @pytest.mark.asyncio
    async def test_none_when_no_thread_is_about_this_document(self) -> None:
        session = session_listing([thread(["guid:other"])])
        with patch.object(chat_threads, "get_async_db_session", return_value=session):
            assert await chat_threads.current(ANA, PATH_URL) is None


def suggestion(
    status: str,
    finished: datetime | None = None,
    outcome: HandoffOutcome | None = None,
    heard: datetime | None = None,
) -> ChatSuggestion:
    return ChatSuggestion(
        id=uuid.uuid4(),
        status=status,  # type: ignore[arg-type]  # the four statuses, as plain strings
        document_name="Draft.docx",
        document_url=PATH_URL,
        items=ITEMS,
        outcome=outcome,
        created_at=NOW - timedelta(hours=1),
        finished_at=finished,
        heard_at=heard,
    )


class TestWhatTheAgentHears:
    def test_an_application_since_the_last_turn_is_described(self) -> None:
        outcome = HandoffOutcome(
            items=[
                ItemOutcome(kind="comment", quote="is the only option", applied=True),
                ItemOutcome(
                    kind="edit",
                    quote="recieve",
                    applied=False,
                    detail=handoffs.REASONS["not_found"],
                ),
            ]
        )
        said = news([suggestion("applied", NOW, outcome)])

        assert "1 of 2" in said
        assert "recieve" in said and handoffs.REASONS["not_found"] in said

    def test_a_dismissal_is_described(self) -> None:
        said = news([suggestion("dismissed", NOW)])

        assert "dismissed" in said and "none were applied" in said

    def test_what_it_was_told_is_not_told_again(self) -> None:
        """By ``ask_to_apply`` while it waited, or as news before: once is enough.

        Told by when it heard, not by when the last turn began, so a card that settled
        while the answer waited on another one is still news.
        """

        heard = suggestion("applied", NOW - timedelta(minutes=10), heard=NOW)
        not_yet = suggestion("dismissed", NOW - timedelta(minutes=10))

        said = news([heard, not_yet])

        assert "dismissed" in said and "1 of" not in said

    def test_ones_still_waiting_are_mentioned(self) -> None:
        said = news([suggestion("pending")])

        assert "1 set(s)" in said and "still waiting" in said

    def test_nothing_to_say_says_nothing(self) -> None:
        assert news([]) == ""


class TestReplacingACardsItems:
    @pytest.mark.asyncio
    async def test_only_a_pending_card_of_theirs_is_changed(self) -> None:
        result = MagicMock()
        result.first.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        with patch.object(
            chat_suggestions, "get_async_db_session", return_value=session
        ):
            changed = await chat_suggestions.replace_items(uuid.uuid4(), ANA, ITEMS)

        assert changed is False
        sql = str(session.execute.await_args.args[0]).lower()
        assert sql.startswith("update microsoft_word_handoffs")
        assert "status =" in sql and "requested_by_oid" in sql
        assert "chat_thread_id is not null" in sql and "created_at >=" in sql
