"""
app/tests/day6/test_memory_accuracy.py
------------------------------------------

Day 6, Task 3 — Memory accuracy.

NO-API TEST. Tests REAL ConversationState (app/graph/state.py) behavior
through the REAL graph, with only LLM/tool I/O mocked. Memory correctness
here is a property of state.py's apply_updates()/reset logic, not of the
LLM, so this is fully verifiable without any external API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.tests.day6 import _harness as H  # noqa: E402

results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(f"[{'OK' if condition else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


def run():
    print("Running memory accuracy tests (NO-API TEST)...\n")

    # --- Test 1: multi-turn retention ---
    sid = "mem_multiturn"
    H.fresh_session(sid)
    H.reset_script()
    H.queue_slot_update({"budget": 30000000})
    H.run_turn(sid, "My budget is 3 crore.")
    H.queue_slot_update({"city": "Lahore", "area": "DHA"})
    H.run_turn(sid, "Mujhe DHA mein options bata dein.")
    H.queue_slot_update({})  # visit-booking turn shouldn't touch budget/city
    H.set_availability(True)
    H.set_booking_result(dict(H.DEFAULT_BOOKING_RESULT))
    H.seed_appointment_details(sid, {
        "client_name": "Test", "phone": "03001234567",
        "property": "Skyline Residency", "date": "2026-08-10", "time": "17:00",
    })
    H.run_turn(sid, "Visit book kar dein.")

    conv = H.memory_store.get_or_create(sid)
    check(
        "budget retained across 3 turns",
        conv.budget == 30000000,
        f"budget={conv.budget}",
    )
    check(
        "city/area retained across turns",
        conv.city == "Lahore" and conv.area == "DHA",
        f"city={conv.city}, area={conv.area}",
    )
    check(
        "budget/city NOT wiped by an unrelated booking turn",
        conv.budget == 30000000 and conv.city == "Lahore",
        "slot fields survive turns that only touch appointment_details",
    )

    # --- Test 2: newer value replaces older value ---
    sid2 = "mem_replace"
    H.fresh_session(sid2)
    H.reset_script()
    H.queue_slot_update({"budget": 30000000})
    H.run_turn(sid2, "Budget 3 crore hai.")
    H.queue_slot_update({"budget": 25000000})
    H.run_turn(sid2, "Budget ab 2.5 crore hai.")
    conv2 = H.memory_store.get_or_create(sid2)
    check(
        "budget update replaces old value, not appends/stacks",
        conv2.budget == 25000000,
        f"budget={conv2.budget} (must be 25000000, not 30000000 or something else)",
    )

    # --- Test 3: unrelated field untouched by an update to a different field ---
    sid3 = "mem_isolation"
    H.fresh_session(sid3)
    H.reset_script()
    H.queue_slot_update({"budget": 30000000, "city": "Karachi"})
    H.run_turn(sid3, "Budget 3 crore, Karachi mein chahiye.")
    H.queue_slot_update({"budget": 40000000})  # only budget changes this turn
    H.run_turn(sid3, "Budget 4 crore kar dein.")
    conv3 = H.memory_store.get_or_create(sid3)
    check(
        "updating budget alone does not clear city",
        conv3.budget == 40000000 and conv3.city == "Karachi",
        f"budget={conv3.budget}, city={conv3.city}",
    )

    # --- Test 4: session reset clears BOTH ConversationState AND pending appointment details ---
    sid4 = "mem_reset"
    H.fresh_session(sid4)
    H.reset_script()
    H.queue_slot_update({"budget": 30000000})
    H.run_turn(sid4, "Budget 3 crore hai.")
    H.seed_appointment_details(sid4, {"phone": "03001234567", "date": "2026-08-10", "time": "17:00"})

    from app.api.routes import reset_session
    reset_session(sid4)

    conv4_after = H.memory_store.get_or_create(sid4)  # get_or_create -> creates fresh since it was reset
    import app.tools.appointment_intent as appt_intent_mod
    check(
        "reset clears ConversationState (fresh budget=None)",
        conv4_after.budget is None,
        f"budget={conv4_after.budget}",
    )
    check(
        "reset clears appointment_intent pending details",
        sid4 not in appt_intent_mod._pending_details,
        "stale phone/date/time from before reset must not resurface",
    )

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"TOTAL: {passed}/{len(results)} memory accuracy tests passed")
    return results


if __name__ == "__main__":
    r = run()
    sys.exit(0 if all(ok for _, ok, _ in r) else 1)
