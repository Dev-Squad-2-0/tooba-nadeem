"""
app/graph/nodes.py
---------------------

LangGraph node functions. Each takes a GraphState and returns a partial
dict of updates (LangGraph merges these into the running state).

Task 5 logging: every node logs "[GRAPH] <node_name>"; tool calls log
"[TOOL] <tool_name> -> <result>". Plain `logging` calls, no new framework.
"""

from __future__ import annotations

import logging

from app.graph.graph_state import GraphState
from app.graph.slot_extractor import extract_and_apply
from app.tools import objection_handler
from app.tools import appointment_intent
from app.graph import tools as biz_tools

logger = logging.getLogger("graph")


def _log_graph(msg: str) -> None:
    logger.info("[GRAPH] %s", msg)


def _log_tool(name: str, result) -> None:
    logger.info("[TOOL] %s -> %s", name, result)


# ---------------------------------------------------------------------------
# Entry: load memory + extract slots
# ---------------------------------------------------------------------------

def load_state_node(state: GraphState) -> dict:
    _log_graph("START")
    _log_graph("load_state")

    conv = state["conversation_state"]
    updates = extract_and_apply(conv, state["message"])
    if updates:
        _log_tool("slot_extractor.extract_and_apply", updates)

    return {}


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

GREETING_KEYWORDS = ["assalam", "salam", "hello", "hi ", "hey", "namaste", "aoa"]
GOODBYE_KEYWORDS = [
    "bye", "khuda hafiz", "allah hafiz", "thank you", "shukriya",
    "thanks", "goodbye", "theek hai bye",
]


def intent_detection_node(state: GraphState) -> dict:
    _log_graph("intent_detection")

    message = state["message"]
    text = message.lower()
    conv = state["conversation_state"]

    objection_type = objection_handler.detect_objection(message)

    # Priority: cancel > reschedule > book, matching
    # appointment_intent.detect_appointment_intent's own ordering.
    appt_intent = appointment_intent.detect_appointment_intent(message)
    if appt_intent == "cancel":
        intent = "cancellation"
    elif appt_intent == "reschedule":
        intent = "reschedule"
    elif appt_intent == "book":
        intent = "booking"
    elif any(kw in text for kw in GOODBYE_KEYWORDS):
        intent = "goodbye"
    elif any(kw in text for kw in GREETING_KEYWORDS) and len(message.split()) <= 4:
        intent = "greeting"
    elif conv.has_any_preference() or any(
        kw in text for kw in ["apartment", "villa", "house", "plot", "property", "properties", "dikhado", "dikha do"]
    ):
        intent = "property_search"
    else:
        intent = "general_question"

    _log_graph(f"intent = {intent}")
    conv.last_intent = intent

    return {
        "intent": intent,
        "objection_type": objection_type,
        "objection_query_hint": objection_handler.get_query_hint(objection_type),
        "objection_instruction": objection_handler.get_instruction(objection_type),
    }


def route_by_intent(state: GraphState) -> str:
    return state["intent"]


# ---------------------------------------------------------------------------
# Property search branch
# ---------------------------------------------------------------------------

def recommendation_node(state: GraphState) -> dict:
    _log_graph("recommendation")
    conv = state["conversation_state"]

    if conv.current_property:
        sql_context = biz_tools.lookup_current_property(conv)
        if sql_context:
            _log_tool("search_property (current_property lookup)", "found")
            return {"sql_context": sql_context}

    sql_context, shown_results = biz_tools.search_property(conv)
    conv.record_recommendations(shown_results)
    _log_tool("search_property", f"{len(shown_results)} result(s)")
    return {"sql_context": sql_context}


# ---------------------------------------------------------------------------
# RAG branch
# ---------------------------------------------------------------------------

def rag_node(state: GraphState) -> dict:
    _log_graph("rag")
    conv = state["conversation_state"]

    query_parts = [state["message"]]
    if conv.current_property:
        query_parts.append(conv.current_property)
    if state.get("objection_query_hint"):
        query_parts.append(state["objection_query_hint"])

    query = " ".join(query_parts)
    rag_context = biz_tools.rag_search(query)
    _log_tool("rag_search", f"{len(rag_context)} chars retrieved")
    return {"rag_context": rag_context}


# ---------------------------------------------------------------------------
# Appointment sub-flow
# ---------------------------------------------------------------------------

def extract_appointment_details_node(state: GraphState) -> dict:
    _log_graph("extract_appointment_details")
    details = appointment_intent.extract_appointment_details(
        state["session_id"], state["message"]
    )
    _log_tool("appointment_intent.extract_appointment_details", details)
    return {"appointment_details": details}


def check_missing_fields_node(state: GraphState) -> dict:
    _log_graph("check_missing_fields")
    conv = state["conversation_state"]
    intent = state["intent"]
    details = state["appointment_details"]

    if intent == "booking":
        property_name = (
            details.get("property")
            or conv.current_property
            or conv.top_recommended_property_name()
        )
        missing = appointment_intent.missing_fields(
            details, appointment_intent.REQUIRED_BOOK_FIELDS
        )
        if not property_name:
            missing.append("property")
    elif intent == "reschedule":
        missing = appointment_intent.missing_fields(
            details, appointment_intent.REQUIRED_RESCHEDULE_FIELDS
        )
    else:  # cancellation
        missing = appointment_intent.missing_fields(
            details, appointment_intent.REQUIRED_CANCEL_FIELDS
        )

    _log_graph(f"missing_fields = {missing}")
    return {"appointment_missing_fields": missing}


def route_after_missing_check(state: GraphState) -> str:
    if state["appointment_missing_fields"]:
        return "ask_clarification"
    if state["intent"] == "cancellation":
        return "cancellation"
    return "availability_check"


def clarification_node(state: GraphState) -> dict:
    _log_graph("ask_clarification")
    intent_label = {"booking": "BOOK", "reschedule": "RESCHEDULE"}.get(
        state["intent"], state["intent"].upper()
    )
    missing = state["appointment_missing_fields"]
    note = (
        f"Buyer wants to {intent_label} but these details are still "
        f"missing: {', '.join(missing)}. Ask the buyer for ONLY the next "
        f"missing item, naturally, one at a time — do not ask for "
        f"everything at once, and do not guess a value."
    )
    return {"appointment_status_note": note}


# ---------------------------------------------------------------------------
# Availability check (Task 4, Rule 1 guardrail)
# ---------------------------------------------------------------------------

def availability_check_node(state: GraphState) -> dict:
    _log_graph("availability_check")
    details = state["appointment_details"]

    result = biz_tools.check_availability(details["date"], details["time"])
    _log_tool("availability_check", "available" if result["available"] else "unavailable")

    return {"availability_result": result["available"]}


def _route_after_availability(state: GraphState) -> str:
    """
    ONE routing decision covering both (1) available/unavailable and
    (2) if available, which action node (booking vs reschedule) matches
    the original intent — both share this node. See build_graph.py for
    why this must be a single registration, not two.
    """
    if not state.get("availability_result"):
        return "unavailable"
    return state["intent"]


# ---------------------------------------------------------------------------
# Booking / Reschedule / Cancellation action nodes
# ---------------------------------------------------------------------------

def _deterministic_failure_response(action_label: str, error: str) -> str:
    """
    Code-authored (never LLM-authored) failure message. Used ONLY when an
    appointment action's outcome is already deterministically known to
    have failed -- see graph_state.py's deterministic_response_override
    field for why this must not be left to the LLM to phrase.
    """
    return (
        f"Maazrat, aapka {action_label} process nahi ho saka. Wajah: {error} "
        f"Barah-e-meherbani dobara try karein ya humari team aapse contact karegi."
    )


def _deterministic_unavailable_response(date: str, time_str: str) -> str:
    return (
        f"Maazrat, {date} ko {time_str} baje ka waqt available nahi hai. "
        f"Kya aap koi doosra din ya waqt bata sakte hain?"
    )


def unavailable_node(state: GraphState) -> dict:
    _log_graph("slot_unavailable")
    conv = state["conversation_state"]
    details = state["appointment_details"]
    note = (
        f"The requested slot ({details.get('date')} at {details.get('time')}) "
        f"is NOT available. Do NOT confirm a booking. Tell the buyer this "
        f"slot is taken and ask them for a different date or time."
    )
    conv.appointment_status = "unavailable"
    return {
        "appointment_status": "unavailable",
        "appointment_status_note": note,
        "deterministic_response_override": _deterministic_unavailable_response(
            details.get("date", "requested date"), details.get("time", "requested time")
        ),
    }


def booking_node(state: GraphState) -> dict:
    _log_graph("booking")
    conv = state["conversation_state"]
    details = state["appointment_details"]
    property_name = (
        details.get("property")
        or conv.current_property
        or conv.top_recommended_property_name()
    )

    result = biz_tools.book_appointment_tool(
        client_name=details["client_name"],
        phone=details["phone"],
        property_name=property_name,
        date=details["date"],
        time_str=details["time"],
        budget=conv.budget,
        preferred_location=conv.city or conv.area,
        property_type=conv.property_type,
        notes=details.get("notes", ""),
        transcript=state["message"],
    )
    _log_tool(
        "calendar.create_event + crm.add_appointment + email.send",
        "success" if result["success"] else result.get("reason"),
    )
    appointment_intent.clear_pending(state["session_id"])

    if result["success"]:
        appt = result["appointment"]
        conv.appointment_status = "booked"
        conv.last_appointment = appt
        note = (
            f"APPOINTMENT CONFIRMED. Property: {property_name}. "
            f"Time: {appt['meeting_time']}. "
            f"Assigned representative: {appt.get('assigned_employee', 'our team')}. "
            f"Confirm this clearly and warmly to the buyer."
        )
        _log_graph("booking_complete")
        return {"appointment_status": "booked", "appointment_status_note": note}

    conv.appointment_status = "failed"
    note = (
        f"APPOINTMENT BOOKING FAILED. Error: {result['error']}. "
        f"Apologize briefly, do not invent a reason, and offer to have "
        f"someone from the office follow up directly."
    )
    return {
        "appointment_status": "failed",
        "appointment_status_note": note,
        "deterministic_response_override": _deterministic_failure_response(
            "booking", result["error"]
        ),
    }


def reschedule_node(state: GraphState) -> dict:
    _log_graph("reschedule")
    details = state["appointment_details"]
    conv = state["conversation_state"]

    result = biz_tools.reschedule_appointment_tool(
        phone=details["phone"],
        new_date=details["date"],
        new_time=details["time"],
        notes=details.get("notes"),
    )
    _log_tool(
        "calendar.update_event + crm.update_appointment_status + email.send",
        "success" if result["success"] else result.get("reason"),
    )
    appointment_intent.clear_pending(state["session_id"])

    if result["success"]:
        conv.appointment_status = "rescheduled"
        conv.last_appointment = result["appointment"]
        note = (
            f"APPOINTMENT RESCHEDULED. New time: "
            f"{result['appointment']['meeting_time']}. Confirm this to the buyer."
        )
        return {"appointment_status": "rescheduled", "appointment_status_note": note}

    conv.appointment_status = "failed"
    note = f"RESCHEDULE FAILED. Error: {result['error']}. Explain honestly and offer to help resolve it."
    return {
        "appointment_status": "failed",
        "appointment_status_note": note,
        "deterministic_response_override": _deterministic_failure_response(
            "reschedule", result["error"]
        ),
    }


def cancellation_node(state: GraphState) -> dict:
    _log_graph("cancellation")
    details = state["appointment_details"]
    conv = state["conversation_state"]

    if not details.get("phone"):
        note = "Buyer wants to CANCEL their appointment but we don't have their phone number yet. Ask for it."
        return {"appointment_status_note": note}

    result = biz_tools.cancel_appointment_tool(phone=details["phone"], notes=details.get("notes"))
    _log_tool(
        "calendar.delete_event + crm.update_appointment_status + email.send",
        "success" if result["success"] else result.get("reason"),
    )
    appointment_intent.clear_pending(state["session_id"])

    if result["success"]:
        conv.appointment_status = "cancelled"
        note = "APPOINTMENT CANCELLED. Confirm this to the buyer and ask if they'd like to reschedule instead."
        return {"appointment_status": "cancelled", "appointment_status_note": note}

    conv.appointment_status = "failed"
    return {
        "appointment_status": "failed",
        "appointment_status_note": f"CANCELLATION FAILED. Error: {result['error']}.",
        "deterministic_response_override": _deterministic_failure_response(
            "cancellation", result["error"]
        ),
    }


# ---------------------------------------------------------------------------
# Greeting / Goodbye — thin, per "do not overengineer" for trivial turns.
# ---------------------------------------------------------------------------

def greeting_node(state: GraphState) -> dict:
    _log_graph("greeting")
    return {}


def goodbye_node(state: GraphState) -> dict:
    _log_graph("goodbye")
    return {
        "appointment_status_note": (
            "The buyer is ending the call. Give a brief, warm sign-off. "
            "Do not ask another question."
        )
    }


# ---------------------------------------------------------------------------
# Final response generation
# ---------------------------------------------------------------------------

def response_generation_node(state: GraphState) -> dict:
    _log_graph("response_generation")

    conv = state["conversation_state"]

    # Correctness guardrail: if an appointment action deterministically
    # failed this turn, the outcome is already known from code -- do not
    # let the LLM re-phrase (and potentially misstate) it. This bypasses
    # the LLM call entirely for this turn. See _deterministic_failure_
    # response / _deterministic_unavailable_response in this file, and
    # graph_state.py's deterministic_response_override field.
    override = state.get("deterministic_response_override")
    if override:
        conv.add_turn("user", state["message"])
        conv.add_turn("assistant", override)
        _log_graph("response_generation: deterministic override used, LLM call skipped")
        _log_graph("END")
        return {"response": override}

    from app.llm.client import generate_chat_response
    from app.llm.prompts import SALES_SYSTEM_PROMPT

    system_content = SALES_SYSTEM_PROMPT.format(
        buyer_preferences=conv.preferences_summary(),
        rag_context=state.get("rag_context") or "No knowledge base search was performed this turn.",
        sql_context=state.get("sql_context") or "No property search was performed this turn.",
    )

    if state.get("objection_instruction"):
        system_content += f"\n\n## This turn's objection-handling guidance\n{state['objection_instruction']}\n"

    if state.get("appointment_status_note"):
        system_content += f"\n\n## Appointment workflow status (factual — do not deviate)\n{state['appointment_status_note']}\n"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(conv.history)
    messages.append({"role": "user", "content": state["message"]})

    response_text = generate_chat_response(messages)

    conv.add_turn("user", state["message"])
    conv.add_turn("assistant", response_text)

    _log_graph("END")

    return {"response": response_text}
