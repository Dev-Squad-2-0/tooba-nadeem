import asyncio

from app.livekit_worker.tts_adapter import EdgeTTS


async def main():
    tts = EdgeTTS()

    stream = tts.synthesize(
        "Assalam o Alaikum, main Ahmed hoon. "
        "Aap ko kis property mein interest hai?"
    )

    audio_chunks = []

    async for event in stream:
        audio_chunks.append(event)

    print(f"Received {len(audio_chunks)} synthesized audio events.")
    print("Edge-TTS adapter synthesis: OK")


if __name__ == "__main__":
    asyncio.run(main())