"""
test_appointments.py
-----------------------

Standalone integration test for app/workflows/appointment_manager.py —
exercises book_appointment() / reschedule_appointment() /
cancel_appointment() end to end, which means it really does:

  - create/update/delete a REAL Google Calendar event
  - send REAL emails (if the property's assigned agent has an email and
    SMTP is configured — a missing/failed email is logged as a warning
    by appointment_manager.py, not a hard failure, matching its own
    "don't roll back a successful booking over a notification failure"
    design)
  - write/update REAL rows in the crm_* SQLite tables

Uses a clearly-tagged test phone number and cleans up the CRM rows and
Calendar event it creates at the end (or on failure), same spirit as
test_calendar.py / test_crm.py.

Usage:
    python test_appointments.py
"""

import sys
from datetime import date, timedelta

from app.calendar.google_calendar import delete_event, GoogleCalendarError
from app.crm.crm_service import CRMService
from app.workflows.appointment_manager import (
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
)

TEST_CLIENT_NAME = "TEST — Appointment Workflow Script"
TEST_PHONE = "+92-300-TEST-APPT"
TEST_PROPERTY = "Skyline Residency"  # must exist in database/structured/properties.csv


def cleanup(client_id: str | None, calendar_event_id: str | None):
    print("\n=== Cleanup ===")
    if calendar_event_id:
        try:
            delete_event(calendar_event_id)
            print(f"OK — deleted calendar event {calendar_event_id}")
        except GoogleCalendarError as exc:
            print(f"WARN — could not auto-delete calendar event {calendar_event_id}: {exc}")

    if client_id:
        crm = CRMService()
        crm.conn.execute("DELETE FROM crm_appointments WHERE client_id = ?", (client_id,))
        crm.conn.execute("DELETE FROM crm_transcripts WHERE client_id = ?", (client_id,))
        crm.conn.execute("DELETE FROM crm_clients WHERE client_id = ?", (client_id,))
        crm.conn.commit()
        crm.close()
        print("OK — removed test CRM rows")


def run():
    client_id = None
    calendar_event_id = None
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")

    print("=== 1. book_appointment() ===")
    result = book_appointment(
        client_name=TEST_CLIENT_NAME,
        phone=TEST_PHONE,
        property_name=TEST_PROPERTY,
        date=tomorrow,
        time_str="15:00",
        budget=30_000_000,
        preferred_location="DHA Lahore",
        property_type="apartment",
        requirements="3 bedroom apartment",
        notes="Automated integration test.",
        transcript="Test transcript for booking flow.",
    )

    if not result["success"]:
        print(f"FAIL — booking failed: {result['error']}")
        sys.exit(1)

    appointment = result["appointment"]
    client_id = appointment["client_id"]
    calendar_event_id = appointment.get("calendar_event_id")

    print(f"OK — booked appointment_id={appointment['appointment_id']}")
    print(f"    calendar_event_id={calendar_event_id}")
    print(f"    assigned_employee={appointment.get('assigned_employee')}")
    print(f"    meeting_time={appointment.get('meeting_time')}")

    try:
        print("\n=== 2. reschedule_appointment() ===")
        result = reschedule_appointment(
            phone=TEST_PHONE,
            new_date=day_after,
            new_time="16:30",
            notes="Rescheduled by automated test.",
        )
        if not result["success"]:
            print(f"FAIL — reschedule failed: {result['error']}")
        else:
            print(f"OK — rescheduled, new meeting_time={result['appointment']['meeting_time']}")
            assert result["appointment"]["status"] == "rescheduled"

        print("\n=== 3. cancel_appointment() ===")
        result = cancel_appointment(phone=TEST_PHONE, notes="Cancelled by automated test.")
        if not result["success"]:
            print(f"FAIL — cancel failed: {result['error']}")
        else:
            print(f"OK — cancelled, status={result['appointment']['status']}")
            assert result["appointment"]["status"] == "cancelled"
            # cancel_appointment already deleted the calendar event —
            # don't try to delete it again in cleanup().
            calendar_event_id = None

        print("\nAll appointment workflow tests completed.")

    except AssertionError as exc:
        print(f"\nFAIL — {exc}")

    cleanup(client_id, calendar_event_id)


if __name__ == "__main__":
    run()