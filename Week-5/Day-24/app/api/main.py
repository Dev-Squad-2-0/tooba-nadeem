import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas import ApprovalDecision, TicketResponse, TicketSubmission, state_to_response
from app.graph import compiled_graph
from app.logging_config import log_event, setup_logging

setup_logging()
logger = logging.getLogger("triage_agent.api")

app = FastAPI(
    title="Web3Geeks Intelligent Support Triage Agent",
    description="Routes, prioritizes, and drafts responses for incoming support tickets across all Web3Geeks products.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketResponse)
def submit_ticket(payload: TicketSubmission) -> TicketResponse:
    ticket_id = str(uuid.uuid4())
    start = time.monotonic()

    initial_state = {
        "ticket_id": ticket_id,
        "customer_email": payload.customer_email,
        "subject": payload.subject,
        "description": payload.description,
        "trace": [],
        "warnings": [],
        "errors": [],
        "status": "",
        "approval_status": None,
    }
    config = {"configurable": {"thread_id": ticket_id}}

    try:
        result_state = compiled_graph.invoke(initial_state, config=config)
    except Exception as exc:  # noqa: BLE001 -- last-resort guard so a bug in
        # one node never surfaces as a raw 500 with a stack trace to the client.
        logger.exception("Unhandled error processing ticket %s", ticket_id)
        raise HTTPException(status_code=500, detail="Internal error processing ticket. Support has been notified.") from exc

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    log_event(
        logger, "ticket_submitted",
        ticket_id=ticket_id, status=result_state.get("status"),
        requires_human_approval=result_state.get("requires_human_approval", False),
        latency_ms=latency_ms,
    )

    # If the graph paused at the interrupt, status won't have been set by a
    # finalize node yet -- reflect that explicitly to the caller.
    if not result_state.get("status"):
        result_state["status"] = "pending_human_review"

    return state_to_response(ticket_id, result_state)


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str) -> TicketResponse:
    config = {"configurable": {"thread_id": ticket_id}}
    snapshot = compiled_graph.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Ticket not found")

    state = dict(snapshot.values)
    if not state.get("status"):
        state["status"] = "pending_human_review"
    return state_to_response(ticket_id, state)


@app.post("/tickets/{ticket_id}/approve", response_model=TicketResponse)
def approve_ticket(ticket_id: str, decision: ApprovalDecision) -> TicketResponse:
    """Resumes a graph run that is paused at the human-approval checkpoint."""
    config = {"configurable": {"thread_id": ticket_id}}
    snapshot = compiled_graph.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if snapshot.next != ("await_human_approval",):
        raise HTTPException(status_code=409, detail="Ticket is not currently awaiting human approval")

    compiled_graph.update_state(config, {
        "approval_status": "approved" if decision.approved else "rejected",
        "reviewer_notes": decision.reviewer_notes,
    })
    result_state = compiled_graph.invoke(None, config=config)

    log_event(
        logger, "ticket_approval_decision",
        ticket_id=ticket_id, approved=decision.approved, final_status=result_state.get("status"),
    )
    return state_to_response(ticket_id, result_state)
