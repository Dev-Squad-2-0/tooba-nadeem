"""
app/tests/day6/_harness.py
-----------------------------

Shared NO-API test harness for Day 6. Import this FIRST, before importing
anything from `app`, in every test file that needs to run without a real
LLM/Calendar/CRM/RAG connection.

This is the same stub/mock pattern proven in the Day 5 dry-run and the
reschedule bug-repro test earlier in this project's history, promoted
into one reusable module instead of being copy-pasted per test file.

Two layers of fakery:
  1. sys.modules stubs for SDKs not installed in this environment
     (openai, chromadb-backed langchain_chroma, langchain_huggingface,
     Google API client libs) -- these exist purely so `import app...`
     doesn't crash. NOT used for real assertions.
  2. Mocked functions on app.graph.tools / app.llm.client -- these ARE
     used for real assertions, via a small scripting API
     (queue_chat_response, queue_slot_update, etc.) so each test controls
     exactly what the "LLM" and "external tools" return.

IMPORTANT: this harness talks to the REAL app.graph.nodes / build_graph /
agent_graph / state / slot_extractor / appointment_intent /
objection_handler code. Only the external I/O boundary is fake. A
passing test here means the real orchestration logic is verified; it
does NOT mean the real LLM/Calendar/CRM will behave the same way in
production -- see each test file's docstring for what it does and does
NOT cover.
"""

import sys
import types
from unittest.mock import MagicMock


def _stub_module(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


def install_sdk_stubs():
    """Idempotent -- safe to call from every test file's import block."""
    if "openai" in sys.modules and isinstance(sys.modules["openai"], types.ModuleType) \
            and hasattr(sys.modules["openai"], "_DAY6_STUB"):
        return  # already installed this run

    class _FakeOpenAI:
        def __init__(self, *a, **k):
            self.chat = MagicMock()

    stub = _stub_module("openai", OpenAI=_FakeOpenAI, BadRequestError=Exception)
    stub._DAY6_STUB = True

    _stub_module("langchain_chroma", Chroma=MagicMock())
    _stub_module("langchain_huggingface", HuggingFaceEmbeddings=MagicMock())
    lc_community = _stub_module("langchain_community")
    lc_community.document_loaders = _stub_module(
        "langchain_community.document_loaders",
        DirectoryLoader=MagicMock(), TextLoader=MagicMock(),
    )
    _stub_module("google")
    _stub_module("google.auth")
    _stub_module("google.auth.transport")
    _stub_module("google.auth.transport.requests", Request=MagicMock())
    _stub_module("google.oauth2")
    _stub_module("google.oauth2.credentials", Credentials=MagicMock())
    _stub_module("google_auth_oauthlib")
    _stub_module("google_auth_oauthlib.flow", InstalledAppFlow=MagicMock())
    _stub_module("googleapiclient")
    _stub_module("googleapiclient.discovery", build=MagicMock())
    _stub_module("googleapiclient.errors", HttpError=Exception)


install_sdk_stubs()

# ---------------------------------------------------------------------------
# Now safe to import the real app code.
# ---------------------------------------------------------------------------

from app.graph import tools as biz_tools           # noqa: E402
from app.graph.agent_graph import handle_turn       # noqa: E402
from app.graph import memory_store                  # noqa: E402
import app.llm.client as llm_client                 # noqa: E402
import app.graph.slot_extractor as slot_extractor_mod  # noqa: E402
import app.tools.appointment_intent as appt_intent_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Scripting API for tests
# ---------------------------------------------------------------------------

_script = {
    "chat_responses": [],       # queued fake LLM chat replies
    "slot_updates": [],         # queued fake slot-extractor JSON diffs
    "availability": True,       # what check_availability returns next
    "search_results": ([], []), # (formatted_text, results_list)
    "rag_context": "",
    "booking_result": None,     # dict or None -> use DEFAULT_BOOKING_RESULT
    "reschedule_result": None,
    "cancel_result": None,
}

DEFAULT_BOOKING_RESULT = {
    "success": True,
    "appointment": {
        "appointment_id": "APT-TEST",
        "meeting_time": "Sunday, 09 August 2026 at 05:00 PM",
        "assigned_employee": "Test Agent",
        "calendar_event_id": "evt-test",
    },
    "error": None,
    "reason": None,
}


def reset_script():
    _script["chat_responses"].clear()
    _script["slot_updates"].clear()
    _script["availability"] = True
    _script["search_results"] = ("", [])
    _script["rag_context"] = ""
    _script["booking_result"] = None
    _script["reschedule_result"] = None
    _script["cancel_result"] = None


def queue_chat_response(text: str):
    _script["chat_responses"].append(text)


def queue_slot_update(updates: dict):
    _script["slot_updates"].append(updates)


def set_availability(available: bool):
    _script["availability"] = available


def set_search_results(formatted_text: str, results: list):
    _script["search_results"] = (formatted_text, results)


def set_rag_context(text: str):
    _script["rag_context"] = text


def set_booking_result(result: dict | None):
    _script["booking_result"] = result


def set_reschedule_result(result: dict | None):
    _script["reschedule_result"] = result


def set_cancel_result(result: dict | None):
    _script["cancel_result"] = result


# ---------------------------------------------------------------------------
# Wire the fakes into the real modules.
# ---------------------------------------------------------------------------

def _fake_generate_chat_response(messages, temperature=None, max_tokens=None):
    if _script["chat_responses"]:
        return _script["chat_responses"].pop(0)
    return "Ji bilkul."


def _fake_extract_json(system_prompt, temperature=None, max_tokens=None):
    if _script["slot_updates"]:
        return _script["slot_updates"].pop(0)
    return {}


def install_function_mocks():
    """
    Call this once per test module (after install_sdk_stubs / real imports
    above). Re-callable safely between tests within a module.
    """
    llm_client.generate_chat_response = _fake_generate_chat_response
    llm_client.extract_json = _fake_extract_json
    slot_extractor_mod.extract_json = _fake_extract_json
    appt_intent_mod.extract_json = _fake_extract_json

    biz_tools.search_property = lambda state: _script["search_results"]
    biz_tools.lookup_current_property = lambda state: ""
    biz_tools.rag_search = lambda query: _script["rag_context"]
    biz_tools.check_availability = lambda date, time_str: {
        "available": _script["availability"], "error": None
    }
    biz_tools.book_appointment_tool = lambda **kwargs: dict(
        _script["booking_result"] or DEFAULT_BOOKING_RESULT
    )
    biz_tools.reschedule_appointment_tool = lambda **kwargs: dict(
        _script["reschedule_result"] or DEFAULT_BOOKING_RESULT
    )
    biz_tools.cancel_appointment_tool = lambda **kwargs: dict(
        _script["cancel_result"]
        or {"success": True, "appointment": {"status": "cancelled"}, "error": None, "reason": None}
    )


install_function_mocks()


def run_turn(session_id: str, message: str):
    """Convenience wrapper: run one turn through the REAL graph."""
    return handle_turn(session_id, message)


def fresh_session(session_id: str):
    memory_store.reset(session_id)
    appt_intent_mod.clear_pending(session_id)
    return memory_store.get_or_create(session_id)


def seed_appointment_details(session_id: str, details: dict):
    """
    Directly seeds appointment_intent's per-session pending-details store,
    bypassing the (mocked) LLM extraction entirely. Use this in tests
    that need extract_appointment_details_node to see specific
    client_name/phone/property/date/time values -- the shared
    slot_updates queue used for buyer-preference extraction is a
    SEPARATE mechanism (slot_extractor.py's SLOT_EXTRACTION_PROMPT has a
    different schema than appointment_intent.py's
    APPOINTMENT_EXTRACTION_PROMPT), so queue_slot_update() alone does
    NOT populate appointment details.
    """
    appt_intent_mod._pending_details[session_id] = dict(details)
