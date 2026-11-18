"""Estimators for the pilot (design v0.4, section 5). Pure numpy; no model code.

Cell effect d_c with sampling variance v_c:
  continuous : Hedges g (pooled within-condition SD), v = (n1+n0)/(n1 n0) + g^2/(2 (n1+n0))
  binary     : log odds ratio, 0.5 added to all four counts when any count is zero, v = sum 1/count
Spread (finite-cell, divisor C):
  S2hat = (1/C) [ sum_c (d_c - dbar)^2 - ((C-1)/C) sum_c v_c ]       (untruncated; S = sqrt(max(0, .)))
Decomposition: unweighted orthogonal ANOVA of the cell effects over a balanced crossed design;
  corrected term SS_t - (df_t / C) sum_c v_c ; corrected terms sum to C * S2hat.
Interval: response-level nonparametric bootstrap within cells; percentile and basic (pivotal) versions
  are both returned (basic is the working interval, see boot_summary).
Orientation: y1 = responses of the x=1 condition (canonical higher outcome), y0 = x=0.

Amendment A1 (statistician, 2026-10-16; see research/reports/statistician/2026-10-16-pilot-estimator-and-ml1-check.md):
  * v_c is estimated by split-half resampling (var_method='splithalf', the new default): the normal-theory formula
    underestimates Var(g) for skewed or heavy-tailed responses (it omits the skewness and kurtosis terms) and the
    bootstrap variance is also too small in heavy tails; split-half uses no distributional model.
  * interval: test inversion with variance-calibrated bootstrap errors ('ti_boot'), valid for the finite-cell S
    (the percentile interval targets the noisy spread of the observed d_c and under-covers).
  * degenerate cells (pooled SD = 0): equal constants -> d = 0, v = (n1+n0)/(n1 n0); different constants ->
    effect undefined, the grid is flagged and the caller switches that model x paradigm to kind='diff'
    (raw mean difference, response units).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np


# ----------------------------------------------------------------------------- effect sizes
def effect_from_moments(kind, n1, m1, s1sq, n0, m0, s0sq, sd_floor=0.0):
    """Vectorised over leading dims. For kind='binary', m is the proportion of ones.
    kind 'cont': Hedges g; sd_floor is a lower bound on the pooled SD (used only to keep bootstrap and split resamples
    finite; with sd_floor = 0 a zero pooled SD gives g = 0 when the arm means are equal, +-inf otherwise).
    kind 'diff': raw mean difference, v = s1^2/n1 + s0^2/n0 (response units; no standardisation)."""
    n1 = np.asarray(n1, float)
    n0 = np.asarray(n0, float)
    if kind == "binary":
        a = m1 * n1
        b = n1 - a
        c = m0 * n0
        dd = n0 - c
        any0 = (a == 0) | (b == 0) | (c == 0) | (dd == 0)
        k = np.where(any0, 0.5, 0.0)
        a, b, c, dd = a + k, b + k, c + k, dd + k
        d = np.log(a * dd / (b * c))
        v = 1 / a + 1 / b + 1 / c + 1 / dd
        return d, v
    if kind == "diff":
        return m1 - m0, s1sq / n1 + s0sq / n0
    df = n1 + n0 - 2
    sp = np.maximum(np.sqrt(((n1 - 1) * s1sq + (n0 - 1) * s0sq) / df), sd_floor)
    with np.errstate(divide="ignore", invalid="ignore"):
        dcoh = np.where((sp == 0) & (m1 == m0), 0.0, (m1 - m0) / sp)
    J = 1 - 3 / (4 * df - 1)
    g = J * dcoh
    v = (n1 + n0) / (n1 * n0) + g ** 2 / (2 * (n1 + n0))
    return g, v


def effect(kind, y1, y0, sd_floor=0.0):
    y1 = np.asarray(y1, float)
    y0 = np.asarray(y0, float)
    return effect_from_moments(kind, len(y1), y1.mean(), y1.var(ddof=1), len(y0), y0.mean(), y0.var(ddof=1), sd_floor)


def is_degenerate(kind, y1, y0):
    """Cell status for kind 'cont': 'ok', 'equal_constant' (pooled SD 0, equal means: g = 0 by rule) or
    'deterministic' (pooled SD 0, different means: g undefined, switch the grid to kind='diff')."""
    if kind != "cont":
        return "ok"
    y1 = np.asarray(y1, float)
    y0 = np.asarray(y0, float)
    # Float-safe (Amendment A2): "constant" = one distinct value per arm up to 1e-9 absolute, because repeated
    # log values have a float variance of about 1e-30, not 0. Inputs hold valid responses only (no NaN).
    const = lambda y: y.size > 0 and bool(np.all(np.abs(y - y[0]) <= 1e-9))
    if const(y1) and const(y0):
        return "equal_constant" if abs(y1[0] - y0[0]) <= 1e-9 else "deterministic"
    return "ok"


def boot_effect(kind, y1, y0, rng, B, sd_floor=0.0):
    """B bootstrap replicates of (d, v) for one cell, resampling responses within condition."""
    y1 = np.asarray(y1, float)
    y0 = np.asarray(y0, float)
    n1, n0 = len(y1), len(y0)
    s1 = y1[rng.integers(0, n1, size=(B, n1))]
    s0 = y0[rng.integers(0, n0, size=(B, n0))]
    return effect_from_moments(kind, n1, s1.mean(1), s1.var(1, ddof=1), n0, s0.mean(1), s0.var(1, ddof=1), sd_floor)


def _boot_var(kind, y1, y0, rng, B, m1, m0, sd_floor):
    s1 = y1[rng.integers(0, len(y1), size=(B, m1))]
    s0 = y0[rng.integers(0, len(y0), size=(B, m0))]
    d, _ = effect_from_moments(kind, m1, s1.mean(1), s1.var(1, ddof=1), m0, s0.mean(1), s0.var(1, ddof=1), sd_floor)
    return float(np.var(d, ddof=1))


def split_half_var(kind, y1, y0, rng, K=200, sd_floor=0.0, calibrate=True, Bc=300):
    """Distribution-free estimate of Var(d_c): K random splits of each arm into halves (A, B); E[(d_A - d_B)^2] =
    Var(d_A) + Var(d_B). The half-sample variances are scaled up to the full sample size.
    calibrate=False: first-order 1/n scaling, Var(d_full) = Var(d_half) * (1/n1 + 1/n0) / (1/n1h + 1/n0h).
    calibrate=True (default): the scaling factor is the bootstrap variance of d at the full size divided by the bootstrap
    variance at the two half sizes, which carries the second-order (1/n^2) terms the first-order law misses (a +4 % over-estimate
    for log odds ratios and +12 % for skewed log responses at n = 50).
    Needs no normal theory, so it keeps the skewness and kurtosis terms the analytic formula drops."""
    y1 = np.asarray(y1, float)
    y0 = np.asarray(y0, float)
    n1, n0 = len(y1), len(y0)
    a1, a0 = n1 // 2, n0 // 2
    p1 = np.argsort(rng.random((K, n1)), axis=1)
    p0 = np.argsort(rng.random((K, n0)), axis=1)
    A1, B1 = y1[p1[:, :a1]], y1[p1[:, a1:]]
    A0, B0 = y0[p0[:, :a0]], y0[p0[:, a0:]]
    mom = lambda x: (x.mean(1), x.var(1, ddof=1))
    dA, _ = effect_from_moments(kind, a1, *mom(A1), a0, *mom(A0), sd_floor)
    dB, _ = effect_from_moments(kind, n1 - a1, *mom(B1), n0 - a0, *mom(B0), sd_floor)
    raw = float(np.mean((dA - dB) ** 2))
    if calibrate:
        vfull = _boot_var(kind, y1, y0, rng, Bc, n1, n0, sd_floor)
        vhalf = _boot_var(kind, y1, y0, rng, Bc, a1, a0, sd_floor) + _boot_var(kind, y1, y0, rng, Bc, n1 - a1, n0 - a0, sd_floor)
        scale = vfull / vhalf if vhalf > 0 else (1 / n1 + 1 / n0) / ((1 / a1 + 1 / a0) + (1 / (n1 - a1) + 1 / (n0 - a0)))
    else:
        scale = (1 / n1 + 1 / n0) / ((1 / a1 + 1 / a0) + (1 / (n1 - a1) + 1 / (n0 - a0)))
    return raw * scale


# ----------------------------------------------------------------------------- spread
def spread_s2(d, v):
    """Untruncated moment estimator over the last axis (cells). d, v: (..., C)."""
    d = np.asarray(d, float)
    v = np.asarray(v, float)
    C = d.shape[-1]
    ss = ((d - d.mean(-1, keepdims=True)) ** 2).sum(-1)
    return (ss - (C - 1) / C * v.sum(-1)) / C


def spread(d, v):
    return np.sqrt(np.maximum(0.0, spread_s2(d, v)))


# ----------------------------------------------------------------------------- decomposition
def _subsets(k):
    for r in range(1, k + 1):
        yield from itertools.combinations(range(k), r)


def term_names(factors):
    return [":".join(factors[i] for i in A) for A in _subsets(len(factors))]


def term_ss(dgrid):
    """Orthogonal ANOVA sums of squares of d over a balanced crossed grid.
    dgrid: (B, L1, ..., Lk). Returns (ss: (B, nterms), df: (nterms,))."""
    B = dgrid.shape[0]
    levels = dgrid.shape[1:]
    k = len(levels)
    m = {}
    for r in range(k + 1):
        for A in itertools.combinations(range(k), r):
            axes = tuple(1 + i for i in range(k) if i not in A)
            m[A] = dgrid.mean(axis=axes, keepdims=True) if axes else dgrid
    ss, df = [], []
    for A in _subsets(k):
        e = 0
        for r in range(len(A) + 1):
            for Bs in itertools.combinations(A, r):
                e = e + (-1) ** (len(A) - r) * m[Bs]
        e = np.broadcast_to(e, dgrid.shape)
        ss.append((e ** 2).reshape(B, -1).sum(1))
        df.append(int(np.prod([levels[i] - 1 for i in A])))
    return np.stack(ss, 1), np.array(df)


def corrected_ss(dgrid, vgrid):
    """Bias-corrected term SS and df. dgrid, vgrid: (B, L1..Lk)."""
    ss, df = term_ss(dgrid)
    C = int(np.prod(dgrid.shape[1:]))
    vsum = vgrid.reshape(vgrid.shape[0], -1).sum(1)
    return ss - (df[None, :] / C) * vsum[:, None], df


# ----------------------------------------------------------------------------- full pipeline
@dataclass
class Design:
    factors: list  # e.g. ["W", "F", "T"]
    levels: list   # e.g. [4, 2, 2]

    @property
    def shape(self):
        return tuple(self.levels)

    @property
    def C(self):
        return int(np.prod(self.levels))


def estimate(cells, design: Design, kind: str, rng=None, B: int = 2000, canonical_sign: int = 1,
             ci_level: float = 0.95, with_boot: bool = True, var_method: str = "formula"):
    """cells: dict mapping a tuple of level indices -> (y1, y0). Returns a result dict.
    The point estimate uses the data; the interval uses B within-cell bootstrap draws.
    var_method 'formula' (design v0.4): v_c from the normal-theory formulas.
    var_method 'bootstrap' (proposed): v_c = variance of d_c over the B bootstrap draws, used everywhere v_c is used
    (the formula underestimates Var(g) for skewed or heavy-tailed responses, which biases S-hat upward)."""
    shape = design.shape
    keys = list(itertools.product(*[range(L) for L in shape]))
    assert set(keys) == set(cells), "cells must enumerate the full crossed design"
    d = np.empty(shape)
    v = np.empty(shape)
    for key in keys:
        d[key], v[key] = effect(kind, *cells[key])
    if with_boot or var_method == "bootstrap":
        rng = rng or np.random.default_rng(0)
        bd = np.empty((B,) + shape)
        bv = np.empty((B,) + shape)
        for key in keys:
            bd[(slice(None),) + key], bv[(slice(None),) + key] = boot_effect(kind, *cells[key], rng, B)
    if var_method == "bootstrap":
        v = bd.var(axis=0, ddof=1)
        bv = np.broadcast_to(v, bd.shape)
    out = point_summary(d, v, design)
    out["var_method"] = var_method
    z = 1.959964
    lo = d - z * np.sqrt(v)
    hi = d + z * np.sqrt(v)
    sig = (lo > 0) if canonical_sign > 0 else (hi < 0)
    out["sign_stability"] = float(sig.mean())
    out["sign_agreement"] = float((np.sign(d) == canonical_sign).mean())
    if with_boot:
        out["boot"] = boot_summary(bd, bv, design, d, v, ci_level)
    return out


def point_summary(d, v, design):
    C = design.C
    s2 = float(spread_s2(d.reshape(-1), v.reshape(-1)))
    css, df = corrected_ss(d[None], v[None])
    css = css[0]
    names = term_names(design.factors)
    denom = C * s2
    return {
        "C": C,
        "dbar": float(d.mean()),
        "S2_untruncated": s2,
        "S": float(np.sqrt(max(0.0, s2))),
        "terms": dict(zip(names, map(float, css))),
        "term_df": dict(zip(names, map(int, df))),
        "shares": {n: float(c / denom) for n, c in zip(names, css)} if s2 > 0 else None,
        "d": d.tolist(),
        "v": v.tolist(),
    }


def boot_summary(bd, bv, design, obs_d, obs_v, ci_level=0.95):
    """Bootstrap intervals for the spread and the corrected term sums of squares, two kinds:
      percentile : quantiles of the bootstrap statistic (design v0.4 wording);
      basic      : stat_hat - (q_{1-a/2} - target*), stat_hat - (q_{a/2} - target*), where target* is the
                   value of the estimand in the bootstrap world (the spread of the observed d_c, which
                   already contains their sampling noise). The percentile interval is centred on
                   target* = S2hat + mean(v)(C-1)/C, i.e. biased upward; the basic interval mimics the
                   estimation error and is the working interval.
    """
    B = bd.shape[0]
    C = design.C
    flat_d = bd.reshape(B, -1)
    flat_v = bv.reshape(B, -1)
    od = np.asarray(obs_d, float)
    ov = np.asarray(obs_v, float)
    s2 = spread_s2(flat_d, flat_v)
    s2_hat = float(spread_s2(od.reshape(-1), ov.reshape(-1)))
    s2_star = float(((od - od.mean()) ** 2).mean())            # spread of the observed d_c (divisor C)
    css, _ = corrected_ss(bd, bv)
    ss_raw, _ = term_ss(od[None])                               # uncorrected observed term SS = bootstrap-world truth
    css_hat, _ = corrected_ss(od[None], ov[None])
    a = (1 - ci_level) / 2
    q = lambda x: [float(np.quantile(x, a)), float(np.quantile(x, 1 - a))]
    basic = lambda hat, star, x: [float(hat - (np.quantile(x, 1 - a) - star)), float(hat - (np.quantile(x, a) - star))]
    sq = lambda iv: [float(np.sqrt(max(0.0, iv[0]))), float(np.sqrt(max(0.0, iv[1])))]
    names = term_names(design.factors)
    with np.errstate(divide="ignore", invalid="ignore"):
        shares = css / (C * s2)[:, None]
    ok = s2 > 0
    S2_basic = basic(s2_hat, s2_star, s2)
    shares_star = ss_raw[0] / ss_raw[0].sum() if ss_raw[0].sum() > 0 else np.full(len(names), np.nan)
    shares_hat = css_hat[0] / (C * s2_hat) if s2_hat > 0 else np.full(len(names), np.nan)
    return {
        "S2_ci_basic": S2_basic,
        "S_ci_basic": sq(S2_basic),
        "S_ci_percentile": q(np.sqrt(np.maximum(0.0, s2))),
        "S2_ci_percentile": q(s2),
        "dbar_ci": q(flat_d.mean(1)),
        "terms_ci_basic": {n: basic(float(css_hat[0, i]), float(ss_raw[0, i]), css[:, i]) for i, n in enumerate(names)},
        "shares_ci_basic": {n: (basic(float(shares_hat[i]), float(shares_star[i]), shares[ok, i])
                                if ok.sum() > 20 and s2_hat > 0 else None) for i, n in enumerate(names)},
        "share_valid_draws": float(ok.mean()),
        "S2_draws": s2,
        "share_draws": shares,
    }


# ============================================================================= Amendment A1 (2026-10-16)
def term_projectors(design: Design):
    """Orthogonal ANOVA term projectors on the C-vector of cell effects (cells in C order of itertools.product).
    Returns names, list of (P, df), and the total-spread projector I - 11'/C = sum of the term projectors.
    d' P_t d is the observed term sum of squares SS_t (identical to term_ss)."""
    k = len(design.levels)
    J = [np.full((L, L), 1.0 / L) for L in design.levels]
    M = [np.eye(L) - j for L, j in zip(design.levels, J)]
    names, out = term_names(design.factors), []
    for A in _subsets(k):
        P = np.ones((1, 1))
        for i in range(k):
            P = np.kron(P, M[i] if i in A else J[i])
        out.append((P, int(round(np.trace(P)))))
    C = design.C
    return names, out, np.eye(C) - np.full((C, C), 1.0 / C)


def _quad(dd, P):
    return np.einsum("...i,ij,...j->...", dd, P, dd)


def ti_interval(d, vsum, P, errors, ci_level=0.95, grid=41):
    """Test-inversion interval for the finite-cell target s = Delta' P Delta (P a term projector or the total-spread
    projector) using the statistic T(d) = d' P d - (tr P / C) * vsum, which is unbiased for s.
    For a candidate s the null effects are base + sqrt(s) * u (u = unit direction of P d, base = the part of d outside P),
    and `errors` (B x C) are added to simulate the sampling distribution of T. The interval is {s : T_obs lies between the
    alpha/2 and 1-alpha/2 quantiles of T under s}. Unlike a bootstrap interval for the plug-in spread it does not
    inherit the noise of the observed d_c as 'true' spread. Returns (lower, upper, T_obs) on the scale of s (>= 0)."""
    d = np.asarray(d, float).ravel()
    C = len(d)
    df = np.trace(P)
    a = (1 - ci_level) / 2
    corr = df / C * vsum
    t_obs = float(d @ P @ d - corr)
    Pd = P @ d
    nrm = np.linalg.norm(Pd)
    if nrm < 1e-12:                       # no observed direction: use the leading column of P
        j = int(np.argmax(np.linalg.norm(P, axis=0)))
        Pd, nrm = P[:, j], np.linalg.norm(P[:, j])
    u = Pd / nrm
    base = d - P @ d

    def q_at(s):
        dd = (base + np.sqrt(s)[:, None] * u[None, :])[:, None, :] + errors[None, :, :]
        T = _quad(dd, P) - corr
        return np.quantile(T, [a, 1 - a], axis=1)

    s0 = max(t_obs, 0.0)
    sd1 = float(np.std(_quad(base[None] + np.sqrt(s0) * u[None] + errors, P)))
    smax = s0 + 6.0 * sd1 + 1e-6
    for _ in range(4):
        s_grid = np.linspace(0.0, np.sqrt(smax), grid) ** 2
        qlo, qhi = q_at(s_grid)
        if qlo[-1] > t_obs:
            break
        smax *= 2.0
    qlo, qhi = np.maximum.accumulate(qlo), np.maximum.accumulate(qhi)
    lower = 0.0 if qhi[0] >= t_obs else float(np.interp(t_obs, qhi, s_grid))
    upper = float(np.interp(t_obs, qlo, s_grid)) if qlo[-1] > t_obs else float(s_grid[-1])
    if qlo[0] > t_obs:                    # even s = 0 is too large for the observed statistic
        upper = 0.0
    return lower, max(lower, upper), t_obs


def _calibrated_errors(bd, v, rng):
    """Bootstrap errors of d_c rescaled so that their variance equals the chosen v_c (cells with no bootstrap
    variation, e.g. constant cells, get Gaussian errors with variance v_c)."""
    e = bd - bd.mean(0, keepdims=True)
    vb = e.var(0, ddof=1)
    ok = vb > 1e-12
    scale = np.where(ok, np.sqrt(v / np.where(ok, vb, 1.0)), 0.0)
    e = e * scale
    z = rng.standard_normal(e.shape)
    return np.where(ok[None, :], e, z * np.sqrt(v)[None, :])


def estimate2(cells, design: Design, kind: str, rng=None, B: int = 2000, K: int = 200, var_method="splithalf",
              sd_floor: float = 0.0, intervals=("ti_boot",), ci_level: float = 0.95, term_intervals: bool = True,
              canonical_sign: int = 1, grid: int = 41):
    """Amendment A1 estimator. cells: {level-index tuple: (y1, y0)}.
    var_method: 'splithalf' (default), 'bootstrap', 'formula' (legacy, for comparison), or a dict {cell tuple: v}
                (oracle variances used by the simulation).
    intervals: any of 'ti_boot' (default; variance-calibrated bootstrap errors), 'ti_gauss' (Gaussian errors with
               variance v_c), 'basic' (legacy star-centred pivotal bootstrap interval, fixed v).
    Returns a dict. If a cell is 'deterministic' (pooled SD 0, unequal means) returns status='deterministic_cells'
    and no estimates: the caller must rerun with kind='diff'."""
    rng = rng or np.random.default_rng(0)
    shape = design.shape
    keys = list(itertools.product(*[range(L) for L in shape]))
    assert set(keys) == set(cells), "cells must enumerate the full crossed design"
    status = {k: is_degenerate(kind, *cells[k]) for k in keys}
    det = [k for k, s in status.items() if s == "deterministic"]
    if det:
        return {"status": "deterministic_cells", "deterministic_cells": det,
                "equal_constant_cells": [k for k, s in status.items() if s == "equal_constant"]}
    C = design.C
    d = np.empty(C)
    vf = np.empty(C)
    for i, k in enumerate(keys):
        d[i], vf[i] = effect(kind, *cells[k], sd_floor)
    need_boot = ("ti_boot" in intervals) or ("basic" in intervals) or var_method == "bootstrap"
    bd = None
    if need_boot:
        bd = np.stack([boot_effect(kind, *cells[k], rng, B, sd_floor)[0] for k in keys], axis=1)   # (B, C)
    if isinstance(var_method, dict):
        v = np.array([var_method[k] for k in keys], float)
    elif var_method == "formula":
        v = vf.copy()
    elif var_method == "bootstrap":
        v = bd.var(0, ddof=1)
    elif var_method == "splithalf":
        v = np.array([split_half_var(kind, *cells[k], rng, K, sd_floor) for k in keys])
    else:
        raise ValueError(var_method)
    for i, k in enumerate(keys):             # constant cells with equal means: no resampling variation, use the formula at g = 0
        if status[k] == "equal_constant":
            v[i] = vf[i]
    names, projs, Ptot = term_projectors(design)
    vsum = float(v.sum())
    t_tot = float(d @ Ptot @ d - (C - 1) / C * vsum)
    s2 = t_tot / C
    terms = {n: float(d @ P @ d - df / C * vsum) for n, (P, df) in zip(names, projs)}
    out = {"status": "ok", "C": C, "kind": kind, "var_method": var_method if isinstance(var_method, str) else "oracle",
           "dbar": float(d.mean()), "S2_untruncated": s2, "S": float(np.sqrt(max(0.0, s2))),
           "terms": terms, "term_df": {n: df for n, (P, df) in zip(names, projs)},
           "degenerate_equal_constant_cells": [k for k, s in status.items() if s == "equal_constant"],
           "d": d.tolist(), "v": v.tolist(), "v_formula": vf.tolist()}
    z = 1.959964
    lo_ = d - z * np.sqrt(v)
    hi_ = d + z * np.sqrt(v)
    sig = (lo_ > 0) if canonical_sign > 0 else (hi_ < 0)
    out["sign_stability"] = float(sig.mean())
    out["sign_agreement"] = float((np.sign(d) == canonical_sign).mean())
    # the finite-cell mean has sampling variance sum(v_c)/C^2 exactly (cells independent, no between-cell component)
    se_dbar = float(np.sqrt(vsum) / C)
    out["dbar_se"] = se_dbar
    out["dbar_ci"] = [float(d.mean() - z * se_dbar), float(d.mean() + z * se_dbar)]
    out["intervals"] = {}
    targets = [("S2", Ptot)] + ([(n, P) for n, (P, df) in zip(names, projs)] if term_intervals else [])
    for method in intervals:
        res = {}
        if method in ("ti_boot", "ti_gauss"):
            errors = _calibrated_errors(bd, v, rng) if method == "ti_boot" else rng.standard_normal((B, C)) * np.sqrt(v)[None, :]
            for name, P in targets:
                lo, hi, _ = ti_interval(d, vsum, P, errors, ci_level, grid)
                res[name] = [lo / C, hi / C] if name == "S2" else [lo, hi]
        elif method == "basic":
            a = (1 - ci_level) / 2
            e = bd - bd.mean(0, keepdims=True)
            for name, P in targets:
                dstar = d[None, :] + e
                df_ = np.trace(P)
                t_star = _quad(dstar, P) - df_ / C * vsum
                plug = float(d @ P @ d)                                   # bootstrap-world target (noisy spread of observed d_c)
                hat = plug - df_ / C * vsum
                lo, hi = hat - (np.quantile(t_star, 1 - a) - plug), hat - (np.quantile(t_star, a) - plug)
                res[name] = [lo / C, hi / C] if name == "S2" else [lo, hi]
        else:
            raise ValueError(method)
        res["S"] = [float(np.sqrt(max(0.0, res["S2"][0]))), float(np.sqrt(max(0.0, res["S2"][1])))]
        # conservative lower/upper range of cell effects, dbar -+ 2S, with the outer bounds of both intervals (not a joint interval)
        res["dbar_minus_2S_lower"] = float(out["dbar_ci"][0] - 2 * res["S"][1])
        res["dbar_plus_2S_upper"] = float(out["dbar_ci"][1] + 2 * res["S"][1])
        res["factor_shares_reportable"] = bool(res["S2"][0] > 0)
        out["intervals"][method] = res
    return out
