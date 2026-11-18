"""A1-S: the Arm S decomposition (errata E7, item 2(a) and 3; EXPERT-statistician.md section 2).

For one item, the array Delta-hat(m, w, o, T) = (ybar1 - ybar0) / sd (ML1-SD units; facets M, W, O, T, or M, W, T for items without an
order) is passed to the frozen A1 estimator of gstudy.py unchanged: untruncated EMS components (gstudy._core / decompose) and shares
corrected by the delete-one-wording jackknife (gstudy.jackknife_shares / jackknife_correct). The residual, which A1 reads as the highest
interaction, is then split into
    draw   = mean over cells of v_c   (v_c = s1^2/n1 + s0^2/n0, binary: binomial at the sampled p, +0.5 continuity at 0 or 1)
    res    = residual - draw          (remainder; untruncated, may be negative: read as indistinguishable from 0)
because independent cell noise of variance v_c adds mean(v_c) to every mean square of a balanced design and cancels from every
EMS difference except the highest interaction. Two share bases, both reported:
    E1  expected-effect variance, shares of {components without draw}      (the sum excludes draw noise)
    E2  variance of one n-draw estimate, shares of {components with draw}  (draw noise is a component; sums to the A1 total)
Both are jackknife-corrected by the delete-one-wording rule of A1 (the same formula, applied to the split components, so that
E2[draw] + E2[res] equals A1's residual share exactly).

Uncertainty (E7 item 3): draw-level cell bootstrap, B = 2000, seed 20261106: within every cell and condition the valid draws are
resampled with replacement, the cell means and v_c recomputed, and the whole estimator (including the jackknife correction) rerun;
percentile interval; labelled "draw uncertainty, conditional on these four wordings". Because the observed cell means carry their own
draw noise as signal in the bootstrap world, each replicate also removes the observed mean(v_c) from the remainder (bootstrap_draws,
parameter baked; the plain recompute without it is kept as "naive" for the synthetic check, where it fails: runs/acme-S-gstudy/synthetic). The four leave-one-wording-out (LOWO) values are
the delete-one-wording shares of the jackknife (A1's own inputs), reported as a range, a measure of fragility and not of uncertainty.
Wording-universe uncertainty is not quantified beyond this.

    .venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py selftest
    .venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py dryrun --roster runs/acme-S-gstudy/roster_strict.csv
        (builds the arrays from cells.csv and prints shapes only; no component is computed)
    .venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --roster R.csv --out DIR --approved-by-lead --no-bootstrap [switches]
        (the real analysis, approved by the lead after the failed synthetic check; E7a: point estimates and LOWO only, no interval of
        any kind. Without --no-bootstrap `run` refuses unless --allow-intervals is given, which is not approved.)
        Sensitivity switches, each changing only what it names: --validity-cells (S-b), --temps 1.0 (S-c), --logit (S-d), --drop-w0 (S-e);
        S-a is --roster runs/acme-S-gstudy/roster_loose.csv.
    .venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py synthetic --out DIR   (one synthetic item through the same code path)
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import gstudy as G  # noqa: E402

TS = (0.7, 1.0)
WS = ("W0", "W1", "W2", "W3")
DEFAULT_B, DEFAULT_SEED = G.DEFAULT_B, G.DEFAULT_SEED
OUT = ROOT / "runs" / "acme-S-gstudy"


def facets_for(ndim: int, has_T: bool = True):
    """Facet names of an effect array. has_T=True: (M, W, O, T) or (M, W, T). has_T=False (sensitivity S-c, one temperature): (M, W, O) or (M, W)."""
    if has_T:
        if ndim == 4:
            return G.FACETS4
        if ndim == 3:
            return G.FACETS3T
        raise ValueError("array must be (M, W, O, T) or (M, W, T)")
    if ndim == 3:
        return G.FACETS3
    if ndim == 2:
        return G.FACETS2
    raise ValueError("array without T must be (M, W, O) or (M, W)")


# ----------------------------------------------------------------------------------------------------------------------------
# estimator
# ----------------------------------------------------------------------------------------------------------------------------
def _loo(x, facets, lead):
    """Delete-one-wording stack of x (lead batch axes, then the facet axes): LOO axis first, W axis shortened by one."""
    wax = lead + facets.index("W")
    nw = x.shape[wax]
    idx = np.array([[j for j in range(nw) if j != i] for i in range(nw)])
    return np.moveaxis(np.take(x, idx, axis=wax), wax, 0)


def _split(arr, v, facets, baked=None):
    """Untruncated components with the residual split. arr, v: (lead..., facet axes). Returns names (A1 names + 'draw'), comps (..., K+1),
    the total tot (...,) of the A1 components minus the baked-in noise, and vbar (...,).
    baked (bootstrap worlds only): cell variances of noise that is already part of arr as signal (the observed noise of the array the
    bootstrap resamples around); it is removed from the residual in addition to v, so that remainder + draw is A1's residual minus baked."""
    k = len(facets)
    names, comps, _ = G._core(arr, facets)
    ax = tuple(range(arr.ndim - k, arr.ndim))
    vbar = np.asarray(v, float).mean(axis=ax)
    tot = comps.sum(axis=-1)
    ir = len(names) - 1      # the highest interaction is the last term of gstudy._core: "res", or "MW" for the two-facet array (M, W)
    c = np.array(comps, float)
    bb = 0.0 if baked is None else np.broadcast_to(np.asarray(baked, float), arr.shape).mean(axis=ax)
    c[..., ir] = c[..., ir] - vbar - bb
    return names + ["draw"], np.concatenate([c, vbar[..., None]], axis=-1), tot - bb, vbar


def _safe(num, den):
    den = np.asarray(den, float)
    ok = den > 0
    return np.where(ok[..., None], num / np.where(ok, den, 1.0)[..., None], 0.0)


def raw_shares(arr, v, facets, limit=False, baked=None):
    """(names, E1 raw shares (..., K), E2 raw shares (..., K+1), comps (..., K+1)) without the jackknife correction. The denominator of
    E2 is the A1 total itself (so E2 with v = 0 is bit-identical to A1's untruncated shares).
    limit=True (synthetic truth only): arr is the noise-free expected-effect array and v the exact cell variances; the residual is NOT
    reduced by mean(v), draw = mean(v) is added as a component: the value the estimator takes with infinitely many draws."""
    if limit:
        names, comps, _ = G._core(arr, facets)
        vbar = np.asarray(v, float).mean(axis=tuple(range(arr.ndim - len(facets), arr.ndim)))
        c = np.concatenate([comps, vbar[..., None]], axis=-1)
        return names + ["draw"], _safe(comps, comps.sum(-1)), _safe(c, c.sum(-1)), c
    names, c, tot, vbar = _split(arr, v, facets, baked)
    e2 = _safe(c, tot)
    e1 = _safe(c[..., :-1], tot - vbar)
    return names, e1, e2, c


def estimate(arr, v, facets, with_loo=True, limit=False, baked=None):
    """The A1-S estimator. arr, v: (lead..., facet axes). Returns dict(names, comps, e1, e2 (jackknife-corrected), e1_raw, e2_raw,
    loo_e1, loo_e2 (n_w, lead..., K))."""
    arr = np.asarray(arr, float)
    v = np.asarray(v, float)
    facets = tuple(facets)
    lead = arr.ndim - len(facets)
    names, e1r, e2r, c = raw_shares(arr, v, facets, limit, baked)
    out = dict(names=names, comps=c, e1_raw=e1r, e2_raw=e2r)
    if not with_loo:
        return out
    lb = None if baked is None else _loo(np.broadcast_to(np.asarray(baked, float), arr.shape), facets, lead)
    _, l1, l2, _ = raw_shares(_loo(arr, facets, lead), _loo(v, facets, lead), facets, limit, lb)
    n = l2.shape[0]
    out.update(loo_e1=l1, loo_e2=l2, e1=n * e1r - (n - 1) * l1.mean(axis=0), e2=n * e2r - (n - 1) * l2.mean(axis=0))
    return out


def a1_reference(arr, facets):
    """gstudy's own A1 point estimate of one array, called unchanged: untruncated shares, jackknife-corrected."""
    arr = np.asarray(arr, float)
    d = G.decompose(arr, facets)
    jk = G.jackknife_shares(arr, facets)
    assert jk["names"] == d["names"]
    pt = np.array([d["shares_untruncated"][nm] for nm in d["names"]])
    return d["names"], G.jackknife_correct(pt, jk["shares_untruncated"])


# ----------------------------------------------------------------------------------------------------------------------------
# draws and the draw-level bootstrap
# ----------------------------------------------------------------------------------------------------------------------------
def pack(draws, shape_cells, keys, nmax=None):
    """Pack per-cell draw vectors into Y (cells..., nmax) with the valid draws first (NaN after) and counts nv (cells...)."""
    nmax = nmax or max(len(draws[k]) for k in keys)
    Y = np.full((len(keys), nmax), np.nan)
    nv = np.zeros(len(keys), int)
    for i, k in enumerate(keys):
        y = np.asarray(draws[k], float)
        Y[i, :len(y)] = y
        nv[i] = len(y)
    return Y.reshape(tuple(shape_cells) + (nmax,)), nv.reshape(tuple(shape_cells))


def _cell_moments(vals, mask, n, binary):
    """Mean and variance of the mean for padded draws vals (..., nmax) with validity mask and counts n (...)."""
    s = (vals * mask).sum(-1)
    mean = s / n
    if binary:
        p = mean
        edge = (p == 0.0) | (p == 1.0)
        pt = np.where(edge, (s + 0.5) / (n + 1.0), p)
        return mean, pt * (1 - pt) / n
    dev = np.where(mask, vals - mean[..., None], 0.0)
    return mean, (dev ** 2).sum(-1) / (n - 1.0) / n


def cells_from_draws(Y1, nv1, Y0, nv0, sd, binary):
    """delta and v_c arrays (cell shape) from packed draws."""
    out = []
    for Y, nv in ((Y1, nv1), (Y0, nv0)):
        mask = np.arange(Y.shape[-1]) < nv[..., None]
        out.append(_cell_moments(np.where(mask, Y, 0.0), mask, nv.astype(float), binary))
    (m1, va1), (m0, va0) = out
    return (m1 - m0) / sd, (va1 + va0) / sd ** 2


def _resample(rng, Y, nv, b):
    """b bootstrap resamples (with replacement, within the valid draws) of every cell. Returns vals (b, cells, nmax) with the draws beyond
    the cell's valid count zeroed, the cell counts n (b, cells) and the cell shape. Y must be centred by cell (see bootstrap_draws)."""
    shp = nv.shape
    ncell, nmax = nv.size, Y.shape[-1]
    Yf, nvf = Y.reshape(ncell, nmax), nv.reshape(ncell)
    if (nvf == nmax).all():
        idx = rng.integers(0, nmax, size=(b, ncell, nmax))
        vals = Yf[np.arange(ncell)[None, :, None], idx]
    else:
        u = rng.random((b, ncell, nmax))
        idx = np.minimum((u * nvf[None, :, None]).astype(np.int64), np.maximum(nvf - 1, 0)[None, :, None])
        vals = Yf[np.arange(ncell)[None, :, None], idx]
        vals = np.where(np.arange(nmax)[None, None, :] < nvf[None, :, None], vals, 0.0)
    return vals, np.broadcast_to(nvf[None, :].astype(float), (b, ncell)), shp


def _moments_resampled(vals, n, binary):
    """Mean and variance of the mean of resampled draws (padding already zero). Continuous draws are passed cell-centred (well-conditioned
    sum of squares); binary draws are the 0/1 values themselves (sums are exact integers)."""
    s = vals.sum(-1)
    mean = s / n
    if binary:
        edge = (s == 0.0) | (s == n)
        pt = np.where(edge, (s + 0.5) / (n + 1.0), mean)
        return mean, pt * (1 - pt) / n
    ss = np.einsum("...i,...i->...", vals, vals)
    return mean, np.maximum(ss - s * s / n, 0.0) / (n - 1.0) / n


def bootstrap_draws(Y1, nv1, Y0, nv0, sd, binary, facets, B=DEFAULT_B, seed=DEFAULT_SEED, chunk=100, both=False):
    """Draw-level cell bootstrap of the whole estimator. Returns e1 (B, K), e2 (B, K+1) (jackknife-corrected shares), or with both=True
    (e1, e2, e1_naive, e2_naive).
    Within each cell the valid draws are resampled with replacement (the number of valid draws is kept).
    The observed cell means carry their own draw noise (variance v_obs), which is signal in the bootstrap world. A replicate is therefore
    scored with the residual reduced by mean(v*) (its own new noise) AND by mean(v_obs) (the noise already in the world); without the
    second term every replicate's remainder is too large by mean(v_obs) and the intervals are shifted (synthetic check: runs/acme-S-gstudy/synthetic/summary.json).
    The "naive" variant (both=True) reduces by mean(v*) only, i.e. the plain recompute."""
    facets = tuple(facets)
    rng = np.random.default_rng(seed)
    if (nv1 < 2).any() or (nv0 < 2).any():
        raise ValueError("every cell and condition needs >= 2 valid draws")
    cond = []
    for Y, nv in ((Y1, nv1), (Y0, nv0)):
        mask = np.arange(Y.shape[-1]) < nv[..., None]
        Yz = np.where(mask, Y, 0.0)
        shift = np.zeros(nv.shape) if binary else Yz.sum(-1) / nv      # continuous: centre by the cell mean of the valid draws
        cond.append((np.where(mask, Yz - shift[..., None], 0.0), nv, shift))
    _, v_obs = cells_from_draws(Y1, nv1, Y0, nv0, sd, binary)
    e1s, e2s, n1s, n2s = [], [], [], []
    for s in range(0, B, chunk):
        b = min(chunk, B - s)
        res = []
        for Yc, nv, shift in cond:
            vals, n, shp = _resample(rng, Yc, nv, b)
            mean_c, va = _moments_resampled(vals, n, binary)
            res.append((mean_c.reshape((b,) + shp) + shift[None], va.reshape((b,) + shp)))
        (m1, va1), (m0, va0) = res
        arr_b, v_b = (m1 - m0) / sd, (va1 + va0) / sd ** 2
        est = estimate(arr_b, v_b, facets, baked=v_obs)
        e1s.append(est["e1"])
        e2s.append(est["e2"])
        if both:
            nv_ = estimate(arr_b, v_b, facets)
            n1s.append(nv_["e1"])
            n2s.append(nv_["e2"])
    if both:
        return np.concatenate(e1s), np.concatenate(e2s), np.concatenate(n1s), np.concatenate(n2s)
    return np.concatenate(e1s), np.concatenate(e2s)


def percentile(x, level=0.95):
    a = (1 - level) / 2
    return np.quantile(x, [a, 1 - a], axis=0)


def analyse(delta, v, facets, draws=None, B=DEFAULT_B, seed=DEFAULT_SEED, level=0.95):
    """Full A1-S result of one item. draws: dict(Y1, nv1, Y0, nv0, sd, binary) for the bootstrap, or None (point and LOWO only)."""
    est = estimate(delta, v, facets)
    names = est["names"]
    res = dict(names=names, facets=list(facets), shape=list(np.shape(delta)), comps=est["comps"], e1=est["e1"], e2=est["e2"],
               e1_raw=est["e1_raw"], e2_raw=est["e2_raw"], lowo_e1=est["loo_e1"], lowo_e2=est["loo_e2"], draw_noise=float(est["comps"][-1]),
               draw_share_e2=float(est["e2"][-1]))
    a1n, a1 = a1_reference(delta, facets)
    # consistency with gstudy's own A1: E2 of every A1 term except 'res' is A1's share; draw + remainder is A1's residual share
    k = len(a1n)
    ir = len(a1n) - 1
    mine = np.array(est["e2"][:k], float)
    mine[ir] += est["e2"][k]
    res["a1_names"], res["a1_shares"] = a1n, a1
    res["a1_max_abs_diff"] = float(np.abs(mine - a1).max())
    if draws is not None:
        b1, b2 = bootstrap_draws(draws["Y1"], draws["nv1"], draws["Y0"], draws["nv0"], draws["sd"], draws["binary"], facets, B, seed)
        res.update(boot_e1=b1, boot_e2=b2, e1_ci=percentile(b1, level), e2_ci=percentile(b2, level), B=B, seed=seed)
    return res


# ----------------------------------------------------------------------------------------------------------------------------
# item inputs from the cell table (real data path)
# ----------------------------------------------------------------------------------------------------------------------------
LOGIT_CLIP = 12.0   # PREREG S4: logit scale for binary items, clip +-12, clip rate reported


def logit_cell(ybar1, ybar0, n1, n0, clip=LOGIT_CLIP):
    """Sensitivity S-d, one cell: delta = logit(p1) - logit(p0) with each logit clipped to +-clip, and the delta-method variance
    v = 1/(n1 p1 (1-p1)) + 1/(n0 p0 (1-p0)); where the sampled p is 0 or 1 the variance uses p~ = (k + 0.5)/(n + 1) (E7 item 2(a) continuity
    rule). Engineer's reading: the continuity rule applies to the variance only; the point value of an edge proportion is the clipped logit
    (+-clip). Returns delta, v and the number of clipped conditions (0, 1 or 2)."""
    d, v, nclip = [], 0.0, 0
    for p, n in ((ybar1, n1), (ybar0, n0)):
        k = p * n
        edge = (p <= 0.0) or (p >= 1.0)
        lg = -np.inf if p <= 0.0 else (np.inf if p >= 1.0 else float(np.log(p / (1.0 - p))))
        c = float(np.clip(lg, -clip, clip))
        nclip += int(c != lg)
        pt = (k + 0.5) / (n + 1.0) if edge else p
        v += 1.0 / (n * pt * (1.0 - pt))
        d.append(c)
    return d[0] - d[1], v, nclip


def item_arrays(cells, item, models, orders, ws=WS, ts=TS, logit=False, info=None):
    """Delta and v arrays of one item from cells.csv rows (a DataFrame), models in the order given. Axes M, W, [O], [T]: the O axis is dropped
    for items without an order, the T axis when a single temperature is requested (S-c). ws, ts select wordings and temperatures (S-e, S-c).
    logit=True (S-d, binary items): delta and v on the logit scale (logit_cell); info (dict) receives n_conditions, n_clipped, clip_rate."""
    c = cells[(cells["item"] == item) & (cells["model"].isin(models))].copy()
    c["O"] = c["O"].fillna("").astype(str)
    shape = (len(models), len(ws), len(orders), len(ts))
    d, v = np.full(shape, np.nan), np.full(shape, np.nan)
    mi, wi = {m: i for i, m in enumerate(models)}, {w: i for i, w in enumerate(ws)}
    oi, ti = {o: i for i, o in enumerate(orders)}, {float(t): i for i, t in enumerate(ts)}
    ncond = nclip = 0
    for r in c.itertuples(index=False):
        if r.W not in wi or float(r.T) not in ti:
            continue
        ix = (mi[r.model], wi[r.W], oi[r.O], ti[float(r.T)])
        if logit:
            d[ix], v[ix], k = logit_cell(r.ybar1, r.ybar0, r.n1, r.n0)
            nclip += k
            ncond += 2
        else:
            d[ix], v[ix] = r.delta, r.v_c
    if info is not None:
        info.update(n_conditions=ncond, n_clipped=nclip, clip_rate=(nclip / ncond if ncond else None))
    if len(ts) == 1:
        d, v = d[..., 0], v[..., 0]
    if len(orders) == 1 and orders[0] == "":
        d, v = d[:, :, 0], v[:, :, 0]     # O is axis 2 with or without a T axis behind it
    return d, v


def validity_roster(cells, roster, thr=0.9):
    """Sensitivity S-b. Operational definition of 'restrict to cells with parse validity >= thr' in a crossed design that needs complete arrays:
    keep a (model, item) pair only when EVERY planned cell has valid1 >= thr and valid0 >= thr (both conditions); the roster passed in is
    restricted further. Returns a roster DataFrame (same columns, plus all_cells_valid) with ok recomputed."""
    good = {}
    for (m, it), x in cells.groupby(["model", "item"]):
        good[(m, it)] = bool(((x["valid1"] >= thr) & (x["valid0"] >= thr)).all())
    r = roster.copy()
    allv = np.array([good.get((m, it), False) for m, it in zip(r["model"], r["item"])], bool)
    r["all_cells_valid"] = allv
    r["ok"] = r["ok"].astype(bool) & allv
    return r


def real_inputs(runs, cells, roster, item, with_draws=False, ts=TS, ws=WS, logit=False, info=None):
    """(delta, v, facets, draws, models) for one item on a roster DataFrame (columns model, item, ok)."""
    import armS_cells as AC
    import gate_g4 as g4
    models = sorted(roster[(roster["item"] == item) & roster["ok"]]["model"])
    orders = [("" if o is None else o) for o in g4.ORDERS.get(item, [None])]
    ts, ws = tuple(ts), tuple(ws)
    if logit and item not in AC.BINARY:
        raise ValueError(f"{item}: the logit scale (S-d) applies to binary items only")
    if with_draws and (ts != tuple(TS) or ws != tuple(WS) or logit):
        raise ValueError("the draw-level bootstrap is implemented for the main design only (no sensitivity switch)")
    d, v = item_arrays(cells, item, models, orders, ws, ts, logit, info)
    if not (np.isfinite(d).all() and np.isfinite(v).all()):
        raise ValueError(f"{item}: incomplete cells on this roster")
    draws = None
    if with_draws:
        sd = float(cells[cells["item"] == item]["sd"].iloc[0])
        Ys = {}
        for x in (1, 0):
            keys, store = [], {}
            for m in models:
                dm = AC.draws_for(Path(runs), m, item)
                for W in WS:
                    for O in g4.ORDERS.get(item, [None]):
                        for T in TS:
                            k = (m, W, O, T)
                            keys.append(k)
                            store[k] = dm[(W, O, T, x)][1]
            shp = d.shape[:1] + (len(WS),) + ((len(orders),) if d.ndim == 4 else ()) + (len(TS),)
            Ys[x] = pack(store, shp, keys, nmax=50)
        draws = dict(Y1=Ys[1][0], nv1=Ys[1][1], Y0=Ys[0][0], nv0=Ys[0][1], sd=sd, binary=item in AC.BINARY)
    return d, v, facets_for(d.ndim, len(ts) > 1), draws, models


def roster_models(roster, item):
    return sorted(roster[(roster["item"] == item) & roster["ok"].astype(bool)]["model"])


# ----------------------------------------------------------------------------------------------------------------------------
# output
# ----------------------------------------------------------------------------------------------------------------------------
def rows_for(item, res, models):
    rows = []
    names = res["names"]
    k = len(names) - 1
    for i, nm in enumerate(names):
        r = dict(item=item, n_models=len(models), term=(nm if i != k - 1 else ("res (remainder)" if nm == "res" else nm + " (remainder)")), component=float(res["comps"][i]),
                 E2_share=float(res["e2"][i]), E2_lowo_min=float(res["lowo_e2"][:, i].min()), E2_lowo_max=float(res["lowo_e2"][:, i].max()))
        if "e2_ci" in res:
            r.update(E2_lo=float(res["e2_ci"][0, i]), E2_hi=float(res["e2_ci"][1, i]))
        if i < k:
            r.update(E1_share=float(res["e1"][i]), E1_lowo_min=float(res["lowo_e1"][:, i].min()), E1_lowo_max=float(res["lowo_e1"][:, i].max()))
            if "e1_ci" in res:
                r.update(E1_lo=float(res["e1_ci"][0, i]), E1_hi=float(res["e1_ci"][1, i]))
        for w in range(res["lowo_e2"].shape[0]):
            r[f"E2_lowo_drop_W{w}"] = float(res["lowo_e2"][w, i])
            if i < k:
                r[f"E1_lowo_drop_W{w}"] = float(res["lowo_e1"][w, i])
        rows.append(r)
    return rows


def write_item(out: Path, item, res, models):
    import pandas as pd
    df = pd.DataFrame(rows_for(item, res, models))
    df.to_csv(out / f"components_{item}.csv", index=False)
    return df


# ----------------------------------------------------------------------------------------------------------------------------
# tests
# ----------------------------------------------------------------------------------------------------------------------------
def selftest():
    rng = np.random.default_rng(7)
    for shape in ((14, 4, 2, 2), (14, 4, 2), (6, 4, 2, 2)):
        arr = rng.standard_normal(shape) + rng.standard_normal(shape[:1] + (1,) * (len(shape) - 1)) * 2
        fac = facets_for(arr.ndim)
        zero = np.zeros_like(arr)
        # (1) noise-free: E1 = E2 = gstudy's A1, bit for bit, and the draw component is exactly 0
        est = estimate(arr, zero, fac)
        nm, a1 = a1_reference(arr, fac)
        k = len(nm)
        assert est["names"] == nm + ["draw"]
        assert np.array_equal(est["e2"][:k], a1), (shape, np.abs(est["e2"][:k] - a1).max())
        assert np.array_equal(est["e1"], a1) and est["e2"][k] == 0.0
        # (2) the batched jackknife formula equals gstudy.jackknife_correct
        e2 = G.jackknife_correct(est["e2_raw"], est["loo_e2"])
        assert np.allclose(e2, est["e2"], rtol=0, atol=1e-13)
        # (3) a batch (lead axis) gives the same numbers as single arrays
        both = estimate(np.stack([arr, arr + 1.0]), np.stack([zero, zero + 0.3]), fac)
        assert np.allclose(both["e2"][0], est["e2"], atol=1e-13)
        # (4) with constant draw noise c the residual moves by exactly c: shares of the split sum like A1 would
        c = 0.37
        withv = estimate(arr, zero + c, fac)
        assert np.isclose(withv["comps"][-1], c) and np.allclose(withv["comps"][:-1][np.array(nm) != "res"], est["comps"][:-1][np.array(nm) != "res"])
        assert np.isclose(withv["comps"][nm.index("res")], est["comps"][nm.index("res")] - c)
        res = analyse(arr, zero + c, fac)
        assert res["a1_max_abs_diff"] < 1e-12                       # draw + remainder is A1's residual share
        # (5) noise-free draws give a degenerate bootstrap: every replicate equals the point estimate
        n = 50
        Y1 = np.repeat(arr[..., None] / 2, n, axis=-1)
        Y0 = np.repeat(-arr[..., None] / 2, n, axis=-1)
        nv = np.full(arr.shape, n)
        d, v = cells_from_draws(Y1, nv, Y0, nv, 1.0, False)
        assert np.allclose(d, arr) and np.allclose(v, 0.0, atol=1e-25)
        b1, b2 = bootstrap_draws(Y1, nv, Y0, nv, 1.0, False, fac, B=60, seed=1)
        assert np.allclose(b2, est["e2"][None, :], atol=1e-9) and np.allclose(b1, est["e1"][None, :], atol=1e-9)
    # (5b) baked-in noise only moves the remainder and the total: remainder(baked=b) = remainder(0) - mean(b)
    b = np.full(arr.shape, 0.21)
    e0, eb = estimate(arr, zero + 0.1, fac, with_loo=False), estimate(arr, zero + 0.1, fac, with_loo=False, baked=b)
    ir = nm.index("res")
    assert np.isclose(eb["comps"][ir], e0["comps"][ir] - 0.21) and np.allclose(np.delete(eb["comps"], ir), np.delete(e0["comps"], ir))
    # (6) binary branch: continuity at p in {0, 1}, binomial variance otherwise
    Yb = np.zeros((1, 50))
    Yb[0, :20] = 1
    for Y, want in ((np.ones((1, 50)), (50.5 / 51) * (0.5 / 51) / 50), (Yb, 0.4 * 0.6 / 50)):
        m = np.ones(1) * 50
        _, va = _cell_moments(Y, np.ones_like(Y, bool), m, True)
        assert np.isclose(va[0], want), (va, want)
    # (7) the resampler draws only valid positions and has the right mean
    rng2 = np.random.default_rng(3)
    Y = np.full((2, 5), np.nan)
    Y[0, :3] = [1.0, 2.0, 3.0]
    Y[1, :5] = [10, 10, 10, 10, 10]
    Y = np.where(np.isnan(Y), 0.0, Y)
    vals, nn, _ = _resample(rng2, Y, np.array([3, 5]), 4000)
    assert set(np.unique(vals[:, 0, :3])) <= {1.0, 2.0, 3.0} and abs(vals[:, 0, :3].mean() - 2.0) < 0.05 and (vals[:, 1, :] == 10).all()
    assert (vals[:, 0, 3:] == 0).all() and (nn[:, 0] == 3).all()
    # (8) binary bootstrap path: all-ones cells use the continuity variance, mixed cells the binomial variance
    Yb = np.stack([np.ones(50), np.r_[np.ones(20), np.zeros(30)]])
    vb, nb, _ = _resample(rng2, Yb, np.array([50, 50]), 3000)
    mb, vv = _moments_resampled(vb, nb, True)
    assert np.allclose(mb[:, 0], 1.0) and np.allclose(vv[:, 0], (50.5 / 51) * (0.5 / 51) / 50)
    assert np.all(vv[:, 1] > 0) and abs(mb[:, 1].mean() - 0.4) < 0.01
    # (9) --no-bootstrap: the point estimates, the LOWO values and the A1 check do not depend on whether draws are bootstrapped
    shape = (5, 4, 2, 2)
    rng3 = np.random.default_rng(11)
    Y1 = rng3.standard_normal(shape + (50,)) + rng3.standard_normal(shape[:1] + (1, 1, 1, 1)) + 0.5
    Y0 = rng3.standard_normal(shape + (50,))
    nv = np.full(shape, 50)
    d9, v9 = cells_from_draws(Y1, nv, Y0, nv, 1.0, False)
    dr = dict(Y1=Y1, nv1=nv, Y0=Y0, nv0=nv, sd=1.0, binary=False)
    with_b = analyse(d9, v9, G.FACETS4, dr, B=20, seed=5)
    no_b = analyse(d9, v9, G.FACETS4, None)
    assert "e2_ci" not in no_b and "boot_e2" not in no_b and "e2_ci" in with_b
    for key in ("e1", "e2", "e1_raw", "e2_raw", "lowo_e1", "lowo_e2", "comps", "a1_shares"):
        assert np.array_equal(with_b[key], no_b[key]), key
    # the real-data row writer prints no interval columns without a bootstrap
    assert not any(k.endswith(("_lo", "_hi")) for r in rows_for("toy", no_b, list("abcde")) for k in r)
    # (10) slicing: S-c (T = 1.0 only) and S-e (drop W0) take exactly the matching entries of the full array
    import pandas as pd
    rows = []
    for mi, m in enumerate(["m0", "m1", "m2"]):
        for wi, w in enumerate(WS):
            for o in ("a", "b"):
                for t in TS:
                    p1, p0 = 0.30 + 0.01 * mi + 0.02 * wi, 0.20 + 0.005 * (o == "b") + 0.1 * (t == 1.0)
                    rows.append(dict(model=m, item="AF", W=w, O=o, T=t, n1=50, n0=50, ybar1=p1, ybar0=p0, delta=(p1 - p0) / 0.5, v_c=0.01 * (1 + wi),
                                     valid1=1.0, valid0=1.0))
    cdf = pd.DataFrame(rows)
    full_d, full_v = item_arrays(cdf, "AF", ["m0", "m1", "m2"], ["a", "b"])
    assert full_d.shape == (3, 4, 2, 2)
    c_d, c_v = item_arrays(cdf, "AF", ["m0", "m1", "m2"], ["a", "b"], ts=(1.0,))
    assert c_d.shape == (3, 4, 2) and np.array_equal(c_d, full_d[..., 1]) and np.array_equal(c_v, full_v[..., 1])
    assert facets_for(c_d.ndim, False) == G.FACETS3 and facets_for(3, True) == G.FACETS3T and facets_for(2, False) == G.FACETS2
    e_d, e_v = item_arrays(cdf, "AF", ["m0", "m1", "m2"], ["a", "b"], ws=WS[1:])
    assert e_d.shape == (3, 3, 2, 2) and np.array_equal(e_d, full_d[:, 1:]) and np.array_equal(e_v, full_v[:, 1:])
    both_d, _ = item_arrays(cdf, "AF", ["m0", "m1", "m2"], ["a", "b"], ws=WS[1:], ts=(1.0,))
    assert np.array_equal(both_d, full_d[:, 1:, :, 1])
    # an item without order: the O axis disappears, T stays (main) or goes (S-c)
    cdf1 = cdf[cdf["O"] == "a"].assign(O="")
    n_d, _ = item_arrays(cdf1, "AF", ["m0", "m1", "m2"], [""])
    assert n_d.shape == (3, 4, 2) and np.array_equal(n_d, full_d[:, :, 0, :])
    n_c, _ = item_arrays(cdf1, "AF", ["m0", "m1", "m2"], [""], ts=(1.0,))
    assert n_c.shape == (3, 4) and np.array_equal(n_c, full_d[:, :, 0, 1])
    # the sliced arrays run through the estimator with their own facets, and the wording LOWO has n_w values
    est_e = estimate(e_d, e_v, facets_for(e_d.ndim))
    assert est_e["loo_e2"].shape[0] == 3
    est_c = estimate(n_c, np.zeros_like(n_c), facets_for(n_c.ndim, False))
    assert est_c["loo_e2"].shape[0] == 4 and est_c["names"][-1] == "draw"
    # (11) logit scale: formula, edge clipping, continuity variance, clip count
    d11, v11, k11 = logit_cell(0.4, 0.2, 50, 50)
    assert np.isclose(d11, np.log(0.4 / 0.6) - np.log(0.2 / 0.8)) and np.isclose(v11, 1 / (50 * 0.24) + 1 / (50 * 0.16)) and k11 == 0
    d12, v12, k12 = logit_cell(1.0, 0.0, 50, 50)
    pt = 50.5 / 51
    assert np.isclose(d12, 2 * LOGIT_CLIP) and np.isclose(v12, 2 / (50 * pt * (1 - pt))) and k12 == 2
    info = {}
    item_arrays(cdf, "AF", ["m0", "m1", "m2"], ["a", "b"], logit=True, info=info)
    assert info["n_conditions"] == 2 * 3 * 4 * 2 * 2 and info["n_clipped"] == 0 and info["clip_rate"] == 0.0
    # (12) S-b roster: one cell below 0.9 in one condition drops that pair only
    bad = cdf.copy()
    bad.loc[(bad["model"] == "m1") & (bad["W"] == "W2") & (bad["O"] == "b") & (bad["T"] == 0.7), "valid0"] = 0.88
    ros = pd.DataFrame(dict(model=["m0", "m1", "m2"], item="AF", ok=[True, True, True]))
    rv = validity_roster(bad, ros)
    assert list(rv["ok"]) == [True, False, True] and list(validity_roster(cdf, ros)["ok"]) == [True, True, True]
    # (13) run refuses without --no-bootstrap unless --allow-intervals is given (E7a item 1); the two flags exclude each other
    for argv in (["run", "--approved-by-lead"], ["run", "--approved-by-lead", "--no-bootstrap", "--allow-intervals"], ["run", "--no-bootstrap"]):
        try:
            main(argv)
        except SystemExit as e:
            assert e.code not in (None, 0)
        else:
            raise AssertionError(argv)
    print("gstudy_armS selftest OK")


def synthetic_demo(out: Path, B=300):
    import synth_armS as S
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(DEFAULT_SEED)
    item = S.make_item("P3", S.load_v("P3"), "e3", ratio=3.0, rng=np.random.default_rng([DEFAULT_SEED, 1]))
    data = S.draw_dataset(item, rng)
    res = analyse(data["delta"], data["v"], item["facets"], data["draws"], B=B, seed=DEFAULT_SEED)
    df = write_item(out, "synthetic-P3", res, ["m%d" % i for i in range(item["shape"][0])])
    print(df[["term", "E1_share", "E1_lo", "E1_hi", "E2_share", "E2_lo", "E2_hi"]].to_string(index=False))


MIN_MODELS = 3   # decomposability floor of the agreed debate (research/debates/2026-11-07-CRP-S09-acme-post-gate-analysis, round 3)


def git_state():
    import subprocess

    def g(*a):
        return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()
    return dict(head=g("rev-parse", "HEAD"), analysis_dirty=bool(g("status", "--porcelain", "--", "analysis/acme")))


def write_readme(out: Path, argv, summary, label, extra=""):
    """README.md of one output directory: what it is, roster, exact command, code commit (HEAD at run time)."""
    ro = summary["meta"]
    gs = ro["git"]
    lines = [f"# {label}", "",
             "A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), "
             "residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.",
             "Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data "
             "(`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.",
             "", f"- roster file: `{ro['roster']}` ({ro['roster_note']})",
             f"- switches: validity_cells={ro['validity_cells']}, temps={ro['temps']}, logit={ro['logit']}, drop_W0={ro['drop_W0']}",
             f"- wordings used: {', '.join(ro['wordings'])}; decomposability floor: >= {ro['min_models']} models on the roster",
             f"- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py {shlex.join(argv)}`",
             f"- code commit at run time (HEAD): `{gs['head']}`; uncommitted changes under analysis/acme at run time: {gs['analysis_dirty']}", "",
             "| item | models | array | facets | note |", "|---|---|---|---|---|"]
    for it, s in summary["items"].items():
        lines.append(f"| {it} | {s['n_models']} | {'x'.join(map(str, s['shape']))} | {''.join(s['facets'])} | {s.get('note', '')} |")
    if summary["not_decomposed"]:
        lines += ["", "Not decomposed (fewer than the floor of models on this roster, or incomplete cells): "
                  + ", ".join(f"{k} ({v})" for k, v in summary["not_decomposed"].items())]
    lines += ["", "Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), "
              "`summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.", ""]
    if extra:
        lines += [extra, ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf8")


def main(argv=None):
    import pandas as pd
    argv_used = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["selftest", "dryrun", "run", "synthetic"])
    ap.add_argument("--cells", default=str(OUT / "cells.csv"))
    ap.add_argument("--roster", default=str(OUT / "roster_strict.csv"))
    ap.add_argument("--runs", default=str(ROOT / "runs"))
    ap.add_argument("--out", default=str(OUT / "analysis"))
    ap.add_argument("--items", default="")
    ap.add_argument("--B", type=int, default=DEFAULT_B)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--approved-by-lead", action="store_true")
    ap.add_argument("--no-bootstrap", action="store_true", help="point estimates and LOWO only; no draw is read, no interval is computed (E7a item 1)")
    ap.add_argument("--allow-intervals", action="store_true", help="E7a: needed to run the draw bootstrap on real Arm S data (not approved)")
    ap.add_argument("--validity-cells", action="store_true", help="S-b: keep only (model, item) pairs whose EVERY cell has validity >= 0.9 in both conditions")
    ap.add_argument("--temps", default="0.7,1.0", help="S-c: --temps 1.0 drops the T facet")
    ap.add_argument("--logit", action="store_true", help="S-d: logit scale for binary items (clip +-12)")
    ap.add_argument("--drop-w0", action="store_true", help="S-e: wordings W1-W3 only")
    ap.add_argument("--min-models", type=int, default=MIN_MODELS)
    ap.add_argument("--label", default="")
    ap.add_argument("--roster-note", default="")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        selftest()
        return
    if a.cmd == "synthetic":
        synthetic_demo(Path(a.out))
        return
    if a.cmd == "run":
        if a.no_bootstrap and a.allow_intervals:
            raise SystemExit("--no-bootstrap and --allow-intervals exclude each other")
        if not (a.no_bootstrap or a.allow_intervals):
            raise SystemExit("refusing to run on real Arm S data without --no-bootstrap (E7a item 1: no interval of any kind is computed); "
                             "--allow-intervals is the explicit override")
        if not a.approved_by_lead:
            raise SystemExit("refusing to run the real analysis without --approved-by-lead (E7: the lead reviews the synthetic check first)")
    ts = tuple(float(t) for t in a.temps.split(","))
    if not set(ts) <= set(TS):
        raise SystemExit(f"--temps must be a subset of {TS}")
    ws = WS[1:] if a.drop_w0 else WS
    cells = pd.read_csv(a.cells, dtype={"O": str, "W": str})
    roster = pd.read_csv(a.roster)
    if a.validity_cells:
        roster = validity_roster(cells, roster)
    import gate_g4 as g4
    items = [i for i in (a.items.split(",") if a.items else g4.TYPE) if i]
    if a.logit:
        import armS_cells as AC
        items = [i for i in items if i in AC.BINARY]
    if a.cmd == "dryrun":
        for it in items:
            if len(roster_models(roster, it)) < a.min_models:
                print(it, "models", len(roster_models(roster, it)), "not decomposed")
                continue
            d, v, fac, _, models = real_inputs(a.runs, cells, roster, it, with_draws=False, ts=ts, ws=ws, logit=a.logit)
            print(it, "models", len(models), "array", d.shape, "facets", "".join(fac), "finite", bool(np.isfinite(d).all() and np.isfinite(v).all()))
        return
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = dict(roster=str(a.roster), roster_note=a.roster_note or "outcome-blind validity rule of EXPERT-statistician.md section 1", cells=str(a.cells),
                validity_cells=a.validity_cells, temps=list(ts), logit=a.logit, drop_W0=a.drop_w0, wordings=list(ws), min_models=a.min_models,
                no_bootstrap=a.no_bootstrap, git=git_state(), argv=argv_used)
    summary = dict(meta=meta, items={}, not_decomposed={})
    for j, it in enumerate(items):
        nm = len(roster_models(roster, it))
        if nm < a.min_models:
            summary["not_decomposed"][it] = f"{nm} models on this roster"
            continue
        info = {}
        try:
            d, v, fac, draws, models = real_inputs(a.runs, cells, roster, it, with_draws=not a.no_bootstrap, ts=ts, ws=ws, logit=a.logit, info=info)
        except ValueError as e:
            summary["not_decomposed"][it] = str(e)
            continue
        res = analyse(d, v, fac, draws, B=a.B, seed=[a.seed, j])
        write_item(out, it, res, models)
        s = dict(models=models, n_models=len(models), shape=list(d.shape), facets=list(fac), wordings=list(ws), temps=list(ts),
                 a1_max_abs_diff=res["a1_max_abs_diff"], draw_share_e2=res["draw_share_e2"])
        if a.logit:
            s.update(info)
            s["note"] = f"logit scale, clip rate {info['clip_rate']:.4f} ({info['n_clipped']} of {info['n_conditions']} conditions)"
        if not a.no_bootstrap:
            s.update(B=a.B, seed=a.seed)
        summary["items"][it] = s
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf8")
    extra = []
    if a.logit:
        extra.append("Logit scale (S-d): cell delta = logit(p1) - logit(p0), each logit clipped to +-12 (PREREG S4); v_c = delta method 1/(n p (1-p)) per "
                 "condition, p replaced by (k + 0.5)/(n + 1) when the sampled p is 0 or 1. Shares are invariant to a common rescaling of an item's "
                 "array, so no ML1-SD rescale is applied. Engineer's reading: the continuity rule is for the variance only; the point value of an "
                 "edge proportion is the clipped logit (+-12). Clip rate per item is in summary.json.")
    if a.validity_cells:
        extra.append("Validity cells (S-b), operational definition: in a crossed design that needs complete arrays, 'restrict to cells with validity >= 0.9' "
                 "is read as keeping a (model, item) pair only when EVERY planned cell has parse validity >= 0.9 in both conditions (x = 1 and x = 0); "
                 "the roster given by --roster is restricted further. Engineer's reading.")
    if a.drop_w0:
        extra.append("Drop W0 (S-e): wordings W1-W3 only; LOWO then has 3 values (each drops one of the three paraphrases).")
    if ts == (1.0,):
        extra.append("T = 1.0 only (S-c): no T facet (facets M, W, O or M, W); LOWO as before over the four wordings.")
    write_readme(out, argv_used, summary, a.label or "A1-S run", "\n\n".join(extra))
    print("wrote", out, "| decomposed:", list(summary["items"]), "| not:", summary["not_decomposed"])


if __name__ == "__main__":
    main()
