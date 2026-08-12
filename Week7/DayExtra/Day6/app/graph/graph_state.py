"""
app/graph/graph_state.py
---------------------------

LangGraph state schema for one turn of the conversational agent.

Two states, not one:
  - ConversationState (app/graph/state.py) — DURABLE, cross-turn memory:
    budget/city/history/appointment_status/etc. Lives in memory_store.py
    between turns. UNCHANGED by Day 5 — this file does not modify
    state.py's schema.
  - GraphState (this file) — EPHEMERAL, per-invocation state LangGraph
    threads through nodes for a SINGLE turn: intent, tool outputs,
    RAG/SQL context gathered this turn, etc. Built at the start of
    handle_turn() and discarded at the end of it.

Note on appointment date/time (see Day 5 audit): this project currently
has appointment date/time captured by app/tools/appointment_intent.py's
own extraction (its `details` dict), which is what the existing,
already-working booking flow in agent_graph.py reads from.
ConversationState ALSO has requested_date/requested_time populated by
slot_extractor.py, but nothing in the live conversational path consumes
those two fields (only app/api/routes.py's /properties/match response
does, for the n8n flow). Day 5 deliberately keeps using
appointment_intent.py as the single source of truth for the graph's
booking sub-flow, to avoid touching the n8n-facing behavior of
slot_extractor.py/state.requested_date/state.requested_time, which are
out of scope for "make Day 5 work" and risk breaking the n8n integration
if changed blind.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from app.graph.state import ConversationState

IntentType = str  # "greeting" | "goodbye" | "booking" | "reschedule" |
                   # "cancellation" | "property_search" | "general_question"


class GraphState(TypedDict, total=False):
    # --------------------------------------------------
    # Turn input
    # --------------------------------------------------
    session_id: str
    message: str

    # Reference to the durable, cross-turn memory object for this
    # session. Loaded once at graph entry, mutated in place by nodes,
    # saved once at the end of handle_turn().
    conversation_state: ConversationState

    # --------------------------------------------------
    # Routing
    # --------------------------------------------------
    intent: IntentType
    objection_type: Optional[str]
    objection_query_hint: str
    objection_instruction: str

    # --------------------------------------------------
    # Appointment sub-flow (booking / reschedule / cancellation)
    # appointment_details mirrors app/tools/appointment_intent.py's
    # accumulated pending-details dict for this turn.
    # --------------------------------------------------
    appointment_details: dict
    appointment_missing_fields: list[str]
    availability_result: Optional[bool]
    appointment_status_note: Optional[str]
    appointment_status: Optional[str]

    # --------------------------------------------------
    # Grounding context gathered this turn
    # --------------------------------------------------
    rag_context: str
    sql_context: str

    # --------------------------------------------------
    # Task 5 — structured record of tool calls this turn, for logging.
    # --------------------------------------------------
    tool_outputs: dict[str, Any]

    # --------------------------------------------------
    # Correctness guardrail: when an appointment action FAILS this turn
    # (reschedule/booking/cancellation not found, unavailable, calendar
    # error), the outcome is already deterministically known from code --
    # it must not be re-decided by the LLM. If set, response_generation_node
    # returns this text directly and skips the LLM call for this turn.
    # This exists because this project's model has already been proven
    # (earlier debugging) to sometimes ignore explicit prompt instructions
    # not to claim success -- a prompt instruction alone is not a reliable
    # enforcement mechanism for a correctness-critical claim.
    # --------------------------------------------------
    deterministic_response_override: Optional[str]

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    response: str
    error: Optional[str]


def new_graph_state(session_id: str, message: str, conversation_state: ConversationState) -> GraphState:
    return GraphState(
        session_id=session_id,
        message=message,
        conversation_state=conversation_state,
        intent="general_question",
        objection_type=None,
        objection_query_hint="",
        objection_instruction="",
        appointment_details={},
        appointment_missing_fields=[],
        availability_result=None,
        appointment_status_note=None,
        appointment_status=None,
        rag_context="",
        sql_context="",
        tool_outputs={},
        deterministic_response_override=None,
        response="",
        error=None,
    )
