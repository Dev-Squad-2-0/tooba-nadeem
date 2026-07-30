from src.graph import app


TEST_QUERIES = [
    "Who is Nick Daicos?",
    "What were Nick Daicos' stats last round?",
    "Will Collingwood beat Geelong this week?",
    "What is the weather in Islamabad?",
]


def run_test(query: str):
    print("=" * 70)
    print(f"QUERY: {query}")

    initial_state = {
        "user_query": query,
        "conversation_history": [],
    }

    result = app.invoke(initial_state)

    print(f"INTENT: {result.get('intent')}")
    print(f"RESPONSE: {result.get('final_response')}")

    print("\nFULL STATE:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    for query in TEST_QUERIES:
        run_test(query)