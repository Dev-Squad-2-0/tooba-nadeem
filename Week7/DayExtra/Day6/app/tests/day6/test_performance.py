"""
app/tests/day6/test_performance.py
--------------------------------------

Day 6, Task 3 — Performance evaluation.

IMPORTANT LABELING: every number this file reports is MOCKED-LLM /
MOCKED-TOOL latency (the harness stubs OpenAI/Calendar/CRM entirely, per
"do not waste OpenRouter credits"). This measures REAL Python-level graph
orchestration overhead (state loading, slot-extraction call site, intent
routing, node dispatch) with the actual external I/O time removed — it is
NOT a substitute for real production latency, which requires a REAL-API
test run separately with actual credentials.

Uses time.perf_counter() per the brief's requirement -- no invented
numbers.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.tests.day6 import _harness as H  # noqa: E402

N_RUNS = 30

TEST_MESSAGES = [
    "Mera budget 3 crore hai.",
    "Lahore mein DHA ke options dikhado.",
    "Skyline Residency ke amenities kya hain?",
    "Yeh price bohat zyada hai.",
    "Aaj mausam kaisa hai?",
]


def run():
    print(f"Running {N_RUNS} mocked-I/O graph invocations ({len(TEST_MESSAGES)} distinct messages, round-robin)...")
    print("LABEL: MOCKED-LLM / MOCKED-TOOL latency (orchestration overhead only, not production latency).\n")

    latencies_ms = []
    successes = 0
    failures = 0

    for i in range(N_RUNS):
        session_id = f"perf_{i}"
        H.fresh_session(session_id)
        H.reset_script()
        H.queue_slot_update({})
        message = TEST_MESSAGES[i % len(TEST_MESSAGES)]

        start = time.perf_counter()
        try:
            H.run_turn(session_id, message)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies_ms.append(elapsed_ms)
            successes += 1
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  [FAIL] run {i}: {type(exc).__name__}: {exc}")

    print()
    if latencies_ms:
        avg = sum(latencies_ms) / len(latencies_ms)
        print(f"Average latency (mocked I/O): {avg:.2f} ms")
        print(f"Minimum latency (mocked I/O): {min(latencies_ms):.2f} ms")
        print(f"Maximum latency (mocked I/O): {max(latencies_ms):.2f} ms")
    else:
        print("No successful runs -- no latency data.")
    print(f"Successful requests: {successes}")
    print(f"Failed requests:     {failures}")
    print()
    print(
        "NOT MEASURED HERE (requires REAL-API run with real credentials): "
        "actual OpenRouter LLM latency, real Deepgram STT latency, real "
        "Edge-TTS synthesis latency, real Google Calendar API round-trip. "
        "This file measures Python orchestration overhead only."
    )

    return {"avg_ms": (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else None,
            "min_ms": min(latencies_ms) if latencies_ms else None,
            "max_ms": max(latencies_ms) if latencies_ms else None,
            "successes": successes, "failures": failures}


if __name__ == "__main__":
    result = run()
    sys.exit(0 if result["failures"] == 0 else 1)
