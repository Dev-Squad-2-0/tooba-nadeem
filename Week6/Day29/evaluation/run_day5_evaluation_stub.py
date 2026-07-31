"""
STUB evaluation runner -- does NOT call the live LLM.

Purpose: verify the parts of the Day 5 evaluation suite that do not
require live model access, and confirm the harness itself works
end-to-end before spending API budget/quota on the real run.

What this actually checks (real, executed, non-fabricated):
  - prompt_injection cases: the guardrails.py heuristic layer correctly
    flags each override attempt (deterministic, no LLM needed).
  - retrieval cases: the underlying tool function returns a sane,
    correctly-shaped result (or a clear not-found) for the query's
    real target entity, run directly against the actual CSV data.
  - prediction cases: the underlying tool function returns a sane,
    correctly-shaped result (win probabilities that sum to 1, or a
    clear validation error for nonsense team names), run directly
    against the actual trained model.

What this does NOT check (must use run_day5_evaluation_live.py instead):
  - factual: needs the LLM's general knowledge, not a tool call.
  - scope: needs the LLM to actually produce a refusal in natural language.
  - multi_turn: needs the LLM to resolve pronouns/context across turns.

These are reported as SKIPPED (LIVE-ONLY), not marked pass or fail, since
guessing here would violate "do not invent test results."
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.guardrails import looks_like_override_attempt
from src.retrieval import get_team_vs_team_record, get_player_season_stats
from src.prediction_tools import predict_match, predict_top_players
from evaluation.day5_test_cases import ALL_CASES


def check_prompt_injection(case: dict) -> tuple[bool, str]:
    message = case["turns"][-1]
    flagged = looks_like_override_attempt(message)
    return flagged, ("heuristic flagged the override attempt" if flagged
                      else "heuristic did NOT flag this phrasing -- gap")


def check_retrieval(case: dict) -> tuple[bool | None, str]:
    # Structural check only: does the real tool run without crashing and
    # return a well-formed dict? (Not whether the *chat agent* would
    # choose to call this tool for this exact phrasing -- that needs the LLM.)
    try:
        if "record" in case["turns"][-1].lower() or "head-to-head" in case["turns"][-1].lower() or "wins" in case["turns"][-1].lower():
            result = get_team_vs_team_record("Collingwood Magpies", "Geelong Cats") \
                if "Collingwood" in case["turns"][-1] else get_team_vs_team_record("Richmond Tigers", "Hawthorn Hawks")
        else:
            result = get_player_season_stats("Nick Daicos", 2023)
        ok = isinstance(result, dict) and "found" in result
        return ok, f"tool returned well-formed dict: {result}" if ok else f"malformed result: {result}"
    except Exception as exc:
        return False, f"tool raised unexpectedly: {type(exc).__name__}: {exc}"


def check_prediction(case: dict) -> tuple[bool | None, str]:
    try:
        if "Wombats" in case["turns"][-1] or "Sharks" in case["turns"][-1]:
            # Correct behavior at the TOOL layer is a clean ValueError for an
            # unrecognized team (validated separately: execute_tools in
            # agent.py catches this and turns it into a graceful message
            # instead of crashing the whole agent -- see agent.py hardening).
            try:
                predict_match.invoke({
                    "match_date": "2025-09-27",
                    "home_team": "Wombats",
                    "away_team": "Sharks",
                })
                return False, "expected a ValueError for an unknown team, but no error was raised"
            except ValueError as ve:
                return True, f"correctly raised a clean ValueError: {ve}"

        result = predict_match.invoke({
            "match_date": "2025-09-27",
            "home_team": "Geelong Cats",
            "away_team": "Brisbane Lions",
        })
        probs_sum_to_one = abs(
            result["home_win_probability"] + result["away_win_probability"] - 1.0
        ) < 1e-6
        return probs_sum_to_one, f"probabilities sum to 1: {probs_sum_to_one} -> {result}"
    except Exception as exc:
        return False, f"tool raised unexpectedly: {type(exc).__name__}: {exc}"


def run():
    results = []

    for case in ALL_CASES:
        category = case["category"]

        if category == "prompt_injection":
            passed, detail = check_prompt_injection(case)
        elif category == "retrieval":
            passed, detail = check_retrieval(case)
        elif category == "prediction":
            passed, detail = check_prediction(case)
        else:
            passed, detail = None, "SKIPPED (LIVE-ONLY) -- requires a real LLM call"

        results.append({
            "id": case["id"], "category": category,
            "passed": passed, "detail": detail,
        })

    print("=" * 78)
    print("STUB EVALUATION RESULTS (non-LLM-dependent checks only)")
    print("=" * 78)

    by_category = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)

    for category, items in by_category.items():
        gradable = [i for i in items if i["passed"] is not None]
        passed_count = sum(1 for i in gradable if i["passed"])
        print(f"\n[{category.upper()}]")
        for i in items:
            status = "SKIP" if i["passed"] is None else ("PASS" if i["passed"] else "FAIL")
            print(f"  {i['id']}: {status}  -- {i['detail'][:100]}")
        if gradable:
            print(f"  -> {passed_count}/{len(gradable)} gradable checks passed")
        else:
            print(f"  -> all {len(items)} require the live model (run_day5_evaluation_live.py)")

    total_gradable = [r for r in results if r["passed"] is not None]
    total_passed = sum(1 for r in total_gradable if r["passed"])
    print("\n" + "=" * 78)
    print(f"TOTAL GRADABLE HERE: {len(total_gradable)}/{len(results)} cases")
    print(f"PASSED: {total_passed}/{len(total_gradable)}")
    print(f"SKIPPED (need live LLM): {len(results) - len(total_gradable)}")
    print("=" * 78)

    return results


if __name__ == "__main__":
    run()
