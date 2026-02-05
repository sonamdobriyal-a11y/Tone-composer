from __future__ import annotations

import logging
import os
import re

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None

logger = logging.getLogger(__name__)


class GeminiABCError(Exception):
    """Problem creating ABC notation with Gemini."""


_CODE_FENCE_RE = re.compile(r"```(?:abc)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _load_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    if load_dotenv:
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            return api_key
    raise GeminiABCError("GEMINI_API_KEY is not set; please export it before generating ABC.")


def _extract_abc(text: str) -> str:
    if not text:
        return ""

    match = _CODE_FENCE_RE.search(text)
    if match:
        text = match.group(1)

    lines = [line.rstrip() for line in text.splitlines()]
    # Find the first 'X:' line and keep everything after.
    for idx, line in enumerate(lines):
        if line.strip().startswith("X:"):
            return "\n".join(lines[idx:]).strip() + "\n"

    # Fallback: if model omitted X: but includes other headers, keep as-is.
    return "\n".join(lines).strip() + "\n"


def generate_abc_from_prompt(
    prompt: str,
    key: str = "D",
    meter: str = "4/4",
    unit_note_length: str = "1/8",
    bars: int = 16,
) -> str:
    if genai is None:
        raise GeminiABCError("`google-genai` is missing; install it with `pip install google-genai` before using Gemini ABC.")

    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        raise GeminiABCError("Provide a prompt to generate ABC notation.")

    api_key = _load_api_key()
    client = genai.Client(api_key=api_key)

    model_id = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    system = (
        "You are an expert music notation assistant. Output ONLY valid ABC notation, no commentary.\n"
        "Rules:\n"
        "- Output must start with headers: X:1, L:, M:, K:\n"
        "- Use L to control default duration; include barlines.\n"
        "- Avoid chord symbols in quotes.\n"
        "- Keep it strictly monophonic.\n"
        f"- Generate about {bars} bars.\n"
    )

    user = (
        f"Create an ABC melody based on this prompt: {clean_prompt}\n"
        f"Use: L:{unit_note_length}, M:{meter}, K:{key}\n"
    )

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[system, user],
        )
    except Exception as exc:
        # Surface the real failure reason (auth, quota, model name, network) without leaking keys.
        raise GeminiABCError(f"Gemini text generation failed: {type(exc).__name__}: {exc}") from exc

    abc_text = _extract_abc(getattr(response, "text", "") or "")
    if "X:" not in abc_text or "K:" not in abc_text:
        raise GeminiABCError("Gemini returned invalid ABC. Try simplifying your prompt.")

    logger.info("Generated ABC length: %d chars", len(abc_text))
    return abc_text
