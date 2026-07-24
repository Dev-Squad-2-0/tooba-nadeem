"""
Graph topology:

    validate_input
        --(invalid)--> finalize_invalid_input --> END
        --(valid)---> identify_project
                            -> classify_issue
                                -> prioritize_and_route
                                    -> retrieve_faq
                                        -> draft_response
                                            -> await_human_approval  [INTERRUPT before this node
                                                                      when requires_human_approval]
                                                --(approved)--> finalize_resolved --> END
                                                --(rejected)--> finalize_rejected_by_reviewer --> END

Why LangGraph for this pipeline specifically: the workflow is a fixed
sequence of deterministic decisions (validate -> classify -> route -> draft)
with exactly one conditional branch point and one human checkpoint -- there
is no need for multiple LLM personas negotiating a plan, which is what
CrewAI's role-based crews are for. LangGraph's explicit state graph gives us
first-class support for the two things this project actually needs:
conditional routing and pause/resume around a human approval gate via a
checkpointer -- with a fully typed, inspectable state object at every step
for logging and evaluation.
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.nodes.classify_issue import classify_issue
from app.nodes.draft_response import draft_response
from app.nodes.finalize import (
    finalize_invalid_input,
    finalize_rejected_by_reviewer,
    finalize_resolved,
)
from app.nodes.human_approval import await_human_approval, route_after_approval
from app.nodes.identify_project import identify_project
from app.nodes.prioritize_and_route import prioritize_and_route
from app.nodes.retrieve_faq import retrieve_faq
from app.nodes.validate import route_after_validation, validate_input
from app.state import TicketState


def _route_after_prioritize(state: TicketState) -> str:
    """Skip the interrupt node entirely for non-sensitive tickets so they
    resolve in a single graph run with no human wait."""
    return "needs_approval" if state.get("requires_human_approval") else "auto_resolve"


def build_graph():
    graph = StateGraph(TicketState)

    graph.add_node("validate_input", validate_input)
    graph.add_node("identify_project", identify_project)
    graph.add_node("classify_issue", classify_issue)
    graph.add_node("prioritize_and_route", prioritize_and_route)
    graph.add_node("retrieve_faq", retrieve_faq)
    graph.add_node("draft_response_node", draft_response)
    graph.add_node("await_human_approval", await_human_approval)
    graph.add_node("finalize_resolved", finalize_resolved)
    graph.add_node("finalize_rejected_by_reviewer", finalize_rejected_by_reviewer)
    graph.add_node("finalize_invalid_input", finalize_invalid_input)

    graph.set_entry_point("validate_input")

    graph.add_conditional_edges(
        "validate_input", route_after_validation,
        {"continue": "identify_project", "reject": "finalize_invalid_input"},
    )
    graph.add_edge("identify_project", "classify_issue")
    graph.add_edge("classify_issue", "prioritize_and_route")

    graph.add_conditional_edges(
        "prioritize_and_route", _route_after_prioritize,
        {"needs_approval": "retrieve_faq", "auto_resolve": "retrieve_faq"},
    )
    # Both branches go through retrieve_faq/draft_response first so the
    # human reviewer sees a drafted response to approve/edit, rather than
    # approving a blank ticket.
    graph.add_edge("retrieve_faq", "draft_response_node")

    graph.add_conditional_edges(
        "draft_response_node",
        lambda s: "gate" if s.get("requires_human_approval") else "skip_gate",
        {"gate": "await_human_approval", "skip_gate": "finalize_resolved"},
    )

    graph.add_conditional_edges(
        "await_human_approval", route_after_approval,
        {"approved": "finalize_resolved", "rejected": "finalize_rejected_by_reviewer"},
    )

    graph.add_edge("finalize_resolved", END)
    graph.add_edge("finalize_rejected_by_reviewer", END)
    graph.add_edge("finalize_invalid_input", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer, interrupt_before=["await_human_approval"])


# Module-level singleton -- the checkpointer holds in-memory conversation
# state keyed by thread_id (== ticket_id), so it must be shared across
# requests within the process. Swap MemorySaver for a persistent
# checkpointer (e.g. SqliteSaver) before running multiple worker processes.
compiled_graph = build_graph()
