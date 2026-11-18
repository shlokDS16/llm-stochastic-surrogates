"""Tests for analysis/acme/gstudy.py. Run: .venv/Scripts/python.exe -I -m pytest analysis/acme/tests -q"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gstudy as g  # noqa: E402


# ---------------------------------------------------------------------------------------------------------------------------
# helpers: build a noiseless array from known effects
# ---------------------------------------------------------------------------------------------------------------------------
def centred_pattern(rng, shape):
    """Random array with zero mean along every axis (sum-to-zero effects), unit sum of squares."""
    x = rng.standard_normal(shape)
    for _ in range(3):
        for ax in range(x.ndim):
            x = x - x.mean(axis=ax, keepdims=True)
    return x / np.sqrt((x ** 2).sum())


def build(rng, sizes, ems):
    """sizes: dict facet -> n (facets in order given); ems: dict term-tuple -> target mean square SS/df (SS = N/n_X * sum eff^2).
    Returns the noiseless array mu + sum of orthogonal sum-to-zero effects with exactly those mean squares."""
    facets = list(sizes)
    N = int(np.prod(list(sizes.values())))
    arr = np.full([sizes[f] for f in facets], 3.7)
    for X, target in ems.items():
        shape = [sizes[f] if f in X else 1 for f in facets]
        pat = centred_pattern(rng, [sizes[f] for f in X])
        df = int(np.prod([sizes[f] - 1 for f in X]))
        nX = int(np.prod([sizes[f] for f in X]))
        ss = target * df
        eff = pat * np.sqrt(ss * nX / N)            # N/nX * sum(eff^2) = ss
        arr = arr + eff.reshape(shape)
    return arr


def ems3(n_m, n_w, n_o, s):
    """Expected mean squares written out exactly as in PREREG section 3 (independent of gstudy's general recursion)."""
    r, mw, wo, w = s["res"], s["MW"], s["WO"], s["W"]
    return {
        ("M", "W", "O"): r,
        ("M", "W"): r + n_o * mw,
        ("W", "O"): r + n_m * wo,
        ("W",): r + n_o * mw + n_m * wo + n_m * n_o * w,
        ("M",): r + n_o * mw + n_w * n_o * s["M"],
        ("O",): r + n_m * wo + n_m * n_w * s["O"],
        ("M", "O"): r + n_w * s["MO"],
    }


TRUE3 = dict(res=0.40, MW=0.20, WO=0.10, W=0.30, M=0.50, O=0.25, MO=0.15)


# ---------------------------------------------------------------------------------------------------------------------------
# exact recovery
# ---------------------------------------------------------------------------------------------------------------------------
def test_exact_recovery_three_facets():
    rng = np.random.default_rng(11)
    n_m, n_w, n_o = 14, 10, 2
    arr = build(rng, dict(M=n_m, W=n_w, O=n_o), ems3(n_m, n_w, n_o, TRUE3))
    d = g.decompose(arr, g.FACETS3)
    for k, v in TRUE3.items():
        assert d["components"][k] == pytest.approx(v, abs=1e-10), k
    tot = sum(TRUE3.values())
    for k, v in TRUE3.items():
        assert d["shares"][k] == pytest.approx(v / tot, abs=1e-10)
        assert d["shares_untruncated"][k] == pytest.approx(v / tot, abs=1e-10)


def test_exact_recovery_one_order():
    rng = np.random.default_rng(12)
    n_m, n_w = 13, 10
    t = dict(MW=0.35, W=0.20, M=0.45)       # no O: the residual is M x W
    ems = {("M", "W"): t["MW"], ("W",): t["MW"] + n_m * t["W"], ("M",): t["MW"] + n_w * t["M"]}
    arr = build(rng, dict(M=n_m, W=n_w), ems)
    d = g.decompose(arr, g.FACETS2)
    assert d["names"] == ["M", "W", "MW"]
    for k, v in t.items():
        assert d["components"][k] == pytest.approx(v, abs=1e-10), k
    assert "res" not in d["components"]


def test_negative_component_truncated_but_reported():
    rng = np.random.default_rng(13)
    n_m, n_w, n_o = 14, 10, 2
    s = dict(TRUE3, WO=-0.1 / 14)          # MS_WO = 0.3 < MS_res = 0.4: negative estimate
    ems = ems3(n_m, n_w, n_o, s)
    arr = build(rng, dict(M=n_m, W=n_w, O=n_o), ems)
    d = g.decompose(arr, g.FACETS3)
    assert d["components"]["WO"] == pytest.approx(s["WO"], abs=1e-10)
    assert d["components_truncated"]["WO"] == 0.0 and d["shares"]["WO"] == 0.0
    tot = sum(max(v, 0) for v in s.values())
    assert d["shares"]["W"] == pytest.approx(s["W"] / tot, abs=1e-10)
    # untruncated shares use the signed sum
    assert d["shares_untruncated"]["WO"] == pytest.approx(s["WO"] / sum(s.values()), abs=1e-10)


def test_four_facet_consistent_with_three_facet_plus_temperature():
    """Replicating a three-facet array over T plus a sum-to-zero T offset: 4-facet components equal the 3-facet ones (the 3-facet
    residual becomes M x W x O) and the T component is the quadratic form of the offsets."""
    rng = np.random.default_rng(14)
    n_m, n_w, n_o, n_t = 14, 10, 2, 4
    arr3 = build(rng, dict(M=n_m, W=n_w, O=n_o), ems3(n_m, n_w, n_o, TRUE3))
    tau = np.array([-0.9, -0.2, 0.3, 0.8])
    tau -= tau.mean()
    arr4 = arr3[..., None] + tau.reshape(1, 1, 1, n_t)
    d4 = g.decompose(arr4, g.FACETS4)
    d3 = g.decompose(arr3, g.FACETS3)
    for k in ("M", "O", "MO", "W", "MW", "WO"):
        assert d4["components"][k] == pytest.approx(d3["components"][k], abs=1e-10), k
    assert d4["components"]["MWO"] == pytest.approx(d3["components"]["res"], abs=1e-10)
    assert d4["components"]["T"] == pytest.approx((tau ** 2).sum() / (n_t - 1), abs=1e-10)
    for k in ("MT", "OT", "MOT", "WT", "MWT", "WOT", "res"):
        assert d4["components"][k] == pytest.approx(0.0, abs=1e-10), k


def test_unbiased_for_known_components_monte_carlo():
    """Independent check of the EMS algebra: mean of the estimates over random draws equals the generating components."""
    rng = np.random.default_rng(15)
    n_m, n_w, n_o = 14, 10, 2
    s = dict(res=0.4, MW=0.2, WO=0.1, W=0.3)
    al = rng.standard_normal(n_m)
    al -= al.mean()
    al *= np.sqrt(0.5 * (n_m - 1) / (al ** 2).sum())                      # theta2_M = sum a^2 / (n_m - 1) = 0.5
    om = np.array([-1.0, 1.0]) * 0.5                                       # theta2_O = sum o^2 / (n_o - 1) = 0.5
    est = []
    names = None
    for _ in range(2500):
        y = (al[:, None, None] + om[None, None, :] + np.sqrt(s["W"]) * rng.standard_normal((1, n_w, 1))
             + np.sqrt(s["MW"]) * rng.standard_normal((n_m, n_w, 1)) + np.sqrt(s["WO"]) * rng.standard_normal((1, n_w, n_o))
             + np.sqrt(s["res"]) * rng.standard_normal((n_m, n_w, n_o)))
        names, c, _ = g._core(y, g.FACETS3)
        est.append(c)
    est = np.array(est)
    truth = dict(M=0.5, O=0.5, MO=0.0, **s)
    for i, nm in enumerate(names):
        se = est[:, i].std(ddof=1) / math.sqrt(len(est))
        assert abs(est[:, i].mean() - truth[nm]) < 4.5 * se, (nm, est[:, i].mean(), truth[nm], se)


# ---------------------------------------------------------------------------------------------------------------------------
# bootstrap
# ---------------------------------------------------------------------------------------------------------------------------
def test_bootstrap_reproducible_and_seed_sensitive():
    rng = np.random.default_rng(21)
    y = rng.standard_normal((14, 10, 2))
    a = g.bootstrap(y, g.FACETS3, B=300, seed=20261106)
    b = g.bootstrap(y, g.FACETS3, B=300, seed=20261106)
    c = g.bootstrap(y, g.FACETS3, B=300, seed=20261107)
    assert np.array_equal(a["comps"], b["comps"]) and np.array_equal(a["shares"], b["shares"])
    assert not np.array_equal(a["comps"], c["comps"])
    d = g.bootstrap(y, g.FACETS3, B=300, seed=20261106, chunk=7)           # chunking does not change the draws
    assert np.allclose(a["comps"], d["comps"])
    assert np.array_equal(g.bootstrap(y, g.FACETS3, 50, [20261106, 3, 1])["comps"], g.bootstrap(y, g.FACETS3, 50, [20261106, 3, 1])["comps"])


def test_bootstrap_matches_manual_resample():
    rng = np.random.default_rng(22)
    y = rng.standard_normal((6, 8, 2))
    b = g.bootstrap(y, g.FACETS3, B=5, seed=3)
    idx = np.random.default_rng(3).integers(0, 8, size=(5, 8))
    for i in range(5):
        ref = g.decompose(y[:, idx[i], :], g.FACETS3)
        assert np.allclose(b["comps"][i], [ref["components"][n] for n in b["names"]])
    assert np.allclose(b["shares"].sum(axis=1), 1.0)


def test_bootstrap_models_resampled_runs_and_differs():
    rng = np.random.default_rng(23)
    y = rng.standard_normal((6, 8, 2))
    a = g.bootstrap(y, g.FACETS3, B=40, seed=5)
    m = g.bootstrap(y, g.FACETS3, B=40, seed=5, resample_models=True)
    assert m["comps"].shape == a["comps"].shape and not np.allclose(a["comps"], m["comps"])


# ---------------------------------------------------------------------------------------------------------------------------
# set-up SD, D-study, pooling
# ---------------------------------------------------------------------------------------------------------------------------
def test_setup_sd_values():
    rng = np.random.default_rng(31)
    y = rng.standard_normal((5, 10, 2)) * np.arange(1, 6)[:, None, None]
    s = g.setup_sd(y, B=200, seed=1)
    assert np.allclose(s["sd"], [y[m].reshape(-1).std(ddof=1) for m in range(5)])
    assert np.all(s["lo"] < s["hi"])
    assert s["median"] == pytest.approx(np.median(s["sd"]))
    s1 = g.setup_sd(y[:, :, 0], B=50, seed=1)           # one order
    assert np.allclose(s1["sd"], y[:, :, 0].std(axis=1, ddof=1))


def test_dstudy_formula_and_monotone():
    comps = dict(W=0.2, MW=0.1, WO=0.05, res=0.15, M=0.4)
    d = g.dstudy(comps, [10, 20], [1, 2])
    assert d["se"][0, 1] == pytest.approx(math.sqrt(0.3 / 10 + 0.2 / 20))
    assert d["se"][0, 0] == pytest.approx(math.sqrt(0.5 / 10))
    assert np.all(np.diff(g.dstudy(comps)["se"], axis=0) < 0)
    assert g.dstudy_min_design(comps, target=0.1)[0] >= 10
    assert g.dstudy(dict(W=-1.0, MW=0.0, WO=0.0, res=0.0), [5], [1])["se"][0, 0] == 0.0


def test_pool_items_median_mean_and_absent_terms():
    rng = np.random.default_rng(41)
    a2 = rng.standard_normal((6, 8, 2))
    a1 = rng.standard_normal((6, 8))
    items = [dict(name="a", arr=a2, facets=g.FACETS3), dict(name="b", arr=a1, facets=g.FACETS2),
             dict(name="c", arr=a2 * 2, facets=g.FACETS3)]
    p = g.pool_items(items, B=100, seed=9)
    assert set(p["names"]) == {"M", "O", "MO", "W", "MW", "WO", "res"}
    assert p["item_point"][1, p["names"].index("O")] == 0.0 and p["item_point"][1, p["names"].index("res")] == 0.0
    assert p["item_point"][1, p["names"].index("MW")] > 0          # the one-order item's M x W (the residual) is MW
    assert np.allclose(p["mean"], p["item_point"].mean(axis=0)) and np.allclose(p["median"], np.median(p["item_point"], axis=0))
    assert np.allclose(p["item_point"][0], p["item_point"][2])      # scale invariance
    assert np.allclose(p["mean_boot"], p["item_boot"].mean(axis=0))
    q = g.pool_items([dict(name="a", arr=a2, facets=g.FACETS3), dict(name="a2", arr=a2, facets=g.FACETS3)], B=60, seed=9)
    assert not np.allclose(q["item_boot"][0], q["item_boot"][1])    # independent wording draws within item


# ---------------------------------------------------------------------------------------------------------------------------
# hypotheses
# ---------------------------------------------------------------------------------------------------------------------------
def test_iu_pvalue():
    assert g.iu_pvalue([0.01, 0.2, 0.03, 0.5, 0.04]) == 0.04          # k = 5 -> 3rd smallest
    assert g.iu_pvalue([0.5, 0.01, 0.2, 0.03]) == 0.03                 # k = 4 -> 2nd smallest
    assert g.iu_pvalue([0.3]) == 0.3
    assert g.iu_pvalue([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]) == 0.6     # k = 7 -> 4th smallest


def test_holm():
    adj = g.holm_adjust({"H1": 0.01, "H2": 0.04, "H3": 0.03})
    assert adj["H1"] == pytest.approx(0.03) and adj["H3"] == pytest.approx(0.06) and adj["H2"] == pytest.approx(0.06)
    assert g.holm_adjust({"H1": None, "H2": 0.001, "H3": 0.5})["H1"] == 1.0


def _items_with_setup_sd(rng, sds, n_m=14, n_w=10, n_o=2):
    return [dict(name=f"P{i}", arr=sd * rng.standard_normal((n_m, n_w, n_o))) for i, sd in enumerate(sds)]


def test_h2_decision_and_p():
    rng = np.random.default_rng(51)
    se = {f"P{i}": 0.1 for i in range(5)}
    hi = g.hypotheses(_items_with_setup_sd(rng, [1, 1, 1, 0.01, 0.01]), None, se, B=400, seed=1)["H2"]
    assert hi["holds"] and hi["n_hold"] == 3 and hi["need"] == 3 and hi["p_raw"] == 0.0
    lo = g.hypotheses(_items_with_setup_sd(rng, [1, 1, 0.01, 0.01, 0.01]), None, se, B=400, seed=1)["H2"]
    assert not lo["holds"] and lo["n_hold"] == 2
    ps = sorted(r["p_one_sided"] for r in lo["items"])
    assert lo["p_raw"] == ps[2] and lo["p_raw"] > 0.5


def test_h3_h1_signs():
    rng = np.random.default_rng(52)
    n_m, n_w = 14, 10

    def item(kind):
        s = dict(res=0.2, MW=0.0, WO=0.0, W=0.0, M=0.3, O=0.0, MO=0.0)
        s.update(kind)
        return build(rng, dict(M=n_m, W=n_w, O=2), ems3(n_m, n_w, 2, s))

    items_mw = [dict(name=f"I{i}", arr=item(dict(MW=0.6))) for i in range(4)]
    out = g.hypotheses(items_mw, None, None, B=300, seed=2)
    assert out["H3"]["estimate"] > 0.4 and out["H3"]["p_raw"] < 0.05
    items_w = [dict(name=f"I{i}", arr=item(dict(W=0.6, MW=0.0))) for i in range(4)]
    assert g.hypotheses(items_w, None, None, B=300, seed=2)["H3"]["estimate"] < -0.2
    # H1: a large wording share and a tiny T offset -> wording share minus T share clearly positive
    arr4 = []
    for i in range(4):
        a3 = item(dict(W=0.5, MW=0.3))
        tau = np.array([-0.05, 0.0, 0.0, 0.05])
        arr4.append(dict(name=f"I{i}", arr=a3[..., None] + tau.reshape(1, 1, 1, 4) + 0.01 * rng.standard_normal((n_m, n_w, 2, 4))))
    h = g.hypotheses(items_mw, arr4, None, B=300, seed=2)["H1"]
    assert h["estimate"] > 0.5 and h["p_raw"] < 0.05 and "T" in h["T_terms"] and "res" not in h["T_terms"]


# ---------------------------------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------------------------------
def test_cli_roundtrip(tmp_path):
    import pandas as pd
    rng = np.random.default_rng(61)
    rows = []
    for item, n_o in (("P1", 2), ("P4", 1)):
        for m in range(5):
            for w in range(6):
                for o in range(n_o):
                    for T in (0.3, 0.7, 1.0, 1.5):
                        rows.append(dict(model=f"m{m}", item=item, W=f"W{w}", O=str(o) if n_o == 2 else "", variant="main", T=str(T),
                                         delta=0.5 * m + rng.standard_normal() * (0.2 + 0.1 * T)))
    rows.append(dict(model="m0", item="P1", W="W0", O="0", variant="decoy", T="1.0", delta=99.0))
    pd.DataFrame(rows).to_csv(tmp_path / "eff.csv", index=False)
    pd.DataFrame(dict(item=["P1", "P4"], sd=[2.0, 4.0])).to_csv(tmp_path / "sc.csv", index=False)
    pd.DataFrame(dict(item=["P1", "P4"], se=[0.01, 0.01])).to_csv(tmp_path / "se.csv", index=False)
    pd.DataFrame(dict(model=["m4"], item=["P4"])).to_csv(tmp_path / "ex.csv", index=False)
    g.main(["--effects", str(tmp_path / "eff.csv"), "--scale", str(tmp_path / "sc.csv"), "--single-site-se", str(tmp_path / "se.csv"),
            "--exclude", str(tmp_path / "ex.csv"), "--out", str(tmp_path / "out"), "--B", "60", "--exploratory-models"])
    out = tmp_path / "out"
    for f in ("components_by_item.csv", "pooled_shares.csv", "setup_sd.csv", "dstudy.csv", "hypotheses.json", "summary.json"):
        assert (out / f).exists(), f
    comp = pd.read_csv(out / "components_by_item.csv")
    assert set(comp["analysis"]) == {"T1", "4facet"}
    p4 = comp[(comp["item"] == "P4") & (comp["analysis"] == "T1")]
    assert p4["n_models"].iloc[0] == 4                                   # m4 excluded for P4
    assert "res" not in set(p4["component"])
    sd = pd.read_csv(out / "setup_sd.csv")
    assert sd[sd["item"] == "P1"]["setup_sd"].max() < 5                  # divided by sd, decoy row ignored


# ---------------------------------------------------------------------------------------------------------------------------
# amendment A1 pieces (separate option; the preregistered estimator above is untouched)
# ---------------------------------------------------------------------------------------------------------------------------
def test_jackknife_correct_leaves_unbiased_mean_alone_and_removes_ratio_bias():
    rng = np.random.default_rng(71)
    x = rng.standard_normal(10)
    loo = np.array([np.delete(x, i).mean() for i in range(10)])[:, None]
    assert g.jackknife_correct(np.array([x.mean()]), loo)[0] == pytest.approx(x.mean())
    # nonlinear statistic 1 / mean(y): bias about CV^2 = 2.5 percent; the corrected value is much closer to the truth on average
    est, cor = [], []
    for _ in range(3000):
        y = 1.0 + 0.5 * rng.standard_normal(10)
        r = 1.0 / y.mean()
        loo_r = np.array([1.0 / np.delete(y, i).mean() for i in range(10)])[:, None]
        est.append(r)
        cor.append(g.jackknife_correct(np.array([r]), loo_r)[0])
    assert abs(np.mean(cor) - 1.0) < 0.5 * abs(np.mean(est) - 1.0)


def test_shrink_offset_sets_fixed_quadratic_form_to_unbiased_estimate():
    rng = np.random.default_rng(72)
    y = rng.standard_normal((14, 10, 2)) + np.linspace(-0.3, 0.3, 14)[:, None, None]
    point = g.decompose(y, g.FACETS3)
    D = g._shrink_offset(y, g.FACETS3, "W", point)
    world_mean = np.broadcast_to(y.mean(axis=1, keepdims=True) + D, y.shape)       # same mean array for every wording, no random terms
    w = g.decompose(world_mean, g.FACETS3)
    for k in ("M", "O", "MO"):
        assert w["components"][k] == pytest.approx(max(point["components"][k], 0.0), abs=1e-10), k
    for k in ("W", "MW", "WO", "res"):
        assert abs(w["components"][k]) < 1e-10
    # a noiseless array whose fixed effects are exact: nothing to shrink
    n_m, n_w, n_o = 14, 10, 2
    exact = build(np.random.default_rng(73), dict(M=n_m, W=n_w, O=n_o), ems3(n_m, n_w, n_o, dict(res=0.0, MW=0.0, WO=0.0, W=0.0, M=0.5, O=0.2, MO=0.1)))
    assert np.abs(g._shrink_offset(exact, g.FACETS3, "W", g.decompose(exact, g.FACETS3))).max() < 1e-9


def test_student_pooled_and_pvalues():
    rng = np.random.default_rng(74)
    n_m, n_w = 14, 10

    def item(kind):
        s = dict(res=0.3, MW=0.0, WO=0.0, W=0.0, M=0.0, O=0.0, MO=0.0)
        s.update(kind)
        return build(rng, dict(M=n_m, W=n_w, O=2), ems3(n_m, n_w, 2, s)) + 0.3 * rng.standard_normal((n_m, n_w, 2))
    items = [dict(name=f"I{i}", arr=item(dict(MW=0.8)), facets=g.FACETS3) for i in range(5)]
    p = g.pool_items(items, B=300, seed=3, estimator="A1")
    assert p["estimator"]["interval"] == "student" and p["loo_boot"].shape[:3] == (5, 300, 10)
    sp = g.student_pooled(p, np.eye(len(p["names"])))
    assert np.allclose(sp["est"], p["item_point"].mean(axis=0))
    assert np.all(sp["lo"] <= sp["est"] + 1e-12) and np.all(sp["est"] <= sp["hi"] + 1e-12)
    c = np.zeros((1, len(p["names"])))
    c[0, p["names"].index("MW")], c[0, p["names"].index("W")] = 1.0, -1.0
    s2 = g.student_pooled(p, c)
    assert s2["est"][0] > 0.3 and g.student_p(s2, 0, "greater") < 0.05 and g.student_p(s2, 0, "two") < 0.1
    # reproducible
    p2 = g.pool_items(items, B=300, seed=3, estimator="A1")
    assert np.array_equal(p["item_boot"], p2["item_boot"])
    # subset of items
    s3 = g.student_pooled(p, np.eye(len(p["names"])), sel=[0])
    assert np.allclose(s3["est"], p["item_point"][0])


def test_estimator_a1_through_hypotheses_and_cli(tmp_path):
    import pandas as pd
    rng = np.random.default_rng(75)
    rows = []
    for item, n_o in (("P1", 2), ("P4", 1), ("P5", 2)):
        for m in range(5):
            for w in range(6):
                for o in range(n_o):
                    for T in (0.3, 0.7, 1.0, 1.5):
                        rows.append(dict(model=f"m{m}", item=item, W=f"W{w}", O=str(o) if n_o == 2 else "", variant="main", T=str(T),
                                         delta=0.5 * m + rng.standard_normal() * (0.2 + 0.1 * T)))
    pd.DataFrame(rows).to_csv(tmp_path / "eff.csv", index=False)
    pd.DataFrame(dict(item=["P1", "P4", "P5"], sd=[2.0, 4.0, 1.0])).to_csv(tmp_path / "sc.csv", index=False)
    pd.DataFrame(dict(item=["P1", "P4", "P5"], se=[0.01, 0.01, 0.01])).to_csv(tmp_path / "se.csv", index=False)
    g.main(["--effects", str(tmp_path / "eff.csv"), "--scale", str(tmp_path / "sc.csv"), "--single-site-se", str(tmp_path / "se.csv"),
            "--out", str(tmp_path / "out"), "--B", "40", "--estimator", "A1"])
    import json
    h = json.loads((tmp_path / "out" / "hypotheses.json").read_text())
    for k in ("H1", "H2", "H3"):
        assert h[k]["p_holm"] is not None and 0 <= h[k]["p_holm"] <= 1
    assert h["H3"]["estimator"] == "A1"
    comp = pd.read_csv(tmp_path / "out" / "components_by_item.csv")
    assert (comp["share_lo"] <= comp["share"] + 1e-9).all() and (comp["share"] <= comp["share_hi"] + 1e-9).all()
