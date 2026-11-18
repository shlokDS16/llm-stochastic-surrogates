"""Tests for Amendment A1 (split-half variance, test-inversion interval, degenerate-cell rules)."""
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import estimators as E  # noqa: E402

DESIGN = E.Design(["W", "F", "T"], [4, 2, 2])
KEYS = list(itertools.product(range(4), range(2), range(2)))


def lognormal(rng, n):
    return (np.exp(rng.standard_normal(n)) - np.exp(0.5)) / np.sqrt((np.exp(1) - 1) * np.exp(1))


def test_projectors_match_term_ss_and_sum_to_total():
    names, projs, ptot = E.term_projectors(DESIGN)
    d = np.random.default_rng(0).normal(size=16)
    ss, df = E.term_ss(d.reshape(1, 4, 2, 2))
    assert np.allclose([d @ P @ d for P, _ in projs], ss[0])
    assert [x for _, x in projs] == list(df)
    assert np.allclose(sum(P for P, _ in projs), ptot)
    assert names == E.term_names(DESIGN.factors)


def test_split_half_variance_tracks_true_variance_for_skewed_outcomes():
    """The normal-theory formula underestimates Var(g) for lognormal responses (about 0.68 of the truth at n = 50);
    split-half is within 12 % of the Monte Carlo truth."""
    rng = np.random.default_rng(1)
    d, vf, vs = [], [], []
    for _ in range(1500):
        y1, y0 = lognormal(rng, 50) + 0.5, lognormal(rng, 50)
        g, v = E.effect("cont", y1, y0)
        d.append(g)
        vf.append(v)
        vs.append(E.split_half_var("cont", y1, y0, rng, K=60))
    truth = np.var(d, ddof=1)
    assert np.mean(vf) / truth < 0.8                      # the defect being repaired
    assert abs(np.mean(vs) / truth - 1) < 0.12


def test_split_half_variance_unbiased_for_normal_and_binary():
    rng = np.random.default_rng(2)
    for kind, draw in [("cont", lambda: (rng.standard_normal(50) + 0.5, rng.standard_normal(50))),
                       ("binary", lambda: ((rng.random(50) < 0.6).astype(float), (rng.random(50) < 0.35).astype(float)))]:
        d, vs = [], []
        for _ in range(1200):
            y1, y0 = draw()
            d.append(E.effect(kind, y1, y0)[0])
            vs.append(E.split_half_var(kind, y1, y0, rng, K=60))
        assert abs(np.mean(vs) / np.var(d, ddof=1) - 1) < 0.10, kind


def test_estimate2_spread_unbiased_and_terms_sum_to_total():
    rng = np.random.default_rng(3)
    delta = 0.5 + 0.3 * (np.array([k[0] for k in KEYS]) - 1.5) / np.sqrt(1.25)       # spread S = 0.3 in W
    s2 = []
    for _ in range(120):
        cells = {k: (rng.standard_normal(50) + delta[i], rng.standard_normal(50)) for i, k in enumerate(KEYS)}
        r = E.estimate2(cells, DESIGN, "cont", rng=rng, intervals=(), K=60)
        s2.append(r["S2_untruncated"])
        assert np.isclose(sum(r["terms"].values()), 16 * r["S2_untruncated"])
    assert abs(np.mean(s2) - 0.09) < 0.015


def test_ti_interval_covers_finite_cell_spread():
    rng = np.random.default_rng(4)
    delta = 0.5 + 0.3 * (np.array([k[0] for k in KEYS]) - 1.5) / np.sqrt(1.25)
    hit, lo0 = 0, 0
    R = 120
    for _ in range(R):
        cells = {k: (rng.standard_normal(50) + delta[i], rng.standard_normal(50)) for i, k in enumerate(KEYS)}
        r = E.estimate2(cells, DESIGN, "cont", rng=rng, B=400, K=60, intervals=("ti_boot",), term_intervals=False)
        lo, hi = r["intervals"]["ti_boot"]["S2"]
        hit += lo <= 0.09 <= hi
        lo0 += lo > 0
    assert hit / R >= 0.88            # nominal 0.95; 120 replicates give a standard error of about 0.02
    assert lo0 / R > 0.85             # at S = 0.3 the test of S = 0 should usually reject


def test_degenerate_rules():
    rng = np.random.default_rng(5)
    ok = lambda: (rng.standard_normal(50) + 0.3, rng.standard_normal(50))
    cells = {k: ok() for k in KEYS}
    # equal constants: g = 0, v = (n1 + n0) / (n1 n0)
    cells[KEYS[0]] = (np.full(50, 5.0), np.full(50, 5.0))
    assert E.is_degenerate("cont", *cells[KEYS[0]]) == "equal_constant"
    g, v = E.effect("cont", *cells[KEYS[0]])
    assert g == 0 and np.isclose(v, 100 / 2500)
    r = E.estimate2(cells, DESIGN, "cont", rng=rng, intervals=(), K=40)
    assert r["status"] == "ok" and r["degenerate_equal_constant_cells"] == [KEYS[0]]
    assert np.isclose(r["v"][0], 100 / 2500) and np.isfinite(r["S2_untruncated"])
    # different constants: effect undefined -> flagged, caller switches to the raw-difference scale
    cells[KEYS[1]] = (np.full(50, 6.0), np.full(50, 5.0))
    assert E.is_degenerate("cont", *cells[KEYS[1]]) == "deterministic"
    r = E.estimate2(cells, DESIGN, "cont", rng=rng, intervals=())
    assert r["status"] == "deterministic_cells" and r["deterministic_cells"] == [KEYS[1]]
    r = E.estimate2(cells, DESIGN, "diff", rng=rng, intervals=(), K=40)           # raw difference: always defined
    assert r["status"] == "ok" and np.isfinite(r["S2_untruncated"]) and abs(r["d"][1] - 1.0) < 1e-12
    # sd_floor keeps resampled cells finite
    g, v = E.effect("cont", np.full(10, 6.0), np.full(10, 5.0), sd_floor=0.3)
    assert np.isfinite(g) and np.isfinite(v)


def test_diff_kind_variance_and_unbiased_spread():
    y1, y0 = np.array([3.0, 5, 7, 9]), np.array([1.0, 2, 3, 4])
    d, v = E.effect("diff", y1, y0)
    assert np.isclose(d, 6 - 2.5) and np.isclose(v, y1.var(ddof=1) / 4 + y0.var(ddof=1) / 4)
