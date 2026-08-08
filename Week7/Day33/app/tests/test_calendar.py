"""
test_calendar.py
------------------

Standalone test script for app/calendar/google_calendar.py, using the
project's existing credentials.json / token.json flow and app/config.py
settings (GOOGLE_CALENDAR_ID, CALENDAR_TIMEZONE) UNCHANGED.

Same pattern as test_rag.py / test_recommender.py / test_sql.py /
test_stt_deepgram.py at the project root: a standalone script, not a
pytest suite, that exercises the real module end to end.

This test creates a REAL event on the configured Google Calendar, then
updates and deletes it as part of the test — cleans up after itself even
on failure, so repeated runs don't accumulate test events.

Usage:
    python test_calendar.py
"""

import sys
from datetime import date, timedelta

from app.calendar.google_calendar import (
    GoogleCalendarError,
    authenticate,
    create_event,
    delete_event,
    find_event,
    update_event,
)

TEST_CLIENT_NAME = "TEST — Calendar Script"
TEST_PHONE = "+92-300-0000000"
TEST_EMPLOYEE = "Test Agent"
TEST_PROPERTY = "Skyline Residency"


def run():
    print("=== 1. authenticate() ===")
    try:
        service = authenticate()
        print(f"OK — authenticated. token.json path confirmed via config.")
    except GoogleCalendarError as exc:
        print(f"FAIL — {exc}")
        sys.exit(1)

    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    print("\n=== 2. create_event() ===")
    try:
        event = create_event(
            client_name=TEST_CLIENT_NAME,
            phone=TEST_PHONE,
            assigned_employee=TEST_EMPLOYEE,
            property_name=TEST_PROPERTY,
            date=tomorrow,
            time_str="15:00",
            notes="Automated test booking — safe to ignore/delete.",
        )
        event_id = event["id"]
        print(f"OK — created event_id={event_id}")
        print(f"    summary: {event.get('summary')}")
        print(f"    start:   {event.get('start', {}).get('dateTime')}")
    except GoogleCalendarError as exc:
        print(f"FAIL — {exc}")
        sys.exit(1)

    print("\n=== 3. find_event() ===")
    try:
        found = find_event(event_id)
        assert found is not None, "find_event returned None for a just-created event"
        print(f"OK — found event: {found.get('summary')}")
    except (GoogleCalendarError, AssertionError) as exc:
        print(f"FAIL — {exc}")

    print("\n=== 4. update_event() (reschedule +1 day, add note) ===")
    try:
        day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        updated = update_event(
            event_id=event_id,
            date=day_after,
            time_str="16:30",
            notes="Rescheduled by automated test.",
        )
        print(f"OK — updated start: {updated.get('start', {}).get('dateTime')}")
        assert "Rescheduled by automated test." in updated.get("description", "")
        print("OK — notes correctly updated in description")
    except (GoogleCalendarError, AssertionError) as exc:
        print(f"FAIL — {exc}")

    print("\n=== 5. delete_event() (cleanup) ===")
    try:
        delete_event(event_id)
        print(f"OK — deleted event_id={event_id}")
    except GoogleCalendarError as exc:
        print(f"FAIL — cleanup failed, you may need to delete event_id={event_id} manually: {exc}")
        sys.exit(1)

    print("\n=== 6. find_event() after delete (should be None) ===")
    try:
        found = find_event(event_id)
        assert found is None, "Event still found after deletion"
        print("OK — event no longer found, as expected")
    except AssertionError as exc:
        print(f"FAIL — {exc}")

    print("\nAll calendar tests completed.")


if __name__ == "__main__":
    run()