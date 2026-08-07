"""
app/workflows/appointment_manager.py
--------------------------------------

Orchestrates the full booking / rescheduling / cancellation workflow:
Calendar + Email + CRM together, per Day 4 Task 3.

This is the ONLY module that calls all three of app/calendar,
app/email, and app/crm together — google_calendar.py, email_service.py,
and crm_service.py each stay independent, reusable, single-purpose
modules (matching the "avoid duplicated code" / "reusable modules"
requirement), and this file is the integration point.

Assigned-employee lookup reuses the EXISTING PropertyRecommender's
SQLRetriever (app/recommendation/recommender.py -> database/sql_retriever.py)
rather than introducing a second way to look up agents — same pattern
already used in app/graph/agent_graph.py's _sql_context_for_current_property().

Every public method returns a plain result dict with a "success" key
rather than letting exceptions propagate to the voice pipeline — a
failed calendar/email/CRM call should degrade to a clear spoken message
("I couldn't confirm that booking, let me have someone call you"), not
crash a live voice turn.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.calendar.google_calendar import (
    GoogleCalendarError,
    create_event,
    delete_event,
    update_event,
)
from app.email.email_service import (
    EmailServiceError,
    send_appointment_notification,
    send_cancellation_notification,
    send_reschedule_notification,
)
from app.crm.crm_service import CRMService
from app.recommendation.recommender import PropertyRecommender

logger = logging.getLogger(__name__)

_crm: CRMService | None = None
_recommender: PropertyRecommender | None = None


def _get_crm() -> CRMService:
    global _crm
    if _crm is None:
        _crm = CRMService()
    return _crm


def _get_recommender() -> PropertyRecommender:
    global _recommender
    if _recommender is None:
        _recommender = PropertyRecommender()
    return _recommender


def _lookup_assigned_agent(property_name: str) -> dict | None:
    """
    Reuses the existing agents table via the shared SQLRetriever instance
    (same _query pattern as recommender.py / agent_graph.py), rather than
    adding a new lookup path.
    """
    sql = _get_recommender().sql
    id_rows = sql._query(
        "SELECT property_id FROM properties WHERE LOWER(project_name) = LOWER(?)",
        (property_name,),
    )
    if not id_rows:
        return None
    agent_rows = sql.get_property_agent(id_rows[0]["property_id"])
    return agent_rows[0] if agent_rows else None


def _format_meeting_time(date: str, time_str: str) -> str:
    dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
    return dt.strftime("%A, %d %B %Y at %I:%M %p")


class AppointmentError(Exception):
    """Raised only for programmer-error-style misuse (e.g. missing client)."""


def book_appointment(
    client_name: str,
    phone: str,
    property_name: str,
    date: str,
    time_str: str,
    budget: int | None = None,
    preferred_location: str | None = None,
    property_type: str | None = None,
    requirements: str = "",
    notes: str = "",
    transcript: str | None = None,
) -> dict:
    """
    Books a property-viewing appointment end to end:
      1. Create/update the CRM client record.
      2. Log the transcript (if provided).
      3. Look up the assigned agent for this property.
      4. Create the Google Calendar event.
      5. Email the assigned employee.
      6. Record the appointment in CRM.

    Returns: {"success": bool, "appointment": dict | None, "error": str | None}
    """

    crm = _get_crm()

    client = crm.upsert_client(
        client_name=client_name,
        phone=phone,
        budget=budget,
        preferred_location=preferred_location,
        property_type=property_type,
        notes=notes,
    )

    if transcript:
        crm.log_transcript(client["client_id"], transcript)

    agent = _lookup_assigned_agent(property_name)
    assigned_employee = agent["name"] if agent else "Unassigned"
    employee_email = agent["email"] if agent else None

    meeting_time_display = _format_meeting_time(date, time_str)

    calendar_event_id = None
    try:
        event = create_event(
            client_name=client_name,
            phone=phone,
            assigned_employee=assigned_employee,
            property_name=property_name,
            date=date,
            time_str=time_str,
            notes=notes,
        )
        calendar_event_id = event.get("id")
    except GoogleCalendarError as exc:
        logger.error("Booking: calendar event creation failed: %s", exc)
        return {"success": False, "appointment": None, "error": f"Calendar error: {exc}"}

    if employee_email:
        try:
            send_appointment_notification(
                employee_email=employee_email,
                employee_name=assigned_employee,
                client_name=client_name,
                client_phone=phone,
                property_name=property_name,
                meeting_time=meeting_time_display,
                requirements=requirements,
                notes=notes,
            )
        except EmailServiceError as exc:
            # A booking with a working calendar event but a failed email
            # is still a real, useful booking — log and continue rather
            # than rolling back a successful calendar event over a
            # notification failure.
            logger.warning("Booking: email notification failed (event still created): %s", exc)
    else:
        logger.warning("Booking: no assigned employee email found for %s", property_name)

    appointment = crm.add_appointment(
        client_id=client["client_id"],
        property_name=property_name,
        meeting_time=meeting_time_display,
        assigned_employee=assigned_employee,
        calendar_event_id=calendar_event_id,
        notes=notes,
    )

    logger.info("Booked appointment %s for %s", appointment["appointment_id"], client_name)
    return {"success": True, "appointment": appointment, "error": None}


def reschedule_appointment(
    phone: str,
    new_date: str,
    new_time: str,
    notes: str | None = None,
) -> dict:
    """
    Reschedules the client's most recent active appointment.

    Returns: {"success": bool, "appointment": dict | None, "error": str | None}
    """

    crm = _get_crm()
    client = crm.get_client_by_phone(phone)
    if not client:
        return {"success": False, "appointment": None, "error": "No client found for this phone number."}

    appointment = crm.get_active_appointment_for_client(client["client_id"])
    if not appointment:
        return {"success": False, "appointment": None, "error": "No active appointment found to reschedule."}

    new_meeting_time_display = _format_meeting_time(new_date, new_time)

    if appointment.get("calendar_event_id"):
        try:
            update_event(
                event_id=appointment["calendar_event_id"],
                date=new_date,
                time_str=new_time,
                notes=notes,
            )
        except GoogleCalendarError as exc:
            logger.error("Reschedule: calendar update failed: %s", exc)
            return {"success": False, "appointment": None, "error": f"Calendar error: {exc}"}

    agent_email = None
    if appointment.get("assigned_employee"):
        agent = _lookup_assigned_agent(appointment["property_name"])
        agent_email = agent["email"] if agent else None

    if agent_email:
        try:
            send_reschedule_notification(
                employee_email=agent_email,
                employee_name=appointment["assigned_employee"],
                client_name=client["client_name"],
                client_phone=phone,
                property_name=appointment["property_name"],
                new_meeting_time=new_meeting_time_display,
                notes=notes or "",
            )
        except EmailServiceError as exc:
            logger.warning("Reschedule: email notification failed (event still updated): %s", exc)

    updated_appointment = crm.update_appointment_status(
        appointment_id=appointment["appointment_id"],
        status="rescheduled",
        meeting_time=new_meeting_time_display,
        notes=notes,
    )

    logger.info("Rescheduled appointment %s", appointment["appointment_id"])
    return {"success": True, "appointment": updated_appointment, "error": None}


def cancel_appointment(phone: str, notes: str | None = None) -> dict:
    """
    Cancels the client's most recent active appointment.

    Returns: {"success": bool, "appointment": dict | None, "error": str | None}
    """

    crm = _get_crm()
    client = crm.get_client_by_phone(phone)
    if not client:
        return {"success": False, "appointment": None, "error": "No client found for this phone number."}

    appointment = crm.get_active_appointment_for_client(client["client_id"])
    if not appointment:
        return {"success": False, "appointment": None, "error": "No active appointment found to cancel."}

    if appointment.get("calendar_event_id"):
        try:
            delete_event(appointment["calendar_event_id"])
        except GoogleCalendarError as exc:
            logger.error("Cancellation: calendar delete failed: %s", exc)
            return {"success": False, "appointment": None, "error": f"Calendar error: {exc}"}

    agent_email = None
    if appointment.get("assigned_employee"):
        agent = _lookup_assigned_agent(appointment["property_name"])
        agent_email = agent["email"] if agent else None

    if agent_email:
        try:
            send_cancellation_notification(
                employee_email=agent_email,
                employee_name=appointment["assigned_employee"],
                client_name=client["client_name"],
                client_phone=phone,
                property_name=appointment["property_name"],
                original_meeting_time=appointment["meeting_time"],
                notes=notes or "",
            )
        except EmailServiceError as exc:
            logger.warning("Cancellation: email notification failed (event still deleted): %s", exc)

    updated_appointment = crm.update_appointment_status(
        appointment_id=appointment["appointment_id"],
        status="cancelled",
        notes=notes,
    )

    logger.info("Cancelled appointment %s", appointment["appointment_id"])
    return {"success": True, "appointment": updated_appointment, "error": None}