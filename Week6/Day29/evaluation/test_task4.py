from src.nodes import (
    prediction_node,
    validation_node,
    clarification_node,
    unsupported_node,
)


def test_unsupported_prediction():

    print("=" * 70)
    print("TEST: Unsupported prediction")

    state = {
        "user_query": "Predict player injury risk",
        "conversation_history": [],
        "intent": "prediction",
        "prediction_input": {
            "prediction_type": "unsupported",
        },
    }

    state = prediction_node(state)

    print("\nAfter prediction_node:")
    print("TOOL RESULT:", state.get("tool_result"))
    print("ERROR:", state.get("error"))
    print("ERROR TYPE:", state.get("error_type"))

    state = validation_node(state)

    print("\nAfter validation_node:")
    print("VALIDATION:", state.get("validation_result"))
    print("VALIDATION ERROR:", state.get("validation_error"))

    state = unsupported_node(state)

    print("\nFINAL RESPONSE:")
    print(state["final_response"])


def test_missing_prediction_information():

    print("=" * 70)
    print("TEST: Missing prediction information")

    state = {
        "user_query": "Who will win?",
        "conversation_history": [],
        "intent": "prediction",
        "prediction_input": None,
    }

    state = prediction_node(state)

    print("\nAfter prediction_node:")
    print("TOOL RESULT:", state.get("tool_result"))
    print("ERROR:", state.get("error"))
    print("ERROR TYPE:", state.get("error_type"))

    state = validation_node(state)

    print("\nAfter validation_node:")
    print("VALIDATION:", state.get("validation_result"))
    print("VALIDATION ERROR:", state.get("validation_error"))

    state = clarification_node(state)

    print("\nFINAL RESPONSE:")
    print(state["final_response"])


if __name__ == "__main__":
    test_unsupported_prediction()
    test_missing_prediction_information()