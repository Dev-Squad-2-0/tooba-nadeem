"""
app/graph/build_graph.py
---------------------------

Builds and compiles the LangGraph StateGraph.

Correctness note: availability_check has exactly ONE
add_conditional_edges() call. LangGraph only honors one routing
registration per source node — calling it twice on the same node does
not "add more branches," it silently drops one or causes unreliable
double-execution. nodes._route_after_availability makes BOTH decisions
(available/unavailable, and if available, booking vs reschedule) in one
routing function.
"""

from langgraph.graph import StateGraph, END

from app.graph.graph_state import GraphState
from app.graph import nodes


def build_graph():
    graph = StateGraph(GraphState)

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------
    graph.add_node("load_state", nodes.load_state_node)
    graph.add_node("intent_detection", nodes.intent_detection_node)

    graph.add_node("recommendation", nodes.recommendation_node)
    graph.add_node("rag", nodes.rag_node)

    graph.add_node("extract_appointment_details", nodes.extract_appointment_details_node)
    graph.add_node("check_missing_fields", nodes.check_missing_fields_node)
    graph.add_node("ask_clarification", nodes.clarification_node)
    graph.add_node("availability_check", nodes.availability_check_node)
    graph.add_node("slot_unavailable", nodes.unavailable_node)

    graph.add_node("booking", nodes.booking_node)
    graph.add_node("reschedule", nodes.reschedule_node)
    graph.add_node("cancellation", nodes.cancellation_node)

    graph.add_node("greeting", nodes.greeting_node)
    graph.add_node("goodbye", nodes.goodbye_node)

    graph.add_node("response_generation", nodes.response_generation_node)

    # --------------------------------------------------
    # Entry
    # --------------------------------------------------
    graph.set_entry_point("load_state")
    graph.add_edge("load_state", "intent_detection")

    # --------------------------------------------------
    # Top-level routing by intent (ONE registration on "intent_detection")
    # --------------------------------------------------
    graph.add_conditional_edges(
        "intent_detection",
        nodes.route_by_intent,
        {
            "general_question": "rag",
            "property_search": "recommendation",
            "booking": "extract_appointment_details",
            "reschedule": "extract_appointment_details",
            "cancellation": "extract_appointment_details",
            "greeting": "greeting",
            "goodbye": "goodbye",
        },
    )

    # Property search: recommendation, then RAG for supplementary
    # grounding, then respond. Static edges — always this order.
    graph.add_edge("recommendation", "rag")
    graph.add_edge("rag", "response_generation")

    # --------------------------------------------------
    # Appointment sub-flow (ONE registration on "check_missing_fields")
    # --------------------------------------------------
    graph.add_edge("extract_appointment_details", "check_missing_fields")

    graph.add_conditional_edges(
        "check_missing_fields",
        nodes.route_after_missing_check,
        {
            "ask_clarification": "ask_clarification",
            "availability_check": "availability_check",
            "cancellation": "cancellation",
        },
    )

    # ONE registration on "availability_check".
    graph.add_conditional_edges(
        "availability_check",
        nodes._route_after_availability,
        {
            "booking": "booking",
            "reschedule": "reschedule",
            "unavailable": "slot_unavailable",
        },
    )

    graph.add_edge("booking", "response_generation")
    graph.add_edge("reschedule", "response_generation")
    graph.add_edge("cancellation", "response_generation")
    graph.add_edge("slot_unavailable", "response_generation")
    graph.add_edge("ask_clarification", "response_generation")

    graph.add_edge("greeting", "response_generation")
    graph.add_edge("goodbye", "response_generation")

    graph.add_edge("response_generation", END)

    return graph.compile()
