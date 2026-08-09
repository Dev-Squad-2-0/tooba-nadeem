"""
test_crm.py
-------------

Standalone test script for app/crm/crm_service.py, using the project's
existing SQLite database (config.SQL_DATABASE_PATH) UNCHANGED — writes
into the same property_data.db Day 1/2 already use, in new
crm_-prefixed tables created automatically on first CRMService() init.

Uses a clearly-tagged test phone number and cleans up all rows it created
at the end, via direct SQL against the same connection pattern
sql_retriever.py already uses — CRMService intentionally has no
delete_* methods (CRM data is normally append-only/audit-trail data), so
cleanup here is a deliberate test-only exception, not a missing feature.

Usage:
    python test_crm.py
"""

import sys

from app.crm.crm_service import CRMService, CRMServiceError

TEST_PHONE = "+92-300-TEST-CRM"
TEST_CLIENT_NAME = "TEST — CRM Script"


def cleanup(crm: CRMService, client_id: str | None):
    if not client_id:
        return
    print("\n=== Cleanup (test-only direct SQL, not a CRMService method) ===")
    crm.conn.execute("DELETE FROM crm_appointments WHERE client_id = ?", (client_id,))
    crm.conn.execute("DELETE FROM crm_transcripts WHERE client_id = ?", (client_id,))
    crm.conn.execute("DELETE FROM crm_clients WHERE client_id = ?", (client_id,))
    crm.conn.commit()
    print("OK — test rows removed")


def run():
    crm = CRMService()
    client_id = None

    try:
        print("=== 1. upsert_client() (insert) ===")
        client = crm.upsert_client(
            client_name=TEST_CLIENT_NAME,
            phone=TEST_PHONE,
            budget=30_000_000,
            preferred_location="DHA Lahore",
            property_type="apartment",
            notes="Initial test note.",
        )
        client_id = client["client_id"]
        print(f"OK — client_id={client_id}")

        print("\n=== 2. upsert_client() (update, same phone) ===")
        updated_client = crm.upsert_client(
            client_name=TEST_CLIENT_NAME,
            phone=TEST_PHONE,
            budget=50_000_000,  # buyer raised budget
        )
        assert updated_client["client_id"] == client_id, "upsert created a duplicate client"
        assert updated_client["budget"] == 50_000_000
        assert updated_client["preferred_location"] == "DHA Lahore", "unrelated field was wiped"
        print("OK — same client_id reused, budget updated, other fields preserved")

        print("\n=== 3. log_transcript() + get_transcripts() ===")
        crm.log_transcript(client_id, "Assalam alaikum, mujhe DHA Lahore mein apartment dekhna hai.")
        crm.log_transcript(client_id, "Budget ab 5 crore hai.")
        transcripts = crm.get_transcripts(client_id)
        assert len(transcripts) == 2
        print(f"OK — {len(transcripts)} transcript entries logged")

        print("\n=== 4. add_appointment() ===")
        appointment = crm.add_appointment(
            client_id=client_id,
            property_name="Skyline Residency",
            meeting_time="Saturday, 09 August 2026 at 03:00 PM",
            assigned_employee="Test Agent",
            calendar_event_id="fake_event_id_123",
            notes="Test appointment.",
        )
        appointment_id = appointment["appointment_id"]
        assert appointment["status"] == "booked"
        print(f"OK — appointment_id={appointment_id}, status=booked")

        print("\n=== 5. get_active_appointment_for_client() ===")
        active = crm.get_active_appointment_for_client(client_id)
        assert active is not None and active["appointment_id"] == appointment_id
        print("OK — correctly returned the active appointment")

        print("\n=== 6. update_appointment_status() (reschedule) ===")
        rescheduled = crm.update_appointment_status(
            appointment_id=appointment_id,
            status="rescheduled",
            meeting_time="Sunday, 10 August 2026 at 04:30 PM",
        )
        assert rescheduled["status"] == "rescheduled"
        print("OK — status/time updated")

        print("\n=== 7. set_follow_up_reminder() + get_due_follow_ups() ===")
        crm.set_follow_up_reminder(appointment_id, "2000-01-01T00:00:00")  # already-past date
        due = crm.get_due_follow_ups()
        assert any(a["appointment_id"] == appointment_id for a in due)
        print(f"OK — {len(due)} appointment(s) due, including our test appointment")

        print("\n=== 8. update_appointment_status() (cancel) ===")
        cancelled = crm.update_appointment_status(appointment_id, status="cancelled")
        assert cancelled["status"] == "cancelled"
        active_after_cancel = crm.get_active_appointment_for_client(client_id)
        assert active_after_cancel is None, "cancelled appointment still counted as active"
        print("OK — cancelled correctly, no longer counted as active")

        print("\n=== 9. get_appointment_history() ===")
        history = crm.get_appointment_history(client_id)
        assert len(history) == 1
        print(f"OK — {len(history)} appointment(s) in history")

        print("\nAll CRM tests passed.")

    except (CRMServiceError, AssertionError) as exc:
        print(f"\nFAIL — {exc}")
        cleanup(crm, client_id)
        crm.close()
        sys.exit(1)

    cleanup(crm, client_id)
    crm.close()


if __name__ == "__main__":
    run()