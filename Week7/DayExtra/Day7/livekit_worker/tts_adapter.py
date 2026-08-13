"""
Adapter: makes the EXISTING app/voice/tts_edge.py (Edge-TTS) usable as a
LiveKit Agents TTS plugin.

LiveKit does not provide an official Edge-TTS plugin, so this adapter
connects the existing Edge-TTS implementation to LiveKit's TTS interface.

Edge-TTS produces MP3 audio. LiveKit expects PCM audio frames, so FFmpeg
is used to decode MP3 -> 16-bit PCM.
"""

from __future__ import annotations

import asyncio
import shutil

from livekit.agents import tts
from livekit.agents.types import APIConnectOptions
from livekit.agents.utils import AudioBuffer

from app.voice.tts_edge import synthesize_stream


SAMPLE_RATE = 24000
NUM_CHANNELS = 1

# Resolved once at import time rather than per-synthesis-call -- shutil.which()
# does a real filesystem PATH search, no need to repeat it on every request.
#
# IMPORTANT (Windows): this reads THIS process's PATH environment variable,
# which was fixed at process creation. If ffmpeg was installed (e.g. via
# winget) AFTER this process -- or the terminal/IDE that launched it -- was
# already running, this will still resolve to None even though `ffmpeg
# -version` works in a fresh terminal. Windows only propagates an updated
# PATH to NEW processes; already-running ones keep whatever PATH they
# started with. Closing and reopening the terminal/IDE (so the venv/python
# process is recreated) is required in that case -- this resolution step
# cannot work around an already-stale process environment, it can only
# fail clearly instead of cryptically when that's the situation.
_FFMPEG_PATH = shutil.which("ffmpeg")


class EdgeTTS(tts.TTS):
    """
    LiveKit TTS adapter around the project's existing Edge-TTS implementation.
    """

    def __init__(self) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = APIConnectOptions(),
    ) -> "EdgeTTSStream":
        return EdgeTTSStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
        )


class EdgeTTSStream(tts.ChunkedStream):
    """
    Collects the MP3 output from the existing Edge-TTS implementation,
    converts it to PCM using FFmpeg, and sends it to LiveKit.
    """

    def __init__(
        self,
        *,
        tts: "EdgeTTS",
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(
            tts=tts,
            input_text=input_text,
            conn_options=conn_options,
        )

    async def _run(self, output_emitter) -> None:
        mp3_chunks: list[bytes] = []

        async for chunk in synthesize_stream(self._input_text):
            mp3_chunks.append(chunk)

        mp3_bytes = b"".join(mp3_chunks)

        if not mp3_bytes:
            raise RuntimeError("Edge-TTS returned no audio data.")

        pcm_bytes = await self._mp3_to_pcm(mp3_bytes)

        if not pcm_bytes:
            raise RuntimeError("FFmpeg produced no PCM audio.")

        # AudioEmitter, not AudioBuffer -- push() takes raw bytes directly.
        # initialize() must be called before the first push(); end_input()/
        # join()/aclose() are handled by ChunkedStream._main_task() after
        # _run() returns, so this method's job ends at flush().
        output_emitter.initialize(
            request_id="edge-tts",
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm_bytes)
        output_emitter.flush()

    @staticmethod
    async def _mp3_to_pcm(mp3_bytes: bytes) -> bytes:
        """
        Convert MP3 bytes to signed 16-bit PCM, 24 kHz, mono using FFmpeg.
        """

        if _FFMPEG_PATH is None:
            raise RuntimeError(
                "ffmpeg was not found on this Python process's PATH "
                "(shutil.which('ffmpeg') returned None). `ffmpeg -version` "
                "working in a terminal does NOT guarantee this Python "
                "process sees it -- if ffmpeg was installed after this "
                "terminal/IDE session was opened, its PATH is stale. "
                "Close ALL terminal windows and your IDE, reopen, "
                "reactivate the venv, and re-run. If "
                "`python -c \"import shutil; print(shutil.which('ffmpeg'))\"` "
                "still prints None in a brand-new window, ffmpeg's install "
                "directory was not actually added to your persistent PATH -- "
                "run `where ffmpeg` in that new terminal and add the "
                "directory it reports to your User PATH manually."
            )

        process = await asyncio.create_subprocess_exec(
            _FFMPEG_PATH,
            "-i",
            "pipe:0",
            "-f",
            "s16le",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            str(NUM_CHANNELS),
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        pcm_bytes, stderr = await process.communicate(input=mp3_bytes)

        if process.returncode != 0:
            error = stderr.decode(errors="replace")
            raise RuntimeError(
                f"FFmpeg failed to decode Edge-TTS audio: {error}"
            )

        return pcm_bytes