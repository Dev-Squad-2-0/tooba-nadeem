import logging
import time

from app.logging_config import log_event
from app.state import TicketState

logger = logging.getLogger("triage_agent.nodes.human_approval")


def await_human_approval(state: TicketState) -> dict:
    """
    Human-in-the-loop checkpoint for consequential actions (refund,
    billing_dispute, account_recovery, security_incident).

    The graph is compiled with interrupt_before=["await_human_approval"], so
    execution physically pauses BEFORE this node runs and the partial state
    is returned to the API caller with status="pending_human_review". This
    function body only runs on RESUME, after a human has set
    approval_status to "approved" or "rejected" via the /approve endpoint.
    """
    start = time.monotonic()
    approval_status = state.get("approval_status")

    log_event(
        logger, "human_approval_resumed",
        ticket_id=state.get("ticket_id"), approval_status=approval_status,
    )

    return {
        "trace": state.get("trace", []) + [{
            "node": "await_human_approval", "approval_status": approval_status,
            "latency_ms": round((time.monotonic() - start) * 1000, 1),
        }],
    }


def route_after_approval(state: TicketState) -> str:
    """Conditional edge evaluated on resume."""
    status = state.get("approval_status")
    if status == "approved":
        return "approved"
    if status == "rejected":
        return "rejected"
    return "approved"  # non-sensitive tickets never enter this node at all
