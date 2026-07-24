import time

from app.state import TicketState


def finalize_resolved(state: TicketState) -> dict:
    return {
        "final_response": state.get("draft_response"),
        "status": "resolved",
        "trace": state.get("trace", []) + [{"node": "finalize_resolved"}],
    }


def finalize_rejected_by_reviewer(state: TicketState) -> dict:
    notes = state.get("reviewer_notes") or "No additional notes provided."
    message = (
        "Thank you for your patience. After review, our team was not able to "
        "action this request as submitted. "
        f"Reviewer notes: {notes} Please reply if you have further "
        "documentation or would like to escalate."
    )
    return {
        "final_response": message,
        "status": "rejected_by_reviewer",
        "trace": state.get("trace", []) + [{"node": "finalize_rejected_by_reviewer"}],
    }


def finalize_invalid_input(state: TicketState) -> dict:
    errors = "; ".join(state.get("validation_errors", []))
    message = (
        "We couldn't process this ticket automatically: "
        f"{errors}. Please resubmit with the missing/corrected information."
    )
    return {
        "final_response": message,
        "status": "rejected_invalid_input",
        "trace": state.get("trace", []) + [{"node": "finalize_invalid_input"}],
    }
