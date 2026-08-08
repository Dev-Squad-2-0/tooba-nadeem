"""
pipeline.py
------------

One VoiceSession instance = one live voice call over a single client
WebSocket.

Flow per turn:
  client audio bytes -> Deepgram (streaming) -> final transcript
    -> agent_graph.handle_turn() (RAG + recommender + memory + objection
       handling, reused from Day 1/2 + this session's new modules)
    -> Edge-TTS (streaming) -> audio bytes back to client, chunk by chunk

Latency notes:
  - agent_graph.handle_turn() is a synchronous/blocking call (the OpenAI
    client is sync). It's run via asyncio.to_thread() so it doesn't block
    the event loop that's simultaneously receiving audio for the NEXT
    utterance and servicing other sessions.
  - TTS chunks are forwarded to the client the moment each one arrives,
    not buffered into one clip — this is what lets playback start before
    the full sentence has finished synthesizing.
"""

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.voice.stt_deepgram import DeepgramSTT
from app.voice.tts_edge import synthesize_stream
from app.graph.agent_graph import handle_turn

from app.voice.transcript_corrections import apply_corrections

logger = logging.getLogger(__name__)


class VoiceSession:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.stt = DeepgramSTT(on_final_transcript=self._on_final_transcript)
        self._turn_lock = asyncio.Lock()

    async def run(self) -> None:
        await self.websocket.accept()
        await self.stt.start()

        try:
            while True:
                message = await self.websocket.receive()

                if "bytes" in message and message["bytes"] is not None:
                    await self.stt.send_audio(message["bytes"])

                elif "text" in message and message["text"] is not None:
                    # Control messages from the client, e.g. {"type": "end"}
                    await self._handle_control_message(message["text"])

        except WebSocketDisconnect:
            logger.info("Voice session %s disconnected", self.session_id)
        finally:
            await self.stt.stop()

    async def _handle_control_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return

        if payload.get("type") == "end":
            await self.stt.stop()

    async def _on_final_transcript(self, transcript: str) -> None:
        """
        Called by DeepgramSTT whenever a finalized transcript segment is
        ready. Runs the full agent turn + TTS response.
        """
        transcript = apply_corrections(transcript)  # <-- added

        # Guard against overlapping turns if Deepgram fires two finals in
        # quick succession (e.g. buyer says two short sentences fast).
        async with self._turn_lock:
            await self._send_event("transcript", {"text": transcript})

            try:
                response_text = await asyncio.to_thread(
                    handle_turn, self.session_id, transcript
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Agent turn failed: %s", exc)
                response_text = (
                    "Sorry, mujhe thora sa masla ho gaya. "
                    "Dobara boliye please."
                )

            await self._send_event("response_text", {"text": response_text})

            async for audio_chunk in synthesize_stream(response_text):
                # Binary audio frames are sent directly (not wrapped in
                # JSON) so the client can pipe them straight into an audio
                # decoder without a base64 round-trip.
                await self.websocket.send_bytes(audio_chunk)

            await self._send_event("response_audio_end", {})

    async def _send_event(self, event_type: str, data: dict) -> None:
        await self.websocket.send_text(
            json.dumps({"type": event_type, **data})
        )