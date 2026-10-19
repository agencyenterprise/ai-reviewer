"""Tests for the add-in chat's routes.

They are thin, so what is pinned is the contract: every call is scoped to the signed-in
Microsoft account, a document that cannot be read is refused before anything runs, and
a turn hears about earlier suggestions.
"""

import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from lib.api.addin_auth import AddinIdentity
from lib.api.routers.microsoft import word_chat
from lib.api.routers.microsoft.word_chat import (
    WordChatClearRequest,
    WordChatResumeRequest,
)
from lib.models.microsoft_word_chat_thread import MicrosoftWordChatThread
from lib.services.image_extraction import ExtractedImage
from lib.services.microsoft.graph.documents import LoadedDocument
from lib.services.microsoft.word.handoffs import Account

ANA = Account(oid="oid-ana", tid="tid-contoso")
URL = "https://contoso.sharepoint.com/sites/Policy/Shared%20Documents/Draft.docx"
NOW = datetime.now(UTC)


@pytest.fixture(autouse=True)
def free_conversation() -> Iterator[AsyncMock]:
    """No other turn holds the conversation, and telling the agent news is recorded."""

    with (
        patch.object(
            word_chat.chat_threads, "claim", AsyncMock(return_value=True)
        ) as claim,
        patch.object(word_chat.chat_threads, "release", AsyncMock()),
        patch.object(word_chat.chat_suggestions, "mark_heard", AsyncMock()),
    ):
        yield claim


def upload(payload: bytes) -> UploadFile:
    return UploadFile(file=BytesIO(payload), filename="Draft.docx")


def caller() -> AddinIdentity:
    return AddinIdentity(oid=ANA.oid, tid=ANA.tid, email="ana@contoso.com")


def a_thread() -> MicrosoftWordChatThread:
    return MicrosoftWordChatThread(
        id=uuid.uuid4(),
        owner_oid=ANA.oid,
        owner_tid=ANA.tid,
        document_name="Draft.docx",
        document_url=URL,
        document_keys=["path:x"],
        created_at=NOW,
        last_turn_at=NOW,
    )


class TestHistory:
    @pytest.mark.asyncio
    async def test_no_conversation_yet_is_empty(self) -> None:
        with patch.object(
            word_chat.chat_threads, "current", AsyncMock(return_value=None)
        ) as current:
            history = await word_chat.get_thread(url=URL, caller=caller())

        current.assert_awaited_once_with(ANA, URL)
        assert history.thread_id is None and history.messages == []

    @pytest.mark.asyncio
    async def test_the_current_conversation_is_read_back(self) -> None:
        thread = a_thread()
        with (
            patch.object(
                word_chat.chat_threads, "current", AsyncMock(return_value=thread)
            ),
            patch.object(
                word_chat, "load_thread_messages", AsyncMock(return_value=[])
            ) as load,
        ):
            history = await word_chat.get_thread(url=URL, caller=caller())

        load.assert_awaited_once_with(str(thread.id))
        assert history.thread_id == thread.id


class TestATurn:
    @pytest.mark.asyncio
    async def test_it_runs_for_the_caller_with_news_of_earlier_suggestions(
        self,
    ) -> None:
        thread = a_thread()
        with (
            patch.object(
                word_chat.chat_threads,
                "current_or_new",
                AsyncMock(return_value=thread),
            ) as start,
            patch.object(
                word_chat.chat_threads, "begin_turn", AsyncMock(return_value=NOW)
            ),
            patch.object(
                word_chat.chat_suggestions, "for_thread", AsyncMock(return_value=[])
            ),
            patch.object(
                word_chat.chat_suggestions, "news", return_value="[news]"
            ) as news,
            patch.object(word_chat, "run_word_chat_turn") as run,
            patch.object(word_chat, "_has_document", AsyncMock(return_value=True)),
        ):
            await word_chat.stream_turn(
                url=URL,
                message="Hi",
                selection="the words",
                caller=caller(),
            )

        assert start.await_args is not None
        assert start.await_args.args[:2] == (ANA, URL)
        news.assert_called_once_with([])
        turn, target = run.call_args.args
        assert turn.thread_id == thread.id and turn.suggestion_news == "[news]"
        assert turn.document is None and turn.selection == "the words"
        assert target.requester.oid == ANA.oid and target.chat_thread_id == thread.id

    @pytest.mark.asyncio
    async def test_a_documents_images_are_stored_for_the_conversation_first(
        self,
    ) -> None:
        thread = a_thread()
        image = ExtractedImage(
            image_path="/uploads/extracted_images/a.png",
            mime_type="image/png",
            file_size=3,
            content_hash="a",
            line_number=1,
        )
        read = LoadedDocument(
            name="Draft.docx", url=URL, markdown="# Draft", images=[image]
        )
        with (
            patch.object(
                word_chat.chat_threads,
                "current_or_new",
                AsyncMock(return_value=thread),
            ),
            patch.object(word_chat.chat_threads, "begin_turn", AsyncMock()),
            patch.object(
                word_chat.chat_suggestions, "for_thread", AsyncMock(return_value=[])
            ),
            patch.object(word_chat.chat_suggestions, "news", return_value=""),
            patch.object(
                word_chat.pane_document, "from_docx", AsyncMock(return_value=read)
            ),
            patch.object(
                word_chat.file_images, "add_conversation_images", AsyncMock()
            ) as store,
            patch.object(word_chat, "run_word_chat_turn") as run,
        ):
            await word_chat.stream_turn(
                url=URL,
                message="Hi",
                document=upload(b"a .docx"),
                caller=caller(),
            )

        store.assert_awaited_once_with(thread.id, [image])
        turn, _target = run.call_args.args
        assert turn.document == read

    @pytest.mark.asyncio
    async def test_a_conversation_without_the_document_asks_for_it(self) -> None:
        # A document just saved, another account, or a chat cleared in another pane:
        # the pane did not send the document, and this conversation has none.
        with (
            patch.object(
                word_chat.chat_threads,
                "current_or_new",
                AsyncMock(return_value=a_thread()),
            ),
            patch.object(word_chat, "_has_document", AsyncMock(return_value=False)),
            patch.object(word_chat.chat_threads, "begin_turn") as begin,
            patch.object(word_chat, "run_word_chat_turn") as run,
        ):
            with pytest.raises(HTTPException) as raised:
                await word_chat.stream_turn(
                    url=URL, message="And now?", caller=caller()
                )

        assert raised.value.status_code == 409
        assert raised.value.detail == word_chat.DOCUMENT_NEEDED
        begin.assert_not_called()
        run.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_file_that_is_not_a_document_is_refused_before_anything_runs(
        self,
    ) -> None:
        with patch.object(word_chat.chat_threads, "current_or_new") as start:
            with pytest.raises(HTTPException) as raised:
                await word_chat.stream_turn(
                    url=URL,
                    message="Hi",
                    document=upload(b"<x/>"),
                    caller=caller(),
                )

        assert raised.value.status_code == 422
        start.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_document_too_large_is_refused(self) -> None:
        with patch.object(word_chat, "MAX_DOCUMENT_BYTES", 3):
            with pytest.raises(HTTPException) as raised:
                await word_chat.stream_turn(
                    url=URL,
                    message="Hi",
                    document=upload(b"<x/>"),
                    caller=caller(),
                )

        assert raised.value.status_code == 413


class TestClearing:
    @pytest.mark.asyncio
    async def test_it_clears_the_callers_conversation(self) -> None:
        with patch.object(
            word_chat.chat_threads, "clear", AsyncMock(return_value=True)
        ) as clear:
            await word_chat.clear_thread(WordChatClearRequest(url=URL), caller=caller())

        clear.assert_awaited_once_with(ANA, URL)


class TestSuggestions:
    @pytest.mark.asyncio
    async def test_someone_elses_or_an_expired_one_is_a_404(self) -> None:
        suggestion_id = uuid.uuid4()
        with patch.object(
            word_chat.chat_suggestions, "suggestion_for", AsyncMock(return_value=None)
        ) as lookup:
            with pytest.raises(HTTPException) as raised:
                await word_chat.get_suggestion(suggestion_id, caller=caller())

        lookup.assert_awaited_once_with(suggestion_id, ANA)
        assert raised.value.status_code == 404


class TestResuming:
    @pytest.mark.asyncio
    async def test_nothing_paused_is_a_409(self) -> None:
        with (
            patch.object(
                word_chat.chat_threads, "current", AsyncMock(return_value=a_thread())
            ),
            patch.object(word_chat, "pending_suggestion", AsyncMock(return_value=None)),
        ):
            with pytest.raises(HTTPException) as raised:
                await word_chat.resume_turn(
                    WordChatResumeRequest(url=URL), caller=caller()
                )

        assert raised.value.status_code == 409

    @pytest.mark.asyncio
    async def test_a_card_still_waiting_is_a_409(self) -> None:
        card = MagicMock(status="pending")
        with (
            patch.object(
                word_chat.chat_threads, "current", AsyncMock(return_value=a_thread())
            ),
            patch.object(
                word_chat, "pending_suggestion", AsyncMock(return_value=uuid.uuid4())
            ),
            patch.object(
                word_chat.chat_suggestions,
                "suggestion_for",
                AsyncMock(return_value=card),
            ),
            patch.object(word_chat, "run_word_chat_resume") as run,
        ):
            with pytest.raises(HTTPException) as raised:
                await word_chat.resume_turn(
                    WordChatResumeRequest(url=URL), caller=caller()
                )

        assert raised.value.status_code == 409
        run.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_settled_card_carries_the_answer_on(self) -> None:
        thread = a_thread()
        card_id = uuid.uuid4()
        with (
            patch.object(
                word_chat.chat_threads, "current", AsyncMock(return_value=thread)
            ),
            patch.object(
                word_chat, "pending_suggestion", AsyncMock(return_value=card_id)
            ),
            patch.object(
                word_chat.chat_suggestions,
                "suggestion_for",
                AsyncMock(return_value=MagicMock(status="applied")),
            ) as lookup,
            patch.object(word_chat.chat_threads, "begin_turn", AsyncMock()) as begin,
            patch.object(word_chat, "run_word_chat_resume") as run,
        ):
            await word_chat.resume_turn(WordChatResumeRequest(url=URL), caller=caller())

        lookup.assert_awaited_once_with(card_id, ANA)
        # Not a new turn: cards that settled meanwhile are still news on the next one.
        begin.assert_not_awaited()
        thread_id, target = run.call_args.args
        assert thread_id == thread.id and target.requester.oid == ANA.oid


class TestOneTurnAtATime:
    @pytest.mark.asyncio
    async def test_a_message_while_another_turn_runs_is_refused(
        self, free_conversation: AsyncMock
    ) -> None:
        free_conversation.return_value = False
        with (
            patch.object(
                word_chat.chat_threads,
                "current_or_new",
                AsyncMock(return_value=a_thread()),
            ),
            patch.object(word_chat, "_has_document", AsyncMock(return_value=True)),
            patch.object(word_chat, "run_word_chat_turn") as run,
        ):
            with pytest.raises(HTTPException) as raised:
                await word_chat.stream_turn(url=URL, message="Hi", caller=caller())

        assert raised.value.status_code == 423
        run.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_conversation_is_let_go_however_the_stream_ends(self) -> None:
        async def failing() -> AsyncIterator[dict]:
            yield {"t": "message", "id": "m"}
            raise RuntimeError("the model went away")

        thread_id = uuid.uuid4()
        with patch.object(word_chat.chat_threads, "release", AsyncMock()) as release:
            with pytest.raises(RuntimeError):
                async for _ in word_chat._released(failing(), thread_id):
                    pass

        release.assert_awaited_once_with(thread_id)
