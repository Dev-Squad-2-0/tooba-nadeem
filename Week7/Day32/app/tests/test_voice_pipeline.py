"""
End-to-end Voice Pipeline Test
------------------------------
[... unchanged docstring ...]
"""

import asyncio
import json
import wave
from pathlib import Path

import websockets

WS_URL = "ws://127.0.0.1:8000/ws/voice/test_voice"
INPUT_AUDIO = "sample_audio/query.wav"
OUTPUT_AUDIO = "test_output/response.mp3"

# Must match app/voice/stt_deepgram.py's connection config
# (encoding="linear16", sample_rate=16000, channels=1). This test sends raw
# PCM straight to the same socket production STT expects audio on -- it
# does not transcode, so the source file must already be in this format.
EXPECTED_SAMPLE_RATE = 16000
EXPECTED_CHANNELS = 1
EXPECTED_SAMPWIDTH = 2  # 16-bit

# Real silence appended after the audio so Deepgram's own endpointing
# (300ms, server-side) fires a final transcript on its own, on the
# still-open connection -- mirroring a real mic client pausing. We
# deliberately do NOT send {"type": "end"} to trigger the response: in
# pipeline.py, "end" calls DeepgramSTT.stop(), which sends send_finalize()
# and immediately cancels the listener task with no guarantee the final
# transcript arrives first. "end" means hang up the call, not "utterance
# done" -- so it's sent once, at the very end, purely for cleanup.
TRAILING_SILENCE_SECONDS = 1.0


def _load_pcm_frames(path: str) -> bytes:
    with wave.open(path, "rb") as wf:
        fmt = (wf.getframerate(), wf.getnchannels(), wf.getsampwidth())
        expected = (EXPECTED_SAMPLE_RATE, EXPECTED_CHANNELS, EXPECTED_SAMPWIDTH)
        if fmt != expected:
            raise ValueError(
                f"{path} is {fmt[0]}Hz/{fmt[1]}ch/{fmt[2]*8}-bit, but the "
                f"STT connection expects {expected[0]}Hz/{expected[1]}ch/"
                f"{expected[2]*8}-bit linear16. Re-record/convert the "
                f"sample file -- this test does not resample."
            )
        return wf.readframes(wf.getnframes())


async def main():
    output_path = Path(OUTPUT_AUDIO)
    output_path.parent.mkdir(exist_ok=True)

    print("=" * 70)
    print("Connecting to Voice Agent...")
    print("=" * 70)

    pcm = _load_pcm_frames(INPUT_AUDIO)
    silence = b"\x00" * int(
        EXPECTED_SAMPLE_RATE * EXPECTED_CHANNELS * EXPECTED_SAMPWIDTH
        * TRAILING_SILENCE_SECONDS
    )

    async with websockets.connect(WS_URL, max_size=None) as ws:
        print("Sending audio...")
        for i in range(0, len(pcm), 4096):
            await ws.send(pcm[i:i + 4096])

        # Trailing silence, not a control message -- see comment above.
        for i in range(0, len(silence), 4096):
            await ws.send(silence[i:i + 4096])

        print("Waiting for response...\n")

        transcript = None
        response_text = None
        audio_bytes = bytearray()

        while True:
            msg = await ws.recv()

            if isinstance(msg, bytes):
                audio_bytes.extend(msg)
                continue

            event = json.loads(msg)

            if event["type"] == "transcript":
                transcript = event["text"]
                print("=" * 70)
                print("TRANSCRIPT")
                print("=" * 70)
                print(transcript)

            elif event["type"] == "response_text":
                response_text = event["text"]
                print("\n" + "=" * 70)
                print("LLM RESPONSE")
                print("=" * 70)
                print(response_text)

            elif event["type"] == "response_audio_end":
                break

        # Clean hang-up, sent only after the response has fully arrived.
        await ws.send(json.dumps({"type": "end"}))

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        print(f"Transcript : {transcript}")
        print(f"Response   : {response_text}")
        print(f"Audio Saved: {output_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())