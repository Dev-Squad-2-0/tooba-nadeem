"""
agent_graph.py
---------------

Day 5: thin entrypoint into the compiled LangGraph
(app/graph/build_graph.py). Public signature —
handle_turn(session_id, message) -> str — is UNCHANGED, so
app/api/routes.py and app/voice/pipeline.py need ZERO changes.

All orchestration logic that used to live directly in this file now
lives in app/graph/nodes.py, invoked via the graph built in
app/graph/build_graph.py. This file:
  1. Loads/creates the session's ConversationState (unchanged mechanism,
     same memory_store.get_or_create()).
  2. Wraps it in a fresh GraphState for this turn.
  3. Invokes the compiled graph.
  4. Saves the (in-place-mutated) ConversationState back to memory_store.
  5. Returns the response text.

Bug fix carried over from the Day 5 audit: the old
_top_recommended_property_name() helper that lived in this file returned
a property_id where a name was expected, because
ConversationState.recommended_properties stores IDs only
(recommended_property_names holds names separately). That helper is
GONE from this file -- the correct logic
(ConversationState.top_recommended_property_name(), already present and
correct in app/graph/state.py) is now what app/graph/nodes.py actually
calls. Verified via simulated graph execution, not just read -- see
chat for the test run.

Note: app/api/routes.py imports `_get_recommender` directly from this
module (`from app.graph.agent_graph import handle_turn, _get_recommender`).
Preserved below as a thin re-export pointing at app/graph/tools.py's
singleton, so that existing import in routes.py does not break.
"""

import logging
import time

from app.graph import memory_store
from app.graph.graph_state import new_graph_state
from app.graph.build_graph import build_graph
from app.graph import tools as _graph_tools
from app import monitoring

logger = logging.getLogger(__name__)

_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def _get_recommender():
    """
    Preserved because app/api/routes.py imports this name directly.
    Delegates to the single cached instance in app/graph/tools.py so
    there is still only one PropertyRecommender instance app-wide.
    """
    return _graph_tools.get_recommender()


def handle_turn(session_id: str, message: str) -> str:
    """
    Main entry point: process one buyer message and return the agent's
    spoken/text response. Called by both the text /chat endpoint and the
    voice pipeline (after Deepgram produces a final transcript).

    Day 6: wraps the graph invocation with a latency measurement and one
    structured monitoring event (app/monitoring.py) — this is the ONE
    call site for turn-level metrics, deliberately kept here rather than
    scattered into individual nodes, so nodes.py's existing [GRAPH]/[TOOL]
    logging is untouched.
    """

    conv_state = memory_store.get_or_create(session_id)
    graph_state = new_graph_state(session_id, message, conv_state)

    start = time.perf_counter()
    error_type = None

    try:
        result = _get_graph().invoke(graph_state)
    except Exception as exc:  # noqa: BLE001 -- a graph failure must not crash a live voice turn
        logger.error("Graph execution failed for session %s: %s", session_id, exc)
        error_type = type(exc).__name__
        latency_ms = (time.perf_counter() - start) * 1000
        memory_store.save(conv_state)
        monitoring.log_turn_event(
            session_id=session_id, intent=None, latency_ms=latency_ms,
            appointment_status=conv_state.appointment_status, error_type=error_type,
        )
        return (
            "Mazrat chahta hoon, mujhe smajah nahi ayi ap kya keh rahay hain. "
            "Dobara boliye please."
        )

    latency_ms = (time.perf_counter() - start) * 1000
    memory_store.save(conv_state)

    monitoring.log_turn_event(
        session_id=session_id,
        intent=result.get("intent"),
        latency_ms=latency_ms,
        appointment_status=result.get("appointment_status"),
    )

    return result.get("response", "")
