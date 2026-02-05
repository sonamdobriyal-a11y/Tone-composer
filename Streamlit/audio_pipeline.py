from __future__ import annotations

import io
import logging
import math
import os
import tempfile
import wave

import numpy as np
from abc_parser import NoteEvent, parse_abc
from music21 import converter, note, stream

logger = logging.getLogger(__name__)

DEFAULT_BPM = 120


def _collapse_tempo(music_stream: stream.Stream) -> float:
    for _, _, mm in music_stream.metronomeMarkBoundaries():
        if mm and mm.number:
            return mm.number
    return DEFAULT_BPM


def _note_velocity(element: note.Note) -> float:
    if element.volume and element.volume.velocityScalar:
        value = float(element.volume.velocityScalar)
    elif element.volume and element.volume.velocity:
        value = float(element.volume.velocity) / 127.0
    else:
        value = 0.5
    return max(0.1, min(value, 1.0))


def _mix_tone(
    audio: np.ndarray,
    start_sample: int,
    length: int,
    freq: float,
    amplitude: float,
    sample_rate: int,
) -> None:
    if length <= 0:
        return

    t = np.linspace(0, length / sample_rate, length, endpoint=False)
    waveform = np.sin(2 * np.pi * freq * t)
    attack = min(int(0.01 * sample_rate), length // 3)
    release = min(int(0.05 * sample_rate), max(1, length - attack))
    envelope = np.ones(length)
    if attack > 0:
        envelope[:attack] = np.linspace(0, 1, attack)
    if release > 0 and release < length:
        envelope[-release:] = np.linspace(1, 0, release)

    window = waveform * envelope * amplitude
    end = min(len(audio), start_sample + length)
    audio[start_sample:end] += window[: end - start_sample]


def _events_from_stream(music_stream: stream.Stream) -> list[NoteEvent]:
    events: list[NoteEvent] = []
    for element in music_stream.recurse().notes:
        if isinstance(element, note.Rest):
            continue
        pitches = element.pitches if element.__class__.__name__ == "Chord" else [element.pitch]
        for single in pitches:
            start = float(element.offset)
            duration = float(element.duration.quarterLength) if element.duration else 0.0
            velocity = _note_velocity(element)
            events.append(
                NoteEvent(
                    pitch=single,
                    start=start,
                    duration=duration,
                    velocity=velocity,
                )
            )
    return events


def synthesize_events_audio(
    events: list[NoteEvent], sample_rate: int = 44100, bpm: float = DEFAULT_BPM
) -> np.ndarray:
    if not events:
        return np.zeros(sample_rate, dtype=np.float32)

    seconds_per_quarter = 60.0 / bpm
    total_beats = max(event.start + event.duration for event in events)
    total_samples = int(math.ceil(total_beats * seconds_per_quarter * sample_rate)) + 1
    audio = np.zeros(total_samples, dtype=np.float32)

    for event in events:
        freq = getattr(event.pitch, "frequency", None)
        if freq is None:
            continue
        start_sample = int(event.start * seconds_per_quarter * sample_rate)
        length_samples = int(event.duration * seconds_per_quarter * sample_rate)
        _mix_tone(
            audio=audio,
            start_sample=start_sample,
            length=max(1, length_samples),
            freq=freq,
            amplitude=event.velocity,
            sample_rate=sample_rate,
        )

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak
        audio *= 0.95
    return audio


def stream_to_midi_bytes(music_stream: stream.Stream) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tf:
        music_stream.write("midi", fp=tf.name)
    try:
        with open(tf.name, "rb") as midi_file:
            return midi_file.read()
    finally:
        try:
            os.remove(tf.name)
        except Exception:
            pass


def stream_to_wav_bytes(events: list[NoteEvent], sample_rate: int = 44100, bpm: float = DEFAULT_BPM) -> bytes:
    audio = synthesize_events_audio(events, sample_rate=sample_rate, bpm=bpm)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        audio_int16 = np.int16(audio * 32767)
        wf.writeframes(audio_int16.tobytes())
    buf.seek(0)
    return buf.getvalue()


def abc_to_wav_bytes(
    abc_notation: str, sample_rate: int = 44100, bpm: float = DEFAULT_BPM
) -> bytes:
    """
    Convert ABC -> WAV without relying on music21's ABC parser.

    This avoids some music21 edge cases (e.g. certain tuplets/objects reused in a Stream)
    while still producing audio for "valid-ish" ABC strings.
    """
    events = parse_abc(abc_notation)
    if not events:
        raise RuntimeError(
            "No note events found in ABC. Try simplifying the ABC or removing unsupported constructs."
        )
    return stream_to_wav_bytes(events, sample_rate=sample_rate, bpm=bpm)


def abc_to_audio(
    abc_notation: str, sample_rate: int = 44100, bpm: float | None = None
) -> tuple[bytes, bytes]:
    # Prefer our parser for audio. music21 is kept for MIDI export when it works.
    events = parse_abc(abc_notation)
    if not events:
        raise RuntimeError("No note events found in ABC.")

    bpm_to_use = bpm or DEFAULT_BPM
    wav_bytes = stream_to_wav_bytes(events, sample_rate=sample_rate, bpm=bpm_to_use)

    midi_bytes = b""
    try:
        music_stream = converter.parseData(abc_notation, format="abc")
        midi_bytes = stream_to_midi_bytes(music_stream)
        bpm_to_use = bpm or _collapse_tempo(music_stream)
        # Re-render WAV with tempo if music21 provided one.
        wav_bytes = stream_to_wav_bytes(events, sample_rate=sample_rate, bpm=bpm_to_use)
    except Exception as exc:
        logger.warning("music21 MIDI conversion failed; returning WAV only (%s)", exc)

    return midi_bytes, wav_bytes
