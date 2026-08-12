"""
Application Configuration
-------------------------

This file contains application-wide configuration settings used across the
Real Estate AI Voice Agent.

Keeping configuration in one place makes the project easier to maintain and
allows quick experimentation (e.g., different chunk sizes or embedding models)
without modifying multiple files.
"""
import os

from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Set offline mode for HuggingFace / Transformers to prevent network calls during embedding loads
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

load_dotenv()


# =============================================================================
# PROJECT PATHS
# =============================================================================

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Structured data (CSV files)
STRUCTURED_DATA_DIR = BASE_DIR / "database" / "structured"

# Knowledge base (Markdown documents)
KNOWLEDGE_BASE_DIR = BASE_DIR / "database" / "knowledge"

# Chroma Vector Database
VECTOR_DB_DIR = BASE_DIR / "database" / "chroma"

# SQLite Database
SQL_DATABASE_PATH = BASE_DIR / "database" / "property_data.db"

# Logs
LOG_DIR = BASE_DIR / "logs"


# =============================================================================
# RAG CONFIGURATION
# =============================================================================

# Sentence Transformer model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Number of retrieved chunks
TOP_K_RESULTS = 5

# Similarity search type
SEARCH_TYPE = "similarity"

# ==========================
# LLM
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "meta-llama/llama-3.3-70b-instruct",
)

OPENAI_MODEL_FALLBACKS = [
    OPENAI_MODEL,
    "google/gemini-2.5-flash",
    "openai/gpt-4o-mini",
]

# NEW — OpenRouter-only: explicitly tells the provider not to return/inline
# reasoning tokens, even if OPENAI_MODEL is ever pointed at a reasoning
# model later. No-op on the current non-reasoning model. See client.py.
EXCLUDE_REASONING_TOKENS = True

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# Default model (change according to your API provider)
# DEFAULT_MODEL = "fast"
# DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
# DEFAULT_MODEL= "openrouter/free"
DEFAULT_MODEL="meta-llama/llama-3.3-70b-instruct:free"

# Maximum response tokens (kept small for RAG's grounded single-shot answers)
MAX_TOKENS = 1024

# Response temperature (0 = strict grounding, used by Day 1 RAG answer())
TEMPERATURE = 0.2

# --------------------------
# Conversational chat settings (Day 3 — voice agent turns)
# --------------------------
# Slightly higher temperature so the sales persona doesn't sound robotic,
# but still low enough to stay grounded and not hallucinate numbers.
CHAT_TEMPERATURE = 0.4

# Kept short deliberately: shorter completions = less TTS wait = lower
# end-to-end voice latency. Voice answers should be 2-4 sentences, not essays.
CHAT_MAX_TOKENS = 300

# Slot extraction should be deterministic — we want a clean JSON diff, not
# creative variation.
SLOT_EXTRACTION_TEMPERATURE = 0.0
SLOT_EXTRACTION_MAX_TOKENS = 200


# =============================================================================
# VOICE CONFIGURATION
# =============================================================================

# Deepgram Speech-to-Text
STT_PROVIDER = "deepgram"
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
# nova-2 is Deepgram's current general-purpose streaming model; good latency
# and accuracy for telephony/voice-agent style audio.
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-2")
# Buyers code-switch between Urdu and English constantly ("DHA mein 3 bed
# available hai?"). Deepgram's multi-language detection handles this far
# better than pinning to a single "ur" or "en" locale.
DEEPGRAM_LANGUAGE = os.getenv("DEEPGRAM_LANGUAGE", "multi")

# Edge-TTS (per project requirement — NOT ElevenLabs / Fish Audio)
TTS_PROVIDER = "edge-tts"
# ur-PK-AsadNeural = male Urdu (Pakistan) voice, sounds like a sales exec.
# Swap to ur-PK-UzmaNeural for a female voice via env var, no code change.
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "ur-PK-AsadNeural")
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%")

# Default language
LANGUAGE = "ur"


# =============================================================================
# CONVERSATION MEMORY / SESSION SETTINGS
# =============================================================================

# How long an idle voice/chat session's memory is kept before it's treated
# as stale and evicted from the in-process store.
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "1800"))  # 30 min


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================

# Maximum number of properties to recommend
MAX_RECOMMENDATIONS = 5

# =============================================================================
# CALENDAR SETTINGS
# =============================================================================

DEFAULT_APPOINTMENT_DURATION = 60  # minutes

# --------------------------
# Google Calendar (Day 4)
# --------------------------
# Reuses the credentials.json already present at the project root — never
# generated or overwritten by this app. token.json is created automatically
# on first OAuth flow (see app/calendar/google_calendar.py:authenticate()).
GOOGLE_CREDENTIALS_PATH = BASE_DIR / "credentials.json"
GOOGLE_TOKEN_PATH = BASE_DIR / "token.json"
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
CALENDAR_TIMEZONE = os.getenv("CALENDAR_TIMEZONE", "Asia/Karachi")


# =============================================================================
# EMAIL / SMTP (Day 4)
# =============================================================================

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"


# =============================================================================
# CREATE REQUIRED DIRECTORIES
# =============================================================================

VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Ensure the structured database directory exists
SQL_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)