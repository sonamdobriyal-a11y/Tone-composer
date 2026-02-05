from __future__ import annotations

import os
from functools import lru_cache

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from audio_pipeline import abc_to_audio, abc_to_wav_bytes
from gemini_abc import GeminiABCError, generate_abc_from_prompt
from gemini_music import GeminiMusicError, generate_gemini_music_audio
from samplings import temperature_sampling, top_p_sampling


APP_TITLE = "Vihaan Music API"


class PromptRequest(BaseModel):
    prompt: str = Field(default="", description="Text prompt.")


class HFGenerateRequest(PromptRequest):
    top_p: float = Field(default=0.9, ge=0.05, le=1.0)
    temperature: float = Field(default=1.0, ge=0.1, le=2.5)
    max_length: int = Field(default=1024, ge=64, le=2048)


class ABCRequest(BaseModel):
    abc: str = Field(min_length=1, description="ABC notation.")


class GeminiABCRequest(PromptRequest):
    key: str = Field(default="D")
    meter: str = Field(default="4/4")
    unit_note_length: str = Field(default="1/8")
    bars: int = Field(default=16, ge=4, le=64)


class GeminiAudioRequest(PromptRequest):
    bpm: int = Field(default=120, ge=40, le=240)
    density: float = Field(default=0.8, ge=0.0, le=1.0)
    brightness: float = Field(default=0.7, ge=0.0, le=1.0)
    guidance: float = Field(default=4.0, ge=0.1, le=20.0)
    duration_seconds: int = Field(default=12, ge=6, le=30)


app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _load_hf_components():
    tokenizer = AutoTokenizer.from_pretrained("sander-wood/text-to-music")
    model = AutoModelForSeq2SeqLM.from_pretrained("sander-wood/text-to-music")
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
    return tokenizer, model


def _hf_generate_abc(prompt: str, top_p: float, temperature: float, max_length: int) -> str:
    tokenizer, model = _load_hf_components()
    clean_prompt = (prompt or "").strip() or "A calm Indian jazz fusion melody."

    input_ids = tokenizer(
        clean_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )["input_ids"].to(next(model.parameters()).device)

    decoder_start_token_id = model.config.decoder_start_token_id
    if decoder_start_token_id is None:
        decoder_start_token_id = (
            tokenizer.bos_token_id
            or tokenizer.cls_token_id
            or tokenizer.pad_token_id
            or 0
        )

    decoder_input_ids = torch.tensor(
        [[decoder_start_token_id]],
        device=next(model.parameters()).device,
        dtype=torch.long,
    )
    eos_token_id = model.config.eos_token_id

    with torch.no_grad():
        for _ in range(max_length):
            outputs = model(input_ids=input_ids, decoder_input_ids=decoder_input_ids)
            logits = outputs.logits[:, -1, :]
            probs = torch.nn.functional.softmax(logits, dim=-1).squeeze(0).cpu().numpy()
            filtered = top_p_sampling(probs, top_p=top_p, return_probs=True)
            sampled_id = temperature_sampling(filtered, temperature=temperature)
            next_token = torch.tensor([[sampled_id]], device=decoder_input_ids.device)
            decoder_input_ids = torch.cat((decoder_input_ids, next_token), dim=1)
            if eos_token_id is not None and sampled_id == eos_token_id:
                break

    tune = tokenizer.decode(decoder_input_ids[0], skip_special_tokens=True)
    tune = tune.strip()
    if not tune:
        raise RuntimeError("Empty ABC output from model.")
    return f"X:1\n{tune}"


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/hf/abc")
def hf_abc(req: HFGenerateRequest):
    try:
        abc = _hf_generate_abc(
            prompt=req.prompt,
            top_p=req.top_p,
            temperature=req.temperature,
            max_length=req.max_length,
        )
        return {"abc": abc}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/abc/audio/wav")
def abc_wav(req: ABCRequest):
    try:
        wav_bytes = abc_to_wav_bytes(req.abc)
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/abc/audio/midi")
def abc_midi(req: ABCRequest):
    try:
        midi_bytes, _ = abc_to_audio(req.abc)
        if not midi_bytes:
            raise HTTPException(
                status_code=400,
                detail="MIDI export failed for this ABC (music21 could not parse it). Use WAV export or simplify the ABC.",
            )
        return Response(content=midi_bytes, media_type="audio/midi")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/gemini/abc")
def gemini_abc(req: GeminiABCRequest):
    try:
        abc = generate_abc_from_prompt(
            prompt=req.prompt,
            key=req.key,
            meter=req.meter,
            unit_note_length=req.unit_note_length,
            bars=req.bars,
        )
        return {"abc": abc}
    except GeminiABCError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/gemini/audio/wav")
def gemini_audio(req: GeminiAudioRequest):
    try:
        wav = generate_gemini_music_audio(
            prompt=req.prompt,
            bpm=req.bpm,
            density=req.density,
            brightness=req.brightness,
            guidance=req.guidance,
            duration_seconds=req.duration_seconds,
        )
        return Response(content=wav, media_type="audio/wav")
    except GeminiMusicError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
