"""Cell effects, spread S, decomposition, validity and sign stability for one model x paradigm.

    .venv/Scripts/python.exe -I analysis/pilot/analyze_pilot.py --model olmo2-1b-instruct --paradigm P1 [--runs runs/pilot] [--B 2000]
        [--no-topup] [--unfinished invalid|f0_parsed_valid]

Reads runs/pilot/<model>/<paradigm>.jsonl (greedy rows excluded from the cell analysis, reported separately),
writes runs/pilot/<model>/analysis_<paradigm>.json. Metrics (design v0.4 + Amendment A1):
  P1  log OR of choosing the sure program (binary)
  P2* Hedges g on log estimate (primary, Amendment A1.2), g on the raw estimate (sensitivity, "not recoverable")
  P3  Hedges g on the rating
  P4  Hedges g on log(1+estimate) (primary), g on the raw estimate (sensitivity)
Cells whose effect is undefined (fewer than 2 valid responses in an arm, or zero pooled SD for a continuous outcome)
are listed; if any exist the grid is incomplete, S is computed over the defined cells (moment formula, C = defined cells)
and the ANOVA decomposition is skipped.
Validity (Amendment A1.10): primary = parsed AND finished, for both formats; sensitivity `--unfinished
f0_parsed_valid` keeps parsed-but-unfinished F0 answers. Top-up (A1.9): rows in <paradigm>.topup512.jsonl replace
the 256-token rows with the same key unless --no-topup. Output: analysis_<paradigm>[.notopup][.f0sens].json.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402

METRICS = {
    "P1": [("primary", "binary", lambda y: y, "log OR (sure option), gain vs loss")],
    "P3": [("primary", "cont", lambda y: y, "Hedges g")],
    "P4": [("primary", "cont", np.log1p, "Hedges g on log(1+x)"), ("sens_raw", "cont", lambda y: y, "Hedges g on raw")],
}
for _p in ("P2a", "P2b", "P2c", "P2d"):
    METRICS[_p] = [("primary", "cont", np.log, "Hedges g on log (A1.2)"),
                   ("sens_raw", "cont", lambda y: y, "Hedges g on raw (sensitivity, not recoverable)")]


# lower bound on the pooled SD of a cell (keeps resampled cells finite; affects only cells with SD below one rounding step / sqrt(12)):
# raw integer responses 1/sqrt(12); log and log(1+x) of integers: (log 2 - log 1)/sqrt(12) = 0.2
SD_FLOOR = {"primary": 1 / np.sqrt(12), "sens_raw": 1 / np.sqrt(12), "sens_log": 0.2}
SD_FLOOR_BY_PARADIGM = {_p: {"primary": 0.2, "sens_raw": 1 / np.sqrt(12)} for _p in ("P2a", "P2b", "P2c", "P2d", "P4")}


def sd_floor(paradigm, mid):
    return SD_FLOOR_BY_PARADIGM.get(paradigm, {}).get(mid, SD_FLOOR[mid])


def load(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf8").splitlines() if l.strip()]


def analyze(model, paradigm, runs="runs/pilot", B=2000, seed=1, topup=True, unfinished="invalid", scale="standardised"):
    rows = load(ROOT / runs / model / f"{paradigm}.jsonl")
    tfile = ROOT / runs / model / f"{paradigm}.topup512.jsonl"
    n_topup = 0
    if topup and tfile.exists():
        rep = {r["key"]: r for r in load(tfile)}
        n_topup = sum(r["key"] in rep for r in rows)
        rows = [rep.get(r["key"], r) for r in rows]
    for r in rows:   # A1.10: an unfinished answer is invalid (sensitivity: parsed unfinished F0 answers kept)
        r["valid_parser"] = r["valid"]
        r["valid"] = bool(r["valid"]) and (r["finished"] or (unfinished == "f0_parsed_valid" and r["F"] == "F0"))
        if paradigm.startswith("P2") and r["valid"] and not (r["y"] is not None and r["y"] > 0):
            r["valid"] = False   # as the human side (analysis/human_ml1/build_tidy.py keeps y > 0 for every P2 metric)
    sampled = [r for r in rows if not r["greedy"]]
    greedy = [r for r in rows if r["greedy"]]
    Ws = sorted({r["W"] for r in sampled})
    Fs = sorted({r["F"] for r in sampled})
    Ts = sorted({r["T"] for r in sampled})
    Os = sorted({r["O"] for r in sampled if r["O"]}) or [None]
    factors = ["W", "F", "T"] + (["O"] if Os != [None] else [])
    levels = [len(Ws), len(Fs), len(Ts)] + ([len(Os)] if Os != [None] else [])
    design = E.Design(factors, levels)
    out = dict(model=model, paradigm=paradigm, validity_rule=unfinished, topup_rows_replaced=n_topup,
               valid_by_parser_but_unfinished=sum(1 for r in sampled if r["valid_parser"] and not r["finished"]), factors=factors, levels=levels, level_names=dict(W=Ws, F=Fs, T=Ts, O=Os),
               n_sampled=len(sampled), n_greedy=len(greedy))
    # validity per cell
    val_cells, cell_rows = {}, {}
    for r in sampled:
        key = (Ws.index(r["W"]), Fs.index(r["F"]), Ts.index(r["T"])) + ((Os.index(r["O"]),) if Os != [None] else ())
        cell_rows.setdefault(key, []).append(r)
    for key, rs in cell_rows.items():
        val_cells["|".join(map(str, key))] = dict(n=len(rs), valid=sum(r["valid"] for r in rs), share=sum(r["valid"] for r in rs) / len(rs))
    out["validity_overall"] = sum(r["valid"] for r in sampled) / max(1, len(sampled))
    out["validity_by_format"] = {F: float(np.mean([r["valid"] for r in sampled if r["F"] == F])) for F in Fs}
    out["cells_below_80pct_validity"] = sorted(k for k, v in val_cells.items() if v["share"] < 0.8)
    out["validity_cells"] = val_cells
    out["parse_methods"] = {m: sum(1 for r in sampled if r["parse_method"] == m) for m in {r["parse_method"] for r in sampled}}
    out["truncated_unfinished"] = sum(1 for r in sampled if not r["finished"])
    if greedy:
        g1 = [r["y"] for r in greedy if r["x"] == 1 and r["valid"]]
        g0 = [r["y"] for r in greedy if r["x"] == 0 and r["valid"]]
        out["greedy"] = dict(n=len(greedy), valid=sum(r["valid"] for r in greedy), mean_x1=float(np.mean(g1)) if g1 else None,
                             mean_x0=float(np.mean(g0)) if g0 else None,
                             share_pairs_canonical_sign=None)
    rng = np.random.default_rng(seed)
    out["metrics"] = {}
    for mid, kind, tf, label in METRICS[paradigm]:
        cells, undefined = {}, []
        for key in itertools.product(*[range(L) for L in levels]):
            rs = [r for r in cell_rows.get(key, []) if r["valid"]]
            y1 = np.array([r["y"] for r in rs if r["x"] == 1], float)
            y0 = np.array([r["y"] for r in rs if r["x"] == 0], float)
            if kind == "cont":
                y1, y0 = tf(y1), tf(y0)
                if len(y1) < 2 or len(y0) < 2 or not np.isfinite(y1).all() or not np.isfinite(y0).all():
                    undefined.append((key, "n<2 or non-finite")); continue
            elif len(y1) < 1 or len(y0) < 1:
                undefined.append((key, "empty arm")); continue
            cells[key] = (y1, y0)
        res = dict(label=label, n_cells_defined=len(cells), n_cells=design.C, undefined=[("|".join(map(str, k)), why) for k, why in undefined])
        if undefined:
            # incomplete grid: S over the defined cells, moment formula with the formula variance, no decomposition, no interval
            d = np.array([E.effect(kind, *cells[k], sd_floor(paradigm, mid))[0] for k in cells])
            v = np.array([E.effect(kind, *cells[k], sd_floor(paradigm, mid))[1] for k in cells])
            s2 = float(E.spread_s2(d, v))
            z = 1.959964
            res.update(dbar=float(d.mean()), S2_untruncated=s2, S=float(np.sqrt(max(0, s2))), sign_stability=float(np.mean(d - z * np.sqrt(v) > 0)),
                       note="incomplete grid: S over defined cells, no decomposition, no interval")
        else:
            floor = sd_floor(paradigm, mid) if kind == "cont" else 0.0
            vmeth = "formula" if kind == "binary" else "splithalf"   # A1: analytic Woolf variance for log OR, split-half for continuous metrics
            if scale == "raw":
                # POST-RESULTS sensitivity analysis (statistician 2026-10-16, near-deterministic cells): force the A1.6 raw-unit route for
                # every cell grid: mean difference on the metric scale (log-estimate, log(1+x), rating points; risk difference for P1).
                r_ = E.estimate2(cells, design, "diff", rng=rng, B=B, K=200, var_method="splithalf", intervals=("ti_boot",))
            else:
                r_ = E.estimate2(cells, design, kind, rng=rng, B=B, K=200, var_method=vmeth, sd_floor=floor, intervals=("ti_boot",))
            if scale == "raw":
                res["scale"] = "raw_difference_forced"
            elif r_["status"] == "deterministic_cells":
                # Amendment A1 rule: pooled SD 0 with different arm means -> Hedges g undefined for that cell. The whole
                # model x paradigm x metric is analysed as the raw mean difference (response units; human counterpart on the same scale).
                res["standardised_unavailable"] = dict(deterministic_cells=["|".join(map(str, k)) for k in r_["deterministic_cells"]])
                r_ = E.estimate2(cells, design, "diff", rng=rng, B=B, K=200, var_method="splithalf", intervals=("ti_boot",))
                res["scale"] = "raw_difference"
            else:
                res["scale"] = "standardised"
            iv = r_.pop("intervals")["ti_boot"]
            r_["S_ci"], r_["S2_ci"] = iv["S"], iv["S2"]
            r_["terms_ci"] = {n: iv[n] for n in r_["terms"]}
            r_["dbar_minus_2S_lower"], r_["dbar_plus_2S_upper"] = iv["dbar_minus_2S_lower"], iv["dbar_plus_2S_upper"]
            r_["factor_shares_reportable"] = iv["factor_shares_reportable"]
            tot = sum(r_["terms"].values())
            r_["shares"] = {n: c / tot for n, c in r_["terms"].items()} if r_["factor_shares_reportable"] and tot > 0 else None
            res["split_half"] = r_
            res.update({k: r_[k] for k in ("dbar", "S", "S2_untruncated", "sign_stability", "S_ci")})
            # legacy comparator: normal-theory variance (design v0.4) point estimate only
            rf = E.estimate2(cells, design, kind if res["scale"] == "standardised" else "diff", rng=rng, var_method="formula", sd_floor=floor,
                             intervals=(), term_intervals=False)
            res["formula_variance_point"] = dict(S=rf["S"], S2_untruncated=rf["S2_untruncated"])
        out["metrics"][mid] = res
    tag = ("" if topup else ".notopup") + ("" if unfinished == "invalid" else ".f0sens") + ("" if scale == "standardised" else ".rawscale")
    dest = ROOT / runs / model / f"analysis_{paradigm}{tag}.json"
    dest.write_text(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)), encoding="utf8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--paradigm", required=True)
    ap.add_argument("--runs", default="runs/pilot")
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--no-topup", action="store_true")
    ap.add_argument("--unfinished", choices=["invalid", "f0_parsed_valid"], default="invalid")
    ap.add_argument("--scale", choices=["standardised", "raw"], default="standardised",
                    help="raw: sensitivity analysis forcing the raw-unit (A1.6) route for every grid; default unchanged (Amendment A1)")
    a = ap.parse_args()
    o = analyze(a.model, a.paradigm, a.runs, a.B, topup=not a.no_topup, unfinished=a.unfinished, scale=a.scale)
    print(f"{a.model} {a.paradigm}: sampled={o['n_sampled']} validity={o['validity_overall']:.3f} by_format={o['validity_by_format']}")
    for mid, m in o["metrics"].items():
        if "split_half" in m:
            r_ = m["split_half"]
            ci = [round(x, 3) for x in r_["S_ci"]]
            print(f"  {mid} [{m['scale']}]: cells {m['n_cells_defined']}/{m['n_cells']} dbar={r_['dbar']:.3f} S={r_['S']:.3f} "
                  f"CI95={ci} shares_reportable={r_['factor_shares_reportable']} sign_stab={r_['sign_stability']:.2f}")
        if "note" in m:
            print("  ", mid, m["note"], "S=", round(m["S"], 3))
