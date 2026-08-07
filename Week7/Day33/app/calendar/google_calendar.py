"""
app/calendar/google_calendar.py
--------------------------------

Google Calendar integration for scheduling property-viewing appointments.

Uses the project's existing credentials.json at the project root (does not
generate or request a new one). token.json is created automatically on
first authenticate() call via the OAuth installed-app flow, and silently
refreshed on later calls once it exists.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 1.5


class GoogleCalendarError(Exception):
    """Raised when a Calendar operation fails after retries are exhausted."""


def _with_retries(operation_name: str, func, *args, **kwargs):
    """
    Retries transient Google API errors (rate limits, 5xx) with exponential
    backoff. Non-retryable errors (auth failures, bad requests) raise
    immediately rather than wasting retry attempts on a request that will
    never succeed.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except HttpError as exc:
            status = getattr(exc.resp, "status", None)
            last_exc = exc
            if status not in _RETRYABLE_STATUS_CODES or attempt == _MAX_RETRIES:
                logger.error("%s failed (status=%s): %s", operation_name, status, exc)
                raise GoogleCalendarError(f"{operation_name} failed: {exc}") from exc
            wait = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "%s transient error (status=%s), retrying in %.1fs (attempt %d/%d)",
                operation_name, status, wait, attempt, _MAX_RETRIES,
            )
            time.sleep(wait)
    raise GoogleCalendarError(f"{operation_name} failed: {last_exc}")


def authenticate() -> Any:
    """
    Returns an authenticated Google Calendar API service (Resource) object.

    Reads token.json if present and valid; refreshes it silently if
    expired; otherwise runs the interactive OAuth installed-app flow ONCE
    (opens a local browser window) and writes token.json so subsequent
    calls don't need to reauthenticate.
    """

    creds: Credentials | None = None
    token_path = config.GOOGLE_TOKEN_PATH
    credentials_path = config.GOOGLE_CREDENTIALS_PATH

    if not credentials_path.exists():
        raise GoogleCalendarError(
            f"credentials.json not found at {credentials_path}. "
            "This file must already exist at the project root."
        )

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google Calendar token.")
            creds.refresh(Request())
        else:
            logger.info("No valid token.json found — starting interactive OAuth flow.")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")
        logger.info("Saved token.json to %s", token_path)

    return build("calendar", "v3", credentials=creds)


def _build_event_body(
    client_name: str,
    phone: str,
    assigned_employee: str,
    property_name: str,
    date: str,
    time_str: str,
    notes: str = "",
    duration_minutes: int | None = None,
) -> dict:
    """
    Builds the Calendar API event body.

    date: 'YYYY-MM-DD'
    time_str: 'HH:MM' (24-hour)
    """

    duration = duration_minutes or config.DEFAULT_APPOINTMENT_DURATION
    start_dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=duration)

    description_lines = [
        f"Client Name: {client_name}",
        f"Phone: {phone}",
        f"Assigned Employee: {assigned_employee}",
        f"Property: {property_name}",
        f"Meeting Notes: {notes or 'N/A'}",
    ]

    return {
        "summary": f"Property Viewing: {property_name} — {client_name}",
        "description": "\n".join(description_lines),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": config.CALENDAR_TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": config.CALENDAR_TIMEZONE},
        # Stored as structured, queryable metadata so find_events_by_client()
        # can locate a booking without the caller needing to track the raw
        # Calendar event_id across the CRM/appointment_manager boundary.
        "extendedProperties": {
            "private": {
                "client_name": client_name,
                "phone": phone,
                "assigned_employee": assigned_employee,
                "property": property_name,
            }
        },
    }


def create_event(
    client_name: str,
    phone: str,
    assigned_employee: str,
    property_name: str,
    date: str,
    time_str: str,
    notes: str = "",
    duration_minutes: int | None = None,
) -> dict:
    """
    Creates a property-viewing appointment on Google Calendar.

    Returns the created event dict (includes 'id', needed for later
    update_event/delete_event calls).
    """

    service = authenticate()
    body = _build_event_body(
        client_name, phone, assigned_employee, property_name,
        date, time_str, notes, duration_minutes,
    )

    event = _with_retries(
        "create_event",
        service.events().insert(calendarId=config.GOOGLE_CALENDAR_ID, body=body).execute,
    )
    logger.info("Created calendar event %s for %s", event.get("id"), client_name)
    return event


def update_event(
    event_id: str,
    date: str | None = None,
    time_str: str | None = None,
    notes: str | None = None,
    duration_minutes: int | None = None,
    **extra_fields: Any,
) -> dict:
    """
    Updates an existing event (used for rescheduling). Only the provided
    fields are changed; everything else on the event is preserved as-is.
    """

    service = authenticate()

    existing = _with_retries(
        "get_event_for_update",
        service.events().get(calendarId=config.GOOGLE_CALENDAR_ID, eventId=event_id).execute,
    )

    if date or time_str:
        current_start = datetime.fromisoformat(existing["start"]["dateTime"])
        current_end = datetime.fromisoformat(existing["end"]["dateTime"])
        duration = (
            timedelta(minutes=duration_minutes)
            if duration_minutes is not None
            else (current_end - current_start)
        )

        new_date = date or current_start.strftime("%Y-%m-%d")
        new_time = time_str or current_start.strftime("%H:%M")
        new_start = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        new_end = new_start + duration

        existing["start"]["dateTime"] = new_start.isoformat()
        existing["end"]["dateTime"] = new_end.isoformat()

    if notes is not None:
        description_lines = [
            line for line in existing.get("description", "").split("\n")
            if not line.startswith("Meeting Notes:")
        ]
        description_lines.append(f"Meeting Notes: {notes}")
        existing["description"] = "\n".join(description_lines)

    existing.update(extra_fields)

    updated = _with_retries(
        "update_event",
        service.events().update(
            calendarId=config.GOOGLE_CALENDAR_ID, eventId=event_id, body=existing
        ).execute,
    )
    logger.info("Updated calendar event %s", event_id)
    return updated


def delete_event(event_id: str) -> None:
    """Deletes an appointment (used for cancellations)."""

    service = authenticate()
    _with_retries(
        "delete_event",
        service.events().delete(calendarId=config.GOOGLE_CALENDAR_ID, eventId=event_id).execute,
    )
    logger.info("Deleted calendar event %s", event_id)


def find_event(event_id: str) -> dict | None:
    """
    Looks up a single event by its Calendar event_id. Returns None if it
    doesn't exist (e.g. already deleted/cancelled) rather than raising,
    since "not found" is an expected, non-error outcome for callers
    checking whether a booking still exists.
    """

    service = authenticate()
    try:
        return service.events().get(
            calendarId=config.GOOGLE_CALENDAR_ID, eventId=event_id
        ).execute()
    except HttpError as exc:
        if getattr(exc.resp, "status", None) == 404:
            return None
        raise GoogleCalendarError(f"find_event failed: {exc}") from exc


def find_events_by_client(
    client_name: str,
    time_min_iso: str | None = None,
    time_max_iso: str | None = None,
) -> list[dict]:
    """
    Searches upcoming events tagged with this client_name in
    extendedProperties (set by create_event). Lets appointment_manager.py
    locate an existing booking to reschedule/cancel without needing to
    separately persist the raw Calendar event_id itself.
    """

    service = authenticate()
    kwargs: dict[str, Any] = {
        "calendarId": config.GOOGLE_CALENDAR_ID,
        "privateExtendedProperty": f"client_name={client_name}",
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min_iso:
        kwargs["timeMin"] = time_min_iso
    if time_max_iso:
        kwargs["timeMax"] = time_max_iso

    result = _with_retries("find_events_by_client", service.events().list(**kwargs).execute)
    return result.get("items", [])