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
    # Urdu-script variants -- "بک" and "اپائنٹمنٹ" confirmed directly
    # from a real Deepgram nova-3/ur transcript in this project's own
    # LiveKit Console session log (not guessed): the ASCII-only keyword
    # list above can never match real transcribed Urdu speech, since
    # "بک"/"اپائنٹمنٹ" are different Unicode strings from "book"/
    # "appointment", not the same text in a different case. Additional
    # entries below are best-effort common variants NOT yet confirmed
    # against a real transcript -- extend this list as real examples
    # surface, same evidence-based approach used for the earlier
    # KNOWN_CORRECTIONS dict in transcript_corrections.py.
    "بک",           # "book" -- CONFIRMED from real transcript
    "اپائنٹمنٹ",     # "appointment" -- CONFIRMED from real transcript
    "دیکھنی ہے",     # "dekhni hai" / want to view -- CONFIRMED from real transcript
    "دیکھنا ہے",     # "dekhna hai" variant, not yet confirmed
    "ملاقات",        # native Urdu word for "meeting", not yet confirmed
    "وزٹ",           # "visit" (transliterated), not yet confirmed
    "شیڈول",         # "schedule" (transliterated), not yet confirmed
    "وقت دیں",       # "give me a time", not yet confirmed
]
RESCHEDULE_KEYWORDS = [
    "reschedule",
    "change kar",
    "date badal",
    "time badal",
    "wakt badal",
    "wqt badal",
    "time change",
    "date change",
    "postpone",
    "aage kar",
    "peeche kar",
    # Urdu-script variants
    "ری شیڈول",
    "ریشیڈول",
    "دوبارہ شیڈول",
    "دوبارہ وقت",
    "تاریخ بدل",
    "تاریخ تبدیل",
    "وقت بدل",
    "وقت تبدیل",
    "ٹائم چینج",
    "آگے کر",
    "پیچھے کر",
    "ری شیڈیول",
]
CANCEL_KEYWORDS = [
    "cancel", "cancel kar", "nahi ana", "cancel karna hai", "band kar",
    # Urdu-script variants -- NOT yet confirmed against a real
    # transcript. Best-effort only.
    "کینسل",
    "منسوخ",
    "نہیں آنا",
]

REQUIRED_BOOK_FIELDS = ["client_name", "date", "time"]
REQUIRED_RESCHEDULE_FIELDS = ["client_name", "date", "time"]
REQUIRED_CANCEL_FIELDS = ["client_name", "date", "time"]

APPOINTMENT_EXTRACTION_PROMPT = """
You extract property-viewing appointment details from ONE new message in a
real estate sales phone call. You are NOT answering the buyer — you are
only extracting data.

Return ONLY a valid JSON object (no markdown, no explanation, no code
fences). Include a key ONLY if the buyer's LATEST message states or
changes that value.

CRITICAL: "date" MUST always be formatted as YYYY-MM-DD. NEVER output a
date as raw text like "12 اگست" or "August 12" — always convert to ISO
format using today's year unless another year is stated.

Allowed keys:
- "client_name": string
- "phone": string (digits, keep as spoken, may include +92)
- "property": string (project name, only if explicitly named in this message)
- "date": string, STRICTLY in YYYY-MM-DD format.
  Resolve dates from English, Roman Urdu, or Urdu script using today's date
  as reference. Month name mappings — convert these to the correct month number:
  • جنوری / January / jan -> 01
  • فروری / February / feb -> 02
  • مارچ / March / mar -> 03
  • اپریل / April / apr -> 04
  • مئی / May -> 05
  • جون / June / jun -> 06
  • جولائی / July / jul -> 07
  • اگست / August / aug -> 08
  • ستمبر / September / sep -> 09
  • اکتوبر / October / oct -> 10
  • نومبر / November / nov -> 11
  • دسمبر / December / dec -> 12
  Relative date words: "kal" / "کل" = tomorrow, "parso" / "پرسوں" = day after tomorrow,
  "agle hafte" / "اگلے ہفتے" = next week (same weekday).
  Example: "12 اگست" with today {today} -> "2026-08-12"
  Example: "kal" with today 2026-08-11 -> "2026-08-12"
- "time": string, 24-hour format HH:MM. Resolve natural language times in English, Urdu, or Roman Urdu.
  Time qualifiers: "subah" / "صبح" = morning (AM), "dopeher" / "دوپہر" = afternoon (noon-3pm),
  "shaam" / "شام" = evening (4pm-8pm), "raat" / "رات" = night (after 8pm).
  Convert Urdu number words to standard 24-hour time:
  • "baraan" / "barah" / "bara" / "بارہ" -> 12 (e.g. "baraan baje" = "12:00", "raat baraan baje" = "00:00")
  • "gyarah" / "گیارہ" -> 11 ("11:00")
  • "das" / "دس" -> 10 ("10:00")
  • "nau" / "no" / "نو" -> 9 ("09:00")
  • "aath" / "آٹھ" -> 8 ("08:00")
  • "saat" / "سات" -> 7 ("07:00" or "19:00" if shaam)
  • "che" / "chhe" / "چھ" -> 6 ("06:00" or "18:00" if shaam)
  • "paanch" / "پانچ" -> 5 ("05:00" or "17:00" if shaam)
  • "char" / "chaar" / "چار" -> 4 ("04:00" or "16:00" if dopeher)
  • "teen" / "تین" -> 3 ("03:00" or "15:00" if dopeher)
  • "do" / "دو" -> 2 ("02:00" or "14:00" if dopeher)
  • "ek" / "aik" / "ایک" -> 1 ("01:00" or "13:00" if dopeher)
  If only an hour is stated without am/pm or morning/night context, assume daytime viewing hours (9:00-19:00) — e.g. "baraan baje" -> "12:00", "3 baje" -> "15:00", "shaam paanch baje" -> "17:00".
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

# Caller-ID phone number, keyed by session_id. Deliberately a SEPARATE
# store from _pending_details: clear_pending() wipes _pending_details
# after every completed booking/reschedule/cancellation action (see its
# docstring), but the caller's phone number does not change mid-call --
# a buyer who books an appointment and then immediately asks to
# reschedule again in the same call must not be asked to repeat their
# number. Populated from Vapi's call.customer.number by
# app/api/routes.py's chat_completions() via set_caller_phone(), which
# is safe to call on every turn.
_caller_phone_by_session: dict[str, str] = {}


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


def set_caller_phone(session_id: str, phone: str | None) -> None:
    """
    Records this call's caller-ID phone number (Vapi's
    call.customer.number, E.164 format e.g. "+923001234567") so
    extract_appointment_details() can use it as the phone value for
    booking/reschedule/cancellation instead of asking the buyer to speak
    their number aloud over a lossy voice channel, which was the actual
    source of the missed/garbled-digits problem this replaces.

    No-op if phone is empty/None (e.g. text-only testing calls through
    /chat/completions that have no Vapi call.customer) -- in that case
    extract_appointment_details() falls back to the old behavior of
    asking for the phone number by voice.
    """
    if not phone or not isinstance(phone, str):
        return
    phone = phone.strip()
    if not phone:
        return
    with _lock:
        _caller_phone_by_session[session_id] = phone


def clear_caller_phone(session_id: str) -> None:
    with _lock:
        _caller_phone_by_session.pop(session_id, None)


def get_caller_phone(session_id: str) -> str | None:
    with _lock:
        return _caller_phone_by_session.get(session_id)


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

    # Caller-ID auto-fill: if no phone has been captured for this
    # booking/reschedule/cancellation yet, use this call's caller ID
    # (set via set_caller_phone()) instead of requiring the buyer to
    # say their number aloud. Only fills in when phone is still
    # missing, so a buyer who explicitly states a different number
    # (e.g. booking on behalf of someone else) still overrides it --
    # extract_json() below can freely set "phone" from the message,
    # and that value wins via the _merge_pending() call at the end of
    # this function.
    if not prior.get("phone"):
        caller_phone = get_caller_phone(session_id)
        if caller_phone:
            prior = _merge_pending(session_id, {"phone": caller_phone})

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

def has_pending_details(session_id: str) -> bool:
    """
    True if this session has an in-progress, not-yet-complete
    booking/reschedule/cancellation collection (i.e. clear_pending()
    hasn't fired yet for it). Used by intent_detection_node to keep
    routing the SAME appointment intent across a multi-turn
    clarification exchange -- see nodes.py for why this is needed.
    """
    with _lock:
        return session_id in _pending_details