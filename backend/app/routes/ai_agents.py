from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.ai.graph import compiled_graph


router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str


async def _stream_response(message: str) -> AsyncIterator[str]:
    """
    Stream the final answer tokens from the LangGraph workflow.
    """
    # We stream on the 'values' channel and yield the growing assistant message.
    async for state in compiled_graph.astream(
        {"messages": [HumanMessage(content=message)], "cypher_query": None, "query_result": None},
        stream_mode="values",
    ):
        messages = state["messages"]
        last = messages[-1]
        if hasattr(last, "content"):
            # yield as simple text chunks; client can accumulate them
            yield str(last.content)


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Streaming AI chat endpoint that routes the request through a LangGraph
    multi-agent workflow which queries Neo4j when helpful.
    """

    async def event_stream() -> AsyncIterator[bytes]:
        async for chunk in _stream_response(request.message):
            yield chunk.encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/plain")

