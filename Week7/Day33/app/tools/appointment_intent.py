"""
app/tools/appointment_intent.py
----------------------------------

Booking-intent detection and detail extraction for the voice agent,
mirroring the same lightweight keyword-based intent check used in the
n8n workflow's "Intent Detection" node (real_estate_workflow.json) —
kept consistent so both entry points (direct FastAPI/graph calls, and
n8n-routed calls) agree on what counts as booking intent.

Deliberately self-contained rather than extending
app/graph/slot_extractor.py or app/llm/prompts.py's SLOT_EXTRACTION_PROMPT
schema: this project's slot-extraction prompt and ConversationState have
evolved since they were first written and their current exact shape isn't
available here, so extending them blind risks silently breaking Day 3
behavior. Appointment details (name/phone/date/time) are a distinct
concern from buyer preference slots (budget/city/property_type/etc.)
anyway, so a separate, narrow extractor is a reasonable boundary even
independent of that constraint.

Pending appointment details are accumulated per session_id across turns
(a buyer typically gives their phone number in one turn and a date in the
next) in a small in-process store here — intentionally NOT added to
ConversationState for the same reason above.
"""

import logging
import threading
from datetime import date

from app.llm.client import extract_json

logger = logging.getLogger(__name__)

BOOK_KEYWORDS = [
    "appointment", "visit", "meeting", "schedule", "book",
    "milna", "milna hai", "dekhna hai", "dikhado", "dikha do",
    "book kar", "time de", "visit karna", "visit karni",
]
RESCHEDULE_KEYWORDS = [
    "reschedule", "change kar", "date badal", "time badal", "postpone",
    "aage kar", "peeche kar",
]
CANCEL_KEYWORDS = [
    "cancel", "cancel kar", "nahi ana", "cancel karna hai", "band kar",
]

REQUIRED_BOOK_FIELDS = ["client_name", "phone", "date", "time"]
REQUIRED_RESCHEDULE_FIELDS = ["phone", "date", "time"]
REQUIRED_CANCEL_FIELDS = ["phone"]

APPOINTMENT_EXTRACTION_PROMPT = """
You extract property-viewing appointment details from ONE new message in a
real estate sales phone call. You are NOT answering the buyer — you are
only extracting data.

Return ONLY a valid JSON object (no markdown, no explanation, no code
fences). Include a key ONLY if the buyer's LATEST message states or
changes that value.

Allowed keys:
- "client_name": string
- "phone": string (digits, keep as spoken, may include +92)
- "property": string (project name, only if explicitly named in this message)
- "date": string, format YYYY-MM-DD. Resolve relative dates ("kal" = tomorrow,
  "parso" = day after tomorrow, "is Friday" / "agle hafte" etc.) using
  today's date given below.
- "time": string, 24-hour format HH:MM
- "notes": string (anything else relevant to the visit)

Today's date is {today}.

Known appointment details so far (do not repeat unchanged values):
{prior_details}

Latest buyer message:
"{message}"

JSON:
"""

_lock = threading.Lock()
_pending_details: dict[str, dict] = {}


def _get_pending(session_id: str) -> dict:
    with _lock:
        return dict(_pending_details.setdefault(session_id, {}))


def _merge_pending(session_id: str, updates: dict) -> dict:
    with _lock:
        current = _pending_details.setdefault(session_id, {})
        current.update({k: v for k, v in updates.items() if v not in (None, "")})
        return dict(current)


def clear_pending(session_id: str) -> None:
    with _lock:
        _pending_details.pop(session_id, None)


def detect_appointment_intent(message: str) -> str | None:
    """
    Returns "cancel", "reschedule", "book", or None.
    Checked in that order deliberately — cancel/reschedule phrasing is
    more specific and destructive/state-changing than generic booking
    language, so it takes priority if both sets of keywords appear.
    """

    text = message.lower()

    if any(kw in text for kw in CANCEL_KEYWORDS):
        return "cancel"
    if any(kw in text for kw in RESCHEDULE_KEYWORDS):
        return "reschedule"
    if any(kw in text for kw in BOOK_KEYWORDS):
        return "book"
    return None


def extract_appointment_details(session_id: str, message: str) -> dict:
    """
    Extracts any appointment fields mentioned in this message, merges them
    into this session's accumulated pending details, and returns the full
    merged dict so far.
    """

    prior = _get_pending(session_id)

    prompt = APPOINTMENT_EXTRACTION_PROMPT.format(
        today=date.today().isoformat(),
        prior_details=prior or "None captured yet.",
        message=message,
    )

    updates = extract_json(prompt)

    if updates:
        logger.info("Appointment detail update for session %s: %s", session_id, updates)

    return _merge_pending(session_id, updates)


def missing_fields(details: dict, required: list[str]) -> list[str]:
    return [f for f in required if not details.get(f)]