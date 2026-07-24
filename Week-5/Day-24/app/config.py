"""
Central configuration.

All values are read from environment variables so nothing sensitive is
hard-coded. Copy .env.example to .env and fill in API_KEY before running.
"""
import os

from dotenv import load_dotenv

# Loads variables from a .env file in the current working directory (or the
# nearest parent) into the process environment. Safe to call even if no
# .env file exists -- it just becomes a no-op, so this doesn't break
# environments (like CI) that set real environment variables directly.
load_dotenv()

# --- Company-provided OpenAI-compatible endpoint ---
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://llm.netixsol.com/v1")
LLM_API_KEY = os.getenv("API_KEY", "")

# Ordered fallback chain. If the first model errors out (rate limit, timeout,
# 5xx, refusal-like content) the client automatically retries with the next
# one. Reorder / trim this list freely -- nothing else in the codebase
# references model names directly.
MODEL_FALLBACK_CHAIN = [
    os.getenv("PRIMARY_MODEL", "smart"),
    os.getenv("FALLBACK_MODEL_1", "smart-lite"),
    os.getenv("FALLBACK_MODEL_2", "fast"),
]

# Per-call timeout in seconds before we treat the model as unresponsive and
# move to the next one in the fallback chain / rule-based degradation.
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

# Categories that must never be auto-resolved without a human clicking
# "approve". Add to this list as the business defines new sensitive flows.
SENSITIVE_ISSUE_CATEGORIES = {
    "refund",
    "billing_dispute",
    "account_recovery",
    "security_incident",
}

# LLM_MODE=live  -> calls the real company endpoint
# LLM_MODE=mock  -> deterministic offline stub, used for local dev/CI and for
#                   the evaluation run in environments with no network egress
#                   to the company endpoint. Swap to "live" in production.
LLM_MODE = os.getenv("LLM_MODE", "live")

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "triage_agent.log")
