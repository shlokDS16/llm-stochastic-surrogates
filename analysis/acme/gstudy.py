"""Preregistered G-study (variance decomposition) for the ACME benchmark, Arm L (PREREG-acme.md sections 3 and 5).

Estimator (section 3, amendment 12 applied): crossed ANOVA on a complete array with ONE value per cell, so the highest
interaction is the residual. W (wording) is random; M (model), O (order) and, in the four-facet analysis, T (temperature) are
fixed. Mixed-model expected mean squares, unrestricted. For fixed facets F, sizes n_f, and n_w wordings:

    E[MS_{S+W}] = sum over S' >= S (S' subset of F)  prod_{f in F minus S'} n_f * sigma2_{S'+W}      (S'= F is the residual, weight 1)
    E[MS_S]     = E[MS_{S+W}] + n_w * prod_{f in F minus S} n_f * theta2_S                          (S a nonempty subset of F)

so sigma2 is solved from the top interaction down, and theta2_S = (MS_S - MS_{SW}) / (n_w prod_{f not in S} n_f), where theta2_S is
the sum of squared effects of S divided by its degrees of freedom (the n-1 convention of the prereg). With three facets this is
exactly the text of section 3. Negative estimates are set to 0 for shares; untruncated values are always returned too.

Labels: facets are single letters in the order given ("M", "W", "O", "T"); a term is the letters of its facets in that order
("MW", "WO", "MO", "MWT", ...), the highest interaction is "res". With ONE fixed facet (a one-order item, facets M, W) the
highest interaction is M x W and is labelled "MW" (there is no "res"); pooling over items fills absent terms with 0.

Two estimators (ESTIMATORS, CLI --estimator): "prereg" (default, exactly this file's text) and "A1", the G1 amendment dated
2026-11-06 (untruncated shares, delete-one-wording jackknife bias correction, studentized bootstrap-t intervals and p-values in a
bootstrap world with shrunk fixed effects). A1 is NOT primary until approved; the reason is in runs/acme-G1/REPORT.md.

Intervals (prereg): percentile bootstrap over wordings (rows resampled with replacement, models, orders and temperatures held fixed),
B = 2000, seed 20261106. Exploratory variant: models are resampled too.

CLI (reads an effects table, writes JSON and CSV):
    .venv/Scripts/python.exe -I analysis/acme/gstudy.py --effects effects.csv --scale scale.csv --single-site-se se.csv --out OUTDIR
effects.csv columns: model,item,W,O,variant,T,delta. Primary arrays use variant == "main" and T == 1.0; the four-facet
arrays use variant == "main" and every T present. scale.csv: item,sd (delta is divided by sd -> ML1-SD units). se.csv: item,se
(single-site SE in ML1-SD units). Optional --exclude exclude.csv (model,item): pairs failing the valid-mass rule.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

DEFAULT_B = 2000
DEFAULT_SEED = 20261106
CONST_VAR = 1e-8   # an effect array with variance below this (ML1-SD^2) is constant: shares undefined (prereg A-G1)
FACETS3 = ("M", "W", "O")
FACETS2 = ("M", "W")
FACETS4 = ("M", "W", "O", "T")
FACETS3T = ("M", "W", "T")          # one-order item with temperature
TEMPERATURES = (0.3, 0.7, 1.0, 1.5)


# --------------------------------------------------------------------------------------------------------------------------
# decomposition
# --------------------------------------------------------------------------------------------------------------------------
def _subsets(items):
    for r in range(1, len(items) + 1):
        for c in itertools.combinations(items, r):
            yield c


def _label(facets, subset):
    return "".join(f for f in facets if f in subset)


def _core(arr, facets, random="W"):
    """Vectorised EMS decomposition. arr has shape (..., n_f1, ..., n_fk) with the facet axes LAST, in the order of `facets`.
    Returns names, comps (..., K) untruncated, and a dict of mean squares keyed by the term label."""
    arr = np.asarray(arr, dtype=float)
    facets = tuple(facets)
    k = len(facets)
    if random not in facets:
        raise ValueError("random facet missing")
    lead = arr.ndim - k
    if lead < 0:
        raise ValueError("array has fewer axes than facets")
    n = {f: arr.shape[lead + i] for i, f in enumerate(facets)}
    pos = {f: lead + i for i, f in enumerate(facets)}
    fixed = tuple(f for f in facets if f != random)
    nw = n[random]
    fac_axes = tuple(range(lead, arr.ndim))
    N = int(np.prod([n[f] for f in facets]))

    cache = {}

    def marg(T):
        T = tuple(sorted(T, key=facets.index))
        if T not in cache:
            axes = tuple(pos[f] for f in facets if f not in T)
            cache[T] = arr.mean(axis=axes, keepdims=True) if axes else arr
        return cache[T]

    grand = marg(())
    ss = {}
    for S in _subsets(facets):
        if len(S) == k:
            continue
        eff = 0.0
        for r in range(0, len(S) + 1):
            for T in itertools.combinations(S, r):
                eff = eff + ((-1) ** (len(S) - r)) * marg(T)
        nS = int(np.prod([n[f] for f in S]))
        ss[S] = (N / nS) * (eff ** 2).sum(axis=fac_axes)
    ss_total = ((arr - grand) ** 2).sum(axis=fac_axes)
    ss_full = ss_total - sum(ss.values())
    ss[tuple(facets)] = ss_full

    def df(S):
        return int(np.prod([n[f] - 1 for f in S]))

    ms = {S: ss[S] / df(S) for S in ss}

    # random terms (S' + W), solved from the largest S' down
    sig = {}
    for r in range(len(fixed), -1, -1):
        for Sp in itertools.combinations(fixed, r):
            term = tuple(f for f in facets if f in Sp or f == random)
            rest = [f for f in fixed if f not in Sp]
            own = int(np.prod([n[f] for f in rest])) if rest else 1
            acc = ms[term]
            for r2 in range(r + 1, len(fixed) + 1):
                for Spp in itertools.combinations(fixed, r2):
                    if not set(Sp) <= set(Spp):
                        continue
                    t2 = tuple(f for f in facets if f in Spp or f == random)
                    c = int(np.prod([n[f] for f in fixed if f not in Spp])) if len(Spp) < len(fixed) else 1
                    acc = acc - c * sig[t2]
            sig[term] = acc / own

    names, comps, mslab = [], [], {}
    # fixed terms first (size order), then W, then the other random terms, residual last
    for S in _subsets(fixed):
        termW = tuple(f for f in facets if f in S or f == random)
        rest = [f for f in fixed if f not in S]
        coef = nw * (int(np.prod([n[f] for f in rest])) if rest else 1)
        names.append(_label(facets, S))
        comps.append((ms[tuple(S)] - ms[termW]) / coef)
        mslab[_label(facets, S)] = ms[tuple(S)]
    for r in range(0, len(fixed) + 1):
        for Sp in itertools.combinations(fixed, r):
            term = tuple(f for f in facets if f in Sp or f == random)
            if r == len(fixed):
                lab = "res" if len(fixed) >= 2 else _label(facets, term)
            else:
                lab = _label(facets, term)
            names.append(lab)
            comps.append(sig[term])
            mslab[lab] = ms[term]
    # a stable order: M, O, T.. (fixed), then W, MW, ..., res
    comps = np.stack([np.asarray(c, dtype=float) for c in comps], axis=-1)
    return names, comps, mslab


def _shares(comps, truncate=True):
    c = np.maximum(comps, 0.0) if truncate else comps
    tot = c.sum(axis=-1, keepdims=True)
    safe = np.where(tot > 0, tot, 1.0)
    return np.where(tot > 0, c / safe, 0.0)


def decompose(arr, facets=FACETS3, random="W"):
    """EMS decomposition of one array. Returns dict(names, components (untruncated), components_truncated, shares (truncated, the
    preregistered rule), shares_untruncated (component / sum of untruncated components), ms, n)."""
    arr = np.asarray(arr, dtype=float)
    if arr.ndim != len(facets):
        raise ValueError(f"array has {arr.ndim} axes, facets {facets}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("array must be complete and finite (one value per cell)")
    names, comps, ms = _core(arr, facets, random)
    return dict(
        names=names,
        facets=list(facets),
        n={f: int(arr.shape[i]) for i, f in enumerate(facets)},
        components=dict(zip(names, map(float, comps))),
        components_truncated=dict(zip(names, map(float, np.maximum(comps, 0.0)))),
        shares=dict(zip(names, map(float, _shares(comps, True)))),
        shares_untruncated=dict(zip(names, map(float, _shares(comps, False)))),
        ms={k: float(v) for k, v in ms.items()},
    )


def percentile_ci(x, level=0.95):
    a = (1 - level) / 2
    return np.quantile(x, [a, 1 - a], axis=0)


# Estimator options. "prereg" is PREREG-acme.md section 3 exactly. "A1" is the G1 amendment (dated 2026-11-06, NOT primary until
# Shlok approves; see runs/acme-G1/REPORT.md): (i) shares from untruncated components (truncation makes a pooled mean of zero
# components positive); (ii) delete-one-wording jackknife bias correction of each item's shares (ratio bias of a share whose own
# numerator is noisy); (iii) a studentized (bootstrap-t) interval: wording bootstrap in a world whose fixed effects are shrunk to the
# unbiased estimates, with an inner delete-one-wording jackknife SE in every bootstrap sample (the raw percentile interval of a
# fixed-effect quadratic form is shifted upward and, with n_w = 10 wordings spanning only 9 of the n_m n_o effect dimensions, too
# wide; the studentized interval self-corrects both).
ESTIMATORS = {
    "prereg": dict(share_mode="truncated", bias="none", interval="percentile", rescale=False, shrink_fixed=False),
    "A1": dict(share_mode="untruncated", bias="jackknife", interval="student", rescale=False, shrink_fixed=True),
}


def get_estimator(e):
    return dict(ESTIMATORS[e]) if isinstance(e, str) else dict(e)


def interval(est, boot, kind="percentile", level=0.95, scale=1.0):
    """Interval for statistic(s) with point estimate est (K,) and bootstrap draws boot (B, K). centered: est + scale * (quantile - mean)
    of the bootstrap draws, so that a shifted bootstrap distribution does not move the interval; scale = sqrt(n_w / (n_w - 1)) undoes
    the (n_w - 1) / n_w shrinkage of the bootstrap variance of a wording-resampled statistic."""
    a = (1 - level) / 2
    q = np.quantile(boot, [a, 1 - a], axis=0)
    if kind == "percentile":
        return q
    if kind == "centered":
        m = boot.mean(axis=0)
        return np.asarray(est) + scale * (q - m)
    raise ValueError(kind)


def centered_p(d_hat, d_boot, sided, scale=1.0):
    """Bootstrap p-value under the centred null distribution c* = scale * (d* - mean(d*)). sided 'greater': P(c* >= d_hat); 'two': 2 min(.,.)."""
    c = scale * (np.asarray(d_boot) - np.mean(d_boot))
    pg, pl = float(np.mean(c >= d_hat)), float(np.mean(c <= d_hat))
    return pg if sided == "greater" else min(1.0, 2 * min(pg, pl))


def jackknife_shares(arr, facets=FACETS3, random="W"):
    """Delete-one-wording shares: dict(names, shares (n_w, K) truncated, shares_untruncated (n_w, K))."""
    arr = np.asarray(arr, float)
    facets = tuple(facets)
    wax = facets.index(random)
    nw = arr.shape[wax]
    idx = np.array([[j for j in range(nw) if j != i] for i in range(nw)])
    sub = np.moveaxis(np.take(arr, idx, axis=wax), wax, 0)
    names, comps, _ = _core(sub, facets, random)
    return dict(names=names, shares=_shares(comps, True), shares_untruncated=_shares(comps, False), n_w=nw)


def jackknife_correct(point, loo):
    """Bias-corrected value n * point - (n - 1) * mean(leave-one-out values)."""
    n = loo.shape[0]
    return n * np.asarray(point) - (n - 1) * loo.mean(axis=0)


def _resample_idx(rng, B, n):
    return rng.integers(0, n, size=(B, n))


def _shrink_offset(arr, facets, random, point):
    """Offset D (shape of the wording-mean array, W axis of length 1) that rescales every fixed-effect contrast of the wording-mean
    array so that its quadratic form equals the unbiased estimate theta_hat (truncated at 0) instead of the plug-in value, which
    carries the sampling noise of the effect estimate. Added to every wording, it changes only the fixed terms of the bootstrap
    world."""
    facets = tuple(facets)
    wax = facets.index(random)
    n = {f: arr.shape[i] for i, f in enumerate(facets)}
    nw = n[random]
    fixed = [f for f in facets if f != random]
    xbar = arr.mean(axis=wax, keepdims=True)
    pos = {f: i for i, f in enumerate(facets)}

    def marg(T):
        axes = tuple(pos[f] for f in fixed if f not in T)
        return xbar.mean(axis=axes, keepdims=True) if axes else xbar

    names, comps, ms = _core(arr, facets, random)
    comp = dict(zip(names, comps))
    D = np.zeros_like(xbar)
    for S in _subsets(fixed):
        eff = 0.0
        for r in range(0, len(S) + 1):
            for T in itertools.combinations(S, r):
                eff = eff + ((-1) ** (len(S) - r)) * marg(T)
        lab = _label(facets, S)
        rest = [f for f in fixed if f not in S]
        coef = nw * (int(np.prod([n[f] for f in rest])) if rest else 1)
        q = float(ms[lab]) / coef
        c = math.sqrt(max(float(comp[lab]), 0.0) / q) if q > 0 else 0.0
        D = D + (c - 1.0) * eff
    return D


def bootstrap(arr, facets=FACETS3, B=DEFAULT_B, seed=DEFAULT_SEED, resample_models=False, random="W", chunk=400, shrink_fixed=False):
    """Percentile bootstrap over wordings (and, if resample_models, over models too; exploratory). Returns dict with the point
    decomposition and the bootstrap arrays comps (B, K) untruncated, shares (B, K) truncated, shares_untruncated (B, K).
    shrink_fixed (amendment A1 only): bootstrap from a world whose fixed effects are shrunk to the unbiased estimates (see _shrink_offset)."""
    arr = np.asarray(arr, dtype=float)
    facets = tuple(facets)
    point = decompose(arr, facets, random)
    rng = np.random.default_rng(seed)
    wax = facets.index(random)
    nw = arr.shape[wax]
    idx_w = _resample_idx(rng, B, nw)
    idx_m = _resample_idx(rng, B, arr.shape[facets.index("M")]) if resample_models else None
    src = arr + _shrink_offset(arr, facets, random, point) if shrink_fixed else arr
    comps = np.empty((B, len(point["names"])))
    for s in range(0, B, chunk):
        e = min(B, s + chunk)
        sub = np.take(src, idx_w[s:e], axis=wax)                # (.., b, n_w, ..)
        sub = np.moveaxis(sub, wax, 0)                           # (b, M.., n_w, ..) with facets axes after
        if idx_m is not None:
            mi = facets.index("M")
            b = e - s
            sub = np.take_along_axis(sub, idx_m[s:e].reshape((b,) + tuple(idx_m.shape[1] if i == mi else 1 for i in range(len(facets)))), axis=mi + 1)
        names, c, _ = _core(sub, facets, random)
        comps[s:e] = c
    return dict(names=point["names"], point=point, comps=comps, shares=_shares(comps, True), shares_untruncated=_shares(comps, False),
                B=B, seed=seed, facets=list(facets), resample_models=resample_models, shrink_fixed=shrink_fixed)


def student_bootstrap(arr, facets=FACETS3, B=DEFAULT_B, seed=DEFAULT_SEED, random="W", shrink_fixed=True, chunk=200):
    """Wording bootstrap that also returns, for every bootstrap sample, the delete-one-wording jackknife variance of each untruncated
    share (inner jackknife over the n_w resampled positions): shares_untruncated (B, K) and jvar (B, K). Used for studentized intervals."""
    arr = np.asarray(arr, dtype=float)
    facets = tuple(facets)
    point = decompose(arr, facets, random)
    rng = np.random.default_rng(seed)
    wax = facets.index(random)
    nw = arr.shape[wax]
    idx_w = _resample_idx(rng, B, nw)
    src = arr + _shrink_offset(arr, facets, random, point) if shrink_fixed else arr
    K = len(point["names"])
    sh = np.empty((B, K))
    jv = np.empty((B, K))
    comps = np.empty((B, K))
    loo_all = np.empty((B, nw, K))
    for s0 in range(0, B, chunk):
        e = min(B, s0 + chunk)
        sub = np.moveaxis(np.take(src, idx_w[s0:e], axis=wax), wax, 0)       # (b, ..., n_w, ...)
        names, c, _ = _core(sub, facets, random)
        comps[s0:e] = c
        sh[s0:e] = _shares(c, False)
        loo = []
        for i in range(nw):
            sl = np.delete(sub, i, axis=wax + 1)
            loo.append(_shares(_core(sl, facets, random)[1], False))
        loo = np.stack(loo)                                                  # (n_w, b, K)
        jv[s0:e] = (nw - 1) / nw * ((loo - loo.mean(axis=0)) ** 2).sum(axis=0)
        loo_all[s0:e] = np.moveaxis(loo, 0, 1)
    return dict(names=point["names"], point=point, comps=comps, shares_untruncated=sh, jvar=jv, loo=loo_all, B=B, seed=seed,
                facets=list(facets), shrink_fixed=shrink_fixed)


def ci_table(boot, arr=None, estimator="prereg", share_mode=None, level=0.95):
    """Per-item table: untruncated and truncated components, shares under the chosen estimator (jackknife-corrected under A1, which
    needs `arr`), and intervals of the shares (percentile or centred) and of the untruncated components (percentile)."""
    est = get_estimator(estimator)
    mode = share_mode or est["share_mode"]
    key = "shares" if mode == "truncated" else "shares_untruncated"
    pt = boot["point"]
    names = boot["names"]
    point = np.array([pt[key][n] for n in names])
    if est["bias"] == "jackknife":
        jk = jackknife_shares(arr, boot["facets"])
        point = jackknife_correct(point, jk[key])
    nwb = boot["point"]["n"]["W"]
    scale = math.sqrt(nwb / (nwb - 1)) if est["rescale"] else 1.0
    if est["interval"] == "student":
        # single-item studentized interval from the same student_bootstrap draws
        nw_ = boot["point"]["n"]["W"]
        jk = jackknife_shares(arr, boot["facets"])
        loo = jk["shares_untruncated"]
        vj = (nw_ - 1) / nw_ * ((loo - loo.mean(axis=0)) ** 2).sum(axis=0)
        se_b = np.sqrt(boot["jvar"])
        t = (boot["shares_untruncated"] - boot["shares_untruncated"].mean(axis=0)) / np.where(se_b > 0, se_b, np.nan)
        qq = np.nanquantile(t, [(1 - level) / 2, 1 - (1 - level) / 2], axis=0)
        lo, hi = point - np.sqrt(vj) * qq[1], point - np.sqrt(vj) * qq[0]
        lo, hi = np.where(np.isnan(lo), point, lo), np.where(np.isnan(hi), point, hi)
    else:
        lo, hi = interval(point, boot[key], est["interval"], level, scale)
    clo, chi = percentile_ci(boot["comps"], level)
    rows = []
    for i, nm in enumerate(names):
        rows.append(dict(component=nm, estimate_untruncated=pt["components"][nm], estimate_truncated=pt["components_truncated"][nm],
                         share=float(point[i]), share_lo=float(lo[i]), share_hi=float(hi[i]), comp_lo=float(clo[i]), comp_hi=float(chi[i])))
    return rows


# --------------------------------------------------------------------------------------------------------------------------
# set-up SD
# --------------------------------------------------------------------------------------------------------------------------
def _as3(arr):
    arr = np.asarray(arr, dtype=float)
    return arr[:, :, None] if arr.ndim == 2 else arr


def setup_sd(arr, B=DEFAULT_B, seed=DEFAULT_SEED, level=0.95):
    """Per model: finite SD of Delta over (w, o) (ddof = 1), percentile bootstrap interval over wordings. arr is (M, W, O) or (M, W).
    Also the median over models, with its bootstrap distribution (used by H2)."""
    a = _as3(arr)
    nm, nw, no = a.shape
    sd = a.reshape(nm, -1).std(axis=1, ddof=1)
    rng = np.random.default_rng(seed)
    idx = _resample_idx(rng, B, nw)
    bs = np.empty((B, nm))
    for s in range(0, B, 500):
        sub = a[:, idx[s:s + 500], :]                       # (M, b, W, O)
        bs[s:s + 500] = sub.reshape(nm, sub.shape[1], -1).std(axis=2, ddof=1).T
    lo, hi = percentile_ci(bs, level)
    med_b = np.median(bs, axis=1)
    return dict(sd=sd, lo=lo, hi=hi, boot=bs, median=float(np.median(sd)), median_boot=med_b,
                median_lo=float(np.quantile(med_b, (1 - level) / 2)), median_hi=float(np.quantile(med_b, 1 - (1 - level) / 2)),
                median_lo_onesided=float(np.quantile(med_b, 1 - level)))


# --------------------------------------------------------------------------------------------------------------------------
# decision study
# --------------------------------------------------------------------------------------------------------------------------
def dstudy(components, n_w_grid=range(1, 21), n_o_grid=(1, 2)):
    """Standard error of ONE model's mean effect when it is estimated from n_w wordings and n_o orders (orders are a fixed design
    facet: n_o only averages the order-by-wording and residual terms; the order main effect and M x O are fixed shifts).
    Var = (s2_W + s2_MW)/n_w + (s2_WO + s2_res)/(n_w n_o), negative components counted as 0. For a one-order item the M x W term (which
    holds the residual) enters with n_o = 1 only. Returns dict with the grid and the SE array (len(n_w_grid), len(n_o_grid))."""
    c = {k: max(float(v), 0.0) for k, v in components.items()}
    vw = c.get("W", 0.0) + c.get("MW", 0.0)
    vr = c.get("WO", 0.0) + c.get("res", 0.0)
    nw = np.asarray(list(n_w_grid), float)
    no = np.asarray(list(n_o_grid), float)
    se = np.sqrt(vw / nw[:, None] + vr / (nw[:, None] * no[None, :]))
    return dict(n_w=nw.astype(int).tolist(), n_o=no.astype(int).tolist(), se=se, var_w=vw, var_r=vr)


def dstudy_min_design(components, target=0.1, n_w_max=200, n_o_grid=(1, 2)):
    """Smallest (n_w, n_o) with SE below `target` (default 0.1 ML1-SD units), cheapest by n_w * n_o; None if not reached."""
    d = dstudy(components, range(1, n_w_max + 1), n_o_grid)
    best = None
    for j, o in enumerate(d["n_o"]):
        for i, w in enumerate(d["n_w"]):
            if d["se"][i, j] < target:
                if best is None or w * o < best[0] * best[1]:
                    best = (w, o)
                break
    return best


# --------------------------------------------------------------------------------------------------------------------------
# pooling over items
# --------------------------------------------------------------------------------------------------------------------------
def _union_names(names_lists):
    allv = set(n for ns in names_lists for n in ns)
    return sorted(allv, key=lambda n: (n == "res", len(n.replace("res", "")), n))


def student_pooled(pool, C, sel=None, level=0.95):
    """Studentized (bootstrap-t) inference for linear contrasts of the mean-over-items shares. C: (R, K) contrast rows (identity gives
    the pooled share of every component). sel: item indices to pool (default all). The statistic of a contrast is the mean over
    items of c . share (jackknife-corrected point). Its SE is the delete-one-wording jackknife SE (items independent); each
    bootstrap sample carries its own inner jackknife SE; t* = (theta* - mean theta*) / SE*.
    Returns est, se0, t (B, R), lo, hi, and a function-ready bundle for p-values (see student_p)."""
    C = np.atleast_2d(np.asarray(C, float))
    sel = list(range(len(pool["items"]))) if sel is None else list(sel)
    n = len(sel)
    sh = pool["item_boot"][sel]                                         # (n, B, K)
    th = np.einsum("nbk,rk->br", sh, C) / n
    contr = np.einsum("nbjk,rk->nbjr", pool["loo_boot"][sel], C)         # (n, B, n_w, R)
    nw = contr.shape[2]
    vj = (nw - 1) / nw * ((contr - contr.mean(axis=2, keepdims=True)) ** 2).sum(axis=2)
    se_b = np.sqrt(vj.sum(axis=0)) / n                                  # (B, R)
    cp = np.einsum("njk,rk->njr", pool["loo_point"][sel], C)
    vp = (nw - 1) / nw * ((cp - cp.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    se0 = np.sqrt(vp.sum(axis=0)) / n
    est = np.einsum("nk,rk->r", pool["item_point"][sel], C) / n
    t = (th - th.mean(axis=0)) / np.where(se_b > 0, se_b, np.nan)
    a = (1 - level) / 2
    q = np.nanquantile(t, [a, 1 - a], axis=0)
    lo, hi = est - se0 * q[1], est - se0 * q[0]
    lo, hi = np.where(np.isnan(lo), est, lo), np.where(np.isnan(hi), est, hi)
    return dict(est=est, se0=se0, t=t, lo=lo, hi=hi)


def student_p(sp, r, sided):
    """p-value for H0: contrast r = 0 from a student_pooled result. 'greater': P(t* >= est/se0); 'two': 2 min of the two tails."""
    if not sp["se0"][r] > 0:
        return 1.0
    t_obs = sp["est"][r] / sp["se0"][r]
    t = sp["t"][:, r]
    t = t[~np.isnan(t)]
    pg, pl = float(np.mean(t >= t_obs)), float(np.mean(t <= t_obs))
    return pg if sided == "greater" else min(1.0, 2 * min(pg, pl))


def pool_items(items, B=DEFAULT_B, seed=DEFAULT_SEED, resample_models=False, share_mode=None, level=0.95, estimator="prereg", jackknife=None,
               shrink_fixed=None, rescale=None, interval_kind=None):
    """items: list of dict(name, arr, facets). Per item a wording bootstrap with its own stream (wordings resampled independently
    within item; draw b of every item is combined, so the pooled bootstrap is joint). Absent terms count as 0 in the pooled share.
    estimator: "prereg" or "A1" (see ESTIMATORS); share_mode overrides the estimator's share rule. Returns names, per-item point
    shares (n_items, K) (jackknife-corrected under A1), pooled median and mean (point), bootstrap distributions of the pooled mean
    and median (B, K) and intervals. The median-over-items interval is exploratory (the prereg gives none)."""
    est = get_estimator(estimator)
    if share_mode is not None:
        est["share_mode"] = share_mode
    mode = est["share_mode"]
    do_jk = (est["bias"] == "jackknife") if jackknife is None else jackknife
    shr = est["shrink_fixed"] if shrink_fixed is None else shrink_fixed
    resc = est["rescale"] if rescale is None else rescale
    ik = est["interval"] if interval_kind is None else interval_kind
    est["interval"] = ik
    boots, jks = [], []
    if ik == "student" and mode != "untruncated":
        raise ValueError("studentized intervals are defined for untruncated shares")
    for j, it in enumerate(items):
        if ik == "student":
            boots.append(student_bootstrap(it["arr"], it["facets"], B=B, seed=[seed, j, 9], shrink_fixed=shr))
        else:
            boots.append(bootstrap(it["arr"], it["facets"], B=B, seed=[seed, j, 1 + int(resample_models)], resample_models=resample_models, shrink_fixed=shr))
        if do_jk:
            jks.append(jackknife_shares(it["arr"], it["facets"]))
    names = _union_names([b["names"] for b in boots])
    K = len(names)
    modes = ("truncated", "untruncated")
    pt = {m: np.zeros((len(items), K)) for m in modes}
    ptc = {m: np.zeros((len(items), K)) for m in modes}        # jackknife-corrected points (equal to pt if not computed)
    bt = {m: np.zeros((len(items), B, K)) for m in modes}
    loo_all = {m: np.zeros((len(items), items[0]["arr"].shape[items[0]["facets"].index("W")], K)) for m in modes} if do_jk else None
    for j, b in enumerate(boots):
        for i, nm in enumerate(b["names"]):
            col = names.index(nm)
            pt["truncated"][j, col] = b["point"]["shares"][nm]
            pt["untruncated"][j, col] = b["point"]["shares_untruncated"][nm]
            if "shares" in b:
                bt["truncated"][j, :, col] = b["shares"][:, i]
            bt["untruncated"][j, :, col] = b["shares_untruncated"][:, i]
        for m in modes:
            ptc[m][j] = pt[m][j]
        if do_jk:
            for m, key in (("truncated", "shares"), ("untruncated", "shares_untruncated")):
                loo = np.zeros((jks[j]["n_w"], K))
                for i, nm in enumerate(jks[j]["names"]):
                    loo[:, names.index(nm)] = jks[j][key][:, i]
                ptc[m][j] = jackknife_correct(pt[m][j], loo)
                if loo.shape[0] == loo_all[m].shape[1]:
                    loo_all[m][j] = loo
    ip = ptc[mode] if est["bias"] == "jackknife" else pt[mode]
    ib = bt[mode]
    loo_b = None
    if ik == "student":
        loo_b = np.zeros((len(items), B, loo_all[mode].shape[1], K))
        for j, b in enumerate(boots):
            for i, nm in enumerate(b["names"]):
                loo_b[j, :, :, names.index(nm)] = b["loo"][:, :, i]
    mean_b = ib.mean(axis=0)
    med_b = np.median(ib, axis=0)
    mean, med = ip.mean(axis=0), np.median(ip, axis=0)
    nws = [it["arr"].shape[it["facets"].index("W")] for it in items]
    scale = float(np.mean([math.sqrt(n / (n - 1)) for n in nws])) if resc else 1.0
    pool = dict(names=names, items=[it["name"] for it in items], item_point=ip, loo_boot=loo_b,
                loo_point=loo_all[mode] if loo_all is not None else None, item_boot=ib)
    if ik == "student":
        sp = student_pooled(pool, np.eye(K))
        mlo, mhi = sp["lo"], sp["hi"]
        dlo = dhi = np.full(K, np.nan)               # no studentized interval for the median over items
    else:
        mlo, mhi = interval(mean, mean_b, ik, level, scale)
        dlo, dhi = interval(med, med_b, ik, level, scale)
    return dict(names=names, items=[it["name"] for it in items], item_point=ip, item_boot=ib,
                item_point_by_mode=pt, item_point_corrected_by_mode=ptc, item_boot_by_mode=bt,
                mean=mean, median=med, mean_boot=mean_b, median_boot=med_b,
                mean_lo=mlo, mean_hi=mhi, median_lo=dlo, median_hi=dhi,
                item_boots=boots, item_loo_by_mode=loo_all, loo_boot=loo_b, loo_point=(loo_all[mode] if loo_all is not None else None), scale=scale, B=B, seed=seed, share_mode=mode, estimator=est)


# --------------------------------------------------------------------------------------------------------------------------
# hypotheses
# --------------------------------------------------------------------------------------------------------------------------
def iu_pvalue(pvals):
    """Intersection-union p for 'at least ceil(k/2) of k items': the ceil(k/2)-th smallest item-level p-value."""
    p = sorted(float(x) for x in pvals)
    if not p:
        return float("nan")
    return p[math.ceil(len(p) / 2) - 1]


def holm_adjust(pvals):
    """Holm step-down. pvals: dict name -> p (None counts as 1). Returns dict name -> adjusted p."""
    names = list(pvals)
    p = np.array([1.0 if pvals[k] is None or (isinstance(pvals[k], float) and math.isnan(pvals[k])) else pvals[k] for k in names])
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return {k: float(a) for k, a in zip(names, adj)}


def _col(pool, names):
    return sum(pool["mean_boot"][:, pool["names"].index(n)] if n in pool["names"] else 0.0 for n in names)


def hypotheses(items3, items4=None, single_site_se=None, B=DEFAULT_B, seed=DEFAULT_SEED, share_mode=None, alpha=0.05,
               pool3=None, pool4=None, estimator="prereg"):
    """Confirmatory hypotheses, Holm over 3.
    items3: list of dict(name, arr) with arr (M, W, O) or (M, W) at T = 1 in ML1-SD units. items4: list of dict(name, arr) with a
    trailing temperature axis, (M, W, O, T) or (M, W, T). single_site_se: dict item -> SE (ML1-SD units).
    H1: mean over items of (W + MW share) minus T share (four-facet decomposition; T share = all terms containing T except the
        residual); one-sided p = share of bootstrap differences <= 0.
    H2: per item the median over valid models of the set-up SD and its bootstrap; holds for an item if the lower end of the 95 percent
        percentile interval exceeds the single-site SE; p = ceil(k/2)-th smallest of the item-level one-sided bootstrap p-values
        (share of bootstrap medians <= SE). The one-sided 95 percent lower bound is reported as well.
    H3: mean over items of MW share minus W share (three-facet); two-sided bootstrap p."""
    out = {}
    # H3
    it3 = [dict(name=i["name"], arr=np.asarray(i["arr"], float), facets=FACETS3 if np.asarray(i["arr"]).ndim == 3 else FACETS2) for i in items3]
    p3 = pool3 or pool_items(it3, B, seed, share_mode=share_mode, estimator=estimator)
    d3 = _col(p3, ["MW"]) - _col(p3, ["W"])
    pt3 = float(p3["mean"][p3["names"].index("MW")] - p3["mean"][p3["names"].index("W")])
    kind = p3["estimator"]["interval"]
    if kind == "student":
        c3 = np.zeros((1, len(p3["names"])))
        c3[0, p3["names"].index("MW")], c3[0, p3["names"].index("W")] = 1.0, -1.0
        sp3 = student_pooled(p3, c3)
        pt3 = float(sp3["est"][0])
        p_h3 = student_p(sp3, 0, "two")
        lo3, hi3 = sp3["lo"], sp3["hi"]
    elif kind == "percentile":
        pl, pg = float(np.mean(d3 <= 0)), float(np.mean(d3 >= 0))
        p_h3 = min(1.0, 2 * min(pl, pg))
    else:
        p_h3 = centered_p(pt3, d3, "two", p3["scale"])
    if kind != "student":
        lo3, hi3 = interval(np.array([pt3]), d3[:, None], kind, scale=p3["scale"])
    out["H3"] = dict(estimate=pt3, pooled_MW=float(p3["mean"][p3["names"].index("MW")]), pooled_W=float(p3["mean"][p3["names"].index("W")]),
                     lo=float(lo3[0]), hi=float(hi3[0]), p_raw=p_h3, k_items=len(it3), estimator=estimator if isinstance(estimator, str) else "custom")
    # H1
    if items4:
        it4 = []
        for i in items4:
            a = np.asarray(i["arr"], float)
            it4.append(dict(name=i["name"], arr=a, facets=FACETS4 if a.ndim == 4 else FACETS3T))
        p4 = pool4 or pool_items(it4, B, seed, share_mode=share_mode, estimator=estimator)
        tnames = [n for n in p4["names"] if "T" in n and n != "res"]
        wnames = [n for n in ("W", "MW") if n in p4["names"]]
        d1 = _col(p4, wnames) - _col(p4, tnames)
        pt1 = float(sum(p4["mean"][p4["names"].index(n)] for n in wnames) - sum(p4["mean"][p4["names"].index(n)] for n in tnames))
        kind = p4["estimator"]["interval"]
        if kind == "student":
            c1 = np.zeros((1, len(p4["names"])))
            for n_ in wnames:
                c1[0, p4["names"].index(n_)] += 1.0
            for n_ in tnames:
                c1[0, p4["names"].index(n_)] -= 1.0
            sp1 = student_pooled(p4, c1)
            pt1 = float(sp1["est"][0])
            p_h1 = student_p(sp1, 0, "greater")
            lo1, hi1 = sp1["lo"], sp1["hi"]
        else:
            p_h1 = float(np.mean(d1 <= 0)) if kind == "percentile" else centered_p(pt1, d1, "greater", p4["scale"])
            lo1, hi1 = interval(np.array([pt1]), d1[:, None], kind, scale=p4["scale"])
        out["H1"] = dict(estimate=pt1, pooled_wording=float(sum(p4["mean"][p4["names"].index(n)] for n in wnames)),
                         pooled_T=float(sum(p4["mean"][p4["names"].index(n)] for n in tnames)), T_terms=tnames,
                         lo=float(lo1[0]), hi=float(hi1[0]), p_raw=p_h1, k_items=len(it4), estimator=estimator if isinstance(estimator, str) else "custom")
    else:
        out["H1"] = dict(p_raw=None, note="no four-facet arrays supplied")
    # H2
    if single_site_se:
        rows, ps = [], []
        for j, i in enumerate(items3):
            if i["name"] not in single_site_se:
                continue
            sd = setup_sd(i["arr"], B, [seed, j, 7])
            se = float(single_site_se[i["name"]])
            p = float(np.mean(sd["median_boot"] <= se))
            rows.append(dict(item=i["name"], median_setup_sd=sd["median"], lb95=sd["median_lo"], lb95_onesided=sd["median_lo_onesided"],
                             single_site_se=se, p_one_sided=p, holds=bool(sd["median_lo"] > se)))
            ps.append(p)
        k = len(rows)
        need = math.ceil(k / 2) if k else 0
        out["H2"] = dict(items=rows, k=k, need=need, n_hold=int(sum(r["holds"] for r in rows)), holds=bool(k and sum(r["holds"] for r in rows) >= need),
                         p_raw=iu_pvalue(ps) if k else None)
    else:
        out["H2"] = dict(p_raw=None, note="no single-site SE supplied")
    adj = holm_adjust({h: out[h].get("p_raw") for h in ("H1", "H2", "H3")})
    for h in adj:
        out[h]["p_holm"] = adj[h]
        out[h]["reject_holm_alpha"] = bool(out[h].get("p_raw") is not None and adj[h] <= alpha)
    return out


# --------------------------------------------------------------------------------------------------------------------------
# CLI: effects table -> arrays -> outputs
# --------------------------------------------------------------------------------------------------------------------------
def build_arrays(d, temps=None):
    """Array (M, W, O, T) for one item from its rows of the long table (variant == main). temps None -> only T == 1.0 (T axis of
    length 1). Returns (arr, models, wordings, orders, temps). Missing cells stay NaN; duplicated cells raise."""
    ts = [1.0] if temps is None else sorted(float(t) for t in temps)
    d = d[[any(np.isclose(t, x) for x in ts) for t in d["T"]]]
    ms = sorted(d["model"].unique())
    ws = sorted(d["W"].unique(), key=lambda x: (len(str(x)), str(x)))
    os_ = sorted(d["O"].unique(), key=str)
    if d.duplicated(["model", "W", "O", "T"]).any():
        raise ValueError("duplicated cells for item " + str(d["item"].iloc[0]))
    arr = np.full((len(ms), len(ws), len(os_), len(ts)), np.nan)
    mi = {m: i for i, m in enumerate(ms)}
    wi = {w: i for i, w in enumerate(ws)}
    oi = {o: i for i, o in enumerate(os_)}
    for r in d.itertuples(index=False):
        arr[mi[r.model], wi[r.W], oi[r.O], int(np.argmin([abs(r.T - x) for x in ts]))] = r.delta
    return arr, ms, ws, os_, ts


def _complete_models(arr, ms, log, item):
    """Drop models with any missing cell so the array is complete; log the dropped."""
    bad = [i for i in range(arr.shape[0]) if not np.all(np.isfinite(arr[i]))]
    if bad:
        log.append(dict(item=item, dropped_models=[ms[i] for i in bad], reason="incomplete cells"))
        keep = [i for i in range(arr.shape[0]) if i not in bad]
        arr = arr[keep]
        ms = [ms[i] for i in keep]
    return arr, ms


def run_cli(args):
    import pandas as pd
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.effects, dtype={"W": str, "O": str, "model": str, "item": str, "variant": str})
    df["O"] = df["O"].fillna("0")
    df["T"] = df["T"].astype(float)
    df = df[df["variant"] == "main"].copy()
    sd = None
    if args.scale:
        sc = pd.read_csv(args.scale, dtype={"item": str})
        sd = dict(zip(sc["item"], sc["sd"].astype(float)))
    se = None
    if args.single_site_se:
        s2 = pd.read_csv(args.single_site_se, dtype={"item": str})
        se = dict(zip(s2["item"], s2["se"].astype(float)))
    excl = set()
    if args.exclude:
        ex = pd.read_csv(args.exclude, dtype=str)
        excl = set(zip(ex["model"], ex["item"]))
    items = sorted(df["item"].unique())
    log, items3, items4 = [], [], []
    for it in items:
        sub = df[df["item"] == it]
        if sd is not None:
            if it not in sd:
                raise SystemExit(f"no scale for item {it}")
            sub = sub.assign(delta=sub["delta"] / sd[it])
        sub = sub[[(m, it) not in excl for m in sub["model"]]]
        arr, ms, ws, os_, _ = build_arrays(sub)
        arr, ms = _complete_models(arr, ms, log, it)
        a3 = arr[..., 0]
        if a3.shape[2] == 1:
            a3 = a3[:, :, 0]
        items3.append(dict(name=it, arr=a3, models=ms, n_w=len(ws), n_o=len(os_)))
        tset = sorted(sub["T"].unique())
        if len(tset) >= 2:
            a4, ms4, _, _, ts = build_arrays(sub, temps=tset)
            a4, ms4 = _complete_models(a4, ms4, log, it + "[T]")
            if a4.shape[2] == 1:
                a4 = a4[:, :, 0, :]
            items4.append(dict(name=it, arr=a4, models=ms4, temps=ts))
    # Denominator rule (prereg A-G1): an item whose effect array is constant (variance < CONST_VAR) has undefined shares. It is left
    # out of the per-item share tables, the pooled shares and H1/H3, and listed; its set-up SD (0) still enters H2.
    const3 = [i["name"] for i in items3 if float(np.var(i["arr"])) < CONST_VAR]
    const4 = [i["name"] for i in items4 if float(np.var(i["arr"])) < CONST_VAR]
    for nm in const3:
        log.append(dict(item=nm, reason="constant effect array: shares undefined, left out of shares, H1 and H3"))
    for nm in const4:
        log.append(dict(item=nm + "[T]", reason="constant effect array: shares undefined, left out of the four-facet shares and H1"))
    items3_all = items3
    items3 = [i for i in items3 if i["name"] not in const3]
    items4 = [i for i in items4 if i["name"] not in const4]
    B, seed = args.B, args.seed
    summary = dict(config=dict(B=B, seed=seed, estimator=args.estimator, share_mode=args.share_mode, effects=str(args.effects), scaled=sd is not None), exclusions=log, items={})
    for j, it in enumerate(items3_all):
        if it["name"] in const3:
            s = setup_sd(it["arr"], B, [seed, j, 7])
            summary["items"][it["name"]] = dict(models=it["models"], constant=True, setup_sd_median=s["median"])
    rows_comp, rows_sd, rows_ds = [], [], []
    for j, it in enumerate(items3):
        fac = FACETS3 if it["arr"].ndim == 3 else FACETS2
        b = (student_bootstrap if get_estimator(args.estimator)["interval"] == "student" else bootstrap)(it["arr"], fac, B, [seed, j, 1], shrink_fixed=get_estimator(args.estimator)["shrink_fixed"])
        for r in ci_table(b, it["arr"], args.estimator, args.share_mode):
            rows_comp.append(dict(item=it["name"], analysis="T1", n_models=it["arr"].shape[0], **r))
        s = setup_sd(it["arr"], B, [seed, j, 7])
        for mi, m in enumerate(it["models"]):
            rows_sd.append(dict(item=it["name"], model=m, setup_sd=float(s["sd"][mi]), lo=float(s["lo"][mi]), hi=float(s["hi"][mi])))
        rows_sd.append(dict(item=it["name"], model="__median__", setup_sd=s["median"], lo=s["median_lo"], hi=s["median_hi"]))
        ds = dstudy(b["point"]["components"])
        for i, w in enumerate(ds["n_w"]):
            for jj, o in enumerate(ds["n_o"]):
                if o <= it["n_o"]:
                    rows_ds.append(dict(item=it["name"], n_w=w, n_o=o, se=float(ds["se"][i, jj])))
        summary["items"][it["name"]] = dict(models=it["models"], dstudy_min_design_0p1=dstudy_min_design(b["point"]["components"]))
    for j, it in enumerate(items4):
        fac = FACETS4 if it["arr"].ndim == 4 else FACETS3T
        b = (student_bootstrap if get_estimator(args.estimator)["interval"] == "student" else bootstrap)(it["arr"], fac, B, [seed, j, 3], shrink_fixed=get_estimator(args.estimator)["shrink_fixed"])
        for r in ci_table(b, it["arr"], args.estimator, args.share_mode):
            rows_comp.append(dict(item=it["name"], analysis="4facet", n_models=it["arr"].shape[0], **r))
    pd.DataFrame(rows_comp).to_csv(out / "components_by_item.csv", index=False)
    pd.DataFrame(rows_sd).to_csv(out / "setup_sd.csv", index=False)
    pd.DataFrame(rows_ds).to_csv(out / "dstudy.csv", index=False)
    pooled_rows = []
    pool3 = pool_items([dict(name=i["name"], arr=i["arr"], facets=FACETS3 if i["arr"].ndim == 3 else FACETS2) for i in items3], B, seed, share_mode=args.share_mode, estimator=args.estimator)
    pool4 = None
    for tag, pool in (("T1_3facet", pool3),):
        for statname in ("mean", "median"):
            for i, nm in enumerate(pool["names"]):
                pooled_rows.append(dict(analysis=tag, stat=statname, component=nm, estimate=float(pool[statname][i]),
                                        lo=float(pool[statname + "_lo"][i]), hi=float(pool[statname + "_hi"][i]),
                                        note="interval for the median is exploratory" if statname == "median" else ""))
    if items4:
        pool4 = pool_items([dict(name=i["name"], arr=i["arr"], facets=FACETS4 if i["arr"].ndim == 4 else FACETS3T) for i in items4], B, seed, share_mode=args.share_mode, estimator=args.estimator)
        for statname in ("mean", "median"):
            for i, nm in enumerate(pool4["names"]):
                pooled_rows.append(dict(analysis="4facet", stat=statname, component=nm, estimate=float(pool4[statname][i]),
                                        lo=float(pool4[statname + "_lo"][i]), hi=float(pool4[statname + "_hi"][i]),
                                        note="interval for the median is exploratory" if statname == "median" else ""))
    if args.exploratory_models:
        pe = pool_items([dict(name=i["name"], arr=i["arr"], facets=FACETS3 if i["arr"].ndim == 3 else FACETS2) for i in items3], B, seed,
                        resample_models=True, share_mode=args.share_mode, estimator=args.estimator)
        for i, nm in enumerate(pe["names"]):
            pooled_rows.append(dict(analysis="T1_3facet_EXPLORATORY_models_resampled", stat="mean", component=nm, estimate=float(pe["mean"][i]),
                                    lo=float(pe["mean_lo"][i]), hi=float(pe["mean_hi"][i]), note="exploratory, bounded to the model set"))
    pd.DataFrame(pooled_rows).to_csv(out / "pooled_shares.csv", index=False)
    hyp = hypotheses([dict(name=i["name"], arr=i["arr"]) for i in items3_all], [dict(name=i["name"], arr=i["arr"]) for i in items4] or None,
                     se if sd is not None else None, B, seed, args.share_mode, pool3=pool3, pool4=pool4, estimator=args.estimator)
    hyp["H3"]["k_items"] = len(items3)   # constant items are not in the share pool
    summary["hypotheses"] = hyp
    (out / "hypotheses.json").write_text(json.dumps(hyp, indent=1, default=float), encoding="utf8")
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf8")
    print("wrote", out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--effects", required=True)
    ap.add_argument("--scale")
    ap.add_argument("--single-site-se", dest="single_site_se")
    ap.add_argument("--exclude")
    ap.add_argument("--out", required=True)
    ap.add_argument("--B", type=int, default=DEFAULT_B)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--estimator", default="prereg", choices=sorted(ESTIMATORS), help="prereg = PREREG section 3 as written (primary); A1 = G1 amendment, not primary until approved")
    ap.add_argument("--share-mode", default=None, choices=["truncated", "untruncated"], help="override the estimator's share rule")
    ap.add_argument("--exploratory-models", action="store_true", help="also write the exploratory models-resampled pooled intervals")
    run_cli(ap.parse_args(argv))


if __name__ == "__main__":
    main()
