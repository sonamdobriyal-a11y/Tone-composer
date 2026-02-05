from __future__ import annotations

import math

from abc_parser import parse_abc


COMPLEX_ABC = """X:1
L:1/8
M:4/4
K:Bb
"Bb" B2 FB- B2 FB- | B2 FB- B2 FB- | B2 FB- B2 Bc- | c2 Bd- d2 Bc- |"C7" c2 =Bd- d2 Bc- |
c2 =Bd- d2 c_B- |"F7" B2 =Bd- d2 Bc- | c8 || 
"Bb" d=BcB cB_BA |"Bb7" BcB_A BcB_A |"Eb" G_AGF GAGF |"Eb7" G_AGF GAGF |"Ab" _AGF_A GF_GF |
"""


def test_parse_glued_runs_and_accidentals():
    events = parse_abc(COMPLEX_ABC)
    assert len(events) >= 20
    names = [event.pitch.nameWithOctave for event in events[:8]]
    assert names[:4] == ["B4", "F4", "B4", "F4"]
    assert "G4" in names


def test_ties_extend_duration():
    abc = """X:1
L:1/4
K:C
B2-B2"""
    events = parse_abc(abc)
    assert len(events) == 1
    assert math.isclose(events[0].duration, 4.0, rel_tol=1e-6)


def test_accidentals_apply_correctly():
    abc = """X:1
L:1/8
K:C
^c _d =e"""
    events = parse_abc(abc)
    names = [event.pitch.nameWithOctave for event in events]
    assert names == ["C#5", "D-5", "E5"]
