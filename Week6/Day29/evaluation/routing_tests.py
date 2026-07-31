from pathlib import Path

import pandas as pd

from src.router import classify_intent


# -------------------------------------------------------------------
# Routing test cases
# -------------------------------------------------------------------

TEST_CASES = [
    # Factual
    {
        "id": "R01",
        "query": "Who won the 2024 AFL Grand Final?",
        "expected_intent": "factual",
    },
    {
        "id": "R02",
        "query": "How many teams are in the AFL?",
        "expected_intent": "factual",
    },
    {
        "id": "R03",
        "query": "What is a behind in Australian Rules Football?",
        "expected_intent": "factual",
    },
    {
        "id": "R04",
        "query": "Which team has won the most AFL premierships?",
        "expected_intent": "factual",
    },
    {
        "id": "R05",
        "query": "Who is Nick Daicos?",
        "expected_intent": "factual",
    },

    # Retrieval
    {
        "id": "R06",
        "query": "What were Nick Daicos' stats last round?",
        "expected_intent": "retrieval",
    },
    {
        "id": "R07",
        "query": "How many disposals did a player have in Round 10?",
        "expected_intent": "retrieval",
    },
    {
        "id": "R08",
        "query": "What were Collingwood's results last season?",
        "expected_intent": "retrieval",
    },
    {
        "id": "R09",
        "query": "Show me the team's statistics from the previous round.",
        "expected_intent": "retrieval",
    },
    {
        "id": "R10",
        "query": "What was the fantasy score for this player last match?",
        "expected_intent": "retrieval",
    },

    # Prediction
    {
        "id": "R11",
        "query": "Will Collingwood beat Geelong this week?",
        "expected_intent": "prediction",
    },
    {
        "id": "R12",
        "query": "Who will win the next Sydney Swans match?",
        "expected_intent": "prediction",
    },
    {
        "id": "R13",
        "query": "Who is likely to top-score in the next match?",
        "expected_intent": "prediction",
    },
    {
        "id": "R14",
        "query": "Who will be the top fantasy player in the Collingwood game?",
        "expected_intent": "prediction",
    },
    {
        "id": "R15",
        "query": "Which team is more likely to win between Carlton and Richmond?",
        "expected_intent": "prediction",
    },

    # Off-topic
    {
        "id": "R16",
        "query": "What is the capital of France?",
        "expected_intent": "off_topic",
    },
    {
        "id": "R17",
        "query": "Can you help me write a Python program?",
        "expected_intent": "off_topic",
    },
    {
        "id": "R18",
        "query": "What is the weather in Islamabad today?",
        "expected_intent": "off_topic",
    },
    {
        "id": "R19",
        "query": "Tell me a joke about computers.",
        "expected_intent": "off_topic",
    },
    {
        "id": "R20",
        "query": "What is the population of Pakistan?",
        "expected_intent": "off_topic",
    },
]


# -------------------------------------------------------------------
# Run evaluation
# -------------------------------------------------------------------

def run_evaluation():
    results = []

    for test_case in TEST_CASES:
        query = test_case["query"]
        expected = test_case["expected_intent"]

        try:
            predicted = classify_intent(query)

            correct = predicted == expected

            error = ""

        except Exception as exc:
            predicted = "ERROR"
            correct = False
            error = str(exc)

        results.append({
            "id": test_case["id"],
            "query": query,
            "expected_intent": expected,
            "predicted_intent": predicted,
            "correct": correct,
            "error": error,
        })

    df = pd.DataFrame(results)

    accuracy = df["correct"].mean()

    print("\n" + "=" * 70)
    print("ROUTING EVALUATION")
    print("=" * 70)

    print(f"Total queries : {len(df)}")
    print(f"Correct       : {df['correct'].sum()}")
    print(f"Incorrect     : {(~df['correct']).sum()}")
    print(f"Accuracy      : {accuracy:.2%}")

    print("\nDetailed Results:")
    print(df.to_string(index=False))

    # ---------------------------------------------------------------
    # Save results
    # ---------------------------------------------------------------

    output_path = (
        Path(__file__).resolve().parent
        / "routing_results.csv"
    )

    df.to_csv(output_path, index=False)

    print(f"\nResults saved to: {output_path}")

    return df


if __name__ == "__main__":
    run_evaluation()