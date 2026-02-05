from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Tuple

from music21 import pitch

logger = logging.getLogger(__name__)


@dataclass
class NoteEvent:
    pitch: pitch.Pitch
    start: float
    duration: float
    velocity: float


_HEADER_RE = re.compile(r"^([A-Za-z]):\s*(.+)$")


def _parse_fraction(value: str) -> Fraction:
    try:
        return Fraction(value.strip())
    except (ValueError, TypeError):
        raise ValueError(f"Invalid fraction value for ABC header: {value!r}")


def _length_multiplier(body: str, index: int) -> Tuple[Fraction, int]:
    start = index
    numerator = 0
    has_numer = False
    while index < len(body) and body[index].isdigit():
        numerator = numerator * 10 + int(body[index])
        has_numer = True
        index += 1

    if index < len(body) and body[index] == "/":
        index += 1
        denominator = 0
        has_denom = False
        while index < len(body) and body[index].isdigit():
            denominator = denominator * 10 + int(body[index])
            has_denom = True
            index += 1
        if not has_denom:
            denominator = 2
        if not has_numer:
            numerator = 1
        return Fraction(numerator, denominator), index

    if has_numer:
        return Fraction(numerator, 1), index
    return Fraction(1, 1), start


def _apply_accidental(p: pitch.Pitch, accidental: str) -> None:
    if not accidental:
        return
    if "=" in accidental:
        p.accidental = pitch.Accidental("natural")
        return

    alter = accidental.count("^") - accidental.count("_")
    if alter:
        acc = pitch.Accidental(alter)
        p.accidental = acc


def parse_abc(abc_text: str) -> List[NoteEvent]:
    lines = []
    default_len = Fraction(1, 8)
    for raw_line in abc_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%"):
            continue
        header = _HEADER_RE.match(line)
        if header:
            key, value = header.groups()
            if key.upper() == "L":
                default_len = _parse_fraction(value)
            continue
        lines.append(line)
    base_quarter = default_len / Fraction(1, 4)
    body = "".join(lines)

    events: List[NoteEvent] = []
    current_time = 0.0
    idx = 0
    last_event: NoteEvent | None = None
    tie_active = False
    # Minimal tuplet support: e.g. "(3ABC" => three notes in the time of two.
    tuplet_remaining = 0
    tuplet_scale = 1.0

    while idx < len(body):
        char = body[idx]
        if char in " \t\r\n|:[]":
            idx += 1
            continue
        if char == "(":
            # Tuplet marker like "(3" or "(2". We only apply scaling to the next N notes.
            idx += 1
            if idx < len(body) and body[idx].isdigit():
                n = int(body[idx])
                idx += 1
                tuplet_remaining = n
                tuplet_scale = 2.0 / 3.0 if n == 3 else 1.0
            continue
        if char == '"':
            idx += 1
            while idx < len(body) and body[idx] != '"':
                idx += 1
            idx += 1
            continue

        if char.lower() == "z":
            idx += 1
            length_multiplier, idx = _length_multiplier(body, idx)
            duration = float(base_quarter * length_multiplier)
            current_time += duration
            tie_active = False
            continue

        accidental = ""
        while idx < len(body) and body[idx] in "^_=":
            accidental += body[idx]
            idx += 1

        if idx >= len(body):
            break

        char = body[idx]
        if char.upper() not in "ABCDEFG":
            logger.warning("Skipping unsupported ABC token: %s", char)
            idx += 1
            continue

        note_letter = char
        idx += 1
        octave_shift = 0
        while idx < len(body) and body[idx] in "',":
            octave_shift += 1 if body[idx] == "'" else -1
            idx += 1

        length_multiplier, idx = _length_multiplier(body, idx)
        duration = float(base_quarter * length_multiplier) * tuplet_scale
        tie_marker = False
        if idx < len(body) and body[idx] == "-":
            tie_marker = True
            idx += 1

        octave = 5 if note_letter.islower() else 4
        octave += octave_shift
        step = note_letter.upper()
        try:
            p = pitch.Pitch(step + str(octave))
        except Exception:
            logger.warning("Could not build pitch for note %s%s", step, octave)
            current_time += duration
            tie_active = False
            continue

        _apply_accidental(p, accidental)
        velocity = 0.8
        event = NoteEvent(pitch=p, start=current_time, duration=duration, velocity=velocity)

        if tie_active and last_event and last_event.pitch.nameWithOctave == event.pitch.nameWithOctave:
            last_event.duration += duration
        else:
            events.append(event)
            last_event = event

        tie_active = tie_marker
        current_time += duration
        if tuplet_remaining > 0:
            tuplet_remaining -= 1
            if tuplet_remaining == 0:
                tuplet_scale = 1.0

    logger.info("Parsed %d note events", len(events))
    logger.debug(
        "First 30 pitch tokens: %s",
        [e.pitch.nameWithOctave for e in events[:30]],
    )
    return events
