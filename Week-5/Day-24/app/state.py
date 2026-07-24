"""
Shared state that flows through every node in the LangGraph graph.

Kept as a plain TypedDict (LangGraph's native state format) rather than a
Pydantic model inside the graph itself, because LangGraph merges partial
dict updates between nodes; the API layer converts to/from Pydantic at the
boundary (see api/schemas.py) so external clients still get validation.
"""
from typing import Any, Optional, TypedDict


class TicketState(TypedDict, total=False):
    # --- input ---
    ticket_id: str
    customer_email: str
    subject: str
    description: str

    # --- validation ---
    is_valid: bool
    validation_errors: list[str]

    # --- classification ---
    project_key: str
    project_display_name: str
    project_confidence: float
    issue_category: str
    priority: str
    classification_source: str  # "llm" or "rule_based_fallback"

    # --- routing ---
    department: str
    escalation_contact: str

    # --- retrieval ---
    faq_matches: list[dict[str, Any]]

    # --- response drafting ---
    draft_response: str

    # --- human-in-the-loop ---
    requires_human_approval: bool
    approval_status: Optional[str]  # None | "pending" | "approved" | "rejected"
    reviewer_notes: Optional[str]

    # --- output ---
    final_response: Optional[str]
    status: str  # "rejected_invalid_input" | "pending_human_review" | "resolved"

    # --- observability (not shown to the customer) ---
    errors: list[str]
    warnings: list[str]
    trace: list[dict[str, Any]]  # per-node timing/model-used log for this run
