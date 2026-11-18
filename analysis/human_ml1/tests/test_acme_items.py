"""Small checks for analysis/human_ml1/acme_items.py (coding rules and grid construction)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acme_items as A  # noqa: E402


def raw_frame():
    # 6 respondents: forbid Yes / forbid No / allow Yes / allow No / Washington 1 / bin Laden 9 etc. built per column
    blank = " "
    d = pd.DataFrame({
        "referrer": ["s1"] * 6,
        "allowedforbiddena": ["Yes", "No", blank, blank, blank, blank],
        "allowedforbiddenb": [blank, blank, "Yes", "No", blank, blank],
        "allowedforbiddenGroup": ["forbidden", "forbidden", "allowed", "allowed", "allowed", "allowed"],
        "quotea": ["1", blank, blank, blank, blank, blank],
        "quoteb": [blank, "9", blank, blank, blank, blank],
        "quote": ["9", "1", blank, blank, blank, blank],
        "quoteGroup": ["liked source", "disliked source"] + ["liked source"] * 4,
        "reciprocityusa": ["Yes", blank, "No", blank, blank, blank],
        "reciprocityusb": [blank, "Yes", blank, "No", blank, blank],
        "reciprocityothera": ["Yes", blank, "Yes", blank, blank, blank],
        "reciprocityotherb": [blank, "Yes", blank, "Yes", blank, blank],
        "reciprocitygroup": ["Asked first", "Asked second", "Asked first", "Asked second", "Asked first", "Asked first"],
        "reciprocityus": ["Yes", "Yes", "No", "No", blank, blank],
    })
    return d


def test_coding_rules():
    tidy, _ = A.code_items(raw_frame())
    af = tidy["AF"].reset_index(drop=True)
    # forbid Yes -> anti-speech 1; forbid No -> 0; allow Yes -> 0; allow No -> 1 ; x1 = forbid
    assert af.x.tolist() == [1, 1, 0, 0] and af.y.tolist() == [1.0, 0.0, 0.0, 1.0]
    qa = tidy["QA"].reset_index(drop=True)
    assert qa.x.tolist() == [1, 0] and qa.y.tolist() == [9.0, 1.0]           # raw 1 (strongly agree) -> 9; raw 9 -> 1
    nr = tidy["NR"].reset_index(drop=True)
    # usa (US first) -> x0; usb (US second, other first) -> x1; y = Yes to US question
    assert nr.x.tolist() == [0, 1, 0, 1] and nr.y.tolist() == [1.0, 1.0, 0.0, 0.0]


def test_round2sig():
    assert A.round2sig_int(1234) == 1200 and A.round2sig_int(0.4) == 1 and A.round2sig_int(5.6) == 6 and A.round2sig_int(98765) == 99000


def test_grid_anchors_unique_sorted():
    rng = np.random.default_rng(1)
    y = np.exp(rng.normal(8, 1, 5000))
    lo_anchor, hi_anchor = 2000, 45500
    g = A.make_grid(y, [hi_anchor, lo_anchor])
    grid = g["grid"]
    assert grid == sorted(set(grid)) and all(isinstance(v, int) and v > 0 for v in grid)
    assert hi_anchor in grid and lo_anchor in grid and g["K_actual"] <= 15
    g2 = A.make_grid(y, [])
    assert g2["K_actual"] == 15
