import csv
from pathlib import Path

from .agent import ask_agent


# Find guardrail_tests.csv in the project root
# (previously pointed at "guardrail_test.csv", which does not exist and
# caused this test file to fail with FileNotFoundError before it ever
# reached the agent -- fixed here as part of Day 5 hardening)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = PROJECT_ROOT / "evaluation" / "guardrail_tests.csv"


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
            result = ask_agent(
                prompt,
                thread_id=f"guardrail-test-{test_id}"
            )

            print("STATUS:", result["status"])
            print("AGENT RESPONSE:")
            print(result["response"])

            if result["tools_called"]:
                print("TOOLS CALLED:", [
                    (c["name"], c["status"]) for c in result["tools_called"]
                ])

        except Exception as error:
            print("ERROR:")
            print(type(error).__name__, error)

        print("=" * 80)


if __name__ == "__main__":
    run_guardrail_tests()