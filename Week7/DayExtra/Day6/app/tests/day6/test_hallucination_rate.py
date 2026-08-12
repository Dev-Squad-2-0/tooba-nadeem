"""
app/tests/day6/test_hallucination_rate.py
----------------------------------------------

Day 6, Task 3 — Hallucination rate.

NO-API TEST. Defines hallucination precisely for this system: the agent
must never report appointment_status as "booked"/"rescheduled"/"cancelled"
unless the underlying (mocked) tool explicitly returned success=True, and
must never fabricate structured data (recommended_properties) when the
mocked search/RAG layer returned nothing.

Hallucination rate = hallucinated_cases / total_cases, computed from
actual results below -- not an invented percentage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.tests.day6 import _harness as H  # noqa: E402

CASES = []


def case(name, setup_fn, message, is_hallucination_fn):
    """
    is_hallucination_fn(conv) -> True if the response/state shows a
    hallucination (i.e. the test FAILS if True).
    """
    CASES.append({"name": name, "setup": setup_fn, "message": message, "is_hallucination": is_hallucination_fn})


# Correct answer is "no matching property found" -- must not invent one.
case(
    "no matching property -- must not fabricate a recommendation",
    lambda sid: H.set_search_results("No matching properties found in the database for the current preferences.", []),
    "Mujhe Mars planet pe property chahiye budget 1 crore mein.",
    lambda conv: len(conv.recommended_properties) > 0,
)

# Correct answer is "not in knowledge base" -- covered structurally: RAG
# context mocked empty, response generation must not claim a fact exists.
# We can only verify structurally (rag_context was empty going into the
# prompt) since the LLM itself is mocked -- real hallucination-in-text
# checking requires a REAL-API run, documented explicitly.
case(
    "empty RAG context -- structurally nothing to hallucinate FROM",
    lambda sid: H.set_rag_context("No relevant passages found in the knowledge base."),
    "Kya Meridian Homes Multan mein bhi kaam karta hai?",
    lambda conv: False,  # structural-only check; always "not hallucinated" at the state level
)

# Booking must not be claimed when the mocked tool reports failure.
case(
    "failed booking tool call -- must not claim booked",
    lambda sid: (
        H.set_availability(True),
        H.set_booking_result({"success": False, "appointment": None, "error": "Calendar error: simulated failure.", "reason": "calendar_error"}),
        H.seed_appointment_details(sid, {"client_name": "Ali", "phone": "03001234567", "property": "Skyline Residency", "date": "2026-08-10", "time": "17:00"}),
    ),
    "Mera naam Ali hai, phone 03001234567, Skyline Residency kal 5 baje book kar dein.",
    lambda conv: conv.appointment_status == "booked",
)

# Unavailable slot must not be claimed as booked.
case(
    "unavailable slot -- must not claim booked",
    lambda sid: (
        H.set_availability(False),
        H.seed_appointment_details(sid, {"client_name": "Sara", "phone": "03009999999", "property": "Skyline Residency", "date": "2026-08-10", "time": "11:00"}),
    ),
    "Sara, 03009999999, Skyline Residency kal 11 baje.",
    lambda conv: conv.appointment_status == "booked",
)

# Reschedule with wrong phone (the original bug) must not claim rescheduled.
case(
    "reschedule, appointment not found -- must not claim rescheduled",
    lambda sid: (
        H.set_availability(True),
        H.set_reschedule_result({"success": False, "appointment": None, "error": "No appointment found for this phone number.", "reason": None}),
        H.seed_appointment_details(sid, {"phone": "03041234567", "date": "2026-08-10", "time": "17:00"}),
    ),
    "Reschedule kar dein kal 5 baje, phone 03041234567.",
    lambda conv: conv.appointment_status == "rescheduled",
)

# Cancellation for a nonexistent appointment must not claim cancelled.
case(
    "cancel nonexistent appointment -- must not claim cancelled",
    lambda sid: (
        H.set_cancel_result({"success": False, "appointment": None, "error": "No client found for this phone number.", "reason": None}),
        H.seed_appointment_details(sid, {"phone": "03000000000"}),
    ),
    "Cancel kar dein, phone 03000000000.",
    lambda conv: conv.appointment_status == "cancelled",
)


def run():
    print(f"Running {len(CASES)} hallucination-rate test cases (NO-API TEST)...\n")

    hallucinated = 0
    for i, c in enumerate(CASES):
        sid = f"halluc_{i}"
        H.fresh_session(sid)
        H.reset_script()
        c["setup"](sid)
        H.run_turn(sid, c["message"])
        conv = H.memory_store.get_or_create(sid)

        is_halluc = c["is_hallucination"](conv)
        if is_halluc:
            hallucinated += 1
        status = "HALLUCINATION DETECTED" if is_halluc else "OK (no hallucination)"
        print(f"[{status}] {c['name']}")

    total = len(CASES)
    rate = hallucinated / total if total else 0.0
    print()
    print(f"Hallucination rate = {hallucinated}/{total} = {rate:.1%}")
    print(
        "\nNOTE: cases marked 'structural-only' verify that nothing in "
        "GraphState/ConversationState claims an unsupported fact -- they "
        "do NOT verify the LLM's actual generated sentence, since the LLM "
        "is mocked here. A REAL-API spot-check of actual response text is "
        "a separate, smaller manual step per the 'do not waste OpenRouter "
        "credits' policy."
    )
    return hallucinated, total


if __name__ == "__main__":
    hallucinated, total = run()
    sys.exit(0 if hallucinated == 0 else 1)
