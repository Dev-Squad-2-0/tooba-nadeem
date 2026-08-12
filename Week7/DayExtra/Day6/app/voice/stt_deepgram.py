"""
stt_deepgram.py
----------------

Streaming Speech-to-Text wrapper around Deepgram's live transcription
websocket API.

Targets deepgram-sdk 7.6.0 (the Fern-generated rewrite — v6+). This SDK
generation has NO DeepgramClientOptions / LiveTranscriptionEvents /
LiveOptions classes; those were removed. Everything now goes through:

  - AsyncDeepgramClient(api_key=...)
  - client.listen.v1.connect(**options)   -> an async context manager
  - connection.on(EventType.MESSAGE, handler) for events
  - connection.start_listening()          -> the receive loop (must run
                                              concurrently with sending)
  - connection.send_media(bytes)          -> push audio
  - connection.send_finalize()            -> flush the last partial before
                                              closing

Isolated behind this one class so app/voice/pipeline.py never touches the
Deepgram SDK directly — if the SDK's API shape changes again or you swap
providers, this is the only file that needs to change. Public interface
(start/send_audio/stop) is unchanged from the previous version.

Because start()/send_audio()/stop() are called as three separate methods
(not one `async with` block), the connection's context manager is driven
manually via __aenter__/__aexit__ here, and the receive loop
(start_listening()) is run as a background asyncio.Task so it doesn't
block send_audio() calls.
"""

import asyncio
import contextlib
import logging
from typing import Callable, Awaitable

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType

from app import config

logger = logging.getLogger(__name__)

OnFinalTranscript = Callable[[str], Awaitable[None]]

# Domain-specific terms Deepgram's general language model won't reliably
# recognize on its own (Pakistani real-estate abbreviations, area names,
# and this project's own developer/project names). Keyterm Prompting
# biases the acoustic model toward these at inference time without
# retraining. Confirmed compatible with Nova-3 + language=ur.
REAL_ESTATE_KEYTERMS = [
    "DHA", "Bahria Town", "Gulberg", "Askari", "Model Town",
    "Skyline Residency", "Emerald Gardens", "Ocean Breeze Towers",
    "Horizon Business Bay", "Capital Greens Enclave", "The Pearl Heights",
    "Al-Noor Valley", "Al-Noor Business Square",
    # Common Pakistani names that nova-3 mis-transcribes —
    # "Tooba" (طوبیٰ) is heard as "Tuba" or "Toba" without this hint.
    "Tooba", "Tooba Ji",
]


class DeepgramSTT:
    """
    One instance = one live streaming session (i.e. one voice call).
    """

    def __init__(self, on_final_transcript: OnFinalTranscript):
        self.on_final_transcript = on_final_transcript
        self._client = AsyncDeepgramClient(api_key=config.DEEPGRAM_API_KEY)
        self._connection_ctx = None
        self._connection = None
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> None:
        # client.listen.v1.connect(...) returns an async context manager.
        # We enter it manually (rather than `async with`) so the
        # connection stays open across separate start()/send_audio()/
        # stop() calls instead of one contiguous block.
        self._connection_ctx = self._client.listen.v1.connect(
            model=config.DEEPGRAM_MODEL,
            language=config.DEEPGRAM_LANGUAGE,
            smart_format=True,
            interim_results=True,
            # Voice-agent turn-taking: Deepgram flags a final segment once
            # ~endpointing ms of silence is detected. 300ms keeps latency
            # low without cutting the buyer off mid-thought.
            endpointing=300, # back to 300 -- the 100ms recommendation from Deepgram's docs was specifically for `language=multi` code-switching; you're on monolingual `ur` now, so the standard default applies
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            keyterm=REAL_ESTATE_KEYTERMS,
        )
        self._connection = await self._connection_ctx.__aenter__()

        async def _on_message(message):
            logger.info("MESSAGE TYPE: %s", type(message))
            logger.info("MESSAGE: %r", message)

            try:
                alternatives = message.channel.alternatives
                transcript = (alternatives[0].transcript or "").strip()

                logger.info("Transcript: %s", transcript)
                logger.info("is_final: %s", getattr(message, "is_final", None))

                if transcript and getattr(message, "is_final", False):
                    await self.on_final_transcript(transcript)

            except Exception as e:
                logger.info("Not a transcript message: %s", e)


        # async def _on_message(message):
        #     # Non-transcript events (Metadata, SpeechStarted, UtteranceEnd,
        #     # etc.) don't have channel.alternatives — attribute access
        #     # fails harmlessly and we just skip them, rather than gating
        #     # on an exact message.type string that may vary by SDK point
        #     # release.
        #     try:
        #         alternatives = message.channel.alternatives
        #         transcript = (alternatives[0].transcript or "").strip()
        #     except (AttributeError, IndexError):
        #         return

        #     if not transcript:
        #         return

        #     if getattr(message, "is_final", False):
        #         logger.info("Deepgram final transcript: %s", transcript)
        #         await self.on_final_transcript(transcript)

        async def _on_error(error):
            logger.error("Deepgram STT error: %s", error)

        self._connection.on(EventType.MESSAGE, _on_message)
        self._connection.on(EventType.ERROR, _on_error)

        # start_listening() is the receive loop — it awaits indefinitely
        # until the connection closes, so it must run as a background
        # task, not be awaited directly here (that would block start()
        # forever and send_audio() would never get called).
        self._listen_task = asyncio.create_task(
            self._connection.start_listening()
        )

        logger.info("Deepgram STT session started")

    async def send_audio(self, chunk: bytes) -> None:
        if self._connection is not None:
            await self._connection.send_media(chunk)

    async def stop(self) -> None:
        if self._connection is not None:
            # Flush any buffered partial transcript before closing, so the
            # last few words of a call aren't silently dropped.
            with contextlib.suppress(Exception):
                await self._connection.send_finalize()

        if self._listen_task is not None:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        if self._connection_ctx is not None:
            with contextlib.suppress(Exception):
                await self._connection_ctx.__aexit__(None, None, None)
            self._connection_ctx = None
            self._connection = None

        logger.info("Deepgram STT session stopped")