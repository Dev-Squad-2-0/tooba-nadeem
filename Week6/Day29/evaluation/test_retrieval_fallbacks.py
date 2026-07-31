from src.nodes import (
    retrieval_node,
    validation_node,
    clarification_node,
)


def test_missing_player():

    print("=" * 70)
    print("TEST: Missing player")

    state = {
        "user_query": "Show me this player's stats.",
        "conversation_history": [],
        "intent": "retrieval",
        "retrieval_input": {
            "retrieval_type": "player_match",
            "player_name": "Definitely Not A Real AFL Player",
            "season": 2026,
            "round_number": 18,
        },
    }

    state = retrieval_node(state)

    print("\nAfter retrieval_node:")
    print("TOOL RESULT:", state.get("tool_result"))
    print("ERROR:", state.get("error"))

    state = validation_node(state)

    print("\nAfter validation_node:")
    print("VALIDATION:", state.get("validation_result"))
    print("VALIDATION ERROR:", state.get("validation_error"))

    if state.get("validation_result") == "clarification_needed":
        state = clarification_node(state)

    print("\nFINAL RESPONSE:")
    print(state["final_response"])


def test_missing_retrieval_information():

    print("=" * 70)
    print("TEST: Missing retrieval information")

    state = {
        "user_query": "Show me the player's stats.",
        "conversation_history": [],
        "intent": "retrieval",
        "retrieval_input": None,
    }

    state = retrieval_node(state)

    print("\nAfter retrieval_node:")
    print("TOOL RESULT:", state.get("tool_result"))
    print("ERROR:", state.get("error"))

    state = validation_node(state)

    print("\nAfter validation_node:")
    print("VALIDATION:", state.get("validation_result"))
    print("VALIDATION ERROR:", state.get("validation_error"))

    if state.get("validation_result") == "clarification_needed":
        state = clarification_node(state)

    print("\nFINAL RESPONSE:")
    print(state["final_response"])


if __name__ == "__main__":
    test_missing_player()
    test_missing_retrieval_information()