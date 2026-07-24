import logging
import re
import time

from app.logging_config import log_event
from app.state import TicketState

logger = logging.getLogger("triage_agent.nodes.validate")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_DESCRIPTION_LENGTH = 8
_MAX_DESCRIPTION_LENGTH = 8000


def validate_input(state: TicketState) -> dict:
    """
    Failure scenario handled here: BAD INPUT.
    Rejects tickets missing required fields, with a malformed email, or with
    a description too short to classify / too long to be a genuine single
    ticket (basic anti-spam/anti-abuse guard). Never raises -- always
    returns a structured, routable result even for invalid input.
    """
    start = time.monotonic()
    errors: list[str] = []

    email = (state.get("customer_email") or "").strip()
    subject = (state.get("subject") or "").strip()
    description = (state.get("description") or "").strip()

    if not email or not _EMAIL_RE.match(email):
        errors.append("customer_email is missing or not a valid email address")
    if not subject:
        errors.append("subject is missing")
    if len(description) < _MIN_DESCRIPTION_LENGTH:
        errors.append(f"description is too short (min {_MIN_DESCRIPTION_LENGTH} chars) to classify")
    if len(description) > _MAX_DESCRIPTION_LENGTH:
        errors.append(f"description exceeds max length ({_MAX_DESCRIPTION_LENGTH} chars)")

    is_valid = len(errors) == 0
    log_event(
        logger, "validate_input",
        ticket_id=state.get("ticket_id"), is_valid=is_valid, errors=errors,
        latency_ms=round((time.monotonic() - start) * 1000, 1),
    )

    return {
        "is_valid": is_valid,
        "validation_errors": errors,
        "status": "rejected_invalid_input" if not is_valid else state.get("status", ""),
        "trace": state.get("trace", []) + [{
            "node": "validate_input", "is_valid": is_valid,
            "latency_ms": round((time.monotonic() - start) * 1000, 1),
        }],
    }


def route_after_validation(state: TicketState) -> str:
    """Conditional edge: stop the graph early on invalid input instead of
    wasting an LLM call classifying garbage."""
    return "continue" if state.get("is_valid") else "reject"
