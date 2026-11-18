"""Design diagnostics for the RQ2-RQ4 full-text estimates (revision-list item B8). CPU only; no extraction, no new coding.

    .venv/Scripts/python.exe -I analysis/fulltext/rq234_design_diagnostics.py [--src runs/rq234-interim] [--out runs/rq234-design-diagnostics]

Rebuilds the survey design exactly as analysis/fulltext/rq234_analysis.py does (imported, not re-implemented: build_units, Design,
feature_table, estimate_all), but from the extraction files frozen in <src>/input-snapshot, after checking that the snapshot, the
sample, the reading list and the records are byte-identical to the hashes recorded in <src>/config.json. Then reports per coder:
  * respondents (analysed records with a full text and a usable extraction): n, weights w_i = N_g / r_g, min / max / ratio, Kish
    n_eff = (sum w)^2 / sum w^2, design effect n / n_eff;
  * eligible studies (the domain of the prevalences): the same quantities over the eligible respondents;
  * strata, estimation groups (after the v0.12.1 merge), groups with >= 2 / exactly 1 / 0 respondents, degrees of freedom of the
    t interval (sum of r_g - 1), the t quantile;
  * for the headline prevalences: unweighted k/n beside the weighted share and its Wald (truncated at 0 and 1) and logit intervals,
    plus the Kish n_eff of the studies in that domain.
The recomputed weighted shares and intervals are asserted equal to <src>/rq4.csv (rounding of that file).
Outputs: design_summary.csv, headline_prevalences.csv, weights_by_group.csv, summary.md, config.json, env.json, log.txt.
"""
import argparse
import copy
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rq234_analysis as R  # noqa: E402

HEADLINE = [("Wording perturbation", "rq4|perturbation|wording"), ("Any of the judged perturbation types", "rq4|robustness_tested|yes"),
            ("f2 temperature stated", "rq4|f2|yes"), ("f11 preregistration cited", "rq4|f11|yes"), ("f12 code or data link", "rq4|f12|yes")]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def kish(w):
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum()) if len(w) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="runs/rq234-interim")
    ap.add_argument("--out", default="runs/rq234-design-diagnostics")
    a = ap.parse_args()
    src, out = ROOT / a.src, ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    LOG = []

    def log(*x):
        s = " ".join(str(i) for i in x)
        LOG.append(s)
        print(s, flush=True)

    cfg = json.loads((src / "config.json").read_text(encoding="utf8"))
    snap = src / "input-snapshot"
    # --- consistency of inputs with the interim run
    checked = 0
    for k, h in cfg["input_sha256"].items():
        if k.startswith("extraction/"):
            p = snap / k.split("/", 1)[1]
            assert p.exists() and sha(p) == h, ("snapshot differs", k)
        elif k in ("data/processed/fulltext-sample/sample.jsonl", "data/processed/fulltext/reading-list.jsonl", "data/processed/records.jsonl"):
            assert sha(ROOT / k) == h, ("input changed since the interim run", k)
        else:
            continue
        checked += 1
    log(f"inputs verified against {a.src}/config.json: {checked} files identical (extraction snapshot, sample, reading list, records)")
    sample = R.jl(ROOT / "data/processed/fulltext-sample/sample.jsonl")
    reading = {r["order"]: r for r in R.jl(ROOT / "data/processed/fulltext/reading-list.jsonl")}
    ids = {s["id"] for s in sample}
    records = {r["id"]: r for r in R.jl(ROOT / "data/processed/records.jsonl") if r["id"] in ids}
    ext = {c: {} for c in R.CODERS}
    for c in R.CODERS:
        for f in sorted((snap / c).glob("[0-9][0-9][0-9].json")):
            ext[c][int(f.stem)] = json.loads(f.read_text(encoding="utf-8"))
    units = R.build_units(sample, reading, records, ext)
    merge_log = []
    des = {c: R.Design(units, c, merge_log) for c in R.CODERS}
    feats, est = {}, {}
    names = list(dict.fromkeys(R.FIXED + sorted({n for c in R.CODERS for on, _ in R.feature_table(units, c, snap)[0].values() for n in on})))
    for c in R.CODERS:
        feats[c], _ = R.feature_table(units, c, snap)
        est[c] = R.estimate_all(units, c, des[c], feats[c], names)

    rows, grp_rows = [], []
    for c in R.CODERS:
        d = des[c]
        w_resp = d.w
        elig = np.array([u["order"] in feats[c] for u in d.resp])
        w_el = w_resp[elig]
        tq = float(stats.t.ppf(0.975, max(d.df, 1)))
        gids = d.gids
        r_by = {g: d.rg[g] for g in gids}
        rows.append(dict(coder=c, n_analysed=len(units), n_full_text=sum(u["ft"] for u in units),
                         n_respondents=len(w_resp), respondents_w_min=float(w_resp.min()), respondents_w_max=float(w_resp.max()),
                         respondents_w_ratio=float(w_resp.max() / w_resp.min()), respondents_kish_neff=kish(w_resp), respondents_deff=len(w_resp) / kish(w_resp),
                         n_eligible=int(elig.sum()), eligible_w_min=float(w_el.min()), eligible_w_max=float(w_el.max()),
                         eligible_w_ratio=float(w_el.max() / w_el.min()), eligible_kish_neff=kish(w_el), eligible_deff=len(w_el) / kish(w_el),
                         n_strata=len(d.Nh), n_estimation_groups=len(gids), groups_ge2_respondents=sum(r_by[g] >= 2 for g in gids),
                         groups_1_respondent=len(d.n_var_dropped), groups_0_respondents=len(d.n_no_resp), df=d.df, t_quantile_975=tq,
                         frame_N=d.Ntot, frame_N_covered=d.Ntot_est, merges_applied=sum(1 for m in merge_log if m.get("coder") == c) if merge_log and "coder" in merge_log[0] else None))
        for g in gids:
            m = d.gi == g
            grp_rows.append(dict(coder=c, group=g, N_g=d.Ng[g], n_analysed_g=d.ag[g], r_g=d.rg[g], weight=(d.Ng[g] / d.rg[g]) if d.rg[g] else None,
                                 n_eligible_g=int((m & elig).sum()), strata="; ".join(s for s in d.grp if d.grp[s] == g)))
        log(f"{c}: respondents {len(w_resp)} (w {w_resp.min():.2f}-{w_resp.max():.2f}, Kish n_eff {kish(w_resp):.1f}); eligible {int(elig.sum())} "
            f"(w {w_el.min():.2f}-{w_el.max():.2f}, Kish n_eff {kish(w_el):.1f}); strata {len(d.Nh)}, groups {len(gids)}, df {d.df}, t {tq:.3f}")

    # --- headline prevalences
    with open(src / "rq4.csv", encoding="utf8", newline="") as fh:
        ref = {r["feature"]: r for r in csv.DictReader(fh)}
    hl = []
    for label, key in HEADLINE:
        for c in R.CODERS:
            e = est[c][key]
            x, y = e["_x"], e["_y"]
            dom_w = des[c].w[x > 0]
            r0 = ref[key]
            for fld, mine in (("est_pct", 100 * e["est"]), ("lo_pct", 100 * e["lo"]), ("hi_pct", 100 * e["hi"])):
                assert abs(float(r0[f"{c}_{fld}"]) - mine) < 0.006, (key, c, fld, r0[f"{c}_{fld}"], mine)
            k, n = int(y.sum()), int(x.sum())
            hl.append(dict(label=label, key=key, coder=c, k=k, n=n, unweighted_pct=100 * k / n, weighted_pct=100 * e["est"], se_pct=100 * e["se"],
                           wald_lo_pct=100 * e["lo"], wald_hi_pct=100 * e["hi"], logit_lo_pct=100 * e["lo_logit"] if e["lo_logit"] == e["lo_logit"] else None,
                           logit_hi_pct=100 * e["hi_logit"] if e["hi_logit"] == e["hi_logit"] else None, df=des[c].df,
                           domain_w_min=float(dom_w.min()), domain_w_max=float(dom_w.max()), domain_kish_neff=kish(dom_w),
                           weighted_minus_unweighted_pp=100 * e["est"] - 100 * k / n))
            log(f"{c} {label}: k/n {k}/{n} = {100 * k / n:.1f}%  weighted {100 * e['est']:.1f}% (Wald {100 * e['lo']:.1f} to {100 * e['hi']:.1f}; logit "
                f"{100 * e['lo_logit']:.1f} to {100 * e['hi_logit']:.1f}) df {des[c].df}; domain Kish n_eff {kish(dom_w):.1f}")
    log("recomputed weighted shares and Wald intervals equal runs/rq234-interim/rq4.csv (assert, tolerance 0.006 percentage points)")

    # --- venue sensitivity (B8): response propensity by venue class, then rescaled within each estimation group
    #     w_i = (N_g / a_g) / p_v, p_v = respondents / analysed in venue class v over all groups; then w_i *= N_g / sum_g w.
    #     Keeps every group total at N_g (as the primary weights do) and shifts weight towards the venue classes with
    #     lower response. A sensitivity, not a replacement for the primary weights.
    VCLASS = {"article": "journal", "book-chapter": "journal", "conference-paper": "conference"}
    vcl = {u["order"]: VCLASS.get(u["vtype"], "preprint/other") for u in units}
    ven = []
    for c in R.CODERS:
        d = des[c]
        a_v, r_v = {}, {}
        for u in units:
            v = vcl[u["order"]]
            a_v[v] = a_v.get(v, 0) + 1
            r_v[v] = r_v.get(v, 0) + int(u[c]["resp"])
        p_v = {v: r_v[v] / a_v[v] for v in a_v}
        raw = np.array([d.Ng[g] / d.ag[g] / p_v[vcl[u["order"]]] for u, g in zip(d.resp, d.gi)])
        w2 = raw.copy()
        for g in d.gids:
            m = d.gi == g
            if m.any():
                w2[m] *= d.Ng[g] / raw[m].sum()
        d2 = copy.copy(d)
        d2.w = w2
        log(f"{c} venue response: " + ", ".join(f"{v} {r_v[v]}/{a_v[v]}" for v in sorted(a_v)) + f"; Kish n_eff {kish(w2):.1f}")
        for label, key in HEADLINE:
            e = est[c][key]
            e2 = d2.ratio(e["_x"], e["_y"])
            ven.append(dict(label=label, key=key, coder=c, primary_pct=100 * e["est"], primary_lo_pct=100 * e["lo"], primary_hi_pct=100 * e["hi"],
                            venue_pct=100 * e2["est"], venue_lo_pct=100 * e2["lo"], venue_hi_pct=100 * e2["hi"],
                            change_pp=100 * (e2["est"] - e["est"]), kish_neff_venue=kish(w2)))
            log(f"{c} {label}: primary {100 * e['est']:.1f}% -> venue-adjusted {100 * e2['est']:.1f}% ({100 * e2['lo']:.1f} to {100 * e2['hi']:.1f})")

    def wcsv(path, rows_):
        keys = list(rows_[0].keys())
        with open(path, "w", encoding="utf8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows_)

    wcsv(out / "design_summary.csv", rows)
    wcsv(out / "headline_prevalences.csv", hl)
    wcsv(out / "weights_by_group.csv", grp_rows)
    wcsv(out / "venue_sensitivity.csv", ven)
    md = ["# Design diagnostics of the interim full-text estimates (B8)\n",
          f"Source run `{a.src}` ({sum(u['ft'] for u in units)} full texts); script `analysis/fulltext/rq234_design_diagnostics.py`; weights w = N_g / r_g per respondent, N_g the frame size of the "
          "estimation group, r_g its respondents (v0.12.1 merge applied). Kish n_eff = (sum w)^2 / sum w^2. Evidence level E4.\n",
          "| coder | respondents | weights min-max (ratio) | Kish n_eff | eligible | weights min-max (ratio) | Kish n_eff (eligible) | strata | groups | groups with 1 / 0 respondents | df | t |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['coder']} | {r['n_respondents']} | {r['respondents_w_min']:.1f}-{r['respondents_w_max']:.1f} ({r['respondents_w_ratio']:.1f}) | {r['respondents_kish_neff']:.1f} | "
                  f"{r['n_eligible']} | {r['eligible_w_min']:.1f}-{r['eligible_w_max']:.1f} ({r['eligible_w_ratio']:.1f}) | {r['eligible_kish_neff']:.1f} | {r['n_strata']} | "
                  f"{r['n_estimation_groups']} | {r['groups_1_respondent']} / {r['groups_0_respondents']} | {r['df']} | {r['t_quantile_975']:.3f} |")
    md += ["", "| prevalence | coder | k/n | unweighted % | weighted % | Wald 95% | logit 95% | df | Kish n_eff (domain) |", "|---|---|---|---|---|---|---|---|---|"]
    for h in hl:
        lg = "NA" if h["logit_lo_pct"] is None else f"{h['logit_lo_pct']:.1f} to {h['logit_hi_pct']:.1f}"
        md.append(f"| {h['label']} | {h['coder']} | {h['k']}/{h['n']} | {h['unweighted_pct']:.1f} | {h['weighted_pct']:.1f} | {h['wald_lo_pct']:.1f} to {h['wald_hi_pct']:.1f} | {lg} | "
                  f"{h['df']} | {h['domain_kish_neff']:.1f} |")
    md += ["", "Venue sensitivity: response propensity by venue class (journal or chapter / conference / preprint or other), rescaled "
           "within each estimation group so group totals stay N_g.", "",
           "| prevalence | coder | primary % (95%) | venue-adjusted % (95%) | change (points) |", "|---|---|---|---|---|"]
    for v in ven:
        md.append(f"| {v['label']} | {v['coder']} | {v['primary_pct']:.1f} ({v['primary_lo_pct']:.1f} to {v['primary_hi_pct']:.1f}) | "
                  f"{v['venue_pct']:.1f} ({v['venue_lo_pct']:.1f} to {v['venue_hi_pct']:.1f}) | {v['change_pp']:+.1f} |")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf8")
    (out / "config.json").write_text(json.dumps(dict(script="analysis/fulltext/rq234_design_diagnostics.py", script_sha256=sha(__file__),
                                                  rq234_analysis_sha256=sha(HERE / "rq234_analysis.py"), source_run=a.src, source_config_sha256=sha(src / "config.json"),
                                                  source_rq4_sha256=sha(src / "rq4.csv"), seed=None, note="no random numbers; deterministic from the frozen snapshot"), indent=1), encoding="utf8")
    (out / "env.json").write_text(json.dumps(dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform()), indent=1), encoding="utf8")
    (out / "log.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
