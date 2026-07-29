import csv
from pathlib import Path

from .agent import ask_agent


# Find guardrail_test.csv in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = PROJECT_ROOT / "guardrail_test.csv"


def run_guardrail_tests():
    """Run all guardrail evaluation prompts from the CSV file."""

    with open(TEST_FILE, "r", encoding="utf-8") as file:
        tests = list(csv.DictReader(file))

    print("=" * 80)
    print(f"Running {len(tests)} guardrail tests")
    print("=" * 80)

    for test in tests:
        test_id = test["id"]
        prompt = test["prompt"]
        category = test["category"]
        expected = test["expected_behavior"]

        print("\n" + "=" * 80)
        print(f"TEST {test_id}")
        print(f"Category: {category}")
        print(f"Prompt: {prompt}")
        print(f"Expected: {expected}")
        print("-" * 80)

        try:
            response = ask_agent(
                prompt,
                thread_id=f"guardrail-test-{test_id}"
            )

            print("AGENT RESPONSE:")
            print(response)

        except Exception as error:
            print("ERROR:")
            print(type(error).__name__, error)

        print("=" * 80)


if __name__ == "__main__":
    run_guardrail_tests()