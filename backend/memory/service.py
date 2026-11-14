"""Permanent conversation storage in MySQL. Sync SQLAlchemy wrapped in threads for async callers."""
import asyncio
import json
import uuid
from typing import Optional

from sqlalchemy import select

from database import SessionLocal
from memory.models import Conversation, Message


def _ensure_conversation(user_id: int, session_id: Optional[str], first_message: str) -> str:
    with SessionLocal() as db:
        if session_id:
            conv = db.get(Conversation, session_id)
            if conv is not None:
                if conv.user_id != user_id:
                    raise PermissionError("Conversation belongs to another user")
                return conv.id
        conv = Conversation(
            id=session_id or str(uuid.uuid4()), user_id=user_id, title=first_message[:60] or "New chat"
        )
        db.add(conv)
        db.commit()
        return conv.id


def _save_message(session_id: str, role: str, content: str, tools: Optional[list]) -> None:
    with SessionLocal() as db:
        db.add(
            Message(
                conversation_id=session_id,
                role=role,
                content=content,
                tools_json=json.dumps(tools) if tools else None,
            )
        )
        conv = db.get(Conversation, session_id)
        if conv is not None:
            conv.title = conv.title  # touch so onupdate refreshes updated_at
        db.commit()


def _get_history(session_id: str, limit: int) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(Message).where(Message.conversation_id == session_id).order_by(Message.id.desc()).limit(limit)
        ).all()
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _list_conversations(user_id: int) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
        ).all()
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in rows]


def _get_messages(user_id: int, session_id: str) -> Optional[list[dict]]:
    with SessionLocal() as db:
        conv = db.get(Conversation, session_id)
        if conv is None or conv.user_id != user_id:
            return None
        return [
            {
                "role": m.role,
                "content": m.content,
                "tools": json.loads(m.tools_json) if m.tools_json else [],
            }
            for m in conv.messages
        ]


def _delete_conversation(user_id: int, session_id: str) -> bool:
    with SessionLocal() as db:
        conv = db.get(Conversation, session_id)
        if conv is None or conv.user_id != user_id:
            return False
        db.delete(conv)
        db.commit()
        return True


async def ensure_conversation(user_id: int, session_id: Optional[str], first_message: str) -> str:
    return await asyncio.to_thread(_ensure_conversation, user_id, session_id, first_message)


async def save_message(session_id: str, role: str, content: str, tools: Optional[list] = None) -> None:
    await asyncio.to_thread(_save_message, session_id, role, content, tools)


async def get_history(session_id: str, limit: int = 10) -> list[dict]:
    return await asyncio.to_thread(_get_history, session_id, limit)


async def list_conversations(user_id: int) -> list[dict]:
    return await asyncio.to_thread(_list_conversations, user_id)


async def get_messages(user_id: int, session_id: str) -> Optional[list[dict]]:
    return await asyncio.to_thread(_get_messages, user_id, session_id)


async def delete_conversation(user_id: int, session_id: str) -> bool:
    return await asyncio.to_thread(_delete_conversation, user_id, session_id)
