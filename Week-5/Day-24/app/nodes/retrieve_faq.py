import time

from app.state import TicketState
from app.tools.faq_tool import retrieve_faq as retrieve_faq_tool


def retrieve_faq(state: TicketState) -> dict:
    start = time.monotonic()
    ticket_text = f"{state.get('subject', '')}\n{state.get('description', '')}"
    matches = retrieve_faq_tool(ticket_text, state.get("project_key", "general"))
    latency_ms = round((time.monotonic() - start) * 1000, 1)

    return {
        "faq_matches": matches,
        "trace": state.get("trace", []) + [{
            "node": "retrieve_faq", "matches_found": len(matches), "latency_ms": latency_ms,
        }],
    }
