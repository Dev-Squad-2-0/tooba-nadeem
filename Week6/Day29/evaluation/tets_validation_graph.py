from src.graph import build_graph


def test_success_path():
    """
    Test that successful validation reaches the response node.
    """

    graph = build_graph()

    state = {
        "user_query": "test",
        "conversation_history": [],
        "intent": "prediction",
        "tool_result": {
            "predicted_winner": "Sydney Swans",
            "home_team": "Sydney Swans",
            "away_team": "Hawthorn Hawks",
            "home_win_probability": 0.60,
            "away_win_probability": 0.40,
        },
        "error": "",
        "validation_result": "success",
        "validation_error": None,
    }

    print("=" * 70)
    print("SUCCESS PATH")

    result = graph.invoke(state)

    print("VALIDATION:", result.get("validation_result"))
    print("FINAL RESPONSE:", result.get("final_response"))


def test_failure_path():
    """
    Test that failed validation reaches clarification.
    """

    graph = build_graph()

    state = {
        "user_query": "test",
        "conversation_history": [],
        "intent": "prediction",
        "tool_result": None,
        "error": "This prediction type is not currently supported.",
        "validation_result": "clarification_needed",
        "validation_error": "This prediction type is not currently supported.",
    }

    print("=" * 70)
    print("FAILURE PATH")

    result = graph.invoke(state)

    print("VALIDATION:", result.get("validation_result"))
    print("VALIDATION ERROR:", result.get("validation_error"))
    print("FINAL RESPONSE:", result.get("final_response"))


if __name__ == "__main__":
    test_success_path()
    test_failure_path()