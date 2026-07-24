import logging
import time

from app.state import TicketState
from app.logging_config import log_event
from app.tools.llm_client import LLMError, chat_completion

logger = logging.getLogger("triage_agent.nodes.draft_response")

_SYSTEM_PROMPT = (
    "You are a professional Web3Geeks support agent. Write a short (3-5 "
    "sentence), warm, factual reply to the customer's ticket using the "
    "provided FAQ context where relevant. Do not invent policies not in the "
    "FAQ context. Do not promise refunds or account changes yourself -- "
    "sensitive requests are already flagged separately for human review; "
    "just acknowledge the ticket and explain next steps."
)


def _template_fallback(state: TicketState) -> str:
    """Deterministic template used if the LLM draft fails outright. Ensures
    the customer always receives *some* professional acknowledgement rather
    than a stalled ticket."""
    faq_matches = state.get("faq_matches", [])
    lines = [
        f"Thank you for reaching out about {state.get('project_display_name', 'our platform')}.",
        f"Your ticket has been categorized as '{state.get('issue_category', 'general_inquiry')}' "
        f"and routed to {state.get('department', 'our support team')}.",
    ]
    if faq_matches:
        lines.append(f"In the meantime: {faq_matches[0]['answer']}")
    if state.get("requires_human_approval"):
        lines.append("Because this involves a sensitive account action, a specialist will review it before any changes are made.")
    else:
        lines.append("We'll follow up shortly if any further information is needed.")
    return " ".join(lines)


def draft_response(state: TicketState) -> dict:
    start = time.monotonic()
    warnings = list(state.get("warnings", []))
    source = "llm"

    faq_context = "\n".join(f"- {m['question']}: {m['answer']}" for m in state.get("faq_matches", []))
    user_prompt = (
        f"Project: {state.get('project_display_name')}\n"
        f"Issue category: {state.get('issue_category')}\n"
        f"Priority: {state.get('priority')}\n"
        f"Ticket subject: {state.get('subject')}\n"
        f"Ticket description: {state.get('description')}\n"
        f"FAQ context:\n{faq_context or '(none found)'}"
    )

    try:
        result = chat_completion(_SYSTEM_PROMPT, user_prompt)
        draft = result.text.strip()
        if result.degraded:
            warnings.append(f"draft_response: used fallback model '{result.model_used}'")
    except LLMError as exc:
        logger.warning("draft_response falling back to template: %s", exc)
        warnings.append(f"draft_response: LLM path failed ({exc}); used template fallback")
        draft = _template_fallback(state)
        source = "template_fallback"

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    log_event(
        logger, "draft_response",
        ticket_id=state.get("ticket_id"), source=source, latency_ms=latency_ms,
    )

    return {
        "draft_response": draft,
        "warnings": warnings,
        "trace": state.get("trace", []) + [{
            "node": "draft_response", "source": source, "latency_ms": latency_ms,
        }],
    }
