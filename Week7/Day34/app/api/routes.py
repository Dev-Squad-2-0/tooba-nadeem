"""
routes.py
----------

REST endpoints.

/chat is a text-only entry point into the same agent_graph.handle_turn()
used by the voice pipeline — useful for testing memory, objection handling,
and grounding without needing a working audio/Deepgram setup.

/properties/match is a thin wrapper for the n8n appointment-booking
workflow (see real_estate_workflow.json's "Property Match" node). It
reuses the SAME slot extraction and PropertyRecommender that /chat and
the voice pipeline already use (via agent_graph.py) — it does not
reimplement matching logic, it just exposes it as its own route so the
booking sub-flow can call it independently of a full conversational turn.

/appointments/book is a thin wrapper over the existing
app/workflows/appointment_manager.py:book_appointment(), which already
performs the availability guardrail + Calendar + Email + CRM steps
end-to-end. This route does not reimplement any of that — it only maps
the n8n Appointment node's request body onto book_appointment()'s
existing parameters and passes its return dict straight through.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.agent_graph import handle_turn, _get_recommender
from app.graph.slot_extractor import extract_and_apply
from app.graph import memory_store
from app.workflows.appointment_manager import book_appointment
from app.tools import appointment_intent

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


class PropertyMatchRequest(BaseModel):
    session_id: str
    message: str


class PropertyMatchResponse(BaseModel):
    session_id: str
    matched: bool
    matched_property_name: str | None = None
    budget: int | None = None
    preferred_location: str | None = None
    property_type: str | None = None
    requirements: str | None = None
    requested_date: str | None = None   # NEW
    requested_time: str | None = None   # NEW

class AppointmentBookRequest(BaseModel):
    client_name: str
    phone: str
    property_name: str
    # date/time_str are Optional for now — no date/time extraction exists
    # upstream yet (n8n sends null). book_appointment() itself requires
    # both; passing None will fail inside _format_meeting_time(), which
    # this route catches below rather than raising a raw 500.
    date: str | None = None
    time_str: str | None = None
    budget: int | None = None
    preferred_location: str | None = None
    property_type: str | None = None
    requirements: str | None = None
    transcript: str | None = None


class AppointmentBookResponse(BaseModel):
    success: bool
    appointment: dict | None = None
    error: str | None = None
    reason: str | None = None


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
    # Bug fix: appointment_intent.py keeps its own separate per-session
    # pending-details dict for in-progress bookings/reschedules
    # (_pending_details), which memory_store.reset() has no knowledge of
    # and never touched. Without this, a stale phone/date/time from an
    # earlier abandoned booking/reschedule attempt under this session_id
    # could silently resurface and get merged into a later, unrelated
    # conversation after a reset.
    appointment_intent.clear_pending(session_id)
    return {"status": "reset", "session_id": session_id}


@router.post("/properties/match", response_model=PropertyMatchResponse)
def match_property(request: PropertyMatchRequest):
    # Same slot-extraction step agent_graph.handle_turn() runs every turn,
    # so a caller hitting this endpoint standalone (e.g. n8n) still gets
    # the buyer's stated budget/area/etc. picked up from this message.
    state = memory_store.get_or_create(request.session_id)
    extract_and_apply(state, request.message)
    memory_store.save(state)

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

    top = results[0] if results else None

    return PropertyMatchResponse(
        session_id=state.session_id,
        matched=bool(top),
        matched_property_name=top.get("project_name") if top else None,
        budget=state.budget,
        preferred_location=state.area or state.city,
        property_type=state.property_type,
        requirements=", ".join(state.amenities) if state.amenities else None,
        requested_date=state.requested_date,
        requested_time=state.requested_time,
    )


@router.post("/appointments/book", response_model=AppointmentBookResponse)
def book_appointment_route(request: AppointmentBookRequest):
    try:
        result = book_appointment(
            client_name=request.client_name,
            phone=request.phone,
            property_name=request.property_name,
            date=request.date,
            time_str=request.time_str,
            budget=request.budget,
            preferred_location=request.preferred_location,
            property_type=request.property_type,
            requirements=request.requirements or "",
            transcript=request.transcript,
        )
    except Exception as exc:  # noqa: BLE001 — never let a malformed
        # request (e.g. missing date/time) crash the endpoint; degrade to
        # a clear result dict instead, same philosophy appointment_manager
        # itself already follows for Calendar/Email/CRM failures.
        logger.error("Appointment booking failed unexpectedly: %s", exc)
        return AppointmentBookResponse(
            success=False,
            appointment=None,
            error=f"Booking failed: {exc}",
            reason="invalid_input",
        )

    return AppointmentBookResponse(**result)