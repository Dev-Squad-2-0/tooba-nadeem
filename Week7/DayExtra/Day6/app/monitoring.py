"""
app/monitoring.py
--------------------

Day 6, Task 4 — Structured event logging for production debugging.

Deliberately stdlib-only (logging + json), no new dependency, per the
"prefer standard library" policy. Emits ONE structured JSON line per
graph turn via the standard `logging` module (so it goes through the
same config.LOG_LEVEL / handlers already set up in main.py) -- this is
NOT a new logging system, it's one additional structured event on top of
the existing [GRAPH]/[TOOL] prefix-style logs from Day 5/reschedule-fix,
which stay exactly as they are.

Fields (per the brief's suggested list): timestamp, session_id, intent,
latency_ms, tool_name, tool_success, booking_status, calendar_status,
email_status, rag_hit, error_type.

NEVER logs: API keys, passwords, tokens, full phone numbers/CNIC, full
transcripts. Phone numbers are masked (last 4 digits only) if present,
since a session_id + full phone number together is more identifying
than needed for a debug log line.

Voice quality: NOT measured here. This project has no real audio-quality
metric (MOS score, WER against ground truth, etc.) wired up anywhere.
Documenting that honestly rather than inventing a number -- see
docs/Day6_README.md's "Known limitations" section for what a real
implementation would need (a labeled test-audio set + Deepgram's
confidence scores, at minimum).
"""

import json
import logging
import time

logger = logging.getLogger("monitoring")


def _mask_phone(phone: str | None) -> str | None:
    if not phone or len(phone) < 4:
        return phone
    return "*" * (len(phone) - 4) + phone[-4:]


def log_turn_event(
    session_id: str,
    intent: str | None,
    latency_ms: float,
    appointment_status: str | None = None,
    tool_outputs: dict | None = None,
    error_type: str | None = None,
) -> None:
    """
    Call once per graph turn (wired into
    app/graph/nodes.py:response_generation_node). Emits one structured
    JSON log line -- easy to grep, easy to pipe into a log aggregator
    later without changing the call site.
    """

    tool_outputs = tool_outputs or {}

    event = {
        "timestamp": time.time(),
        "session_id": session_id,
        "intent": intent,
        "latency_ms": round(latency_ms, 2),
        "booking_status": appointment_status,
        "calendar_status": tool_outputs.get("calendar_status"),
        "email_status": tool_outputs.get("email_status"),
        "rag_hit": tool_outputs.get("rag_hit"),
        "error_type": error_type,
    }

    logger.info("[METRICS] %s", json.dumps(event))


def log_tool_failure(
    session_id: str,
    tool_name: str,
    reason: str,
) -> None:
    """
    Call from any tool-call site (app/graph/tools.py) on a caught
    failure, in addition to that function's own existing error log --
    this one is specifically structured for later aggregation ("how many
    Calendar failures this week"), not just human-readable debugging.
    """
    logger.warning(
        "[METRICS] %s",
        json.dumps({
            "timestamp": time.time(),
            "session_id": session_id,
            "tool_name": tool_name,
            "tool_success": False,
            "error_type": reason,
        }),
    )
