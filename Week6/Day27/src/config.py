import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

ROUND_STATS_PATH = DATA_DIR / "cleaned_round_by_round_stats_v2.csv"
TEAM_MATCHES_PATH = DATA_DIR / "cleaned_team_matches.csv"
SEASONAL_STATS_PATH = DATA_DIR / "cleaned_seasonal_stats.csv"


load_dotenv(BASE_DIR / ".env")


# ============================================================
# NetixSol configuration
# Kept here for reference, but currently disabled.
# ============================================================

# LLM_BASE_URL = os.getenv(
#     "LLM_BASE_URL",
#     "https://llm.netixsol.com/v1",
# )

# LLM_API_KEY = os.getenv("NETIXSOL_API_KEY")

# PRIMARY_MODEL = os.getenv(
#     "PRIMARY_MODEL",
#     "smart",
# )

# FALLBACK_MODELS = [
#     PRIMARY_MODEL,
#     "fast",
#     "coder",
#     "batch",
# ]


# ============================================================
# OpenRouter configuration
# ============================================================

LLM_BASE_URL = "https://openrouter.ai/api/v1"

LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")

PRIMARY_MODEL = "openrouter/free"

FALLBACK_MODELS = [
    PRIMARY_MODEL,
]