"""
main.py
--------

FastAPI application entrypoint.

Startup:
  - Builds the Chroma vector DB if it doesn't exist yet (reuses
    RAGPipeline.build() from Day 1, unmodified).
  - Builds the SQLite structured DB if it doesn't exist yet (reuses
    PropertyDatabase.build_database() from Day 2, unmodified).

Routes:
  - GET  /health
  - POST /chat                    (text-only agent testing)
  - POST /chat/reset/{session_id}
  - WS   /ws/voice/{session_id}   (Day 3 streaming voice pipeline)
"""

import logging

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api.routes import router as api_router
from app.rag.rag_pipeline import RAGPipeline
from database.database import PropertyDatabase
from app.voice.pipeline import VoiceSession

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meridian Homes Pakistan — Real Estate Voice Agent")

# CORS left permissive for local dev/testing (browser mic client, Streamlit,
# etc.). Tighten allow_origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    if not config.SQL_DATABASE_PATH.exists():
        logger.info("SQLite database not found — building it now.")
        PropertyDatabase().build_database()
    else:
        logger.info("SQLite database already exists.")

    logger.info("Ensuring RAG vector store is built...")
    RAGPipeline().build()


@app.websocket("/ws/voice/{session_id}")
async def voice_endpoint(websocket: WebSocket, session_id: str):
    session = VoiceSession(websocket, session_id)
    await session.run()