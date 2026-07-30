from src.nodes import (
    prediction_node,
    validation_node,
    clarification_node,
)


def run_test(name, initial_state):
    print("=" * 70)
    print(f"TEST: {name}")

    # ---------------------------------------------------------------
    # Prediction node
    # ---------------------------------------------------------------

    state = prediction_node(initial_state)

    print("\nAfter prediction_node:")
    print("TOOL RESULT:", state.get("tool_result"))
    print("ERROR:", state.get("error"))

    # ---------------------------------------------------------------
    # Validation node
    # ---------------------------------------------------------------

    state = validation_node(state)

    print("\nAfter validation_node:")
    print("VALIDATION:", state.get("validation_result"))
    print("VALIDATION ERROR:", state.get("validation_error"))

    # ---------------------------------------------------------------
    # Clarification path
    # ---------------------------------------------------------------

    if state.get("validation_result") == "clarification_needed":
        state = clarification_node(state)

    print("\nFINAL RESPONSE:")
    print(state.get("final_response"))


# -------------------------------------------------------------------
# Test 1: Unsupported prediction type
# -------------------------------------------------------------------

unsupported_prediction = {
    "user_query": "How many goals will Collingwood score?",
    "conversation_history": [],
    "intent": "prediction",
    "prediction_input": {
        "prediction_type": "unsupported",
    },
}


# -------------------------------------------------------------------
# Test 2: Missing prediction information
# -------------------------------------------------------------------

missing_prediction_information = {
    "user_query": "Who will win?",
    "conversation_history": [],
    "intent": "prediction",
}


if __name__ == "__main__":

    run_test(
        "Unsupported prediction",
        unsupported_prediction,
    )

    run_test(
        "Missing prediction information",
        missing_prediction_information,
    )