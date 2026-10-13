"""Tests for the add-in's side of Teams handoffs.

The routes are thin, so what is pinned is the contract around them: every call is
scoped to the signed-in Microsoft account, a handoff that is not theirs (or no longer
open) is a 404, and results that do not describe the handoff's own items are refused
rather than posted.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from lib.api.addin_auth import AddinIdentity
from lib.api.routers.microsoft import word
from lib.api.routers.microsoft.word import HandoffReport
from lib.services.microsoft.word.handoffs import Account, InvalidResults, ItemResult

ANA = Account(oid="oid-ana", tid="tid-contoso")
RESULTS = [
    ItemResult(index=0, applied=True),
    ItemResult(index=1, applied=False, reason="not_found"),
]


def caller() -> AddinIdentity:
    return AddinIdentity(oid=ANA.oid, tid=ANA.tid, email="ana@contoso.com")


class TestListing:
    @pytest.mark.asyncio
    async def test_it_looks_up_by_the_signed_in_account(self) -> None:
        with patch.object(word.handoffs, "pending_for", AsyncMock(return_value=[])) as pending:
            result = await word.list_pending(url="https://x/doc.docx", caller=caller())

        pending.assert_awaited_once_with(ANA)
        assert result.here == [] and result.elsewhere == []


class TestStarting:
    @pytest.mark.asyncio
    async def test_a_pending_handoff_is_claimed_for_the_caller(self) -> None:
        handoff_id = uuid.uuid4()
        with patch.object(word.handoffs, "start", AsyncMock(return_value=True)) as start:
            await word.start(handoff_id, caller=caller())

        start.assert_awaited_once_with(handoff_id, ANA)

    @pytest.mark.asyncio
    async def test_one_already_started_or_not_theirs_is_a_404(self) -> None:
        with patch.object(word.handoffs, "start", AsyncMock(return_value=False)):
            with pytest.raises(HTTPException) as raised:
                await word.start(uuid.uuid4(), caller=caller())

        assert raised.value.status_code == 404


class TestReporting:
    @pytest.mark.asyncio
    async def test_results_are_reported_for_the_caller(self) -> None:
        handoff_id = uuid.uuid4()
        with patch.object(word.handoffs, "report_applied", AsyncMock(return_value=True)) as report:
            await word.report_applied(handoff_id, HandoffReport(results=RESULTS), caller=caller())

        report.assert_awaited_once_with(handoff_id, ANA, RESULTS)

    @pytest.mark.asyncio
    async def test_not_theirs_is_a_404(self) -> None:
        with patch.object(word.handoffs, "report_applied", AsyncMock(return_value=False)):
            with pytest.raises(HTTPException) as raised:
                await word.report_applied(uuid.uuid4(), HandoffReport(results=RESULTS), caller=caller())

        assert raised.value.status_code == 404

    @pytest.mark.asyncio
    async def test_results_for_items_it_does_not_have_are_refused(self) -> None:
        with patch.object(
            word.handoffs, "report_applied", AsyncMock(side_effect=InvalidResults("no item 9"))
        ):
            with pytest.raises(HTTPException) as raised:
                await word.report_applied(uuid.uuid4(), HandoffReport(results=RESULTS), caller=caller())

        assert raised.value.status_code == 422

    def test_a_report_is_capped(self) -> None:
        with pytest.raises(ValueError):
            HandoffReport(results=[ItemResult(index=i, applied=True) for i in range(501)])


class TestDismissing:
    @pytest.mark.asyncio
    async def test_dismissing_someone_elses_is_a_404(self) -> None:
        with patch.object(word.handoffs, "finish", AsyncMock(return_value=None)):
            with pytest.raises(HTTPException) as raised:
                await word.dismiss(uuid.uuid4(), caller=caller())

        assert raised.value.status_code == 404

    @pytest.mark.asyncio
    async def test_dismissing_closes_it_for_the_caller(self) -> None:
        handoff_id = uuid.uuid4()
        with patch.object(word.handoffs, "finish", AsyncMock(return_value=object())) as finish:
            await word.dismiss(handoff_id, caller=caller())

        finish.assert_awaited_once_with(handoff_id, ANA, "dismissed")
