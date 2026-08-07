"""
agent_graph.py
---------------

Per-turn orchestration for the conversational voice/chat agent.

Combines, for a single incoming buyer message:
  1. Slot extraction + memory update  (app/graph/slot_extractor.py, state.py)
  2. Objection detection              (app/tools/objection_handler.py)
  3. Appointment intent + workflow    (app/tools/appointment_intent.py,
                                        app/workflows/appointment_manager.py
                                        — Day 4, NEW)
  4. RAG retrieval                    (app/rag/retriever.py — REUSED, Day 1)
  5. Structured recommendation/lookup (app/recommendation/recommender.py,
                                        database/sql_retriever.py — REUSED, Day 2)
  6. Grounded, persona-driven response generation (app/llm/client.py)

Retriever and PropertyRecommender are cached as module-level singletons —
Retriever() loads the Chroma store and PropertyRecommender() opens a
SQLite-backed retriever on init, and re-doing that on every single voice
turn would blow the <2s latency budget for no benefit.

Day 4 change: appointment booking/rescheduling/cancellation is
DELIBERATELY not a separate short-circuit code path that bypasses the
sales persona. The actual booking action (Calendar/Email/CRM) is
deterministic and performed directly via appointment_manager -- never by
the LLM -- but the confirmation the buyer hears is still phrased by the
LLM through the existing SALES_SYSTEM_PROMPT, grounded in a factual status
note appended the same way objection_instruction already is. This keeps
one single response-generation path instead of two, and keeps the
"never invent information" grounding rule enforced uniformly.
"""

import logging

from app import config
from app.rag.retriever import Retriever
from app.recommendation.recommender import PropertyRecommender
from app.llm.client import generate_chat_response
from app.llm.prompts import SALES_SYSTEM_PROMPT
from app.graph import memory_store
from app.graph.slot_extractor import extract_and_apply
from app.tools import objection_handler
from app.tools import appointment_intent
from app.workflows.appointment_manager import (
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
)

logger = logging.getLogger(__name__)

_retriever: Retriever | None = None
_recommender: PropertyRecommender | None = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _get_recommender() -> PropertyRecommender:
    global _recommender
    if _recommender is None:
        _recommender = PropertyRecommender()
    return _recommender


def _format_pkr(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 10_000_000:
        return f"PKR {n / 10_000_000:.2f} Crore"
    if n >= 100_000:
        return f"PKR {n / 100_000:.1f} Lakh"
    return f"PKR {n:,}"


def _sql_context_for_recommendations(state) -> tuple[str, list[dict]]:
    """
    Uses the Day 2 recommender, driven by whatever slots are currently
    known in state. Returns (formatted_text, property_ids_shown).
    """

    recommender = _get_recommender()

    investment_goal = None
    if state.investment_intent or (state.purpose or "").lower() == "investment":
        investment_goal = "investment"

    results = recommender.recommend(
        budget=state.budget,
        city=state.city,
        area=state.area,
        bedrooms=state.bedrooms,
        purpose=state.purpose,
        amenities=state.amenities or None,
        investment_goal=investment_goal,
    )

    results = results[: config.MAX_RECOMMENDATIONS]

    if not results:
        return "No matching properties found in the database for the current preferences.", []

    lines = []
    for p in results:
        lines.append(
            f"- {p.get('project_name')} | {p.get('city')} | "
            f"{p.get('property_type')} | Status: {p.get('status')} | "
            f"Price: {_format_pkr(p.get('price_range_min_pkr'))} to "
            f"{_format_pkr(p.get('price_range_max_pkr'))}"
        )

    return "\n".join(lines), results


def _sql_context_for_current_property(state) -> str:
    """
    When the buyer is discussing a specific named project, pull its exact
    price/availability/size/agent info directly rather than relying only
    on the recommender's filters.

    NOTE: matches on exact project_name (case-insensitive) since that's
    what sql_retriever.py's queries support. If the buyer's phrasing
    doesn't exactly match a project_name (e.g. "Skyline" vs "Skyline
    Residency"), this will find nothing and the RAG context / recommender
    results still cover the gap. Fuzzy project-name matching would be a
    good follow-up improvement but is out of scope here.
    """

    recommender = _get_recommender()
    sql = recommender.sql

    name = state.current_property

    price_rows = sql.get_property_price(name)
    availability_rows = sql.get_property_availability(name)
    size_rows = sql.get_plot_size(name)

    if not price_rows:
        return ""

    price = price_rows[0]
    lines = [
        f"{price['project_name']} — {price['city']}",
        f"Price: {_format_pkr(price['price_range_min_pkr'])} to "
        f"{_format_pkr(price['price_range_max_pkr'])}",
    ]

    if availability_rows:
        a = availability_rows[0]
        lines.append(f"Status: {a['status']} | Total units: {a['total_units']}")

    if size_rows:
        s = size_rows[0]
        lines.append(f"Size range: {s['size_range_sqft']} sq. ft.")

    id_rows = sql._query(
        "SELECT property_id FROM properties WHERE LOWER(project_name)=LOWER(?)",
        (name,),
    )
    if id_rows:
        agent_rows = sql.get_property_agent(id_rows[0]["property_id"])
        if agent_rows:
            ag = agent_rows[0]
            lines.append(
                f"Assigned agent: {ag['name']} ({ag['phone']}, {ag['email']})"
            )

    return "\n".join(lines)


def _top_recommended_property_name(state) -> str | None:
    """
    Defensive helper: state.recommended_properties currently stores full
    property dicts (per record_recommendations(shown_results) below), but
    handles a plain string/id defensively too in case that shape changes
    again.
    """
    props = getattr(state, "recommended_properties", None)
    if not props:
        return None
    first = props[0]
    if isinstance(first, dict):
        return first.get("project_name")
    return first


def _handle_appointment_workflow(session_id: str, message: str, state) -> str | None:
    """
    Day 4: detects and handles booking/reschedule/cancel intent.

    Returns a factual status note to append to the system prompt (so the
    LLM phrases the confirmation/question in Ahmed's voice), or None if
    no appointment intent was detected this turn. Never returns text
    directly to the buyer itself -- the actual response is always
    generated by generate_chat_response() below, keeping one single
    response path.
    """

    intent_type = appointment_intent.detect_appointment_intent(message)
    if intent_type is None:
        return None

    details = appointment_intent.extract_appointment_details(session_id, message)

    if intent_type == "book":
        property_name = (
            details.get("property")
            or state.current_property
            or _top_recommended_property_name(state)
        )
        missing = appointment_intent.missing_fields(
            details, appointment_intent.REQUIRED_BOOK_FIELDS
        )
        if not property_name:
            missing.append("property")

        if missing:
            return (
                f"Buyer wants to BOOK a property-viewing appointment but these "
                f"details are still missing: {', '.join(missing)}. Ask the buyer "
                f"for ONLY the next missing item, naturally, one at a time -- "
                f"do not ask for everything at once."
            )

        result = book_appointment(
            client_name=details["client_name"],
            phone=details["phone"],
            property_name=property_name,
            date=details["date"],
            time_str=details["time"],
            budget=state.budget,
            preferred_location=state.city or state.area,
            property_type=state.property_type,
            notes=details.get("notes", ""),
            transcript=message,
        )
        appointment_intent.clear_pending(session_id)

        if result["success"]:
            appt = result["appointment"]
            return (
                f"APPOINTMENT CONFIRMED. Property: {property_name}. "
                f"Time: {appt['meeting_time']}. "
                f"Assigned representative: {appt.get('assigned_employee', 'our team')}. "
                f"Confirm this clearly and warmly to the buyer."
            )
        return (
            f"APPOINTMENT BOOKING FAILED. Error: {result['error']}. "
            f"Apologize briefly, do not invent a reason, and offer to have "
            f"someone from the office follow up directly."
        )

    if intent_type == "reschedule":
        missing = appointment_intent.missing_fields(
            details, appointment_intent.REQUIRED_RESCHEDULE_FIELDS
        )
        if missing:
            return (
                f"Buyer wants to RESCHEDULE their appointment but these details "
                f"are still missing: {', '.join(missing)}. Ask for the next "
                f"missing item naturally."
            )

        result = reschedule_appointment(
            phone=details["phone"],
            new_date=details["date"],
            new_time=details["time"],
            notes=details.get("notes"),
        )
        appointment_intent.clear_pending(session_id)

        if result["success"]:
            return (
                f"APPOINTMENT RESCHEDULED. New time: "
                f"{result['appointment']['meeting_time']}. Confirm this to the buyer."
            )
        return (
            f"RESCHEDULE FAILED. Error: {result['error']}. Explain honestly "
            f"and offer to help resolve it."
        )

    if intent_type == "cancel":
        if not details.get("phone"):
            return (
                "Buyer wants to CANCEL their appointment but we don't have "
                "their phone number yet to look up the booking. Ask for it."
            )

        result = cancel_appointment(phone=details["phone"], notes=details.get("notes"))
        appointment_intent.clear_pending(session_id)

        if result["success"]:
            return (
                "APPOINTMENT CANCELLED. Confirm this to the buyer and ask "
                "if they'd like to reschedule instead of cancelling outright."
            )
        return f"CANCELLATION FAILED. Error: {result['error']}."

    return None


def handle_turn(session_id: str, message: str) -> str:
    """
    Main entry point: process one buyer message and return the agent's
    spoken/text response. Called by both the text /chat endpoint and the
    voice pipeline (after Deepgram produces a final transcript).
    """

    state = memory_store.get_or_create(session_id)

    # 1. Update long-term slot memory from this message only.
    extract_and_apply(state, message)

    # 2. Detect objection type (if any) to steer retrieval + instructions.
    objection_type = objection_handler.detect_objection(message)
    query_hint = objection_handler.get_query_hint(objection_type)
    objection_instruction = objection_handler.get_instruction(objection_type)

    # 3. Day 4: appointment booking/reschedule/cancel workflow.
    appointment_status_note = _handle_appointment_workflow(session_id, message, state)

    # 4. RAG retrieval (Day 1, reused as-is) — query enriched with buyer
    #    context and objection hints so retrieval surfaces the right facts.
    rag_query_parts = [message]
    if state.current_property:
        rag_query_parts.append(state.current_property)
    if query_hint:
        rag_query_parts.append(query_hint)
    rag_query = " ".join(rag_query_parts)

    rag_docs = _get_retriever().retrieve(rag_query)
    rag_context = "\n\n".join(doc.page_content for doc in rag_docs) or (
        "No relevant passages found in the knowledge base."
    )

    # 5. Structured data (Day 2, reused as-is).
    if state.current_property:
        sql_context = _sql_context_for_current_property(state)
        if not sql_context:
            sql_context, shown_results = _sql_context_for_recommendations(state)
            state.record_recommendations(shown_results)
    else:
        if state.has_any_preference():
            sql_context, shown_results = _sql_context_for_recommendations(state)
            state.record_recommendations(shown_results)
        else:
            sql_context = "No buyer preferences captured yet."

    # 6. Build the persona prompt, with objection + appointment status
    #    appended (kept as separate trailing blocks so SALES_SYSTEM_PROMPT
    #    stays reusable/unmodified per-turn — same pattern as before).
    system_content = SALES_SYSTEM_PROMPT.format(
        buyer_preferences=state.preferences_summary(),
        rag_context=rag_context,
        sql_context=sql_context,
    )
    if objection_instruction:
        system_content += f"\n\n## This turn's objection-handling guidance\n{objection_instruction}\n"
    if appointment_status_note:
        system_content += f"\n\n## Appointment workflow status (factual — do not deviate)\n{appointment_status_note}\n"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(state.history)  # bounded short-term history
    messages.append({"role": "user", "content": message})

    response_text = generate_chat_response(messages)

    # 7. Persist this exchange to short-term history, then save state.
    state.add_turn("user", message)
    state.add_turn("assistant", response_text)
    memory_store.save(state)

    return response_text