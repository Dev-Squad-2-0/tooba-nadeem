"""
Deterministic keyword-based classification.

This is the graceful-degradation path used when the LLM client raises
LLMError (rate limit, timeout, refusal). It is intentionally simple and
dependency-free so the pipeline can always produce *some* structured,
routable output instead of hard-failing a support ticket.
"""
import json
import os
from typing import Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(_DATA_DIR, "projects.json"), encoding="utf-8") as f:
    _PROJECTS = json.load(f)["projects"]

_ISSUE_KEYWORDS = {
    "refund": ["refund", "money back", "want my money"],
    "billing_dispute": ["overcharged", "wrong charge", "dispute", "chargeback", "billing"],
    "account_recovery": ["locked out", "lost access", "recover my account", "can't access my wallet",
                          "lost wallet", "seed phrase"],
    "technical_issue": ["bug", "error", "stuck", "pending", "not working", "crash", "failed",
                        "missing", "not showing", "not recorded", "didn't receive", "did not receive",
                        "isn't working", "not appearing", "not reflected"],
    "general_inquiry": ["how do i", "how to", "question", "information", "apply"],
}

_PRIORITY_KEYWORDS = {
    "urgent": ["urgent", "immediately", "asap", "lost funds", "hacked", "unauthorized", "stolen"],
    "high": ["refund", "overcharged", "locked out", "lost access", "billing"],
    "low": ["question", "how do i", "information", "curious"],
}


def identify_project(ticket_text: str) -> tuple[str, float]:
    """Returns (project_key, confidence 0-1) via keyword overlap."""
    lowered = ticket_text.lower()
    best_key, best_score = "general", 0.0
    for project in _PROJECTS:
        if project["key"] == "general":
            continue
        hits = sum(1 for kw in project["keywords"] if kw in lowered)
        if hits > 0:
            score = min(1.0, 0.4 + 0.2 * hits)
            if score > best_score:
                best_key, best_score = project["key"], score
    if best_score == 0.0:
        return "general", 0.3
    return best_key, best_score


def classify_issue(ticket_text: str) -> str:
    lowered = ticket_text.lower()
    for category, keywords in _ISSUE_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return category
    return "general_inquiry"


def determine_priority(ticket_text: str, issue_category: str) -> str:
    lowered = ticket_text.lower()
    for level in ("urgent", "high", "low"):
        if any(kw in lowered for kw in _PRIORITY_KEYWORDS[level]):
            return level
    return "medium"


def get_department(project_key: str) -> tuple[str, str]:
    for project in _PROJECTS:
        if project["key"] == project_key:
            return project["department"], project["escalation_contact"]
    general = next(p for p in _PROJECTS if p["key"] == "general")
    return general["department"], general["escalation_contact"]


def get_project_display_name(project_key: str) -> str:
    for project in _PROJECTS:
        if project["key"] == project_key:
            return project["name"]
    return "Unknown"
