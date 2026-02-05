from __future__ import annotations

import asyncio
import io
import logging
import os
import wave

import numpy as np

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None

logger = logging.getLogger(__name__)

PCM_SAMPLE_RATE = 48_000
PCM_CHANNELS = 2
PCM_WIDTH = 2
DEFAULT_DURATION = 18


class GeminiMusicError(Exception):
    """Problem creating a Gemini music tone."""


def _convert_pcm_to_wav(raw_bytes: bytes) -> bytes:
    if not raw_bytes:
        raise GeminiMusicError("Gemini returned no audio chunks.")
    samples = np.frombuffer(raw_bytes, dtype=np.int16)
    remainder = samples.size % PCM_CHANNELS
    if remainder:
        samples = samples[: -remainder]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(PCM_CHANNELS)
        wf.setsampwidth(PCM_WIDTH)
        wf.setframerate(PCM_SAMPLE_RATE)
        wf.writeframes(samples.tobytes())
    buffer.seek(0)
    return buffer.read()


async def _request_gemini_audio(
    prompt: str,
    bpm: int,
    density: float,
    brightness: float,
    guidance: float,
    duration_seconds: int,
) -> bytes:
    if genai is None or types is None:
        raise GeminiMusicError("`google-genai` is missing; install it with `pip install google-genai` before using Gemini audio.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and load_dotenv:
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiMusicError("GEMINI_API_KEY is not set; please export it before generating audio.")

    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
    audio_buffer = bytearray()

    async def receive_audio(session):
        async for message in session.receive():
            chunk_list = getattr(message.server_content, "audio_chunks", [])
            for chunk in chunk_list:
                audio_buffer.extend(chunk.data)

    async def run_session() -> None:
        model_id = os.environ.get("GEMINI_MUSIC_MODEL", "models/lyria-realtime-exp")
        async with client.aio.live.music.connect(model=model_id) as session:
            receive_task = asyncio.create_task(receive_audio(session))
            try:
                await session.set_weighted_prompts(
                    prompts=[types.WeightedPrompt(text=prompt, weight=1.0)]
                )
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(
                        bpm=bpm,
                        density=density,
                        brightness=brightness,
                        temperature=guidance,
                    )
                )

                await session.play()
                await asyncio.sleep(duration_seconds)
                try:
                    await session.stop()
                except Exception as exc:  # pragma: no cover
                    logger.debug("Gemini session stop failed: %s", exc)
            finally:
                # Ensure we don't hang waiting for the receive loop to finish.
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

    try:
        # Defensive timeout in case the underlying stream doesn't close cleanly.
        await asyncio.wait_for(run_session(), timeout=max(duration_seconds + 20, 45))
    except Exception as exc:
        raise GeminiMusicError(
            "Gemini audio generation failed or timed out. Verify GEMINI_API_KEY, network access, and try a shorter duration."
        ) from exc

    return bytes(audio_buffer)


def generate_gemini_music_audio(
    prompt: str,
    bpm: int = 120,
    density: float = 0.8,
    brightness: float = 0.7,
    guidance: float = 4.0,
    duration_seconds: int = DEFAULT_DURATION,
) -> bytes:
    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        raise GeminiMusicError("Provide a prompt to generate Gemini music.")

    loop = asyncio.new_event_loop()
    try:
        raw_audio = loop.run_until_complete(
            _request_gemini_audio(
                clean_prompt,
                bpm=bpm,
                density=density,
                brightness=brightness,
                guidance=guidance,
                duration_seconds=duration_seconds,
            )
        )
    finally:
        loop.close()

    return _convert_pcm_to_wav(raw_audio)
