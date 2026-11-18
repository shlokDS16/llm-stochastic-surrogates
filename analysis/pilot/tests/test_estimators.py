import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import estimators as E  # noqa: E402


def test_anova_terms_sum_to_total():
    rng = np.random.default_rng(1)
    d = rng.normal(size=(3, 4, 2, 2))
    ss, df = E.term_ss(d)
    total = ((d - d.mean(axis=(1, 2, 3), keepdims=True)) ** 2).sum(axis=(1, 2, 3))
    assert np.allclose(ss.sum(1), total)
    assert df.sum() == 4 * 2 * 2 - 1


def test_corrected_terms_sum_to_C_S2():
    rng = np.random.default_rng(2)
    d = rng.normal(size=(1, 4, 2, 2))
    v = rng.uniform(0.02, 0.05, size=d.shape)
    css, df = E.corrected_ss(d, v)
    C = 16
    s2 = E.spread_s2(d.reshape(1, -1), v.reshape(1, -1))[0]
    assert np.isclose(css.sum(), C * s2)


def test_spread_unbiased_for_known_S():
    rng = np.random.default_rng(3)
    C, S, v = 16, 0.3, 0.04
    delta = rng.normal(size=C)
    delta = (delta - delta.mean()) / np.sqrt(((delta - delta.mean()) ** 2).mean()) * S
    est = [E.spread_s2(delta + rng.normal(scale=np.sqrt(v), size=C), np.full(C, v)) for _ in range(4000)]
    assert abs(np.mean(est) - S ** 2) < 0.004


def test_hedges_and_logor_basic():
    rng = np.random.default_rng(4)
    y1, y0 = rng.normal(0.5, 1, 4000), rng.normal(0, 1, 4000)
    g, v = E.effect("cont", y1, y0)
    assert abs(g - 0.5) < 0.05 and abs(v - 2 / 4000) < 0.0005
    a, b = np.array([1] * 30 + [0] * 20, float), np.array([1] * 10 + [0] * 40, float)
    lor, v = E.effect("binary", a, b)
    assert np.isclose(lor, np.log(30 * 40 / (20 * 10))) and np.isclose(v, 1 / 30 + 1 / 20 + 1 / 10 + 1 / 40)
    lor0, v0 = E.effect("binary", np.ones(10), np.zeros(10))   # zero cells -> 0.5 correction, finite
    assert np.isfinite(lor0) and np.isfinite(v0)


def test_estimate_runs_and_basic_interval_contains_point():
    rng = np.random.default_rng(5)
    design = E.Design(["W", "F", "T"], [4, 2, 2])
    import itertools
    cells = {k: (rng.normal(0.5 + 0.3 * (k[0] - 1.5), 1, 50), rng.normal(0, 1, 50)) for k in itertools.product(range(4), range(2), range(2))}
    res = E.estimate(cells, design, "cont", rng=rng, B=300)
    lo, hi = res["boot"]["S2_ci_basic"]
    assert lo <= res["S2_untruncated"] <= hi
    assert set(res["terms"]) == {"W", "F", "T", "W:F", "W:T", "F:T", "W:F:T"}
