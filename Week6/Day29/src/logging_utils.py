"""
Structured logging for the AFL agent.

Every turn of the conversation produces one JSON-line log record with:
- timestamp
- conversation_id
- query (truncated for log size, not for processing)
- detected_intent (best-effort; None if not classified)
- tools_called (name + latency_ms + status for each tool invocation)
- total_latency_ms
- status ("ok", "tool_error", "rate_limited", "agent_error")
- error (string, if any)

Logs are written to a local file (logs/agent_events.jsonl) as newline-delimited
JSON, plus a short human-readable line to stdout. Both are safe to parse with
standard log-aggregation tools (e.g. ELK, CloudWatch, Datadog) without any
custom parsing logic.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "agent_events.jsonl"

MAX_LOGGED_QUERY_CHARS = 300


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    conversation_id: str,
    query: str,
    status: str,
    intent: str | None = None,
    tools_called: list | None = None,
    total_latency_ms: float | None = None,
    error: str | None = None,
    model_used: str | None = None,
) -> dict:
    """
    Write one structured event record. Returns the record that was written
    (useful for tests / the FastAPI response's debug metadata).
    """

    record = {
        "timestamp": _now_iso(),
        "conversation_id": conversation_id,
        "query": (query or "")[:MAX_LOGGED_QUERY_CHARS],
        "intent": intent,
        "tools_called": tools_called or [],
        "model_used": model_used,
        "total_latency_ms": round(total_latency_ms, 2) if total_latency_ms is not None else None,
        "status": status,
        "error": error,
    }

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:
        # Logging must never crash the request path.
        print(f"[LOGGING ERROR] Failed to write log record: {exc}")

    print(
        f"[EVENT] conv={conversation_id} status={status} "
        f"intent={intent} tools={[t.get('name') for t in (tools_called or [])]} "
        f"latency_ms={record['total_latency_ms']}"
    )

    return record


class Timer:
    """Small helper: `with Timer() as t: ...` then `t.elapsed_ms`."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
