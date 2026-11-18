"""Shared simulation pieces for the recoverability check (statistician, 2026-10-16): outcome samplers, empirical shapes
taken from the observed pilot responses, and the true-effect grids. Imported by diagnose_variance.py and simulate_recovery2.py."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def expit(z):
    return 1 / (1 + np.exp(-z))


def pattern(levels):
    v = np.arange(levels, dtype=float)
    v -= v.mean()
    return v / np.sqrt((v ** 2).mean())


def true_effects(shape, S, structure, mu):
    """Grid of true cell effects with finite-cell spread exactly S. shape = (W, F, T[, O])."""
    w = pattern(shape[0]).reshape((-1,) + (1,) * (len(shape) - 1))
    f = pattern(shape[1]).reshape((1, -1) + (1,) * (len(shape) - 2))
    g = w * np.ones(shape) if structure == "W" else (np.sqrt(0.5) * w + np.sqrt(0.5) * f) * np.ones(shape)
    g = g - g.mean()
    g = g / np.sqrt((g ** 2).mean()) if S > 0 else g * 0
    return mu + S * g


# observed pilot shapes: (file, paradigm key, transform). OLMo-2 1B probe responses (W0, T = 1.0, both formats).
EMP_SOURCES = {
    "emp_P2d_raw": ("runs/pilot-probe/olmo2-1b-instruct/P2d.jsonl", "raw"),     # babies per day, raw estimate: skew 4.8, ex.kurt 25
    "emp_P2b_raw": ("runs/pilot-probe/olmo2-1b-instruct/P2b.jsonl", "raw"),     # Chicago population, raw: skew 3.9, ex.kurt 16
    "emp_P4_raw": ("runs/pilot-probe/olmo2-1b-instruct/P4.jsonl", "raw"),       # gambler, raw count: skew 7.6, ex.kurt 57
    "emp_P2c_log": ("runs/pilot-probe/olmo2-1b-instruct/P2c.jsonl", "log"),     # Everest, log estimate: skew -2.3, ex.kurt 5
    "emp_P3": ("runs/pilot-stage-test/olmo2-1b-instruct/P3.jsonl", "raw"),      # sunk cost rating 1-9, ceiling at 9 (621 responses)
    "emp_P2d_log": ("runs/pilot-probe/olmo2-1b-instruct/P2d.jsonl", "log"),     # babies, log estimate: skew 0.4, ex.kurt -1
    "emp_P2b_log": ("runs/pilot-probe/olmo2-1b-instruct/P2b.jsonl", "log"),     # Chicago, log estimate: skew -2.3, ex.kurt 7
    "emp_P4_log1p": ("runs/pilot-probe/olmo2-1b-instruct/P4.jsonl", "log1p"),   # gambler, log(1+x) (the preregistered primary): skew 3.4, ex.kurt 15
}


def load_empirical(name):
    """Within-arm-centred, pooled, unit-SD responses of one observed pilot paradigm (valid, non-greedy)."""
    path, tf = EMP_SOURCES[name]
    rows = [json.loads(l) for l in (ROOT / path).read_text(encoding="utf8").splitlines() if l.strip()]
    rows = [r for r in rows if r["valid"] and not r["greedy"]]
    y = np.array([r["y"] for r in rows], float)
    x = np.array([r["x"] for r in rows])
    if tf == "log":
        keep = y > 0
        y, x = np.log(y[keep]), x[keep]
    elif tf == "log1p":
        y = np.log1p(y)
    for a in (0, 1):
        y[x == a] -= y[x == a].mean()
    return y / y.std(ddof=1)


class Sampler:
    """draw(rng, delta) -> (y1, y0) for one cell with true standardised effect delta (log odds ratio for binary)."""

    def __init__(self, family, n, emp=None):
        self.family, self.n, self.emp = family, n, emp

    def draw(self, rng, delta):
        n = self.n
        f = self.family
        if f == "binary":
            p0 = 0.35
            p1 = expit(np.log(p0 / (1 - p0)) + delta)
            return (rng.random(n) < p1).astype(float), (rng.random(n) < p0).astype(float)
        if f == "normal":
            return rng.standard_normal(n) + delta, rng.standard_normal(n)
        if f == "skew":
            z = lambda: (np.exp(rng.standard_normal(n)) - np.exp(0.5)) / np.sqrt((np.exp(1) - 1) * np.exp(1))
            return z() + delta, z()
        if f.startswith("emp_"):
            return self.emp[rng.integers(0, len(self.emp), n)] + delta, self.emp[rng.integers(0, len(self.emp), n)]
        raise ValueError(f)


FAMILIES = ["binary", "normal", "skew"] + list(EMP_SOURCES)
PRIMARY_FAMILIES = ["binary", "normal", "emp_P3", "emp_P2c_log", "emp_P2d_log", "emp_P2b_log", "emp_P4_log1p"]   # preregistered primary metrics
STRESS_FAMILIES = ["skew", "emp_P2d_raw", "emp_P2b_raw", "emp_P4_raw"]                                           # raw-scale / heavy-tail shapes
