"""
memory_store.py
----------------

Session memory storage for conversation state.

WHERE MEMORY IS STORED: an in-process Python dict, keyed by session_id,
guarded by a lock. This is appropriate for a single-process FastAPI dev/demo
deployment (one uvicorn worker). It is intentionally isolated behind this
one file: swapping to Redis or Postgres for a multi-worker production
deployment means rewriting get()/save()/reset() here only — nothing in
agent_graph.py or the voice pipeline needs to change.

HOW IT'S RETRIEVED: app/graph/agent_graph.py calls get_or_create(session_id)
at the start of every turn, mutates the returned ConversationState via
apply_updates(), and the object is saved back in place (dict holds a
reference, so no explicit save() call is required after mutation — save()
exists mainly for explicit clarity / potential future backends where an
explicit write matters).
"""

import threading
import time

from app import config
from app.graph.state import ConversationState

_lock = threading.Lock()
_sessions: dict[str, ConversationState] = {}


def get_or_create(session_id: str) -> ConversationState:
    with _lock:
        _evict_stale()

        if session_id not in _sessions:
            _sessions[session_id] = ConversationState(session_id=session_id)

        return _sessions[session_id]


def save(state: ConversationState) -> None:
    with _lock:
        state.last_updated = time.time()
        _sessions[state.session_id] = state


def reset(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)


def _evict_stale() -> None:
    """Must be called while holding _lock."""
    now = time.time()
    stale = [
        sid
        for sid, state in _sessions.items()
        if now - state.last_updated > config.SESSION_TTL_SECONDS
    ]
    for sid in stale:
        _sessions.pop(sid, None)