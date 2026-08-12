"""
evaluate_voice.py
-------------------

Human-evaluation harness for the Day 3 voice agent (Task 5).

Runs each scripted conversation in voice_eval_conversations.py through the
REAL agent_graph.handle_turn() — the exact same function the voice pipeline
calls — measuring per-turn latency automatically. Naturalness,
persuasiveness, fluency, and conversation-flow scores are NOT computed
automatically (they require a human listening/reading judgment call); this
script produces the transcript + latency data and a ready-to-score table so
a human evaluator fills in the remaining rubric columns.

Usage:
    python -m evaluation.evaluate_voice
"""

import time
import logging
from pathlib import Path
from datetime import datetime

from app import config
from app.graph import memory_store
from app.graph.agent_graph import handle_turn
from evaluation.voice_eval_conversations import EVAL_CONVERSATIONS

logging.basicConfig(level=logging.WARNING)  # quiet the RAG/SQL debug noise

REPORT_PATH = Path(config.BASE_DIR) / "evaluation" / "voice_eval_report.md"


def run_scenario(scenario_name: str, turns: list[str]) -> dict:
    """
    Runs one scripted conversation end-to-end on a fresh session, timing
    each turn. Returns transcript + latency data for the report.
    """

    session_id = f"eval_{scenario_name}"
    memory_store.reset(session_id)  # fresh memory per scenario

    turn_results = []

    for user_message in turns:
        start = time.perf_counter()
        response_text = handle_turn(session_id, user_message)
        elapsed = time.perf_counter() - start

        turn_results.append({
            "user": user_message,
            "assistant": response_text,
            "latency_seconds": round(elapsed, 3),
        })

    avg_latency = round(
        sum(t["latency_seconds"] for t in turn_results) / len(turn_results),
        3,
    )

    return {
        "scenario": scenario_name,
        "turns": turn_results,
        "avg_latency_seconds": avg_latency,
    }


def latency_score(avg_latency: float) -> int:
    """Maps measured latency to the 1-5 rubric band from voice_eval_rubric.md."""
    if avg_latency < 1.0:
        return 5
    if avg_latency < 1.5:
        return 4
    if avg_latency < 2.0:
        return 3
    if avg_latency < 3.0:
        return 2
    return 1


def render_report(results: list[dict]) -> str:
    lines = []
    lines.append("# Voice Agent Evaluation Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(
        "Scoring rubric: see `evaluation/voice_eval_rubric.md`. Latency is "
        "measured automatically (RAG + recommender + LLM orchestration "
        "time only — see the rubric's note on measuring full end-to-end "
        "voice latency separately). Naturalness / Persuasiveness / Fluency "
        "/ Conversation Flow require human scoring — fill in the blank "
        "cells below after reading each transcript."
    )
    lines.append("")

    lines.append("## Summary Scoring Table")
    lines.append("")
    lines.append(
        "| Scenario | Naturalness | Persuasiveness | Fluency | "
        "Latency (auto) | Flow | Notes |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['scenario']} |  |  |  | "
            f"{latency_score(r['avg_latency_seconds'])}/5 "
            f"({r['avg_latency_seconds']}s avg) |  |  |"
        )
    lines.append("")

    lines.append("## Example Conversations")
    lines.append("")

    for r in results:
        lines.append(f"### Scenario: `{r['scenario']}`")
        lines.append("")
        lines.append(
            f"Average turn latency: **{r['avg_latency_seconds']}s** "
            f"(rubric score: {latency_score(r['avg_latency_seconds'])}/5)"
        )
        lines.append("")
        for i, turn in enumerate(r["turns"], start=1):
            lines.append(f"**Turn {i} — Buyer:** {turn['user']}")
            lines.append("")
            lines.append(f"**Turn {i} — Agent** (`{turn['latency_seconds']}s`): {turn['assistant']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    results = []

    for scenario_name, turns in EVAL_CONVERSATIONS.items():
        print(f"Running scenario: {scenario_name}")
        result = run_scenario(scenario_name, turns)
        results.append(result)
        print(
            f"  -> avg latency: {result['avg_latency_seconds']}s "
            f"({len(turns)} turns)"
        )

    report = render_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nReport written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()