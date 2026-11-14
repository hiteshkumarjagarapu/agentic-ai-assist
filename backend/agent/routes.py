import asyncio
import json
from typing import Any, AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent.graph import agent_graph
from agent.nodes import SYSTEM_PROMPT
from auth.dependencies import get_current_user
from auth.models import User
from config import settings
from memory import redis_memory, service

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: Optional[str] = None


def sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def chunk_text(text: str) -> list[str]:
    """Split an answer into word-sized tokens (whitespace preserved)."""
    out: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if ch.isspace():
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


async def run_agent_stream(user: User, req: ChatRequest) -> AsyncIterator[str]:
    try:
        session_id = await service.ensure_conversation(user.id, req.session_id, req.message)
    except PermissionError:
        yield sse({"type": "error", "content": "Conversation not found"})
        yield sse({"type": "done"})
        return

    yield sse({"type": "session", "session_id": session_id})
    yield sse({"type": "thinking", "content": "Analyzing your question..."})

    # Load last 10 messages: Redis buffer first, MySQL fallback.
    history = await redis_memory.get_buffer(session_id)
    if history is None:
        history = await service.get_history(session_id, 10)

    await service.save_message(session_id, "user", req.message)
    await redis_memory.append_buffer(session_id, "user", req.message)

    state: dict[str, Any] = {
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *history,
                     {"role": "user", "content": req.message}],
        "tool_calls_log": [],
        "current_step": 0,
        "max_steps": settings.MAX_STEPS,
        "final_answer": None,
        "session_id": session_id,
    }

    final_answer = ""
    tools_used: list[dict] = []
    try:
        async for update in agent_graph.astream(state, stream_mode="updates"):
            for node, delta in update.items():
                if node == "think":
                    last = delta["messages"][-1]
                    if last.get("tool_calls"):
                        if last.get("content"):
                            yield sse({"type": "thinking", "content": last["content"]})
                        for tc in last["tool_calls"]:
                            try:
                                args = json.loads(tc["function"]["arguments"] or "{}")
                            except json.JSONDecodeError:
                                args = {}
                            yield sse({"type": "tool_start", "tool": tc["function"]["name"], "args": args})
                    else:
                        final_answer = delta.get("final_answer") or ""
                elif node == "execute":
                    new = delta["tool_calls_log"][len(tools_used):]
                    for entry in new:
                        tools_used.append(entry)
                        yield sse({"type": "tool_result", "tool": entry["tool"], "result": entry["result"]})
                    yield sse({"type": "thinking", "content": "Reviewing the results..."})
    except Exception as e:
        final_answer = f"Sorry, something went wrong while running the agent: {e}"

    if not final_answer:
        final_answer = "I couldn't produce an answer. Please try rephrasing."

    for token in chunk_text(final_answer):
        yield sse({"type": "token", "content": token})
        await asyncio.sleep(0.01)

    await service.save_message(session_id, "assistant", final_answer, tools_used)
    await redis_memory.append_buffer(session_id, "assistant", final_answer)
    await redis_memory.cache_answer(session_id, final_answer)
    yield sse({"type": "done"})


@router.post("/chat")
async def chat(req: ChatRequest, user: User = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(
        run_agent_stream(user, req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations")
async def conversations(user: User = Depends(get_current_user)) -> list[dict]:
    return await service.list_conversations(user.id)


@router.get("/conversations/{session_id}/messages")
async def conversation_messages(session_id: str, user: User = Depends(get_current_user)) -> list[dict]:
    msgs = await service.get_messages(user.id, session_id)
    if msgs is None:
        raise HTTPException(404, "Conversation not found")
    return msgs


@router.delete("/conversations/{session_id}", status_code=204)
async def delete_conversation(session_id: str, user: User = Depends(get_current_user)) -> None:
    if not await service.delete_conversation(user.id, session_id):
        raise HTTPException(404, "Conversation not found")
