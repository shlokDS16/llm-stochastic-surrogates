"""Human benchmark for the three new ACME items (AF, QA, NR), single-site SEs for all 10 items, canonical signs, numeric grids.

Stages (run in this order; `all` runs them all, calling Rscript for the REML step):
  build    raw ML1 file -> data/processed/ml1/{AF,QA,NR}.csv  + runs/human-ml1-acme/coding_audit.md (+ audit.json)
  effects  site-level effects (n1, n0, d, v, sd_pooled, mean1, mean0, rd, v_rd) -> runs/human-ml1-acme/site_effects.csv,
           moment_summary.json (S^H moment estimator, basic bootstrap CI, as analysis/human_ml1/site_effects.py)
  spread   test-inversion S^H (analysis/human_ml1/spread_a1.py code path) -> spread_a1.json / spread_a1.txt
  reml     Rscript analysis/human_ml1/metafor_acme.R -> metafor_results.json
  table    benchmark_table.md/.csv, single_site_se.csv, canonical_signs.csv, published_comparison.json
  grids    analysis/acme/grids.yaml
Run from the project root: .venv/Scripts/python.exe -I analysis/human_ml1/acme_items.py all

Coding conventions (x = 1 for the condition expected to give the higher outcome in the canonical direction of the P1-P4 files is
NOT assumed here; x1/x0 are fixed by P1-CONTRACT.md and the canonical sign is measured, not imposed):
  AF  x1 = forbid question, x0 = allow question; y = 1 if the answer is anti-speech (Yes to forbid, No to allow)
  QA  x1 = Washington, x0 = bin Laden; y = agreement, 1..9, higher = more agreement (raw ML1: 1 = strongly agree, so y = 10 - raw)
  NR  x1 = other-country question first (US question second), x0 = US question first; y = 1 if Yes to the US question
x is taken from the question the respondent actually answered (as for P4 in build_tidy.py), never from the group variable alone;
the audit counts every respondent for whom the two disagree.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "pilot"))
import estimators as E  # noqa: E402

RAW = ROOT / "data/raw/ml1/extracted/data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.labels.dat"
RAW_VALUES = ROOT / "data/raw/ml1/extracted/data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.values.dat"
TIDY = ROOT / "data/processed/ml1"
OUT = ROOT / "runs/human-ml1-acme"
OLD = ROOT / "runs/human-ml1"
B = 2000
SEED = 20261106
NEW = ["AF", "QA", "NR"]
ALL_ITEMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR"]
# paradigm -> [(metric id, kind, column)]; primary = effect used for the benchmark, sens_raw = raw-scale effect
METRICS = {
    "AF": [("primary", "binary", "y"), ("sens_raw", "diff", "y"), ("check_ml1_published_yes_coding", "binary", "y_yes")],
    "QA": [("primary", "cont", "y"), ("sens_raw", "diff", "y")],
    "NR": [("primary", "binary", "y"), ("sens_raw", "diff", "y")],
}


# ---------------------------------------------------------------- coding
def _blank_to_nan(s):
    return s.astype(str).str.strip().replace({"": np.nan})


def _yn(s):
    """'Yes'/'No' text -> 1/0 (NaN if blank)."""
    t = _blank_to_nan(s).str.lower()
    return t.map({"yes": 1.0, "no": 0.0})


def _num(s):
    return pd.to_numeric(_blank_to_nan(s), errors="coerce")


def code_items(d):
    """d: raw labelled frame. Returns ({item: tidy frame}, {item: respondent-level frame used for the audit})."""
    site = d["referrer"].astype(str)
    # ---- AF: a = forbid question, b = allow question (Codebook.xlsx rows allowedforbiddena / b)
    fa, fb = _yn(d["allowedforbiddena"]), _yn(d["allowedforbiddenb"])
    af = pd.DataFrame({"site": site, "ans_forbid": fa, "ans_allow": fb})
    af["x"] = np.where(fa.notna() & fb.isna(), 1.0, np.where(fb.notna() & fa.isna(), 0.0, np.nan))
    af["y_yes"] = fa.where(fa.notna(), fb)                       # raw Yes (the coding behind ML1's published d = 1.96)
    af["y"] = np.where(af.x == 1, fa, np.where(af.x == 0, 1 - fb, np.nan))   # anti-speech: Yes to forbid, No to allow
    af["group_var"] = d["allowedforbiddenGroup"].astype(str).str.strip()
    # ---- QA: quotea = Washington, quoteb = bin Laden; raw 1 = strongly agree .. 9 = strongly disagree
    qa_, qb_ = _num(d["quotea"]), _num(d["quoteb"])
    qa = pd.DataFrame({"site": site, "raw_wash": qa_, "raw_bl": qb_})
    qa["x"] = np.where(qa_.notna() & qb_.isna(), 1.0, np.where(qb_.notna() & qa_.isna(), 0.0, np.nan))
    qa["y"] = np.where(qa.x == 1, 10 - qa_, np.where(qa.x == 0, 10 - qb_, np.nan))
    qa["released_quote"] = _num(d["quote"])
    qa["group_var"] = d["quoteGroup"].astype(str).str.strip()
    # ---- NR: reciprocityusa = US question asked first, usb = US question asked second (other-country first)
    ua, ub = _yn(d["reciprocityusa"]), _yn(d["reciprocityusb"])
    oa, ob = _yn(d["reciprocityothera"]), _yn(d["reciprocityotherb"])
    nr = pd.DataFrame({"site": site, "us_first": ua, "us_second": ub, "other_second": oa, "other_first": ob})
    nr["x"] = np.where(ub.notna() & ua.isna(), 1.0, np.where(ua.notna() & ub.isna(), 0.0, np.nan))
    nr["y"] = np.where(nr.x == 1, ub, np.where(nr.x == 0, ua, np.nan))
    nr["group_var"] = d["reciprocitygroup"].astype(str).str.strip()
    nr["released_us"] = _yn(d["reciprocityus"])
    full = {"AF": af, "QA": qa, "NR": nr}
    tidy = {}
    for k, f in full.items():
        cols = ["site", "x", "y"] + (["y_yes"] if k == "AF" else [])
        t = f[cols].dropna(subset=["x", "y"]).copy()
        t["x"] = t.x.astype(int)
        tidy[k] = t
    return tidy, full


def audit(full, d, d_values):
    """Group-coding audit. Returns (markdown text, json-able dict)."""
    L, J = [], {}
    L.append("# Group-coding audit for AF, QA, NR (ML1 cleaned dataset, labels file)\n")
    L.append(f"Source: `{RAW.relative_to(ROOT).as_posix()}`, {len(d)} rows; numeric-code twin `{RAW_VALUES.relative_to(ROOT).as_posix()}`. "
             "Written by `analysis/human_ml1/acme_items.py build`. The condition x used for every value is the question the respondent "
             "answered (which of the two item variables is non-missing); the released group variable is only audited against it.\n")

    NICE = {"ans_f": "forbid Q", "ans_a": "allow Q", "ans_w": "Washington", "ans_b": "bin Laden", "ans_us1": "US Q first-version (usa)",
            "ans_us2": "US Q second-version (usb)", "ans_o_second": "other Q second-version (othera)", "ans_o_first": "other Q first-version (otherb)"}

    def ct(df, row, cols_flags):
        key = pd.Series(["; ".join(f"{NICE[c]} {'answered' if r[i] else 'blank'}" for i, c in enumerate(cols_flags)) for r in df[cols_flags].to_numpy()],
                        index=df.index, name="answers")
        return pd.crosstab(df[row], key)

    def md_table(t):
        t = t.copy()
        t.columns = [" / ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        h = "| " + t.index.name + " | " + " | ".join(t.columns) + " |\n|" + "---|" * (len(t.columns) + 1) + "\n"
        return h + "\n".join("| " + str(i) + " | " + " | ".join(str(v) for v in r) + " |" for i, r in t.iterrows()) + "\n"

    # ---------- AF
    af = full["AF"]
    af["ans_f"], af["ans_a"] = af.ans_forbid.notna(), af.ans_allow.notna()
    L.append("## AF allowed/forbidden\nCodebook: `allowedforbiddena` = forbid question, `allowedforbiddenb` = allow question; 1 = Yes, 2 = No.\n")
    L.append("Group variable `allowedforbiddenGroup` against the question answered (counts of respondents):\n")
    L.append(md_table(ct(af, "group_var", ["ans_f", "ans_a"])))
    exp = {"forbidden": (True, False), "allowed": (False, True)}
    contra = af[[(r.group_var in exp and (r.ans_f, r.ans_a) != exp[r.group_var]) and (r.ans_f or r.ans_a) for r in af.itertuples()]]
    both = int((af.ans_f & af.ans_a).sum())
    neither = int((~af.ans_f & ~af.ans_a).sum())
    L.append(f"\nRespondents who answered both questions: {both}. Respondents who answered neither: {neither} "
             f"(missing, dropped; the file notes 52 invalid responses). Respondents whose answered question contradicts the group "
             f"variable (answered the allow question while grouped 'forbidden', or the reverse): **{len(contra)}**.\n")
    # composite check
    comp = d["allowedforbidden"].astype(str).str.strip().str.upper().map({"YES": 1.0, "NO": 0.0})
    mism = int((comp.notna() & af.y_yes.notna() & (comp != af.y_yes)).sum())
    L.append(f"Released composite `allowedforbidden` (YES/NO) against the raw Yes of the answered question: {mism} mismatches "
             f"(composite non-missing {int(comp.notna().sum())}, raw non-missing {int(af.y_yes.notna().sum())}).\n")
    n1, n0 = int((af.x == 1).sum()), int((af.x == 0).sum())
    p1, p0 = af.loc[af.x == 1, "y"].mean(), af.loc[af.x == 0, "y"].mean()
    L.append(f"Result: x1 (forbid) n = {n1}, share anti-speech (Yes to forbid) = {p1:.4f}; x0 (allow) n = {n0}, share anti-speech "
             f"(No to allow) = {p0:.4f}. The coding is the one in the ML1 supplement (7.2 percent Yes to forbid, 23.7 percent No to allow).\n")
    L.append("**Note on the published ML1 effect for this item.** The supplement's chi-square (3088.69, d = 1.96) compares the raw Yes answer "
             "across the two questions, so it measures opposite positions against each other (Yes to forbid is anti-speech, Yes to allow is "
             "pro-speech). The anti-speech coding used here (and by Rugg 1941) gives a much smaller effect; the raw-Yes coding is kept as the "
             "metric `check_ml1_published_yes_coding` in `site_effects.csv` and reproduces the published number. See REPORT.md.\n")
    J["AF"] = dict(rows=len(af), both=both, neither=neither, contradict_group=len(contra), composite_mismatch=mism,
                   n_x1=n1, n_x0=n0, share_anti_x1=float(p1), share_anti_x0=float(p0))

    # ---------- QA
    qa = full["QA"]
    qa["ans_w"], qa["ans_b"] = qa.raw_wash.notna(), qa.raw_bl.notna()
    L.append("\n## QA quote attribution\nCodebook: `quotea` = Washington, `quoteb` = Bin Laden; 1 = strongly agree, 9 = strongly disagree. "
             "Analysed y = 10 - raw (higher = more agreement), which equals the released `quote` variable.\n")
    L.append("Group variable `quoteGroup` against the quote answered:\n")
    L.append(md_table(ct(qa, "group_var", ["ans_w", "ans_b"])))
    expq = {"liked source": (True, False), "disliked source": (False, True)}
    contra = qa[[(r.group_var in expq and (r.ans_w, r.ans_b) != expq[r.group_var]) and (r.ans_w or r.ans_b) for r in qa.itertuples()]]
    both = int((qa.ans_w & qa.ans_b).sum())
    neither = int((~qa.ans_w & ~qa.ans_b).sum())
    L.append(f"\nAnswered both: {both}. Answered neither: {neither} (the supplement notes 19 invalid responses). Contradicting the group "
             f"variable: **{len(contra)}**.\n")
    ok = qa.x.notna()
    rel_mm = int((ok & qa.released_quote.notna() & (qa.y != qa.released_quote)).sum())
    rng_bad = int((ok & ~qa.y.between(1, 9)).sum())
    L.append(f"Recoded y against released `quote`: {rel_mm} mismatches; values outside 1..9: {rng_bad}.\n")
    m1, m0 = qa.loc[qa.x == 1, "y"].mean(), qa.loc[qa.x == 0, "y"].mean()
    s1, s0 = qa.loc[qa.x == 1, "y"].std(), qa.loc[qa.x == 0, "y"].std()
    L.append(f"Result: Washington (x1) n = {int((qa.x == 1).sum())}, mean = {m1:.3f}, SD = {s1:.3f}; bin Laden (x0) n = {int((qa.x == 0).sum())}, "
             f"mean = {m0:.3f}, SD = {s0:.3f} (supplement: 5.93 / 2.2 and 5.23 / 2.11).\n")
    J["QA"] = dict(rows=len(qa), both=both, neither=neither, contradict_group=len(contra), released_mismatch=rel_mm, out_of_range=rng_bad,
                   n_x1=int((qa.x == 1).sum()), n_x0=int((qa.x == 0).sum()), mean_x1=float(m1), mean_x0=float(m0), sd_x1=float(s1), sd_x0=float(s0))

    # ---------- NR
    nr = full["NR"]
    nr["ans_us1"], nr["ans_us2"] = nr.us_first.notna(), nr.us_second.notna()
    nr["ans_o_second"], nr["ans_o_first"] = nr.other_second.notna(), nr.other_first.notna()
    L.append("\n## NR norm of reciprocity\nCodebook: `reciprocityusa` = US question asked first, `reciprocityusb` = US question asked second "
             "(other-country question first); `reciprocityothera` = other-country question asked second, `reciprocityotherb` = asked first; "
             "1 = Yes, 2 = No. x1 = other first (US second), x0 = US first; y = 1 if Yes to the US question.\n")
    L.append("Group variable `reciprocitygroup` ('Asked first' / 'Asked second' refers to the US question) against the US question answered:\n")
    L.append(md_table(ct(nr, "group_var", ["ans_us1", "ans_us2"])))
    L.append("\nSame group variable against the other-country question answered:\n")
    L.append(md_table(ct(nr, "group_var", ["ans_o_second", "ans_o_first"])))
    expn = {"Asked first": (True, False), "Asked second": (False, True)}
    contra = nr[[(r.group_var in expn and (r.ans_us1, r.ans_us2) != expn[r.group_var]) and (r.ans_us1 or r.ans_us2) for r in nr.itertuples()]]
    both = int((nr.ans_us1 & nr.ans_us2).sum())
    neither = int((~nr.ans_us1 & ~nr.ans_us2).sum())
    # within-respondent order consistency: US first (usa) should pair with other asked second (othera), US second (usb) with otherb
    inc = int(((nr.ans_us1 & nr.ans_o_first) | (nr.ans_us2 & nr.ans_o_second)).sum())
    L.append(f"\nAnswered both US versions: {both}. Answered neither: {neither} (the supplement notes 68 invalid responses). Contradicting the "
             f"group variable: **{len(contra)}**. Respondents whose US-question version and other-country-question version imply different "
             f"orders: **{inc}**.\n")
    mm = int((nr.x.notna() & nr.released_us.notna() & (nr.y != nr.released_us)).sum())
    L.append(f"Recoded y against released `reciprocityus`: {mm} mismatches.\n")
    q1, q0 = nr.loc[nr.x == 1, "y"].mean(), nr.loc[nr.x == 0, "y"].mean()
    L.append(f"Result: US question second (x1) n = {int((nr.x == 1).sum())}, share Yes = {q1:.4f}; US question first (x0) n = {int((nr.x == 0).sum())}, "
             f"share Yes = {q0:.4f} (supplement: 77.3 and 63.9 percent).\n")
    J["NR"] = dict(rows=len(nr), both=both, neither=neither, contradict_group=len(contra), order_inconsistent=inc, released_mismatch=mm,
                   n_x1=int((nr.x == 1).sum()), n_x0=int((nr.x == 0).sum()), share_yes_x1=float(q1), share_yes_x0=float(q0))

    # ---------- numeric twin cross-check of the group variables
    L.append("\n## Cross-check against the numeric-code file\n")
    tw = []
    for name, gcol, ref in [("AF", "allowedforbiddenGroup", full["AF"]), ("QA", "quoteGroup", full["QA"]), ("NR", "reciprocitygroup", full["NR"])]:
        t = pd.crosstab(ref.group_var, d_values[gcol].astype(str).str.strip())
        tw.append(f"{name}: label -> numeric code in the values file: " + "; ".join(f"{i} -> {[c for c in t.columns if t.loc[i, c] > 0]}" for i in t.index))
    L.append("\n".join("- " + x for x in tw) + "\n")
    L.append("\n## Sites\n")
    return "\n".join(L), J


# ---------------------------------------------------------------- stage: build
def stage_build():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(RAW, sep="\t", low_memory=False, encoding="latin-1")
    dv = pd.read_csv(RAW_VALUES, sep="\t", low_memory=False, encoding="latin-1")
    assert len(d) == len(dv) and (d.referrer == dv.referrer).all()
    tidy, full = code_items(d)
    text, J = audit(full, d, dv)
    lines = []
    for k, t in tidy.items():
        t.to_csv(TIDY / f"{k}.csv", index=False)
        g = t.groupby("site").x.agg(["sum", "count"])
        g["n0"] = g["count"] - g["sum"]
        J[k]["sites"] = int(t.site.nunique())
        J[k]["min_arm_n"] = int(min(g["sum"].min(), g["n0"].min()))
        J[k]["n_tidy"] = len(t)
        lines.append(f"- {k}: {len(t)} usable respondents, {t.site.nunique()} sites, smallest arm within a site {J[k]['min_arm_n']}, "
                     f"x counts {t.x.value_counts().to_dict()}")
        print(lines[-1])
    P1 = pd.read_csv(TIDY / "P1.csv")
    same = set(P1.site) == set(tidy["AF"].site) == set(tidy["QA"].site) == set(tidy["NR"].site)
    lines.append(f"- Site keys (`referrer`, as in build_tidy.py) identical to P1.csv: {same} ({P1.site.nunique()} sites).")
    (OUT / "coding_audit.md").write_text(text + "\n".join(lines) + "\n", encoding="utf8")
    (OUT / "audit.json").write_text(json.dumps(J, indent=2), encoding="utf8")


# ---------------------------------------------------------------- stage: effects
def site_rows(df, p, mets):
    rows = []
    for mid, kind, col in mets:
        for s in sorted(df.site.unique()):
            g = df[df.site == s]
            y1, y0 = g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float)
            dd, vv = E.effect(kind, y1, y0)
            n1, n0 = len(y1), len(y0)
            sp = float(np.sqrt(((n1 - 1) * y1.var(ddof=1) + (n0 - 1) * y0.var(ddof=1)) / (n1 + n0 - 2))) if kind == "cont" else np.nan
            row = dict(paradigm=p, metric=mid, kind=kind, site=s, n1=n1, n0=n0, d=float(dd), v=float(vv), sd_pooled=sp,
                       mean1=float(y1.mean()), mean0=float(y0.mean()), rd=np.nan, v_rd=np.nan)
            if p in ("AF", "NR"):    # binary items: risk difference (x1 - x0) and its variance (sample-variance form, as kind 'diff')
                row["rd"], row["v_rd"] = [float(z) for z in E.effect("diff", g.loc[g.x == 1, "y"].to_numpy(float), g.loc[g.x == 0, "y"].to_numpy(float))]
            rows.append(row)
    return rows


def stage_effects():
    rng = np.random.default_rng(SEED)
    rows, summary = [], {}
    for p, mets in METRICS.items():
        df = pd.read_csv(TIDY / f"{p}.csv")
        rows += site_rows(df, p, mets)
        sites = sorted(df.site.unique())
        for mid, kind, col in mets:
            ys = [(df.loc[(df.site == s) & (df.x == 1), col].to_numpy(float), df.loc[(df.site == s) & (df.x == 0), col].to_numpy(float)) for s in sites]
            dv = [E.effect(kind, a, b) for a, b in ys]
            dd, vv = np.array([z[0] for z in dv]), np.array([z[1] for z in dv])
            bd = np.empty((B, len(sites)))
            bv = np.empty((B, len(sites)))
            for j, (y1, y0) in enumerate(ys):
                bd[:, j], bv[:, j] = E.boot_effect(kind, y1, y0, rng, B)
            s2_b = E.spread_s2(bd, bv)
            S_b = np.sqrt(np.maximum(0, s2_b))
            s2 = float(E.spread_s2(dd, vv))
            s2_star = float(((dd - dd.mean()) ** 2).mean())
            q = lambda x, p_: float(np.quantile(x, p_))
            basic = [s2 - (q(s2_b, .975) - s2_star), s2 - (q(s2_b, .025) - s2_star)]
            summary[f"{p}/{mid}"] = dict(
                paradigm=p, metric=mid, kind=kind, n_sites=len(sites), n_total=int(sum(len(a) + len(b) for a, b in ys)),
                dbar=float(dd.mean()), S2_untruncated=s2, S=float(np.sqrt(max(0, s2))),
                S_ci95=[float(np.sqrt(max(0, basic[0]))), float(np.sqrt(max(0, basic[1])))], S2_ci95_basic=basic,
                S_ci95_percentile=[float(np.quantile(S_b, .025)), float(np.quantile(S_b, .975))],
                share_sites_positive_sign=float((dd > 0).mean()), boot_B=B, seed=SEED)
            s = summary[f"{p}/{mid}"]
            print(p, mid, "k=%d dbar=%.3f S=%.3f CI=[%.3f, %.3f]" % (len(sites), dd.mean(), s["S"], *s["S_ci95"]))
    pd.DataFrame(rows).to_csv(OUT / "site_effects.csv", index=False)
    (OUT / "moment_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")


# ---------------------------------------------------------------- stage: spread (test inversion)
def stage_spread():
    rng = np.random.default_rng(SEED + 1)
    res, lines = {}, []
    lines.append(f"{'metric':36s} {'sites':>5s} {'S2hat':>8s} {'S^H':>6s} {'TI 95% S':>16s} {'lower>0':>8s} | formula-v S^H")
    for p, mets in METRICS.items():
        df = pd.read_csv(TIDY / f"{p}.csv")
        for mid, kind, col in mets:
            cells = {}
            for i, (s, g) in enumerate(df.groupby("site", sort=True)):
                cells[(i,)] = (g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float))
            design = E.Design(["site"], [len(cells)])
            r = E.estimate2(cells, design, kind, rng=rng, B=2000, K=200, var_method="splithalf", sd_floor=0.0, intervals=("ti_boot",), term_intervals=False)
            name = f"{p}/{mid}"
            if r["status"] != "ok":
                lines.append(f"{name:36s} status {r['status']}: {r.get('deterministic_cells')}")
                res[name] = {"status": r["status"]}
                continue
            rf = E.estimate2(cells, design, kind, rng=rng, var_method="formula", intervals=(), term_intervals=False)
            iv = r["intervals"]["ti_boot"]
            res[name] = dict(sites=len(cells), S2hat=float(r["S2_untruncated"]), S=float(r["S"]), TI_S=[float(iv["S"][0]), float(iv["S"][1])],
                             TI_S2=[float(iv["S2"][0]), float(iv["S2"][1])], S_formula=float(rf["S"]), seed=SEED + 1)
            lines.append(f"{name:36s} {len(cells):5d} {r['S2_untruncated']:8.4f} {r['S']:6.3f} [{iv['S'][0]:6.3f}, {iv['S'][1]:6.3f}] {str(iv['S2'][0] > 0):>8s} | {rf['S']:.3f}")
    (OUT / "spread_a1.json").write_text(json.dumps(res, indent=2), encoding="utf8")
    (OUT / "spread_a1.txt").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))


def stage_reml():
    rs = Path(r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe")
    r = subprocess.run([str(rs), "analysis/human_ml1/metafor_acme.R"], cwd=ROOT, capture_output=True, text=True)
    (OUT / "metafor.log").write_text(r.stdout + "\n" + r.stderr, encoding="utf8")
    print(r.stdout[-3000:])
    if r.returncode != 0:
        raise SystemExit(r.stderr)


# ---------------------------------------------------------------- stage: tables
NAMES = {"AF": "AF allowed/forbidden (log OR, anti-speech; forbid vs allow)", "QA": "QA quote attribution (g; Washington vs bin Laden)",
         "NR": "NR norm of reciprocity (log OR, Yes to US question; other first vs US first)"}
RAWSCALE = {"P1": ("risk difference (sure option)", "y"), "P2a": ("miles", "y"), "P2b": ("people", "y"), "P2c": ("feet", "y"),
            "P2d": ("babies per day", "y"), "P3": ("rating points (1-9)", "y"), "P4": ("estimated earlier rolls (count)", "y_raw"),
            "AF": ("risk difference (anti-speech)", "y"), "QA": ("rating points (1-9, higher = agree)", "y"), "NR": ("risk difference (Yes to US question)", "y")}


def stage_table():
    mom = json.loads((OUT / "moment_summary.json").read_text(encoding="utf8"))
    rma = json.loads((OUT / "metafor_results.json").read_text(encoding="utf8"))
    ti = json.loads((OUT / "spread_a1.json").read_text(encoding="utf8"))
    rows = ["paradigm|metric|k|N|mu_REML [95% CI]|tau_REML [Q-profile 95% CI]|I2 %|Q (p)|unweighted mean d|S^H moment (basic bootstrap 95% CI)"]
    csv = ["paradigm,metric,k,N,mu,mu_lo,mu_hi,tau,tau_lo,tau_hi,I2,Q,Q_p,dbar,S_H,S_H_lo,S_H_hi,S_TI,S_TI_lo,S_TI_hi"]
    ti_rows = ["| paradigm | metric | S^H test inversion | 95% interval (S) | lower bound of S^2 interval above 0 |", "|---|---|---|---|---|"]
    for key, r in rma.items():
        m = mom[key]
        t = ti.get(key, {})
        rows.append("%s|%s|%d|%d|%.3f [%.3f, %.3f]|%.3f [%.3f, %.3f]|%.1f|%.1f (%.3f)|%.3f|%.3f [%.3f, %.3f]" % (
            NAMES.get(r["paradigm"], r["paradigm"]), r["metric"], r["k"], m["n_total"], r["mu"], r["mu_ci"][0], r["mu_ci"][1], r["tau"],
            r["tau_ci_qprofile"][0], r["tau_ci_qprofile"][1], r["I2"], r["Q"], r["Q_p"], m["dbar"], m["S"], m["S_ci95"][0], m["S_ci95"][1]))
        tv = [t.get("S", np.nan), *t.get("TI_S", [np.nan, np.nan])]
        csv.append(",".join(map(str, [r["paradigm"], r["metric"], r["k"], m["n_total"], r["mu"], *r["mu_ci"], r["tau"], *r["tau_ci_qprofile"], r["I2"],
                                      r["Q"], r["Q_p"], m["dbar"], m["S"], *m["S_ci95"], *tv])))
        if t:
            ti_rows.append("| %s | %s | %.3f | [%.3f, %.3f] | %s |" % (r["paradigm"], r["metric"], t["S"], t["TI_S"][0], t["TI_S"][1], t["TI_S2"][0] > 0))
    md = ("| " + " | ".join(rows[0].split("|")) + " |\n|" + "---|" * 10 + "\n" + "\n".join("| " + " | ".join(x.split("|")) + " |" for x in rows[1:]) + "\n")
    md += ("\nMetrics: `primary` = log odds ratio (AF, NR) or Hedges g (QA), x1 minus x0; `sens_raw` = raw-scale difference (risk difference, or rating points) "
           "with variance s1^2/n1 + s0^2/n0, so mu, tau and S^H are in raw units; `check_ml1_published_yes_coding` (AF only) = log OR of the raw Yes answer, "
           "the coding behind the published d = 1.96. Same estimators as `runs/human-ml1/benchmark_table.md` (metafor REML with Q-profile CI; moment estimator "
           "with within-site bootstrap, B = %d, seed %d).\n\nTest-inversion spread (code path of `spread_a1.py`, seed %d):\n\n" % (B, SEED, SEED + 1)
           + "\n".join(ti_rows) + "\n")
    (OUT / "benchmark_table.md").write_text(md, encoding="utf8")
    (OUT / "benchmark_table.csv").write_text("\n".join(csv), encoding="utf8")
    print(md)

    # ---- canonical signs and single-site SE for all 10 items
    old_rma = json.loads((OLD / "metafor_results.json").read_text(encoding="utf8"))
    old_se = pd.read_csv(OLD / "site_effects.csv")
    new_se = pd.read_csv(OUT / "site_effects.csv")
    se_all = pd.concat([old_se[old_se.paradigm.isin(ALL_ITEMS)], new_se[new_se.paradigm.isin(NEW)]])
    X1 = {"P1": "gain frame", "P2a": "high anchor", "P2b": "high anchor", "P2c": "high anchor", "P2d": "high anchor", "P3": "paid ticket",
          "P4": "three 6s", "AF": "forbid question", "QA": "Washington", "NR": "other-country question first"}
    X0 = {"P1": "loss frame", "P2a": "low anchor", "P2b": "low anchor", "P2c": "low anchor", "P2d": "low anchor", "P3": "free ticket",
          "P4": "one 3 and two 6s", "AF": "allow question", "QA": "bin Laden", "NR": "US question first"}
    cs, ss = [], []
    for it in ALL_ITEMS:
        r = (old_rma if it not in NEW else rma)[f"{it}/primary"]
        prim = se_all[(se_all.paradigm == it) & (se_all.metric == "primary")]
        sign = int(np.sign(r["mu"]))
        mu_ci_excl0 = bool(r["mu_ci"][0] > 0 or r["mu_ci"][1] < 0)
        unw = float(prim.d.mean())
        scale = "log odds ratio" if prim.kind.iloc[0] == "binary" else "Hedges g"
        cs.append(dict(item=it, x1=X1[it], x0=X0[it], scale=scale, mu_reml=r["mu"], mu_lo=r["mu_ci"][0], mu_hi=r["mu_ci"][1], unweighted_mean=unw,
                       canonical_sign=sign, ci_excludes_zero=mu_ci_excl0, share_sites_positive=float((prim.d > 0).mean()), k_sites=len(prim)))
        tidy = pd.read_csv(TIDY / f"{it}.csv")
        rawlab, rawcol = RAWSCALE[it]
        rawse = []
        for s, g in tidy.groupby("site"):
            _, v = E.effect("diff", g.loc[g.x == 1, rawcol].to_numpy(float), g.loc[g.x == 0, rawcol].to_numpy(float))
            rawse.append(np.sqrt(v))
        ss.append(dict(item=it, scale_primary=scale, se_single_site_primary=float(np.median(np.sqrt(prim.v))), median_n1=float(prim.n1.median()),
                       median_n0=float(prim.n0.median()), median_sd_pooled=float(prim.sd_pooled.median()) if prim.kind.iloc[0] == "cont" else np.nan,
                       scale_raw=rawlab, se_single_site_raw=float(np.median(rawse)), k_sites=len(prim),
                       definition="median over the sites of sqrt(v) of the site's primary effect (x1 minus x0); raw: sqrt(s1^2/n1 + s0^2/n0)"))
    pd.DataFrame(cs).to_csv(OUT / "canonical_signs.csv", index=False)
    pd.DataFrame(ss).to_csv(OUT / "single_site_se.csv", index=False)
    print(pd.DataFrame(cs)[["item", "scale", "mu_reml", "canonical_sign", "ci_excludes_zero"]])
    print(pd.DataFrame(ss)[["item", "se_single_site_primary", "median_n1", "median_n0", "se_single_site_raw"]])

    # ---- published comparison (all respondents pooled, as in the ML1 supplement)
    pc = {}
    af, qa, nr = (pd.read_csv(TIDY / f"{k}.csv") for k in NEW)
    from scipy import stats

    def phi_d(t):
        chi2 = stats.chi2_contingency(t, correction=False)[0]
        r = np.sqrt(chi2 / t.sum())
        return float(chi2), float(2 * r / np.sqrt(1 - r * r))

    # AF anti-speech vs raw-yes
    t = pd.crosstab(af.x, af.y).to_numpy()
    c, dphi = phi_d(t)
    t2 = pd.crosstab(af.x, af.y_yes).to_numpy()
    c2, dphi2 = phi_d(t2)
    pc["AF"] = dict(n=int(len(af)), share_no_allow=float(af.loc[af.x == 0, "y"].mean()), share_yes_forbid=float(af.loc[af.x == 1, "y"].mean()),
                    chi2_antispeech=c, d_phi_antispeech=dphi, chi2_raw_yes=c2, d_phi_raw_yes=dphi2,
                    published=dict(share_no_allow=0.237, share_yes_forbid=0.072, chi2=3088.69, d=1.96))
    t = pd.crosstab(nr.x, nr.y).to_numpy()
    c, dphi = phi_d(t)
    pc["NR"] = dict(n=int(len(nr)), share_yes_us_second=float(nr.loc[nr.x == 1, "y"].mean()), share_yes_us_first=float(nr.loc[nr.x == 0, "y"].mean()),
                    chi2=c, d_phi=dphi, published=dict(share_us_second=0.773, share_us_first=0.639, chi2=135.32, d=0.3))
    a, b = qa.loc[qa.x == 1, "y"], qa.loc[qa.x == 0, "y"]
    tt = stats.ttest_ind(a, b, equal_var=True)
    sp = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2))
    pc["QA"] = dict(n=int(len(qa)), mean_washington=float(a.mean()), sd_washington=float(a.std()), mean_binladen=float(b.mean()), sd_binladen=float(b.std()),
                    t=float(tt.statistic), df=int(len(a) + len(b) - 2), d=float((a.mean() - b.mean()) / sp),
                    published=dict(mean_washington=5.93, sd_washington=2.2, mean_binladen=5.23, sd_binladen=2.11, t=12.79, df=6323, d=0.32))
    k3 = np.sqrt(3) / np.pi   # log OR -> Cohen's d
    pub_Q = {"AF": 180.40, "QA": 67.69, "NR": 38.89}   # ManyLabsManuscript.md Table 3 (Q, df 35)
    for k, mk in [("AF", "primary"), ("QA", "primary"), ("NR", "primary")]:
        r = rma[f"{k}/{mk}"]
        pc[k]["reml_primary"] = dict(mu=r["mu"], mu_ci=r["mu_ci"], d_equivalent=r["mu"] * (k3 if k != "QA" else 1.0), Q=r["Q"], Q_p=r["Q_p"], tau=r["tau"], I2=r["I2"])
        pc[k]["published_Q_table3"] = pub_Q[k]
    r = rma["AF/check_ml1_published_yes_coding"]
    pc["AF"]["reml_raw_yes_coding"] = dict(mu=r["mu"], d_equivalent=r["mu"] * k3, Q=r["Q"], Q_p=r["Q_p"], tau=r["tau"], I2=r["I2"])
    (OUT / "published_comparison.json").write_text(json.dumps(pc, indent=2), encoding="utf8")
    print(json.dumps(pc, indent=1))


# ---------------------------------------------------------------- grids
def round2sig_int(v):
    """Round to 2 significant digits, then to a positive integer."""
    return max(1, int(round(float(f"{v:.1e}"))))


def make_grid(y, anchors=(), K=15, p_lo=1.0, p_hi=99.0):
    """K log-spaced integers from the p_lo-th to the p_hi-th percentile of y (lower end floored at 1), 2 significant digits, unique and
    sorted; each anchor replaces the nearest not-yet-anchored grid value (log distance) and is kept exactly."""
    y = np.asarray(y, float)
    lo_raw, hi_raw = float(np.percentile(y, p_lo)), float(np.percentile(y, p_hi))
    lo, hi = max(lo_raw, 1.0), hi_raw
    pts = np.exp(np.linspace(np.log(lo), np.log(hi), K))
    grid = [round2sig_int(v) for v in pts]
    kept_anchor_idx = set()
    for a in anchors:
        order = np.argsort(np.abs(np.log(np.array(grid, float)) - np.log(a)))
        j = next(i for i in order if i not in kept_anchor_idx)
        grid[j] = int(a)
        kept_anchor_idx.add(j)
    uniq = sorted(set(grid))
    alt = None
    if len(uniq) < K:   # rounding to integers/2 s.f. merged neighbours: search the smallest oversampling m that gives K unique values
        for m in range(K + 1, 60):
            g2 = [round2sig_int(v) for v in np.exp(np.linspace(np.log(lo), np.log(hi), m))]
            if len(set(g2)) == K:
                alt = sorted(set(g2))
                break
    return dict(grid_alt_exactly_K=alt, p_lo=p_lo, p_hi=p_hi, lo_raw=lo_raw, hi_raw=hi_raw, lo_used=lo, hi_used=hi, K_requested=K, K_actual=len(uniq),
               grid=[int(v) for v in uniq], anchors=[int(a) for a in anchors])


def stage_grids():
    import yaml
    anchors = {}
    for it in ["P2a", "P2b", "P2c", "P2d"]:
        y = yaml.safe_load((ROOT / f"analysis/pilot/prompts/W0/{it}.yaml").read_text(encoding="utf8"))
        import re
        nums = []
        for k in ("x1", "x0"):
            m = re.search(r"(\d[\d,]*)", y["conditions"][k])
            nums.append(int(m.group(1).replace(",", "")))
        anchors[it] = nums
    anchors["P4"] = []
    out = {"generated_by": "analysis/human_ml1/acme_items.py grids", "source": "data/processed/ml1/<item>.csv (raw y; P4: y_raw), all respondents, both arms, 36 sites",
           "rule": "K = 15 log-spaced values from the 1st to the 99th percentile (numpy linear-interpolation percentile; lower end floored at 1), rounded to 2 significant digits, positive integers, unique, sorted; both anchors replace the nearest grid value (log distance) and are kept exactly",
           "items": {}}
    for it in ["P2a", "P2b", "P2c", "P2d", "P4"]:
        df = pd.read_csv(TIDY / f"{it}.csv")
        col = "y_raw" if it == "P4" else "y"
        g = make_grid(df[col].to_numpy(float), anchors[it])
        g["n_responses"] = int(len(df))
        g["column"] = col
        out["items"][it] = g
        print(it, g["K_actual"], g["grid"])
    (ROOT / "analysis/acme").mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis/acme/grids.yaml").write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf8")


STAGES = {"build": stage_build, "effects": stage_effects, "spread": stage_spread, "reml": stage_reml, "table": stage_table, "grids": stage_grids}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name in (STAGES if which == "all" else [which]):
        print("==", name)
        STAGES[name]()
