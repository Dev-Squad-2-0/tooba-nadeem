"""
Basic abuse-handling guardrails for the AFL agent.

This is intentionally simple (in-memory, single-process) since the project
runs as a single FastAPI/uvicorn process without a shared cache like Redis.
It is enough to stop obvious abuse (spamming one conversation_id, or sending
huge payloads) but is NOT a substitute for a real API gateway / WAF in a
multi-instance production deployment. See monitoring_checklist.md for the
recommended upgrade path.
"""

import time
from collections import defaultdict, deque

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MAX_MESSAGE_CHARS = 2000
MAX_REQUESTS_PER_WINDOW = 20
WINDOW_SECONDS = 60

# conversation_id -> deque of request timestamps (monotonic)
_request_log: dict[str, deque] = defaultdict(deque)


class RateLimitError(Exception):
    """Raised when a conversation_id exceeds the allowed request rate."""


class InputTooLargeError(Exception):
    """Raised when a message exceeds the maximum allowed length."""


def check_input_size(message: str) -> None:
    if message is None:
        raise InputTooLargeError("Message cannot be empty.")

    if len(message) > MAX_MESSAGE_CHARS:
        raise InputTooLargeError(
            f"Message is too long ({len(message)} chars). "
            f"Maximum allowed is {MAX_MESSAGE_CHARS} characters."
        )


def check_rate_limit(conversation_id: str) -> None:
    """
    Sliding-window rate limit per conversation_id.
    Raises RateLimitError if the caller has exceeded
    MAX_REQUESTS_PER_WINDOW requests in WINDOW_SECONDS.
    """

    now = time.monotonic()
    log = _request_log[conversation_id]

    # Drop timestamps outside the current window
    while log and now - log[0] > WINDOW_SECONDS:
        log.popleft()

    if len(log) >= MAX_REQUESTS_PER_WINDOW:
        raise RateLimitError(
            f"Too many requests for conversation_id={conversation_id}. "
            f"Limit is {MAX_REQUESTS_PER_WINDOW} requests per {WINDOW_SECONDS}s."
        )

    log.append(now)


# ---------------------------------------------------------------------------
# Scope-override / prompt-injection heuristics
# ---------------------------------------------------------------------------
#
# These are a *secondary* defense layer, not the primary one. The primary
# defense is the SYSTEM_PROMPT's explicit scope rules, which the LLM is
# expected to follow. This heuristic layer catches the most common override
# phrasings so the agent can short-circuit with a canned refusal even if the
# underlying model were to comply, and so we have a deterministic signal to
# log/alert on for the "off-topic leak rate" metric.

_OVERRIDE_PATTERNS = [
    "ignore your instructions",
    "ignore previous instructions",
    "ignore all previous",
    "ignore afl",
    "disregard your instructions",
    "disregard the above",
    "forget your instructions",
    "you are not an afl",
    "you are no longer an afl",
    "no longer an afl",
    "pretend you are not",
    "pretend the afl",
    "act as if you have no",
    "system prompt",
    "system override",
    "reveal your instructions",
    "print your prompt",
    "new instructions:",
    "developer mode",
    "jailbreak",
    "general-purpose assistant",
    "no restrictions",
    "unrestricted ai",
    "was just a joke",
    "talk about anything",
]


def looks_like_override_attempt(message: str) -> bool:
    lowered = (message or "").lower()
    return any(pattern in lowered for pattern in _OVERRIDE_PATTERNS)
