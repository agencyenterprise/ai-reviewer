"""Chat thread persistence API.

Backs the assistant-ui thread list + message history for the /chat page.
All endpoints are scoped to the authenticated user.
"""

import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field

from lib.api.auth import get_current_user
from lib.models.chat_thread import ChatMessage, ChatThread
from lib.models.user import User
from lib.services import chat_thread_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Optional[str]
    is_archived: bool
    created_at: datetime
    last_updated_at: datetime


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    parent_id: Optional[str]
    content: dict[str, Any]


class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class AppendMessageRequest(BaseModel):
    message_id: str
    parent_id: Optional[str] = None
    content: dict[str, Any] = Field(
        description="The assistant-ui ExportedMessageRepositoryItem JSON"
    )


@router.get("/threads", response_model=List[ChatThreadResponse])
async def list_threads(
    current_user: User = Depends(get_current_user),
) -> List[ChatThread]:
    return list(await chat_thread_service.list_threads(user=current_user))


@router.post("/threads", response_model=ChatThreadResponse)
async def create_thread(
    request: CreateThreadRequest,
    current_user: User = Depends(get_current_user),
) -> ChatThread:
    return await chat_thread_service.create_thread(
        user=current_user, title=request.title
    )


@router.patch("/threads/{thread_id}", response_model=ChatThreadResponse)
async def update_thread(
    thread_id: uuid.UUID,
    request: UpdateThreadRequest,
    current_user: User = Depends(get_current_user),
) -> ChatThread:
    thread: Optional[ChatThread] = None
    if request.title is not None:
        thread = await chat_thread_service.rename_thread(
            thread_id=thread_id, user=current_user, title=request.title
        )
    if request.is_archived is not None:
        thread = await chat_thread_service.set_archived(
            thread_id=thread_id, user=current_user, is_archived=request.is_archived
        )
    if thread is None:
        thread = await chat_thread_service.get_thread(
            thread_id=thread_id, user=current_user
        )
    return thread


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> Response:
    await chat_thread_service.delete_thread(thread_id=thread_id, user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/threads/{thread_id}/messages", response_model=List[ChatMessageResponse]
)
async def list_messages(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> List[ChatMessage]:
    return list(
        await chat_thread_service.list_messages(
            thread_id=thread_id, user=current_user
        )
    )


@router.post(
    "/threads/{thread_id}/messages", response_model=ChatMessageResponse
)
async def append_message(
    thread_id: uuid.UUID,
    request: AppendMessageRequest,
    current_user: User = Depends(get_current_user),
) -> ChatMessage:
    return await chat_thread_service.append_message(
        thread_id=thread_id,
        user=current_user,
        message_id=request.message_id,
        parent_id=request.parent_id,
        content=request.content,
    )
