"""Side-by-side tables of the Many Labs 1 pilot (RQ5): each LLM x paradigm next to the human ML1 benchmark.

    .venv/Scripts/python.exe -I analysis/pilot/side_by_side.py [--out runs/pilot-side-by-side]

Table building only (CPU, no model run, no new estimator). Reads, never writes, the earlier runs:
  runs/pilot/<model>/analysis_<paradigm>{,.rawscale,.f0sens,.notopup}.json   (full-precision source of the summary tables;
        checked against runs/pilot-analysis/summary*.md with analysis/pilot/summarise_pilot.fmt)
  runs/human-ml1/metafor_results.json, moment_summary.json, runs/pilot-sim2/human_spread_a1.fixed.txt,
  runs/pilot-analysis/near-deterministic/human_sd.csv, rawscale.csv, data/processed/ml1/P1.csv (human P1 raw-scale interval)
  runs/pilot-side-by-side/nd_rerun/*.csv  (analysis/pilot/diagnose_near_deterministic.py re-run into a new folder, so that
        olmo2-1b-instruct has flags; the 30 earlier grids reproduce the earlier summary.csv, see log)
Writes (all under --out, plus paper/tables): table_a1.csv, table_a2.csv, paper/tables/pilot_a1.tex, pilot_a2.tex,
  fig_inputs/{fig11_forest,fig12_variance_terms,fig13_sign_cells,fig13_sign_factor_levels}.csv, summary.md, config.json, log.txt.
Rules applied (research/prereg/pilot-design.md, section 6 and Amendment A1): see rule_outcome() and spread_statement().
The ratio S / S^H is written to the csv only (column name says NOT preregistered): section 5 says "No ratio".
"""
import argparse
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402
from summarise_pilot import fmt  # noqa: E402  (same 3-decimal formatting as runs/pilot-analysis/summary*.md)

MODELS = ["granite-3.3-2b-instruct", "granite-3.3-8b-instruct", "olmo2-1b-instruct", "olmo2-7b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-7b-instruct"]
PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
PLABEL = {"P1": "P1 framing", "P2a": "P2a anchoring (SF-NYC)", "P2b": "P2b anchoring (Chicago)", "P2c": "P2c anchoring (Everest)",
          "P2d": "P2d anchoring (babies/day)", "P3": "P3 sunk cost", "P4": "P4 gambler's fallacy"}
A1_SCALE = {"P1": "log OR (sure option)", "P2a": "Hedges g on log", "P2b": "Hedges g on log", "P2c": "Hedges g on log", "P2d": "Hedges g on log",
            "P3": "Hedges g", "P4": "Hedges g on log(1+x)"}
A2_SCALE = {"P1": "risk difference (sure option)", "P2a": "mean difference of log estimate", "P2b": "mean difference of log estimate",
            "P2c": "mean difference of log estimate", "P2d": "mean difference of log estimate", "P3": "mean difference, rating points",
            "P4": "mean difference of log(1+x)"}
HUMAN_A1_KEY = {"P1": "P1/primary", "P2a": "P2a/sens_log", "P2b": "P2b/sens_log", "P2c": "P2c/sens_log", "P2d": "P2d/sens_log", "P3": "P3/primary", "P4": "P4/primary"}
HUMAN_SH_LABEL = {"P1": "P1 framing log OR", "P2a": "P2a NYC g (log)", "P2b": "P2b Chicago g (log)", "P2c": "P2c Everest g (log)", "P2d": "P2d babies g (log)",
                   "P3": "P3 sunk g", "P4": "P4 gambler g log1p"}
LOW_VALIDITY = 0.80

OUT = None
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ----------------------------------------------------------------------------------------------------------- inputs
def load_llm(tag):
    res = {}
    for m in MODELS:
        for p in PARADIGMS:
            f = ROOT / "runs/pilot" / m / f"analysis_{p}{tag}.json"
            if f.exists():
                res[(m, p)] = (json.loads(f.read_text(encoding="utf8")), f)
    return res


def parse_summary_md(path):
    rows = {}
    for line in Path(path).read_text(encoding="utf8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 9 and c[0] in MODELS and c[1] in PARADIGMS:
            rows[(c[0], c[1])] = c
    return rows


def check_against_md(llm, md_path, label):
    """Every dbar [CI], S [TI], validity, S2>0 and sign stability printed in the summary table is reproduced by the json."""
    md = parse_summary_md(md_path)
    n = 0
    for (m, p), (o, f) in llm.items():
        mt = o["metrics"]["primary"]
        r = mt["split_half"]
        dci = r["dbar_ci"]
        want = [fmt(o["validity_overall"]), f"{mt['n_cells_defined']}/{mt['n_cells']}", f"{fmt(r['dbar'])} [{fmt(dci[0])}, {fmt(dci[1])}]",
                f"{fmt(r['S'])} [{fmt(r['S_ci'][0])}, {fmt(r['S_ci'][1])}]", str(r["S2_ci"][0] > 0), fmt(r["sign_stability"], 2)]
        got = md[(m, p)][3:9]
        assert want == got, (label, m, p, want, got)
        n += 1
    log(f"check {label}: {n} rows of {Path(md_path).name} reproduced from the json (dbar, CI, S, TI, S2>0, sign stability, validity)")
    return n


def human_fixed_txt(path):
    out = {}
    rx = re.compile(r"^(.+?)\s{2,}36\s+(-?[\d.]+)\s+([\d.]+)\s+\[\s*([\d.]+),\s*([\d.]+)\]\s+(True|False)\s*\|\s*([\d.]+)\s*$")
    for line in Path(path).read_text(encoding="utf8").splitlines():
        m = rx.match(line.strip())
        if m:
            out[m.group(1).strip()] = dict(S2hat=float(m.group(2)), SH=float(m.group(3)), SH_lo=float(m.group(4)), SH_hi=float(m.group(5)),
                                           S2_lower_gt0=m.group(6) == "True", SH_formula_v=float(m.group(7)))
    return out


# ----------------------------------------------------------------------------------------------------------- rules
def rule_outcome(ss, dbar, S, dm2s_lower):
    """Section 6 + A1.4. Canonical sign is positive for every paradigm (all ML1 effects are positive; asserted below).
    Stable: sign stability >= 0.9 and the conservative lower range dbar_lo - 2 S_hi stays above 0.
    Fragile: sign stability < 0.6, or dbar - 2S and dbar + 2S lie on opposite sides of zero (point estimates, literal reading).
    Otherwise: neither (the preregistered rules name no third label)."""
    if ss >= 0.9 and dm2s_lower > 0:
        return "stable"
    if ss < 0.6 or (dbar - 2 * S < 0 < dbar + 2 * S):
        return "fragile"
    return "neither"


def spread_statement(S_lo, S_hi, H_lo, H_hi):
    """Section 5/6: 'larger' or 'smaller' only when the two intervals do not overlap; conservative descriptive rule."""
    if S_lo > H_hi:
        return "larger"
    if S_hi < H_lo:
        return "smaller"
    return "no statement (intervals overlap)"


def sign_text(dbar, lo, hi, hsign):
    agree = np.sign(dbar) == hsign
    excl = (lo > 0) or (hi < 0)
    return agree, excl


# ----------------------------------------------------------------------------------------------------------- builders
def human_a1(metafor, moment, fixed):
    H = {}
    for p in PARADIGMS:
        mf, mo, fx = metafor[HUMAN_A1_KEY[p]], moment[HUMAN_A1_KEY[p]], fixed[HUMAN_SH_LABEL[p]]
        H[p] = dict(k=mf["k"], N=mo["n_total"], mu=mf["mu"], mu_lo=mf["mu_ci"][0], mu_hi=mf["mu_ci"][1], tau=mf["tau"], tau_lo=mf["tau_ci_qprofile"][0],
                    tau_hi=mf["tau_ci_qprofile"][1], I2=mf["I2"], dbar_unweighted=mo["dbar"], SH=fx["SH"], SH_lo=fx["SH_lo"], SH_hi=fx["SH_hi"],
                    SH_S2_lower_gt0=fx["S2_lower_gt0"], SH_formula_v=fx["SH_formula_v"], human_metric_key=HUMAN_A1_KEY[p])
        assert H[p]["mu"] > 0, p
    return H


def human_a2(hsd, rawscale_orig, p1_dbar_ci):
    H = {}
    hs = hsd.set_index("paradigm")
    rs = rawscale_orig[rawscale_orig.paradigm == "P1"].iloc[0]
    for p in PARADIGMS:
        if p == "P1":
            H[p] = dict(k=36, mu=float(rs.human_raw_dbar), mu_lo=p1_dbar_ci[0], mu_hi=p1_dbar_ci[1], SH=float(rs.human_raw_S), SH_lo=float(rs.human_raw_S_lo),
                        SH_hi=float(rs.human_raw_S_hi), sigma=np.nan, mu_ci_source="recomputed here (estimators.estimate2 'diff' on data/processed/ml1/P1.csv, seed 20261016)")
        else:
            r = hs.loc[p]
            H[p] = dict(k=int(r.k_sites), mu=float(r.raw_dbar), mu_lo=float(r.raw_dbar_lo), mu_hi=float(r.raw_dbar_hi), SH=float(r.raw_S), SH_lo=float(r.raw_S_lo),
                        SH_hi=float(r.raw_S_hi), sigma=float(r.sd_pooled), mu_ci_source="human_sd.csv")
        assert H[p]["mu"] > 0, p
    return H


def flags_for(o, nd_row, p1_sep, notopup_o):
    n = o["n_sampled"]
    low_cells = len(o["cells_below_80pct_validity"])
    f = dict(
        validity_overall=o["validity_overall"], low_validity_overall=o["validity_overall"] < LOW_VALIDITY,
        n_cells_validity_lt80=low_cells,
        topup_rows_replaced=o["topup_rows_replaced"], topup_used=o["topup_rows_replaced"] > 0,
        unfinished_excluded_n=o["valid_by_parser_but_unfinished"], unfinished_excluded_share_of_sampled=o["valid_by_parser_but_unfinished"] / n,
        unfinished_total_n=o["truncated_unfinished"], n_sampled=n,
        nd_flag_rule=nd_row["flag_rule"], nd_n_flagged=int(nd_row["n_flagged"]), nd_C=int(nd_row["C"]), nd_flag_any=int(nd_row["n_flagged"]) > 0,
        nd_share_ss_flagged=nd_row["share_ss_flagged"],
        nd_n_at_floor=(int(nd_row["n_at_floor"]) if not pd.isna(nd_row.get("n_at_floor")) else np.nan),
        nd_n_le_2xfloor=(int(nd_row["n_le_2xfloor"]) if not pd.isna(nd_row.get("n_le_2xfloor")) else np.nan),
        p1_complete_separation_cells=p1_sep,
    )
    return f


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/pilot-side-by-side")
    a = ap.parse_args()
    OUT = ROOT / a.out
    (OUT / "fig_inputs").mkdir(parents=True, exist_ok=True)
    (ROOT / "paper/tables").mkdir(parents=True, exist_ok=True)

    P = ROOT / "runs"
    inputs = [P / "pilot-analysis/summary.md", P / "pilot-analysis/summary.rawscale.md", P / "pilot-analysis/summary.f0sens.md", P / "pilot-analysis/summary.notopup.md",
              P / "human-ml1/benchmark_table.md", P / "human-ml1/benchmark_table.csv", P / "human-ml1/metafor_results.json", P / "human-ml1/moment_summary.json",
              P / "pilot-sim2/human_spread_a1.fixed.txt", P / "pilot-analysis/near-deterministic/human_sd.csv", P / "pilot-analysis/near-deterministic/rawscale.csv",
              P / "pilot-analysis/near-deterministic/summary.csv", P / "pilot-side-by-side/nd_rerun/summary.csv", P / "pilot-side-by-side/nd_rerun/p1_arm_proportions.csv",
              P / "pilot-side-by-side/nd_rerun/rawscale.csv", P / "pilot-topup/trigger.txt", ROOT / "data/processed/ml1/P1.csv", ROOT / "research/prereg/pilot-design.md"]
    llm = {tag: load_llm(tag) for tag in ["", ".rawscale", ".f0sens", ".notopup"]}
    log(f"json grids found: primary {len(llm[''])}, rawscale {len(llm['.rawscale'])}, f0sens {len(llm['.f0sens'])}, notopup {len(llm['.notopup'])}")
    assert len(llm[""]) == 42 and len(llm[".rawscale"]) == 42 and len(llm[".f0sens"]) == 42
    json_hashes = {str(f.relative_to(ROOT)).replace("\\", "/"): sha(f) for tag in llm for (_, f) in llm[tag].values()}
    in_hashes = {str(f.relative_to(ROOT)).replace("\\", "/"): sha(f) for f in inputs}

    # consistency of json with the printed summary tables (A1 primary, A2 raw, the two sensitivities)
    check_against_md(llm[""], P / "pilot-analysis/summary.md", "A1 primary")
    check_against_md(llm[".rawscale"], P / "pilot-analysis/summary.rawscale.md", "A2 rawscale")
    check_against_md(llm[".f0sens"], P / "pilot-analysis/summary.f0sens.md", "f0sens")
    check_against_md(llm[".notopup"], P / "pilot-analysis/summary.notopup.md", "notopup (analysed grids only)")

    metafor = json.loads((P / "human-ml1/metafor_results.json").read_text(encoding="utf8"))
    moment = json.loads((P / "human-ml1/moment_summary.json").read_text(encoding="utf8"))
    fixed = human_fixed_txt(P / "pilot-sim2/human_spread_a1.fixed.txt")
    assert all(v in fixed for v in HUMAN_SH_LABEL.values()), fixed.keys()
    H1 = human_a1(metafor, moment, fixed)
    log("human A1 side: " + "; ".join(f"{p} mu {H1[p]['mu']:.3f} tau {H1[p]['tau']:.3f} S^H {H1[p]['SH']:.3f}" for p in PARADIGMS))

    # human P1 raw-scale interval: not in any earlier output; same call as diagnose_near_deterministic.py (seed 20261016)
    hsd = pd.read_csv(P / "pilot-analysis/near-deterministic/human_sd.csv")
    rs_orig = pd.read_csv(P / "pilot-analysis/near-deterministic/rawscale.csv")
    p1h = pd.read_csv(ROOT / "data/processed/ml1/P1.csv")
    cells = {(i,): (g.loc[g.x == 1, "y"].to_numpy(float), g.loc[g.x == 0, "y"].to_numpy(float)) for i, (_, g) in enumerate(p1h.groupby("site", sort=True))}
    rr = E.estimate2(cells, E.Design(["site"], [len(cells)]), "diff", rng=np.random.default_rng(20261016), B=2000, K=200, var_method="splithalf",
                     intervals=("ti_boot",), term_intervals=False)
    p1_rs = rs_orig[rs_orig.paradigm == "P1"].iloc[0]
    assert abs(rr["dbar"] - p1_rs.human_raw_dbar) < 1e-9, (rr["dbar"], p1_rs.human_raw_dbar)
    log(f"human P1 raw dbar recomputed {rr['dbar']:.4f} equals rawscale.csv human_raw_dbar {p1_rs.human_raw_dbar:.4f}; 95% CI {rr['dbar_ci'][0]:.3f}, {rr['dbar_ci'][1]:.3f}"
        f" (S^H from this call {rr['intervals']['ti_boot']['S']} versus stored [{p1_rs.human_raw_S_lo:.4f}, {p1_rs.human_raw_S_hi:.4f}]; stored values are used)")
    H2 = human_a2(hsd, rs_orig, [float(rr["dbar_ci"][0]), float(rr["dbar_ci"][1])])

    nd = pd.read_csv(P / "pilot-side-by-side/nd_rerun/summary.csv")
    nd = nd[nd.metric == "primary"].set_index(["model", "paradigm"])
    old = pd.read_csv(P / "pilot-analysis/near-deterministic/summary.csv")
    old = old[old.metric == "primary"].set_index(["model", "paradigm"])
    com = old.index
    for c in ["n_flagged", "n_le_1xfloor", "n_le_2xfloor", "share_ss_flagged", "dbar"]:
        x, y = old.loc[com, c].astype(float).to_numpy(), nd.loc[com, c].astype(float).to_numpy()
        assert np.nanmax(np.abs(x - y)) < 1e-12, c
    dS = (old.loc[com, "S"] - nd.loc[com, "S"]).abs()
    log(f"near-deterministic re-run vs earlier summary.csv: {len(com)} primary grids, flag counts, SD counts, share_ss_flagged, dbar identical; "
        f"S differs in {int((dS > 1e-9).sum())} grid(s): {[(i, round(float(old.loc[i, 'S']), 4), round(float(nd.loc[i, 'S']), 4)) for i in dS[dS > 1e-9].index]} "
        "(inference, not checked: the earlier file predates a later re-analysis of that grid; the json and summary.md carry the current value)")
    p1sep = pd.read_csv(P / "pilot-side-by-side/nd_rerun/p1_arm_proportions.csv").set_index("model").cells_complete_separation.to_dict()

    # ------------------------------------------------------------------------------------------------ A1 and A2 rows
    def build(tag, H, scale_labels, is_a1):
        rows, fig12, fig13c = [], [], []
        for m in MODELS:
            for p in PARADIGMS:
                o, f = llm[tag][(m, p)]
                mt = o["metrics"]["primary"]
                assert "split_half" in mt and not mt["undefined"], (m, p)
                r = mt["split_half"]
                assert mt["scale"] == ("standardised" if is_a1 else "raw_difference_forced"), (m, p, mt["scale"])
                h = H[p]
                S_lo, S_hi = r["S_ci"]
                agree, excl = sign_text(r["dbar"], r["dbar_ci"][0], r["dbar_ci"][1], 1)
                outcome = rule_outcome(r["sign_stability"], r["dbar"], r["S"], r["dbar_minus_2S_lower"])
                spread = spread_statement(S_lo, S_hi, h["SH_lo"], h["SH_hi"])
                row = dict(model=m, paradigm=p, paradigm_label=PLABEL[p], scale=scale_labels[p], scale_status="preregistered (A1)" if is_a1 else "post-results (A2, not preregistered)",
                           C=r["C"], validity=o["validity_overall"],
                           llm_mu=r["dbar"], llm_mu_lo=r["dbar_ci"][0], llm_mu_hi=r["dbar_ci"][1],
                           llm_S=r["S"], llm_S_lo=S_lo, llm_S_hi=S_hi, llm_S2_lower_gt0=bool(r["S2_ci"][0] > 0),
                           human_k=h["k"], human_mu=h["mu"], human_mu_lo=h["mu_lo"], human_mu_hi=h["mu_hi"],
                           human_S=h["SH"], human_S_lo=h["SH_lo"], human_S_hi=h["SH_hi"], human_S_interval_includes_0=h["SH_lo"] <= 0,
                           ratio_S_over_SH_NOT_PREREGISTERED=(r["S"] / h["SH"] if h["SH"] > 0 else np.nan),
                           sign_agrees_with_human=bool(agree), llm_mu_ci_excludes_0=bool(excl), sign_stability=r["sign_stability"], sign_agreement_point_share=r["sign_agreement"],
                           dbar_minus_2S_lower=r["dbar_minus_2S_lower"], dbar_plus_2S_upper=r["dbar_plus_2S_upper"],
                           rule_outcome=outcome, spread_vs_human=spread,
                           shares_reportable=bool(r["factor_shares_reportable"]))
                if is_a1:
                    row.update(human_tau_REML=h["tau"], human_tau_lo=h["tau_lo"], human_tau_hi=h["tau_hi"], human_I2=h["I2"], human_dbar_unweighted=h["dbar_unweighted"],
                               human_metric_key=h["human_metric_key"], human_SH_formula_v=h["SH_formula_v"])
                else:
                    row.update(human_tau_REML=np.nan, human_tau_lo=np.nan, human_tau_hi=np.nan, human_I2=np.nan, human_mu_ci_source=h["mu_ci_source"])
                    sg = h["sigma"]
                    if np.isnan(sg):
                        for k in ["mu_sd", "mu_sd_lo", "mu_sd_hi", "S_sd", "S_sd_lo", "S_sd_hi", "human_mu_sd", "human_S_sd", "human_sigma_ML1"]:
                            row[k] = np.nan
                    else:
                        row.update(human_sigma_ML1=sg, mu_sd=r["dbar"] / sg, mu_sd_lo=r["dbar_ci"][0] / sg, mu_sd_hi=r["dbar_ci"][1] / sg,
                                   S_sd=r["S"] / sg, S_sd_lo=S_lo / sg, S_sd_hi=S_hi / sg, human_mu_sd=h["mu"] / sg, human_S_sd=h["SH"] / sg)
                # flags
                row.update(flags_for(o, nd.loc[(m, p)], p1sep[m] if p == "P1" else np.nan, None))
                if is_a1:
                    # sensitivities: same rule on the two sensitivity analyses of the primary metric
                    for stag, nm in ((".f0sens", "f0sens"), (".notopup", "notopup")):
                        if (m, p) in llm[stag]:
                            ro = llm[stag][(m, p)][0]["metrics"]["primary"]["split_half"]
                            row[f"dbar_{nm}"], row[f"S_{nm}"] = ro["dbar"], ro["S"]
                            row[f"rule_{nm}"] = rule_outcome(ro["sign_stability"], ro["dbar"], ro["S"], ro["dbar_minus_2S_lower"])
                            row[f"rule_changes_{nm}"] = row[f"rule_{nm}"] != outcome
                            row[f"spread_vs_human_{nm}"] = spread_statement(ro["S_ci"][0], ro["S_ci"][1], h["SH_lo"], h["SH_hi"])
                        else:
                            row[f"dbar_{nm}"] = row[f"S_{nm}"] = np.nan
                            row[f"rule_{nm}"] = "NA (grid has no such analysis)"
                            row[f"rule_changes_{nm}"] = np.nan
                            row[f"spread_vs_human_{nm}"] = "NA"
                rows.append(row)

                # figure 12 inputs: corrected SS_t per term
                tot = sum(r["terms"].values())
                assert abs(tot - r["C"] * r["S2_untruncated"]) < 1e-8 * max(1, abs(tot)), (m, p, tot, r["C"] * r["S2_untruncated"])
                for t, ss in r["terms"].items():
                    fig12.append(dict(model=m, paradigm=p, scale="A1_preregistered" if is_a1 else "A2_post_results", term=t, term_order=len(t.split(":")), df=r["term_df"][t],
                                      ss_corrected=ss, ss_lo=r["terms_ci"][t][0], ss_hi=r["terms_ci"][t][1], total_ss_corrected=tot, S2_untruncated=r["S2_untruncated"],
                                      S2_lo=r["S2_ci"][0], S2_hi=r["S2_ci"][1], shares_reportable=bool(r["factor_shares_reportable"]),
                                      share=(r["shares"][t] if r["factor_shares_reportable"] and r["shares"] else np.nan),
                                      share_na_reason=("" if r["factor_shares_reportable"] else "lower bound of S^2 not above 0 (A1.5): shares not reported")))
                # figure 13 inputs: effect per perturbation cell
                keys = list(itertools.product(*[range(L) for L in o["levels"]]))
                d, v = np.array(r["d"]), np.array(r["v"])
                assert len(keys) == len(d) == r["C"]
                lo, hi = d - 1.959964 * np.sqrt(v), d + 1.959964 * np.sqrt(v)
                assert abs(np.mean(lo > 0) - r["sign_stability"]) < 1e-12, (m, p)
                for i, k in enumerate(keys):
                    rec = dict(model=m, paradigm=p, scale="A1_preregistered" if is_a1 else "A2_post_results", cell="|".join(map(str, k)))
                    for fac, kk in zip(o["factors"], k):
                        rec[fac] = o["level_names"][fac][kk]
                    for fac in ["W", "F", "T", "O"]:
                        rec.setdefault(fac, "")
                    rec.update(d=d[i], v=v[i], ci_lo=lo[i], ci_hi=hi[i], sign_positive=bool(d[i] > 0), canonical_sign_and_ci_excludes_0=bool(lo[i] > 0),
                               ci_excludes_0_opposite_sign=bool(hi[i] < 0))
                    fig13c.append(rec)
        return pd.DataFrame(rows), pd.DataFrame(fig12), pd.DataFrame(fig13c)

    A1, F12a1, F13a1 = build("", H1, A1_SCALE, True)
    A2, F12a2, F13a2 = build(".rawscale", H2, A2_SCALE, False)

    A1.to_csv(OUT / "table_a1.csv", index=False)
    A2.to_csv(OUT / "table_a2.csv", index=False)
    fig = OUT / "fig_inputs"
    # figure 11: one row per model x paradigm x scale
    cols11 = ["model", "paradigm", "scale", "scale_status", "llm_mu", "llm_mu_lo", "llm_mu_hi", "llm_S", "llm_S_lo", "llm_S_hi", "human_mu", "human_mu_lo", "human_mu_hi",
              "human_S", "human_S_lo", "human_S_hi", "human_tau_REML", "human_tau_lo", "human_tau_hi", "rule_outcome", "spread_vs_human", "nd_flag_any", "nd_n_flagged", "nd_C",
              "low_validity_overall", "llm_S2_lower_gt0"]
    f11 = pd.concat([A1[cols11], A2[cols11]], ignore_index=True)
    f11.to_csv(fig / "fig11_forest.csv", index=False)
    pd.concat([F12a1, F12a2], ignore_index=True).to_csv(fig / "fig12_variance_terms.csv", index=False)
    F13 = pd.concat([F13a1, F13a2], ignore_index=True)
    F13.to_csv(fig / "fig13_sign_cells.csv", index=False)
    # per factor level: share of cells with the canonical sign (point) and with canonical sign and CI excluding 0
    lv = []
    for (m, p, sc), g in F13.groupby(["model", "paradigm", "scale"], sort=False):
        for fac in ["W", "F", "T", "O"]:
            if (g[fac].astype(str) == "").all():
                continue
            for level, gg in g.groupby(fac, sort=True):
                lv.append(dict(model=m, paradigm=p, scale=sc, factor=fac, level=level, n_cells=len(gg), share_sign_positive=gg.sign_positive.mean(),
                               share_canonical_sign_ci_excl_0=gg.canonical_sign_and_ci_excludes_0.mean(), share_opposite_sign_ci_excl_0=gg.ci_excludes_0_opposite_sign.mean(),
                               mean_d=gg.d.mean()))
    pd.DataFrame(lv).to_csv(fig / "fig13_sign_factor_levels.csv", index=False)
    log(f"tables: A1 {len(A1)} rows, A2 {len(A2)} rows; fig12 {len(F12a1) + len(F12a2)} term rows; fig13 cells {len(F13)}; fig13 levels {len(lv)}")

    # ------------------------------------------------------------------------------------------------ tex
    def tx(x, d=3):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "NA"
        s = f"{x:.{d}f}"
        return s.replace("-", "$-$")

    def ci(a, b, d=3):
        return f"[{tx(a, d)}, {tx(b, d)}]"

    def flagcodes(r):
        c = []
        if r["nd_flag_any"]:
            c.append(f"ND {r['nd_n_flagged']}/{r['nd_C']}")
        if r["topup_used"]:
            c.append(f"TU {r['topup_rows_replaced']}")
        if r["unfinished_excluded_n"] > 0:
            c.append(f"UF {r['unfinished_excluded_n']}")
        if r["low_validity_overall"]:
            c.append("LV")
        if not r["llm_S2_lower_gt0"]:
            c.append("S0")
        return ", ".join(c) if c else "--"

    SPREAD_SHORT = {"larger": "larger", "smaller": "smaller", "no statement (intervals overlap)": "overlap"}

    def write_tex(df, path, a1):
        L = []
        L.append("% generated by analysis/pilot/side_by_side.py; do not edit by hand")
        L.append("% needs \\usepackage{booktabs,longtable}; wrap in \\begin{landscape} (pdflscape) or use \\scriptsize as set here")
        if a1:
            ncol = 9
            L.append("\\begingroup\\scriptsize\\setlength{\\tabcolsep}{3pt}")
            L.append("\\begin{longtable}{@{}l l l l l l c l l@{}}")
            L.append("\\caption{Many Labs 1 pilot, \\textbf{preregistered analysis (A1)}: each LLM next to the human benchmark. "
                     "$\\bar\\Delta$ = mean of the 16 (P1: 32) cell effects with 95\\% interval; $S$ = finite-cell spread with 95\\% test-inversion interval; "
                     "human $\\mu$ = REML pooled effect over 36 sites; $\\tau$ = REML between-site SD with Q-profile interval; $S^H$ = the same spread estimator over the 36 sites "
                     "(no coverage claim for the human intervals). Effect scale: log odds ratio (P1), Hedges $g$ on the log answer (P2a--d), Hedges $g$ (P3), Hedges $g$ on $\\log(1+x)$ (P4). "
                     "Sign = point sign agrees with the human effect, stability = share of cells with the canonical sign and 95\\% CI excluding 0. "
                     "Rule = pilot-design section 6 (stable / fragile / neither). Spread = larger or smaller than $S^H$ only if the intervals do not overlap (conservative descriptive rule; "
                     "the two spreads arise from different sources: prompt changes versus site and sample differences). "
                     "Flags: ND k/C = cells with pooled SD at most 2 floors (continuous) or a zero count (P1), where standardised $S$ is not interpretable; TU = top-up responses used (A1.9); "
                     "UF = parsed but unfinished responses excluded (A1.10); LV = validity below 0.80; S0 = lower bound of $S^2$ not above 0 (shares not reported).}\\label{tab:pilot-a1}\\\\")
            hdr = "Model & $\\bar\\Delta$ [95\\% CI] & $S$ [95\\% TI] & Human $\\mu$ / $\\tau$ / $S^H$ & Sign & Stab. & Rule & Spread vs $S^H$ & Flags \\\\"
        else:
            ncol = 11
            L.append("\\begingroup\\scriptsize\\setlength{\\tabcolsep}{3pt}")
            L.append("\\begin{longtable}{@{}l l l r r l c l l l l@{}}")
            L.append("\\caption{Many Labs 1 pilot, \\textbf{post-results analysis (A2, not preregistered)}: raw-scale effects. "
                     "P1: risk difference of choosing the sure option; P2--P4: mean difference on the metric scale (log answer, rating points, $\\log(1+x)$), "
                     "also in units of the fixed ML1 pooled within-site SD of that paradigm (a linear rescaling; none for P1). "
                     "$S$ and $S^H$ are the same finite-cell spread estimator on the raw scale; human values are over the 36 ML1 sites on the same scale. "
                     "The rule text of section 6 is applied mechanically to these results and was not preregistered for them. "
                     "The preregistered analysis is Table~\\ref{tab:pilot-a1}. Flag codes as in that table (ND is defined on the A1 cells).}\\label{tab:pilot-a2}\\\\")
            hdr = ("Model & $\\bar\\Delta$ [95\\% CI] & $S$ [95\\% TI] & $\\bar\\Delta/\\sigma_{ML1}$ & $S/\\sigma_{ML1}$ & Human $\\mu$ [CI] / $S^H$ [TI] & Sign / stab. & Rule & Spread vs $S^H$ & Flags & \\\\")
            hdr = hdr.replace(" & \\\\", " \\\\")
            # CRP-S05: the human column repeated the values of each effect's header row and pushed the table past the
            # landscape page in sn-jnl; the header row keeps them.
            hdr = hdr.replace(" & Human $\\mu$ [CI] / $S^H$ [TI]", "")
            ncol = 9
            L[-2] = "\\begin{longtable}{@{}l l l r r l l l l@{}}"
        L.append("\\toprule")
        L.append(hdr)
        L.append("\\midrule")
        L.append("\\endfirsthead")
        L.append("\\toprule")
        L.append(hdr)
        L.append("\\midrule")
        L.append("\\endhead")
        L.append("\\bottomrule")
        L.append("\\endfoot")
        for p in PARADIGMS:
            sub = df[df.paradigm == p]
            r0 = sub.iloc[0]
            if a1:
                head = (f"Human ML1 benchmark, {tx(r0.human_k, 0)} sites: $\\mu$ = {tx(r0.human_mu)} {ci(r0.human_mu_lo, r0.human_mu_hi)}; "
                        f"$\\tau$ = {tx(r0.human_tau_REML)} {ci(r0.human_tau_lo, r0.human_tau_hi)}; $S^H$ = {tx(r0.human_S)} {ci(r0.human_S_lo, r0.human_S_hi)}")
            else:
                head = (f"Human ML1 benchmark, {tx(r0.human_k, 0)} sites: $\\mu$ = {tx(r0.human_mu)} {ci(r0.human_mu_lo, r0.human_mu_hi)}; "
                        f"$S^H$ = {tx(r0.human_S)} {ci(r0.human_S_lo, r0.human_S_hi)}"
                        + ("" if np.isnan(r0.human_mu_sd) else f"; in $\\sigma_{{ML1}}$ = {tx(r0.human_sigma_ML1)}: $\\mu$ = {tx(r0.human_mu_sd)}, $S^H$ = {tx(r0.human_S_sd)}"))
            L.append("\\midrule" if p != "P1" else "")
            # Two header rows (CRP-S05): one long unbreakable row set the table width beyond the landscape page in sn-jnl.
            L.append(f"\\multicolumn{{{ncol}}}{{@{{}}l}}{{\\textbf{{{PLABEL[p]}}} ({r0.scale}).}} \\\\")
            L.append(f"\\multicolumn{{{ncol}}}{{@{{}}l}}{{{head}}} \\\\")
            for _, r in sub.iterrows():
                if a1:
                    hum = f"{tx(r.human_mu, 2)} / {tx(r.human_tau_REML, 2)} / {tx(r.human_S, 2)}"
                    L.append(f"{r.model} & {tx(r.llm_mu)} {ci(r.llm_mu_lo, r.llm_mu_hi)} & {tx(r.llm_S)} {ci(r.llm_S_lo, r.llm_S_hi)} & {hum} & "
                             f"{'Y' if r.sign_agrees_with_human else 'N'} & {tx(r.sign_stability, 2)} & {r.rule_outcome} & {SPREAD_SHORT[r.spread_vs_human]} & {flagcodes(r)} \\\\")
                else:
                    L.append(f"{r.model} & {tx(r.llm_mu)} {ci(r.llm_mu_lo, r.llm_mu_hi)} & {tx(r.llm_S)} {ci(r.llm_S_lo, r.llm_S_hi)} & {tx(r.mu_sd, 2)} & {tx(r.S_sd, 2)} & "
                             f"{'Y' if r.sign_agrees_with_human else 'N'} / {tx(r.sign_stability, 2)} & {r.rule_outcome} & {SPREAD_SHORT[r.spread_vs_human]} & {flagcodes(r)} \\\\")
        L.append("\\end{longtable}")
        L.append("\\endgroup")
        path.write_text("\n".join(x for x in L if x != "") + "\n", encoding="utf8")

    write_tex(A1, ROOT / "paper/tables/pilot_a1.tex", True)
    write_tex(A2, ROOT / "paper/tables/pilot_a2.tex", False)

    # ------------------------------------------------------------------------------------------------ summary.md
    write_summary(A1, A2, H1, H2, llm, F12a1, F13a1, in_hashes)

    cfg = dict(script="analysis/pilot/side_by_side.py", script_sha256=sha(Path(__file__)), python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__,
               inputs_sha256=in_hashes, analysis_json_sha256=json_hashes, outputs=sorted(str(f.relative_to(ROOT)).replace("\\", "/") for f in OUT.rglob("*") if f.is_file()),
               rng_seed_human_p1_interval=20261016, ci_z=1.959964, rule_labels=dict(stable="sign stability >= 0.9 and dbar_lo - 2 S_hi > 0",
                                                                                   fragile="sign stability < 0.6 or dbar-2S < 0 < dbar+2S (point estimates)"),
               low_validity_threshold=LOW_VALIDITY)
    (OUT / "config.json").write_text(json.dumps(cfg, indent=1, default=str), encoding="utf8")
    (OUT / "log.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")


def write_summary(A1, A2, H1, H2, llm, F12, F13, in_hashes):
    L = []
    w = L.append
    w("# Pilot side-by-side tables (RQ5): what each column means\n")
    w("Generated by `analysis/pilot/side_by_side.py` from existing outputs only (no model run). Source facts: the earlier run directories listed in `config.json` (sha256). "
      "Evidence level E4 (computed here from stored outputs). Nothing below interprets beyond the preregistered rules of `research/prereg/pilot-design.md` section 5-6 and Amendment A1.\n")
    w("## 1. Status of the two tables")
    w("- `table_a1.csv`, `paper/tables/pilot_a1.tex`: **preregistered (A1)** analysis. This is the primary analysis (A2.1 says A2 is reported next to it and is not called primary).")
    w("- `table_a2.csv`, `paper/tables/pilot_a2.tex`: **post-results (A2, not preregistered)**. Chosen after the first analysis was seen (A2 timeline). Never presented as primary.\n")
    w("## 2. Denominators")
    w("- 6 models x 7 paradigms = 42 model x paradigm grids; each A1/A2 grid is complete (no undefined cell). Cells per grid: C = 16 (P2a-d, P3, P4) or 32 (P1, with option order O); n = 50 sampled responses per condition per cell (design), fewer after invalid responses are dropped.")
    w("- Human side: 36 ML1 sites per paradigm (N: " + ", ".join(f"{p} {H1[p]['N']:,}" for p in PARADIGMS) + ").")
    w("- Validity (column `validity`): share of sampled responses that parse AND finished (A1.10), over all sampled responses of the grid.\n")
    w("## 3. Columns")
    w("| column (csv) | meaning |")
    w("|---|---|")
    w("| llm_mu, llm_mu_lo, llm_mu_hi | Delta-bar: unweighted mean of the C cell effects, with dbar +- 1.96 sqrt(sum v)/C (A1.4) |")
    w("| llm_S, llm_S_lo, llm_S_hi | S: finite-cell spread (square root of the bias-corrected moment S^2, truncated at 0) with the 95 percent test-inversion interval (A1.4). Called tau in the brief; it is not a random-effects tau |")
    w("| human_mu (+CI) | A1: metafor REML pooled effect over 36 sites (`metafor_results.json`; P2 uses the `sens_log` rows = g on log(answer), the metric the LLM side uses). A2: unweighted mean site effect on the raw scale with its interval (`human_sd.csv`; P1 interval recomputed here, see log) |")
    w("| human_tau_REML (+Q-profile CI) | A1 only: metafor REML between-site SD. Not available on the raw scale (metafor was run only on the A1 scales): NA in table A2 |")
    w("| human_S (+TI) | S^H: the A1 spread estimator over the 36 sites (`human_spread_a1.fixed.txt`, A2.4-corrected; A2: `human_sd.csv` / `rawscale.csv`). This, not tau, is the like-for-like human counterpart of S (A1.8). No coverage claim for the human intervals (A1.8) |")
    w("| sign_agrees_with_human | point sign of Delta-bar equals the sign of the human effect (positive for every paradigm); `llm_mu_ci_excludes_0` says whether the 95 percent interval excludes 0 |")
    w("| sign_stability | share of cells with the canonical (positive) sign and a 95 percent CI excluding 0 (section 5 secondary outcome) |")
    w("| rule_outcome | section 6 labels, see below |")
    w("| spread_vs_human | 'larger' or 'smaller' only when the S interval and the S^H interval do not overlap (section 6); otherwise 'no statement (intervals overlap)' |")
    w("| ratio_S_over_SH_NOT_PREREGISTERED | csv only. Section 5 says: \"No ratio, no difference test\". Kept out of the tex tables; where S^H = 0 it is NA. Do not cite without a deviation note |")
    w("| nd_* | near-deterministic flag, from `diagnose_near_deterministic.py` (post-results diagnosis): cells with pooled SD at most 2 x the A1 floor (continuous) or a zero count (P1); `nd_share_ss_flagged` = share of the between-cell sum of squares from flagged cells; `nd_n_at_floor` = cells at or below the floor |")
    w("| topup_rows_replaced | A1.9 responses replaced by the 512-token regeneration (analysis json `topup_rows_replaced`) |")
    w("| unfinished_excluded_n | parsed but unfinished responses excluded as invalid (A1.10; json `valid_by_parser_but_unfinished`) |")
    w("| low_validity_overall, n_cells_validity_lt80 | grid validity below 0.80; number of cells below 0.80 (section 5: such a cell is flagged) |")
    w("| llm_S2_lower_gt0, shares_reportable | lower bound of the S^2 interval above 0; factor shares are reported only then (A1.5) |")
    w("| *_f0sens, *_notopup | the same rule on the two A1.10 sensitivity analyses (parsed-but-unfinished F0 answers counted valid; no top-up). NA where the grid has no such analysis (no-top-up exists only for olmo2-1b-instruct and was run only there) |")
    w("| A2 only: mu_sd, S_sd (+ intervals) | Delta-bar and S divided by the fixed ML1 pooled within-site SD of the paradigm (`human_sd.csv` sd_pooled: " + ", ".join(f"{p} {H2[p]['sigma']:.3f}" for p in PARADIGMS if p != "P1") + "); NA for P1 (a proportion difference) |\n")
    w("## 4. Preregistered interpretation rules (quoted) and how they were applied")
    w("- Stable: \"sign stability >= 0.9 and the 95 percent bootstrap interval of Delta-bar - 2S (a conservative lower range of cell effects) stays on the canonical side of zero\" (section 6; A1.4 replaces the bootstrap by Delta-bar_lo - 2 S_hi, \"conservative, combined from separate bounds, not a joint interval\"). Applied as sign stability >= 0.9 and `dbar_minus_2S_lower` > 0.")
    w("- Fragile: \"sign stability < 0.6, or Delta-bar - 2S and Delta-bar + 2S lie on opposite sides of zero\". Applied to the point estimates (literal reading).")
    w("- Neither label: the rules name no third class; rows that are neither stable nor fragile are labelled `neither`.")
    w("- Spread: \"'Larger' or 'smaller' between LLM and human spreads is stated only when the intervals do not overlap, labelled as a conservative descriptive rule, not a significance test.\" Any such sentence must name the two sources (prompt perturbation versus site and sample differences) in the same sentence.")
    w("- \"The human-tau comparison is described only as placing LLM prompt-spread on the scale of human between-site spread; no claim that one system is 'more variable' in a general sense.\"")
    w("- Factor shares: descriptive allocations, reported only when the lower bound of S^2 exceeds 0; not causal contributions (section 6, A1.5).")
    w("- A1.5: with n = 50 and 16 cells the pilot cannot distinguish S near 0.1 from 0.\n")

    def counts(df):
        return df.groupby("paradigm", sort=False).agg(n=("model", "size"), stable=("rule_outcome", lambda s: (s == "stable").sum()), fragile=("rule_outcome", lambda s: (s == "fragile").sum()),
                                                      neither=("rule_outcome", lambda s: (s == "neither").sum()), sign_agree=("sign_agrees_with_human", "sum"),
                                                      sign_agree_ci=("sign_agrees_with_human", lambda s: 0), larger=("spread_vs_human", lambda s: (s == "larger").sum()),
                                                      smaller=("spread_vs_human", lambda s: (s == "smaller").sum()))
    w("## 5. Outcome of the preregistered rules per paradigm (A1; counts over the 6 models)")
    w("| paradigm | stable | fragile | neither | sign agrees (point) | sign agrees and CI excludes 0 | spread larger than S^H | spread smaller | intervals overlap |")
    w("|---|---|---|---|---|---|---|---|---|")
    headlines = {}
    for p in PARADIGMS:
        s = A1[A1.paradigm == p]
        n_se = int((s.sign_agrees_with_human & s.llm_mu_ci_excludes_0).sum())
        lg, sm = int((s.spread_vs_human == "larger").sum()), int((s.spread_vs_human == "smaller").sum())
        w(f"| {p} | {(s.rule_outcome == 'stable').sum()} | {(s.rule_outcome == 'fragile').sum()} | {(s.rule_outcome == 'neither').sum()} | {int(s.sign_agrees_with_human.sum())}/6 | {n_se}/6 | {lg} | {sm} | {6 - lg - sm} |")
        headlines[p] = (int((s.rule_outcome == 'stable').sum()), int((s.rule_outcome == 'fragile').sum()), int((s.rule_outcome == 'neither').sum()), n_se, lg, sm)
    w("")
    w("Same count on the post-results raw scale (A2, not preregistered; the rule text applied mechanically):\n")
    w("| paradigm | stable | fragile | neither | sign agrees and CI excludes 0 | spread larger | spread smaller |")
    w("|---|---|---|---|---|---|---|")
    for p in PARADIGMS:
        s = A2[A2.paradigm == p]
        w(f"| {p} | {(s.rule_outcome == 'stable').sum()} | {(s.rule_outcome == 'fragile').sum()} | {(s.rule_outcome == 'neither').sum()} | {int((s.sign_agrees_with_human & s.llm_mu_ci_excludes_0).sum())}/6 | "
          f"{int((s.spread_vs_human == 'larger').sum())} | {int((s.spread_vs_human == 'smaller').sum())} |")
    w("")
    w("## 6. Rule outcome per grid (A1, preregistered)")
    w("| model | paradigm | Delta-bar [CI] | S [TI] | sign stab. | rule | spread vs S^H (human S^H [TI]) | A2 rule (post-results) |")
    w("|---|---|---|---|---|---|---|---|")
    for (_, r), (_, r2) in zip(A1.iterrows(), A2.iterrows()):
        w(f"| {r.model} | {r.paradigm} | {r.llm_mu:.3f} [{r.llm_mu_lo:.3f}, {r.llm_mu_hi:.3f}] | {r.llm_S:.3f} [{r.llm_S_lo:.3f}, {r.llm_S_hi:.3f}] | {r.sign_stability:.2f} | {r.rule_outcome} | "
          f"{r.spread_vs_human} ({r.human_S:.3f} [{r.human_S_lo:.3f}, {r.human_S_hi:.3f}]) | {r2.rule_outcome} |")
    w("")
    w("## 7. Flags and why")
    fl = A1[A1.nd_flag_any]
    w(f"**Near-deterministic (ND), A1 cells.** {len(fl)} of 42 grids have at least one flagged cell (continuous: pooled SD at most 2 x floor, floor 0.2 on log scales and 0.289 rating points for P3; P1: a cell with a zero count and the 0.5 correction). "
      "Standardised S (and for P1 the log OR) is not interpretable in such grids (A2.2; `research/reports/statistician/2026-10-16-pilot-near-deterministic-cells.md`: g is raw difference / floor; A1 intervals fail in simulation there, coverage 0.65 to 0.89). "
      "The A2 table is the post-results companion. Flagged grids (n flagged / C; share of the between-cell sum of squares from flagged cells):\n")
    w("| model | paradigm | flagged / C | cells at floor | share SS flagged | P1 complete-separation cells (per model) |")
    w("|---|---|---|---|---|---|")
    for _, r in fl.iterrows():
        w(f"| {r.model} | {r.paradigm} | {r.nd_n_flagged}/{r.nd_C} | {'' if pd.isna(r.nd_n_at_floor) else int(r.nd_n_at_floor)} | {r.nd_share_ss_flagged:.2f} | {'' if pd.isna(r.p1_complete_separation_cells) else int(r.p1_complete_separation_cells)} |")
    w("")
    nf = A1[~A1.nd_flag_any]
    w("Grids with no flagged cell: " + ", ".join(f"{r.model} {r.paradigm}" for _, r in nf.iterrows()) + ".\n")
    tu = A1[A1.topup_used]
    w(f"**Top-up used (A1.9).** {len(tu)} grids: " + "; ".join(f"{r.model} {r.paradigm} ({r.topup_rows_replaced} responses replaced)" for _, r in tu.iterrows()) + ". "
      "A1.9/A1.10 count 27 top-up cells (all olmo2-1b-instruct, F1); `runs/pilot-topup/trigger.txt` lists 187 responses to regenerate. Rule outcome without the top-up differs from the primary in: "
      + (", ".join(f"{r.paradigm}" for _, r in tu.iterrows() if r.rule_changes_notopup is True or r.rule_changes_notopup == True) or "no grid") + ".\n")
    uf = A1[A1.unfinished_excluded_n > 0]
    w(f"**Unfinished responses excluded (A1.10).** {len(uf)} of 42 grids exclude at least one parsed-but-unfinished response; the largest shares of the sampled responses: "
      + ", ".join(f"{r.model} {r.paradigm} {100 * r.unfinished_excluded_share_of_sampled:.1f}%" for _, r in uf.sort_values('unfinished_excluded_share_of_sampled', ascending=False).head(6).iterrows())
      + ". Rule outcome changes under the F0 sensitivity (parsed-but-unfinished F0 counted valid) in: "
      + (", ".join(f"{r.model} {r.paradigm} ({r.rule_outcome} -> {r.rule_f0sens})" for _, r in A1[A1.rule_changes_f0sens == True].iterrows()) or "no grid") + ". "
      "The Codex open check (A1.10: blinded review of whether unfinished F0 answers contain the complete answer) was not done; unknown whether F0 should be primary.\n")
    lv = A1[A1.low_validity_overall]
    w(f"**Validity below 0.80 over the grid.** {len(lv)} grids: " + (", ".join(f"{r.model} {r.paradigm} ({r.validity:.3f})" for _, r in lv.iterrows()) or "none") + ". "
      f"Grids with at least one cell below 0.80 validity: {int((A1.n_cells_validity_lt80 > 0).sum())} of 42 (n_cells_validity_lt80 gives the count per grid).\n")
    s0 = A1[~A1.llm_S2_lower_gt0]
    w(f"**Lower bound of S^2 not above 0 (S0).** {len(s0)} of 42 A1 grids ({int((~A2.llm_S2_lower_gt0).sum())} of 42 under A2): no factor shares are reported for them (A1.5).\n")
    pos1 = [p for p in PARADIGMS if H1[p]["SH_lo"] > 0]
    pos2 = [p for p in PARADIGMS if H2[p]["SH_lo"] > 0]
    w("**Where 'smaller' can be stated at all.** The human S^H interval has a lower bound above 0 only for " + ", ".join(pos1) + " (A1) and " + ", ".join(pos2) + " (A2); "
      "for every other paradigm the human interval starts at 0, so under the non-overlap rule an LLM spread cannot be called smaller. The human intervals carry no coverage claim (A1.8).\n")
    stable = A1[A1.rule_outcome == "stable"]
    w("**Stable grids under A1.** " + (", ".join(f"{r.model} {r.paradigm} (ND flag {r.nd_n_flagged}/{r.nd_C})" for _, r in stable.iterrows()) or "none")
      + ". A stable label on a grid with ND-flagged cells rests on the floored or continuity-corrected cell effects (A2.2).\n")
    w("## 8. Figure inputs (`fig_inputs/`)")
    w("- `fig11_forest.csv`: one row per model x paradigm x scale (A1_preregistered, A2_post_results; the `scale_status` column says which): LLM mu and S with intervals, human mu, tau (A1 only), S^H with intervals, rule outcome, flags. Draw A1 as the main panel; A2 as a separate, labelled panel.")
    w("- `fig12_variance_terms.csv`: **available.** The analysis jsons store, for every grid and both scales, the bias-corrected sum of squares SS_t of every term (W, F, T, [O], and all interactions) with its 95 percent interval, df, the total (= C x S^2 untruncated; checked), and the share where reportable (A1.5: only if the S^2 lower bound is above 0; NA with reason otherwise). "
      "These are corrected sums of squares of an enumerated set of cells, not estimated variance components (section 5: \"no variance components are estimated\"); shares are descriptive allocations; a corrected SS (and so a share) can be slightly negative because the sampling-variance correction is subtracted (kept as computed, not truncated). "
      f"Shares are reportable in {int(F12.drop_duplicates(['model', 'paradigm']).shares_reportable.sum())} of 42 A1 grids.")
    w("- `fig13_sign_cells.csv` (one row per perturbation cell: factor levels, d, v, 95% Wald limits, sign, canonical-sign-and-CI-excludes-0 indicator; their mean reproduces the stored sign stability, checked) and `fig13_sign_factor_levels.csv` (per factor level: share of cells with positive sign, share with canonical sign and CI excluding 0, share with the opposite sign and CI excluding 0). **Available** for A1 and A2.")
    w("- Nothing needed for figures 12-13 is missing. Caveats: for ND-flagged grids the A1 cell effects are g on a floored SD (A2.2); the 'W' levels W0-W3 are the frozen wordings, 'T' = 0.7 and 1.0, 'F' = F0/F1, 'O' = option order for P1 only.\n")
    w("## 9. Missing (NA) and why")
    w("- Human tau (REML) on the A2 raw scale: NA. metafor was run only on the A1 scales (`metafor_results.json`); only S^H exists on the raw scale. A new metafor run would be needed.")
    w("- Human mu and tau for A1 P2 use the `sens_log` rows (g on log answer), because the benchmark's `primary` P2 row is raw g, which the A1.2 LLM metric does not use.")
    w("- Human P1 raw-scale (risk difference) interval for the pooled effect: not in any earlier output; recomputed here with `estimators.estimate2` ('diff') on `data/processed/ml1/P1.csv`, seed 20261016; the point value reproduces `rawscale.csv` human_raw_dbar. Only this interval is new; all other human numbers are read.")
    w("- SD-unit columns are NA for P1 (risk difference).")
    w("- Ratio S / S^H is NA where S^H = 0 (P3) and is not preregistered.")
    w("- `*_notopup` columns are NA for the 35 grids with no top-up (the no-top-up analysis was run only for olmo2-1b-instruct).")
    w("- Near-deterministic flags for olmo2-1b-instruct were not in the earlier `near-deterministic/summary.csv` (that run predates its analysis); they come from re-running `diagnose_near_deterministic.py` into `runs/pilot-side-by-side/nd_rerun/` (30 earlier grids reproduced; see log).")
    w("- Cell-level validity flag: only the count of cells below 0.80 is carried; the cell ids are in the json (`cells_below_80pct_validity`).\n")
    w("## 10. Deviations from the brief")
    w("- The brief asks for a ratio of LLM tau to human tau; section 5 of the preregistration says \"No ratio, no difference test\". The ratio is in the csv only, under a column name that says NOT preregistered, and is absent from the tex tables.")
    w("- The brief's inputs list the summary tables; the full-precision source is the per-grid analysis json (`runs/pilot/<model>/analysis_<paradigm>*.json`), which the summaries are rendered from. The script asserts that every printed number in the four summaries is reproduced from the json. Figure 12-13 inputs exist only in the json.")
    (OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf8")
    log("summary.md written")


if __name__ == "__main__":
    main()
