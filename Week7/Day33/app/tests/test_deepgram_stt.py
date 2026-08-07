"""
test_stt_deepgram.py
----------------------

Standalone test script for app/voice/stt_deepgram.py (Deepgram streaming
STT), using the project's existing configuration (app/config.py) and the
existing DeepgramSTT class UNCHANGED.

Test/debug script only -- no application code is modified. Same pattern
as test_rag.py / test_recommender.py / test_sql.py at the project root.

Two modes:

  1. FILE MODE (default, no extra dependencies, deterministic --
     recommended for reproducible testing/grading):

         python test_stt_deepgram.py path/to/audio.wav

     The WAV file MUST be 16-bit PCM, mono, 16000 Hz -- this matches the
     encoding/sample_rate/channels hardcoded in
     app/voice/stt_deepgram.py's connect() call, which this script does
     NOT modify or override. If you have an MP3 or other format, convert
     it first:

         ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav

  2. MIC MODE (optional -- requires `pip install sounddevice`, which is
     NOT added to requirements.txt since this is a manual test tool, not
     part of the application):

         python test_stt_deepgram.py --mic
         python test_stt_deepgram.py --mic --seconds 15
"""

import argparse

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

import asyncio
import sys
import time
import wave
from pathlib import Path

from app.voice.stt_deepgram import DeepgramSTT
from app import config

from app.voice.transcript_corrections import apply_corrections

TRANSCRIPTS: list[str] = []


async def _on_final_transcript(transcript: str) -> None:
    transcript = apply_corrections(transcript)  # <-- added
    TRANSCRIPTS.append(transcript)
    print(f"[FINAL TRANSCRIPT] {transcript}")


async def run_file_mode(wav_path: Path) -> None:
    if not wav_path.exists():
        print(f"ERROR: file not found: {wav_path}")
        sys.exit(1)

    with wave.open(str(wav_path), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frame_rate = wf.getframerate()
        n_frames = wf.getnframes()

        if channels != 1 or sample_width != 2 or frame_rate != 16000:
            print(
                "ERROR: audio format mismatch.\n"
                f"  Found:    channels={channels}, sample_width_bytes={sample_width}, "
                f"sample_rate={frame_rate}\n"
                "  Required: channels=1, sample_width_bytes=2 (16-bit), sample_rate=16000\n"
                "  (must match app/voice/stt_deepgram.py's connect() options)\n\n"
                "Convert with:\n"
                f'  ffmpeg -i "{wav_path}" -ar 16000 -ac 1 -sample_fmt s16 fixed.wav'
            )
            sys.exit(1)

        audio_bytes = wf.readframes(n_frames)

    duration_seconds = n_frames / frame_rate
    print(f"Loaded {wav_path.name}: {duration_seconds:.2f}s of 16kHz mono PCM16 audio")

    if not config.DEEPGRAM_API_KEY:
        print("ERROR: DEEPGRAM_API_KEY is not set in .env")
        sys.exit(1)

    stt = DeepgramSTT(on_final_transcript=_on_final_transcript)
    print("Starting Deepgram connection...")
    await stt.start()

    # Paced roughly like real-time audio rather than dumped in one call --
    # closer to how the live pipeline actually feeds it.
    chunk_size = 3200  # 100ms of 16kHz 16-bit mono audio
    chunk_duration = chunk_size / (16000 * 2)

    print("Streaming audio to Deepgram...")
    start = time.perf_counter()
    for i in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[i : i + chunk_size]
        await stt.send_audio(chunk)
        await asyncio.sleep(chunk_duration)

    print("Finished streaming. Waiting for final transcript(s)...")
    await asyncio.sleep(2.0)  # let Deepgram flush the last is_final segment

    await stt.stop()
    elapsed = time.perf_counter() - start

    print(f"\nDone in {elapsed:.2f}s (audio duration was {duration_seconds:.2f}s)")
    if TRANSCRIPTS:
        print(f"\nFull combined transcript:\n  {' '.join(TRANSCRIPTS)}")
    else:
        print(
            "\nWARNING: no final transcript was received. Check:\n"
            "  - DEEPGRAM_API_KEY is valid\n"
            "  - the WAV file actually contains speech\n"
            "  - DEEPGRAM_LANGUAGE in .env matches the spoken language\n"
        )


async def run_mic_mode(seconds: int) -> None:
    try:
        import sounddevice as sd
    except ImportError:
        print(
            "Mic mode requires `sounddevice`, which is not part of "
            "requirements.txt (manual test tool only). Install with:\n\n"
            "  pip install sounddevice\n"
        )
        sys.exit(1)

    if not config.DEEPGRAM_API_KEY:
        print("ERROR: DEEPGRAM_API_KEY is not set in .env")
        sys.exit(1)

    stt = DeepgramSTT(on_final_transcript=_on_final_transcript)
    print("Starting Deepgram connection...")
    await stt.start()

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def _callback(indata, frames, time_info, status):
        if status:
            print("sounddevice status:", status)

            print("Max amplitude:", abs(indata).max())
        loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))

    print(f"Recording for {seconds}s -- speak now (Ctrl+C to stop early)...")

    stream = sd.RawInputStream(
        samplerate=16000, channels=1, dtype="int16", callback=_callback,
    )

    async def _pump_queue():
        with stream:
            end_time = time.perf_counter() + seconds
            while time.perf_counter() < end_time:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=0.5)
                    await stt.send_audio(chunk)
                except asyncio.TimeoutError:
                    continue

    try:
        await _pump_queue()
    except KeyboardInterrupt:
        pass

    print("Recording stopped. Waiting for final transcript(s)...")
    await asyncio.sleep(2.0)
    await stt.stop()

    if TRANSCRIPTS:
        print(f"\nFull combined transcript:\n  {' '.join(TRANSCRIPTS)}")
    else:
        print("\nWARNING: no final transcript was received.")


def main():
    parser = argparse.ArgumentParser(
        description="Standalone Deepgram STT test (does not modify app code)."
    )
    parser.add_argument(
        "wav_path", nargs="?", default=None,
        help="Path to a 16-bit PCM mono 16kHz WAV file (file mode).",
    )
    parser.add_argument(
        "--mic", action="store_true",
        help="Use live microphone input instead of a file (requires sounddevice).",
    )
    parser.add_argument(
        "--seconds", type=int, default=10,
        help="Recording duration in mic mode (default: 10s).",
    )
    args = parser.parse_args()

    if args.mic:
        asyncio.run(run_mic_mode(args.seconds))
    elif args.wav_path:
        asyncio.run(run_file_mode(Path(args.wav_path)))
    else:
        parser.print_help()
        print(
            "\nExample:\n"
            "  python test_stt_deepgram.py sample_audio/test_query.wav\n"
            "  python test_stt_deepgram.py --mic --seconds 8"
        )


if __name__ == "__main__":
    main()