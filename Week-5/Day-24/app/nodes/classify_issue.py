import logging
import time

from app.state import TicketState
from app.logging_config import log_event
from app.tools import classifier_rules
from app.tools.llm_client import LLMError, chat_completion

logger = logging.getLogger("triage_agent.nodes.classify_issue")

_VALID_CATEGORIES = {
    "refund", "billing_dispute", "account_recovery",
    "technical_issue", "general_inquiry", "security_incident",
}

_SYSTEM_PROMPT = (
    "You classify a Web3Geeks support ticket's issue type. Reply with ONLY "
    "one lowercase_snake_case label from: " + ", ".join(sorted(_VALID_CATEGORIES)) +
    ". Reply with nothing else."
)


def classify_issue(state: TicketState) -> dict:
    start = time.monotonic()
    ticket_text = f"{state.get('subject', '')}\n{state.get('description', '')}"
    warnings = list(state.get("warnings", []))
    source = "llm"

    try:
        result = chat_completion(_SYSTEM_PROMPT, ticket_text)
        candidate = result.text.strip().lower()
        if candidate not in _VALID_CATEGORIES:
            raise LLMError(f"Model returned unrecognized issue category: '{candidate}'")
        issue_category = candidate
        if result.degraded:
            warnings.append(f"classify_issue: used fallback model '{result.model_used}'")
    except LLMError as exc:
        logger.warning("classify_issue falling back to rule-based classifier: %s", exc)
        warnings.append(f"classify_issue: LLM path failed ({exc}); used rule-based fallback")
        issue_category = classifier_rules.classify_issue(ticket_text)
        source = "rule_based_fallback"

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    log_event(
        logger, "classify_issue",
        ticket_id=state.get("ticket_id"), issue_category=issue_category,
        source=source, latency_ms=latency_ms,
    )

    return {
        "issue_category": issue_category,
        "warnings": warnings,
        "trace": state.get("trace", []) + [{
            "node": "classify_issue", "source": source,
            "issue_category": issue_category, "latency_ms": latency_ms,
        }],
    }
