from src.graph import app

# -------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "Factual AFL question",
        "query": "Who is Nick Daicos?",
        "expected_intent": "factual",
    },
    {
        "name": "Factual AFL rules question",
        "query": "What is a behind in AFL?",
        "expected_intent": "factual",
    },
    {
        "name": "Retrieval request",
        "query": "What were Nick Daicos' stats last round?",
        "expected_intent": "retrieval",
    },
    {
        "name": "Retrieval failure",
        "query": "What were the stats for Definitely Not A Real AFL Player?",
        "expected_intent": "retrieval",
    },
    {
        "name": "Match prediction",
        "query": "Will Collingwood beat Geelong this week?",
        "expected_intent": "prediction",
    },
    {
        "name": "Top-player prediction",
        "query": "Who will be the top fantasy player in the Collingwood game?",
        "expected_intent": "prediction",
    },
    {
        "name": "Unsupported prediction",
        "query": "Predict the exact number of goals each player will score.",
        "expected_intent": "prediction",
    },
    {
        "name": "Missing information",
        "query": "Who will win the next match?",
        "expected_intent": "prediction",
    },
    {
        "name": "Off-topic request",
        "query": "What is the weather in Islamabad?",
        "expected_intent": "off_topic",
    },
    {
        "name": "Follow-up conversation",
        "query": "What were his stats last round?",
        "expected_intent": "retrieval",
        "conversation_history": [
            {
                "role": "user",
                "content": "Tell me about Nick Daicos.",
            },
            {
                "role": "assistant",
                "content": "Nick Daicos is an AFL player for Collingwood.",
            },
        ],
    },
]


# -------------------------------------------------------------------
# Run one test
# -------------------------------------------------------------------

def run_test(test_case: dict) -> dict:

    print("=" * 70)
    print(f"TEST: {test_case['name']}")
    print(f"QUERY: {test_case['query']}")

    expected_intent = test_case["expected_intent"]

    initial_state = {
        "user_query": test_case["query"],
        "conversation_history": test_case.get(
            "conversation_history",
            [],
        ),
    }

    try:

        result = app.invoke(initial_state)

        actual_intent = result.get("intent")
        validation = result.get("validation_result")
        validation_error = result.get("validation_error")
        response = result.get("final_response")
        error = result.get("error")

        # -----------------------------------------------------------
        # Intent check
        # -----------------------------------------------------------

        intent_pass = actual_intent == expected_intent

        print(f"EXPECTED INTENT:  {expected_intent}")
        print(f"ACTUAL INTENT:    {actual_intent}")

        if intent_pass:
            print("ROUTING STATUS:   PASS")
        else:
            print("ROUTING STATUS:   FAIL")

        # -----------------------------------------------------------
        # Validation / response information
        # -----------------------------------------------------------

        print(f"VALIDATION:       {validation}")
        print(f"VALIDATION ERROR: {validation_error}")
        print(f"ERROR:            {error}")
        print(f"RESPONSE:         {response}")

        return {
            "name": test_case["name"],
            "query": test_case["query"],
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "validation": validation,
            "validation_error": validation_error,
            "response": response,
            "error": error,
            "passed": intent_pass,
        }

    except Exception as exc:

        print(f"ERROR: {type(exc).__name__}: {exc}")

        return {
            "name": test_case["name"],
            "query": test_case["query"],
            "expected_intent": expected_intent,
            "actual_intent": None,
            "validation": None,
            "validation_error": None,
            "response": None,
            "error": f"{type(exc).__name__}: {exc}",
            "passed": False,
        }


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

if __name__ == "__main__":

    results = []

    for test_case in TEST_CASES:
        result = run_test(test_case)
        results.append(result)

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("END-TO-END TEST SUMMARY")
    print("=" * 70)

    passed = 0
    failed = 0

    for index, result in enumerate(results, start=1):

        if result["passed"]:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(
            f"{index:02d}. "
            f"{result['name']} | "
            f"expected={result['expected_intent']} | "
            f"actual={result['actual_intent']} | "
            f"{status}"
        )

    # ---------------------------------------------------------------
    # Overall result
    # ---------------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("OVERALL RESULT")
    print("=" * 70)

    print(f"TOTAL TESTS: {len(results)}")
    print(f"PASSED:      {passed}")
    print(f"FAILED:      {failed}")

    if failed == 0:
        print("STATUS: ALL TESTS PASSED")
    else:
        print("STATUS: SOME TESTS FAILED")

        print("\nNOTE:")
        print(
            "If the LLM router is unavailable because of an API "
            "rate limit, the router may fall back to off_topic. "
            "In that case, routing failures do not necessarily "
            "indicate a problem with the LangGraph structure."
        )