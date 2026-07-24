import logging
import time

from app.config import SENSITIVE_ISSUE_CATEGORIES
from app.state import TicketState
from app.logging_config import log_event
from app.tools import classifier_rules
from app.tools.llm_client import LLMError, chat_completion

logger = logging.getLogger("triage_agent.nodes.prioritize_and_route")

_VALID_PRIORITIES = {"low", "medium", "high", "urgent"}

_SYSTEM_PROMPT = (
    "You assign a priority to a Web3Geeks support ticket given its issue "
    "category. Reply with ONLY one word from: low, medium, high, urgent. "
    "Financial loss, security, or account-lockout issues are usually high "
    "or urgent. Reply with nothing else."
)


def prioritize_and_route(state: TicketState) -> dict:
    """Combines priority scoring + department routing + the human-checkpoint
    decision, since all three depend only on (issue_category, project_key)
    and keeping them in one node avoids an extra LLM round-trip."""
    start = time.monotonic()
    ticket_text = f"{state.get('subject', '')}\n{state.get('description', '')}"
    issue_category = state.get("issue_category", "general_inquiry")
    warnings = list(state.get("warnings", []))
    source = "llm"

    try:
        result = chat_completion(_SYSTEM_PROMPT, f"issue_category={issue_category}\n{ticket_text}")
        candidate = result.text.strip().lower()
        if candidate not in _VALID_PRIORITIES:
            raise LLMError(f"Model returned unrecognized priority: '{candidate}'")
        priority = candidate
        if result.degraded:
            warnings.append(f"prioritize: used fallback model '{result.model_used}'")
    except LLMError as exc:
        logger.warning("prioritize falling back to rule-based scoring: %s", exc)
        warnings.append(f"prioritize: LLM path failed ({exc}); used rule-based fallback")
        priority = classifier_rules.determine_priority(ticket_text, issue_category)
        source = "rule_based_fallback"

    department, escalation_contact = classifier_rules.get_department(state.get("project_key", "general"))
    requires_human_approval = issue_category in SENSITIVE_ISSUE_CATEGORIES

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    log_event(
        logger, "prioritize_and_route",
        ticket_id=state.get("ticket_id"), priority=priority, department=department,
        requires_human_approval=requires_human_approval, source=source, latency_ms=latency_ms,
    )

    return {
        "priority": priority,
        "department": department,
        "escalation_contact": escalation_contact,
        "requires_human_approval": requires_human_approval,
        "approval_status": "pending" if requires_human_approval else None,
        "warnings": warnings,
        "trace": state.get("trace", []) + [{
            "node": "prioritize_and_route", "source": source, "priority": priority,
            "department": department, "requires_human_approval": requires_human_approval,
            "latency_ms": latency_ms,
        }],
    }
