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

from dotenv import load_dotenv

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
    "fast",
)

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# Default model (change according to your API provider)
DEFAULT_MODEL = "fast"

# Maximum response tokens
MAX_TOKENS = 1024

# Response temperature
TEMPERATURE = 0.2


# =============================================================================
# VOICE CONFIGURATION
# =============================================================================

# Deepgram Speech-to-Text
STT_PROVIDER = "deepgram"

# Fish Audio Text-to-Speech
TTS_PROVIDER = "fish-audio"

# Default language
LANGUAGE = "ur"


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================

# Maximum number of properties to recommend
MAX_RECOMMENDATIONS = 5


# =============================================================================
# CALENDAR SETTINGS
# =============================================================================

DEFAULT_APPOINTMENT_DURATION = 60  # minutes


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