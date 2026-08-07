"""
routes.py
----------

REST endpoints.

/chat is a text-only entry point into the same agent_graph.handle_turn()
used by the voice pipeline — useful for testing memory, objection handling,
and grounding without needing a working audio/Deepgram setup.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.agent_graph import handle_turn
from app.graph import memory_store

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    response_text = handle_turn(request.session_id, request.message)
    return ChatResponse(session_id=request.session_id, response=response_text)


@router.post("/chat/reset/{session_id}")
def reset_session(session_id: str):
    memory_store.reset(session_id)
    return {"status": "reset", "session_id": session_id}