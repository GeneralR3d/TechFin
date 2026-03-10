from __future__ import annotations

import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.graph import compiled_graph
from app.auth import get_current_user
from app.database import async_session, get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatSessionDetailResponse,
    ChatSessionResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_response(s: ChatSession) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=str(s.id),
        user_id=str(s.user_id),
        title=s.title,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _message_response(m: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=str(m.id),
        session_id=str(m.session_id),
        role=m.role,
        content=m.content,
        created_at=m.created_at,
    )


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(user_id=user.id, title="New Chat")
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return _session_response(session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return [_session_response(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return ChatSessionDetailResponse(
        id=str(chat_session.id),
        user_id=str(chat_session.user_id),
        title=chat_session.title,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        messages=[_message_response(m) for m in messages],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == user.id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if chat_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(chat_session)


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------


@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Streaming chat endpoint with session persistence.
    Emits [SESSION:uuid]\\n as the first chunk when a new session is auto-created.
    """
    # 1. Resolve or auto-create session
    is_new_session = False
    if request.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == uuid.UUID(request.session_id),
                ChatSession.user_id == user.id,
            )
        )
        chat_session = result.scalar_one_or_none()
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        chat_session = ChatSession(
            user_id=user.id,
            title=request.message[:50],
        )
        db.add(chat_session)
        await db.flush()
        is_new_session = True

    session_id = chat_session.id

    # 2. Load conversation history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    prior_messages = history_result.scalars().all()

    # 3. Save user message; update title on first message of a "New Chat" session
    if chat_session.title == "New Chat" and len(prior_messages) == 0:
        chat_session.title = request.message[:50].strip()
    user_msg = ChatMessage(session_id=session_id, role="user", content=request.message)
    db.add(user_msg)
    await db.commit()

    # 4. Build LangChain message list (history + new user message)
    lc_messages: list = []
    for m in prior_messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        else:
            lc_messages.append(AIMessage(content=m.content))
    lc_messages.append(HumanMessage(content=request.message))

    # 5. Stream LangGraph output and persist assistant reply
    captured_session_id = str(session_id)
    captured_new = is_new_session

    async def event_stream() -> AsyncIterator[bytes]:
        if captured_new:
            yield f"[SESSION:{captured_session_id}]\n".encode()

        last_content = ""
        async for state in compiled_graph.astream(
            {"messages": lc_messages},
            stream_mode="values",
        ):
            msgs = state["messages"]
            last = msgs[-1]
            if hasattr(last, "content") and isinstance(last, AIMessage):
                content = str(last.content)
                yield content.encode()
                last_content = content

        # Persist assistant message after streaming completes
        if last_content:
            async with async_session() as save_db:
                assistant_msg = ChatMessage(
                    session_id=uuid.UUID(captured_session_id),
                    role="assistant",
                    content=last_content,
                )
                save_db.add(assistant_msg)
                await save_db.commit()

    return StreamingResponse(event_stream(), media_type="text/plain")
