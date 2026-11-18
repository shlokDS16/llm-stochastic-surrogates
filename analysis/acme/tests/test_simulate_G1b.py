"""Tests for analysis/acme/simulate_G1b.py. Run: .venv/Scripts/python.exe -I -m pytest analysis/acme/tests/test_simulate_G1b.py -q"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gstudy as G  # noqa: E402
import simulate_G1b as B  # noqa: E402
import simulate_G1 as S1  # noqa: E402

TOL = 0.02


def _shares(arr, facets):
    return G.decompose(arr, facets)["shares_untruncated"]


@pytest.mark.parametrize("lvl,wording,tsh", [("null", 0.25, 0.25), ("alt", 0.40, 0.10)])
def test_h1_generator_hits_target_shares(lvl, wording, tsh):
    name = f"H1_{lvl}"
    specs = B.scenario(name)
    rng = np.random.default_rng(1)
    for j in (0, B.N2):                                       # one two-order and one one-order item
        sp = specs[j]
        arr = B.gen_term_array(rng, sp, nw=3000)
        facets = G.FACETS4 if arr.ndim == 4 else G.FACETS3T
        sh = _shares(arr, facets)
        w = sh["W"] + sh["MW"]
        t = sum(v for k, v in sh.items() if "T" in k and k != "res")
        assert abs(w - wording) < TOL, (name, j, w)
        assert abs(t - tsh) < TOL, (name, j, t)


@pytest.mark.parametrize("lvl,mw,w", [("null", 0.30, 0.30), ("alt", 0.45, 0.15)])
def test_h3_generator_hits_target_shares(lvl, mw, w):
    specs = B.scenario(f"H3_{lvl}")
    rng = np.random.default_rng(2)
    for j in (0, B.N2):
        arr = S1.gen_delta(rng, specs[j], 6000, False, None)
        sh = _shares(arr, G.FACETS3 if arr.ndim == 3 else G.FACETS2)
        assert abs(sh["MW"] - mw) < TOL and abs(sh["W"] - w) < TOL, (j, sh)


@pytest.mark.parametrize("lvl,target", [("null", 0.2), ("alt", 0.4)])
def test_h2_true_median_setup_sd(lvl, target):
    specs = B.scenario(f"H2_{lvl}")
    rng = np.random.default_rng(3)
    for sp in specs:
        assert abs(B.true_median_sd(sp) - target) < 1e-12
    for j in (0, B.N2):                                       # empirical check of the definition on a large wording draw
        arr = S1.gen_delta(rng, specs[j], 40000, False, None)
        a = arr.reshape(arr.shape[0], -1) if arr.ndim == 2 else arr.reshape(arr.shape[0], -1)
        assert abs(np.median(a.std(axis=1, ddof=1)) - target) < 0.01 * target + 0.005


def test_h2_matches_hypotheses():
    specs = B.scenario("H2_null")
    rng = np.random.default_rng(4)
    items3 = [dict(name=f"i{j}", arr=S1.gen_delta(rng, sp, B.N_W, False, None)) for j, sp in enumerate(specs)]
    se = {i["name"]: B.C_P for i in items3}
    out = G.hypotheses(items3, None, se, B=60, seed=123, estimator="A1")
    p, _, _ = B.h2_from_arrays(items3, 60, 123, se)
    assert out["H2"]["p_raw"] == pytest.approx(p)


def test_resume_skips_done_replicates(tmp_path):
    name = "H2_null"
    assert len(B.pending_tasks(tmp_path, name, 5, 40)) == 5
    for rep in (0, 1, 3):
        row = {c: float("nan") for c in B.COLS}
        row.update(rep=rep, scenario=name)
        B.append_row(B.results_path(tmp_path, name), row)
    assert B.done_reps(B.results_path(tmp_path, name)) == {0, 1, 3}
    todo = B.pending_tasks(tmp_path, name, 5, 40)
    assert [t[1] for t in todo] == [2, 4]


def test_run_rep_smoke_and_determinism():
    r1 = B.run_rep(("H3_null", 0, 30))
    r2 = B.run_rep(("H3_null", 0, 30))
    assert 0.0 <= r1["p_H3"] <= 1.0 and r1["p_H3"] == r2["p_H3"] and r1["est_H3"] == r2["est_H3"]
    r = B.run_rep(("H1_null", 0, 30))
    assert 0.0 <= r["p_H1"] <= 1.0
