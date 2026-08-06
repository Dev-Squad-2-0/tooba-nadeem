"""
test_tts_edge.py
------------------

Standalone test script for app/voice/tts_edge.py (Edge-TTS), using the
project's existing configuration (app/config.py: EDGE_TTS_VOICE,
EDGE_TTS_RATE) and the existing synthesize_stream()/synthesize_full()
functions UNCHANGED.

Test/debug script only -- no application code is modified. Same pattern
as test_rag.py / test_recommender.py / test_sql.py at the project root.

Usage:
    python test_tts_edge.py
    python test_tts_edge.py "Ji bilkul, DHA Phase 6 mein Skyline Residency available hai."
    python test_tts_edge.py --voice ur-PK-UzmaNeural "Custom text here"
"""

import argparse
import asyncio
import time
from pathlib import Path

from app.voice.tts_edge import synthesize_stream, synthesize_full
from app import config

DEFAULT_TEXT = (
    "Ji bilkul, aap ka budget aur city ke hisaab se maine kuch options "
    "dekhe hain. Skyline Residency Lahore ke DHA Phase 6 mein available hai."
)

OUTPUT_DIR = Path(__file__).resolve().parent / "test_output"


async def test_streaming(text: str, voice_override: str | None) -> None:
    """
    Exercises synthesize_stream() chunk by chunk, the same way
    app/voice/pipeline.py consumes it.
    """

    print(f"Voice: {voice_override or config.EDGE_TTS_VOICE}")
    print(f"Rate:  {config.EDGE_TTS_RATE}")
    print(f"Text:  {text}\n")

    original_voice = config.EDGE_TTS_VOICE
    if voice_override:
        # Temporarily override the existing config value for this run
        # rather than adding a new parameter to tts_edge.py -- keeps the
        # app module's interface unmodified.
        config.EDGE_TTS_VOICE = voice_override

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "test_stream_output.mp3"

    chunks = []
    chunk_count = 0
    first_chunk_time = None
    start = time.perf_counter()

    try:
        async for chunk in synthesize_stream(text):
            now = time.perf_counter()
            if first_chunk_time is None:
                first_chunk_time = now - start
                print(f"Time to FIRST audio chunk: {first_chunk_time:.3f}s")
            chunk_count += 1
            chunks.append(chunk)
    finally:
        config.EDGE_TTS_VOICE = original_voice

    total_time = time.perf_counter() - start

    if not chunks:
        print(
            "ERROR: no audio chunks were produced. Check network access to "
            "Edge-TTS and that the voice name is valid (run "
            "`edge-tts --list-voices` to see valid IDs)."
        )
        return

    audio_bytes = b"".join(chunks)
    out_path.write_bytes(audio_bytes)

    print(f"Total chunks:     {chunk_count}")
    print(f"Total audio size: {len(audio_bytes) / 1024:.1f} KB")
    print(f"Total synth time: {total_time:.3f}s")
    print(f"Saved to:         {out_path}")


async def test_full(text: str) -> None:
    """
    Exercises the non-streaming synthesize_full() convenience wrapper
    (the one used by the text-only /chat path, which has no live socket
    to stream into).
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / "test_full_output.mp3"

    start = time.perf_counter()
    audio_bytes = await synthesize_full(text)
    elapsed = time.perf_counter() - start

    if not audio_bytes:
        print("ERROR: synthesize_full() returned no audio.")
        return

    out_path.write_bytes(audio_bytes)
    print(f"synthesize_full(): {len(audio_bytes) / 1024:.1f} KB in {elapsed:.3f}s")
    print(f"Saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Standalone Edge-TTS test (does not modify app code)."
    )
    parser.add_argument("text", nargs="?", default=DEFAULT_TEXT)
    parser.add_argument(
        "--voice", default=None,
        help="Override config.EDGE_TTS_VOICE for this run only "
             "(e.g. ur-PK-UzmaNeural).",
    )
    args = parser.parse_args()

    print("=== Streaming test (synthesize_stream) ===")
    asyncio.run(test_streaming(args.text, args.voice))

    print("\n=== Non-streaming test (synthesize_full) ===")
    asyncio.run(test_full(args.text))


if __name__ == "__main__":
    main()