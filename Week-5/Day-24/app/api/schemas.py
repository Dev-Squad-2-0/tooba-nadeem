from typing import Any, Optional

from pydantic import BaseModel, Field


class TicketSubmission(BaseModel):
    customer_email: str = Field(..., examples=["alice@example.com"])
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=8000)


class TicketResponse(BaseModel):
    ticket_id: str
    status: str  # resolved | pending_human_review | rejected_invalid_input | rejected_by_reviewer
    project: Optional[str] = None
    issue_category: Optional[str] = None
    priority: Optional[str] = None
    department: Optional[str] = None
    requires_human_approval: bool = False
    draft_response: Optional[str] = None
    final_response: Optional[str] = None
    validation_errors: list[str] = []
    warnings: list[str] = []


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer_notes: Optional[str] = None


def state_to_response(ticket_id: str, state: dict[str, Any]) -> TicketResponse:
    return TicketResponse(
        ticket_id=ticket_id,
        status=state.get("status", "unknown"),
        project=state.get("project_display_name"),
        issue_category=state.get("issue_category"),
        priority=state.get("priority"),
        department=state.get("department"),
        requires_human_approval=state.get("requires_human_approval", False),
        draft_response=state.get("draft_response"),
        final_response=state.get("final_response"),
        validation_errors=state.get("validation_errors", []),
        warnings=state.get("warnings", []),
    )
