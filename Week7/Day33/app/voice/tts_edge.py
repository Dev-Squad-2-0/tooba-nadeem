"""
tts_edge.py
------------

Streaming Text-to-Speech wrapper around Microsoft Edge-TTS (edge-tts
package). Per project requirement, this replaces the ElevenLabs/Fish Audio
placeholder that was in the original config.

Streams audio chunks as they're generated (edge_tts's own streaming
interface) rather than waiting for the full clip to synthesize — this is
the single biggest latency win in the pipeline, since playback can start
before the whole response has finished synthesizing.
"""

import logging
from typing import AsyncGenerator

import edge_tts

from app import config

logger = logging.getLogger(__name__)


async def synthesize_stream(text: str) -> AsyncGenerator[bytes, None]:
    """
    Yields raw MP3 audio chunks for `text` as they become available.
    """

    if not text or not text.strip():
        return

    communicate = edge_tts.Communicate(
        text,
        voice=config.EDGE_TTS_VOICE,
        rate=config.EDGE_TTS_RATE,
    )

    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    except Exception as exc:  # noqa: BLE001
        # A TTS failure should not crash the call — log and stop yielding,
        # the client-side player just gets a shorter/empty response.
        logger.error("Edge-TTS synthesis failed: %s", exc)
        return


async def synthesize_full(text: str) -> bytes:
    """
    Non-streaming convenience wrapper (used by the text-only /chat test
    endpoint, where there's no live audio socket to stream chunks into).
    """
    chunks = []
    async for chunk in synthesize_stream(text):
        chunks.append(chunk)
    return b"".join(chunks)