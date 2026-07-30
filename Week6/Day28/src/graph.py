from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .nodes import (
    router_node,
    factual_node,
    retrieval_node,
    prediction_node,
    off_topic_node,
    validation_node,
    response_node,
    clarification_node,
    unsupported_node,
)


# -------------------------------------------------------------------
# Routing function
# -------------------------------------------------------------------

def route_by_intent(state: AgentState) -> str:
    """
    Decide which branch of the graph should execute based on
    the router's classification.
    """

    intent = state.get("intent")

    if intent == "factual":
        return "factual"

    if intent == "retrieval":
        return "retrieval"

    if intent == "prediction":
        return "prediction"

    if intent == "off_topic":
        return "off_topic"

    return "off_topic"


# -------------------------------------------------------------------
# Validation routing function
# -------------------------------------------------------------------

def route_after_validation(state: AgentState) -> str:
    """
    Decide what should happen after validation.

    Successful results continue to the normal response node.
    Missing or ambiguous information goes to clarification.
    Unsupported requests go to the unsupported-response node.
    """

    validation_result = state.get("validation_result")

    if validation_result == "success":
        return "response"

    if validation_result == "clarification_needed":
        return "clarification"

    if validation_result == "unsupported":
        return "unsupported"

    # Safe fallback
    return "clarification"


# -------------------------------------------------------------------
# Build graph
# -------------------------------------------------------------------

def build_graph():
    """
    Build the complete AFL LangGraph workflow.
    """

    graph = StateGraph(AgentState)

    # ---------------------------------------------------------------
    # Add nodes
    # ---------------------------------------------------------------

    graph.add_node(
        "router",
        router_node,
    )

    graph.add_node(
        "factual",
        factual_node,
    )

    graph.add_node(
        "retrieval",
        retrieval_node,
    )

    graph.add_node(
        "prediction",
        prediction_node,
    )

    graph.add_node(
        "off_topic",
        off_topic_node,
    )

    graph.add_node(
        "validation",
        validation_node,
    )

    graph.add_node(
        "response",
        response_node,
    )

    graph.add_node(
        "clarification",
        clarification_node,
    )

    graph.add_node(
        "unsupported",
        unsupported_node,
    )

    # ---------------------------------------------------------------
    # Entry point
    # ---------------------------------------------------------------

    graph.add_edge(
        START,
        "router",
    )

    # ---------------------------------------------------------------
    # Router branching
    # ---------------------------------------------------------------

    graph.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "factual": "factual",
            "retrieval": "retrieval",
            "prediction": "prediction",
            "off_topic": "off_topic",
        },
    )

    # ---------------------------------------------------------------
    # All main branches converge on validation
    # ---------------------------------------------------------------

    graph.add_edge(
        "factual",
        "validation",
    )

    graph.add_edge(
        "retrieval",
        "validation",
    )

    graph.add_edge(
        "prediction",
        "validation",
    )

    graph.add_edge(
        "off_topic",
        "validation",
    )

    # ---------------------------------------------------------------
    # Validation branching
    # ---------------------------------------------------------------

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "response": "response",
            "clarification": "clarification",
            "unsupported": "unsupported",
        },
    )

    # ---------------------------------------------------------------
    # Successful response
    # ---------------------------------------------------------------

    graph.add_edge(
        "response",
        END,
    )

    # ---------------------------------------------------------------
    # Clarification response
    # ---------------------------------------------------------------

    graph.add_edge(
        "clarification",
        END,
    )

    # ---------------------------------------------------------------
    # Unsupported response
    # ---------------------------------------------------------------

    graph.add_edge(
        "unsupported",
        END,
    )

    return graph.compile()


# -------------------------------------------------------------------
# Ready-to-use graph
# -------------------------------------------------------------------

app = build_graph()


# -------------------------------------------------------------------
# Example
# -------------------------------------------------------------------

if __name__ == "__main__":

    result = app.invoke({
        "user_query": "Will Sydney beat Hawthorn?",
        "conversation_history": [],
    })

    print(result["final_response"])