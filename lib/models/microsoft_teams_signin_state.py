"""Cross-worker state for a Teams sign-in that is still in progress.

A sign-in spans two requests: the message that posts the Sign in card, and the
``signin/*`` invoke that completes it. Between them the Agents SDK keeps the flow's
state and the question it parked, so it can replay the question once a token arrives.

That state cannot live in process memory. Production runs Uvicorn with
``--workers 4`` (``Dockerfile`` and ``railway.toml``), so the two requests usually
land on different workers and the second one would find nothing -- first-time
sign-in failing perhaps three times in four, and only once deployed. Same shape of
bug as the one ``mcp_oauth_kv`` exists for, and a separate table because this is a
different subsystem with a different lifetime.

Rows are short lived when a sign-in finishes -- the SDK deletes its own entries as the
flow completes or fails. A sign-in nobody finishes deletes nothing, so
``lib/services/microsoft/teams/storage.py`` sweeps rows left untouched for an hour on
every write. That matters because one of the two things stored is the parked message,
text and sender included, and this table is not the place for it to accumulate.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class MicrosoftTeamsSignInState(SQLModel, table=True):
    __tablename__ = "microsoft_teams_signin_state"

    key: str = Field(
        sa_column=Column(String, primary_key=True),
        description=(
            "The SDK's own storage key. It embeds the channel, conversation and user, "
            "so it is already scoped to one person's flow in one conversation."
        ),
    )
    value: dict = Field(
        sa_column=Column(JSONB, nullable=False),
        description=(
            "The SDK's serialised StoreItem: flow state, and the activity parked to be "
            "replayed after sign-in. No token -- those live in the Bot Framework token "
            "service, never here."
        ),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description=(
            "When this row was last written. Indexed because the sweep filters on it: "
            "a write deletes rows left untouched past the abandonment window."
        ),
    )
