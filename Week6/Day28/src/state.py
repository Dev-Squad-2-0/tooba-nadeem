from typing import Any, Literal, TypedDict


Intent = Literal[
    "factual",
    "retrieval",
    "prediction",
    "off_topic",
]


class AgentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph nodes.
    """

    # ---------------------------------------------------------
    # User / conversation
    # ---------------------------------------------------------

    user_query: str
    conversation_history: list[dict[str, Any]]

    # ---------------------------------------------------------
    # Routing
    # ---------------------------------------------------------

    intent: Intent

    # ---------------------------------------------------------
    # Prediction
    # ---------------------------------------------------------

    prediction_type: str | None
    prediction_input: dict[str, Any] | None
    resolved_entities: dict[str, Any] | None

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    retrieval_input: dict[str, Any] | None

    # ---------------------------------------------------------
    # Tool execution
    # ---------------------------------------------------------

    tool_result: Any
    error: str | None

    # ---------------------------------------------------------
    # Validation / errors
    # ---------------------------------------------------------

    validation_result: str | None
    validation_error: str | None

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------

    final_response: str | None