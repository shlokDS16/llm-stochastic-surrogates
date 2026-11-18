#!/usr/bin/env python
"""Generate paper/common/autonumbers.tex and paper/common/autonumbers-index.md.

Every number the results sections quote is read from a run output or a ledger-style
processed file; nothing is typed in here. Rerun after the final extraction:

    .venv/Scripts/python.exe -I analysis/paper_numbers.py

Conventions
  * one \\newcommand{\\nXxx}{value} per number, followed by "% src: <file>#<row/key>"
  * macro names are letters only (LaTeX); digits in source keys become words
  * counts are integers with {,} thousands separators; percentages have one decimal and
    no % sign; intervals are separate macros (...Lo, ...Hi); kappa has three decimals
  * negative values are written \\ensuremath{-}x so they work in text and in maths
  * p-values are never emitted. The pilot LLM/human spread ratio column is never read.

Prefixes: nSearch nScreen nRqOne nFt nRqTwo nRqThree nRqFour nAgree nPilot nInterim.
Added 2026-10-17: for every RQ3 and RQ4 prevalence stem <stem> (the stem of ...Est/...Lo/...Hi) the macros <stem>BoundLo and
<stem>BoundHi (nonresponse bounds, runs/rq234-interim/nonresponse_bounds.csv) and <stem>Pass (pass or fail, v0.12 rule, from the
prevalence csv, which carries agreement.csv); nPair... (paired like-for-like contrasts, paired_contrasts.csv); nZeroEvt... (exact upper
bounds at zero events, zero_event_bounds.csv); nPilotNd... (near-deterministic split, runs/pilot-nd-split/summary.csv).
Added 2026-10-17 (CRP-S04, B1/B3/B8): nCal... (rule calibration, clause split, human sites; runs/pilot-rule-calibration), nPlace... (placement
sensitivity; runs/pilot-placement-sensitivity), nDesign... (design weights, Kish n_eff, unweighted k/n; runs/rq234-design-diagnostics).
Missing input files stop the run (nothing is half-written).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_TEX = ROOT / "paper" / "common" / "autonumbers.tex"
OUT_IDX = ROOT / "paper" / "common" / "autonumbers-index.md"

# --------------------------------------------------------------------------- helpers
ONES = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
        "Eighteen", "Nineteen"]
TENS = {2: "Twenty", 3: "Thirty", 4: "Forty", 5: "Fifty", 6: "Sixty", 7: "Seventy",
        8: "Eighty", 9: "Ninety"}


def num_word(s: str) -> str:
    """Digits to letters. 0-99 as a number word, longer runs digit by digit."""
    if len(s) <= 2 and not (len(s) == 2 and s[0] == "0"):
        n = int(s)
        if n < 20:
            return ONES[n]
        return TENS[n // 10] + (ONES[n % 10] if n % 10 else "")
    return "".join(ONES[int(c)] for c in s)


def slug(text: str) -> str:
    """CamelCase letters-only token from an arbitrary label."""
    t = str(text)
    t = re.sub(r"\([^)]*\)", " ", t)           # drop parentheticals
    t = t.replace("<=", " upto ").replace(">=", " atleast ").replace("%", " pct ")
    parts = re.findall(r"[A-Za-z]+|\d+", t)
    out = []
    for p in parts:
        if re.fullmatch(r"20\d\d", p):
            out.append("Y" + num_word(p[2:]))
        else:
            out.append(num_word(p) if p.isdigit() else p[:1].upper() + p[1:])
    return "".join(out)


def sign_wrap(s: str) -> str:
    return s.replace("-", "\\ensuremath{-}", 1) if s.startswith("-") else s


def f_int(x) -> str:
    v = float(x)
    if abs(v - round(v)) > 1e-9:
        raise ValueError(f"not an integer: {x!r}")
    return sign_wrap(f"{int(round(v)):,}".replace(",", "{,}"))


def f_pct(x) -> str:
    return sign_wrap(f"{float(x):.1f}")


def f_dec(x, k: int) -> str:
    return sign_wrap(f"{float(x):.{k}f}")


def f_num1(x) -> str:
    """One decimal with {,} thousands separators (estimated counts)."""
    return sign_wrap(f"{float(x):,.1f}".replace(",", "{,}"))


def blank(x) -> bool:
    return x is None or str(x).strip() == ""


class Sink:
    def __init__(self):
        self.rows = []
        self.names = set()
        self.skipped = []

    def add(self, name, value, src, meaning):
        assert re.fullmatch(r"\\n[A-Za-z]+", name), f"bad macro name {name}"
        assert name not in self.names, f"duplicate macro {name} ({src})"
        assert "\n" not in value and "\n" not in src
        self.names.add(name)
        self.rows.append((name, value, src, meaning))

    def n(self, name, raw, src, meaning):          # count
        self.add(name, f_int(raw), src, meaning)

    def p(self, name, raw, src, meaning):          # percentage, one decimal
        self.add(name, f_pct(raw), src, meaning)

    def d(self, name, raw, src, meaning, k=3):     # decimal
        self.add(name, f_dec(raw, k), src, meaning)

    def s(self, name, raw, src, meaning):          # string
        self.add(name, str(raw), src, meaning)


S = Sink()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def need(p: Path) -> Path:
    if not p.exists():
        sys.exit(f"MISSING INPUT: {rel(p)} (nothing written)")
    return p


def read_csv(p: Path):
    with open(need(p), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(p: Path):
    with open(need(p), encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- 1. search and screening
def do_prisma():
    pc = ROOT / "research/protocol/prisma-counts.json"
    d = read_json(pc)
    r = rel(pc)
    tot = 0
    for k, v in d["identified"].items():
        S.n(f"\\nSearchIdent{slug(k)}", v, f"{r}#identified/{k}",
            f"Records identified from source/batch {k}")
        tot += v
    S.n("\\nSearchIdentTotal", tot, f"{r}#identified (sum over sources)",
        "Records identified, all sources, before duplicate removal (sum of the per-source counts)")
    S.n("\\nSearchDup", d["duplicates_removed"], f"{r}#duplicates_removed", "Duplicates removed")
    S.n("\\nSearchUnique", d["unique"], f"{r}#unique", "Unique records after de-duplication")
    assert tot - d["duplicates_removed"] == d["unique"], "PRISMA identification does not reconcile"
    S.p("\\nSearchDupPct", 100 * d["duplicates_removed"] / tot, f"{r}#duplicates_removed/identified (computed)",
        "Duplicates as percent of records identified")

    t, a = d["screening_title"], d["screening_abstract"]
    S.n("\\nScreenTitleN", t["screened"], f"{r}#screening_title/screened", "Records screened on title")
    S.n("\\nScreenTitleExcl", t["excluded"], f"{r}#screening_title/excluded", "Excluded at title stage")
    S.n("\\nScreenTitleToStageTwo", t["to_stage2"], f"{r}#screening_title/to_stage2",
        "Passed to abstract screening")
    S.p("\\nScreenTitleExclPct", 100 * t["excluded"] / t["screened"],
        f"{r}#screening_title excluded/screened (computed)", "Percent excluded at title stage")
    S.d("\\nScreenTitleKappa", t["kappa_3class"], f"{r}#screening_title/kappa_3class",
        "Cohen kappa between the two title screeners, three classes (include/maybe/exclude)")
    S.n("\\nScreenAbsN", a["screened"], f"{r}#screening_abstract/screened", "Records screened on abstract")
    S.n("\\nScreenAbsExcl", a["excluded"], f"{r}#screening_abstract/excluded", "Excluded at abstract stage")
    S.n("\\nScreenAbsBoth", a["to_full_text_both_include"], f"{r}#screening_abstract/to_full_text_both_include",
        "Passed to full text: both screeners include")
    S.n("\\nScreenAbsDisagree", a["to_full_text_disagreement_or_maybe"],
        f"{r}#screening_abstract/to_full_text_disagreement_or_maybe",
        "Passed to full text: screeners disagree or one said maybe")
    S.p("\\nScreenAbsExclPct", 100 * a["excluded"] / a["screened"],
        f"{r}#screening_abstract excluded/screened (computed)", "Percent excluded at abstract stage")
    S.d("\\nScreenAbsKappa", a["kappa_3class"], f"{r}#screening_abstract/kappa_3class",
        "Cohen kappa between the two abstract screeners, three classes")
    S.n("\\nScreenFtInput", d["full_text_input"], f"{r}#full_text_input",
        "Records entering the full-text stage (liberal frame input)")
    assert t["to_stage2"] == a["screened"], "title->abstract counts do not reconcile"
    assert a["to_full_text_both_include"] + a["to_full_text_disagreement_or_maybe"] == d["full_text_input"]


def do_fulltext_flag() -> bool:
    p = ROOT / "data/processed/prisma-fulltext.json"
    d = read_json(p)
    r = rel(p)
    interim = bool(d.get("interim"))
    S.s("\\nInterimFlag", "interim" if interim else "final", f"{r}#interim",
        "The word 'interim' while prisma-fulltext.json has interim: true; 'final' once it is false")
    S.n("\\nFtSought", d["fulltext_sought"], f"{r}#fulltext_sought",
        "Full texts sought: analysed sample drawn for full-text reading")
    S.n("\\nFtNotRetrievable", d["fulltext_not_retrievable"], f"{r}#fulltext_not_retrievable",
        "Full texts not retrievable (no open copy)")
    S.n("\\nFtAssessed", d["fulltext_assessed"], f"{r}#fulltext_assessed", "Full texts assessed for eligibility")
    S.n("\\nFtExcluded", d["excluded_fulltext_total"], f"{r}#excluded_fulltext_total",
        "Excluded after full-text assessment")
    for k, v in d["excluded_fulltext_reasons"].items():
        S.n(f"\\nFtExclReason{slug(k)}", v, f"{r}#excluded_fulltext_reasons/{k}",
            f"Full-text exclusions with reason: {k}")
    S.n("\\nFtIncluded", d["included_rq2_rq4"], f"{r}#included_rq2_rq4",
        "Studies included in the RQ2-RQ4 analysis (Claude primary coder)")
    S.n("\\nFtPending", d["fulltext_pending_assessment"], f"{r}#fulltext_pending_assessment",
        "Full texts pending assessment")
    S.n("\\nFtUnresolved", d["fulltext_unresolved_unclear"], f"{r}#fulltext_unresolved_unclear",
        "Full texts with unresolved eligibility")
    S.p("\\nFtRetrievedPct", 100 * d["fulltext_assessed"] / d["fulltext_sought"],
        f"{r}#fulltext_assessed/fulltext_sought (computed)", "Percent of sought full texts that were retrieved and assessed")
    assert d["fulltext_assessed"] + d["fulltext_not_retrievable"] == d["fulltext_sought"]
    assert d["fulltext_assessed"] == d["included_rq2_rq4"] + d["excluded_fulltext_total"] + \
        d["fulltext_pending_assessment"] + d["fulltext_unresolved_unclear"]
    return interim


# --------------------------------------------------------------------------- 2. RQ1
VIEWS = [("A", "A", "View A (liberal frame)"), ("B", "B", "View B (coder flag = yes)"),
         ("S", "Strict", "Strict frame (sensitivity)")]


def do_rq1_tables():
    base = ROOT / "runs/rq1-tables"
    m = read_json(base / "metrics.json")
    mr = rel(base / "metrics.json")
    for v, vn, vl in VIEWS:
        S.n(f"\\nRqOneDenom{vn}", m["denominators"][v], f"{mr}#denominators/{v}", f"Denominator N, {vl}")
    for k, v in m["flag_counts_in_frame"].items():
        S.n(f"\\nRqOneFlag{slug(k)}", v, f"{mr}#flag_counts_in_frame/{k}",
            f"Records in view A with abstract-coder flag meets_criteria = {k}")

    def table(csvname, tag, tlabel, namer, pct_fmt=f_pct):
        rows = read_csv(base / csvname)
        src = rel(base / csvname)
        seen = set()
        for row in rows:
            item = row["item"]
            nm = namer(item)
            assert nm not in seen, f"duplicate item key {item}"
            seen.add(nm)
            is_den = item.startswith("N (")
            for col, vn, vl in [("A", "A", "View A"), ("B", "B", "View B"), ("S", "Strict", "Strict frame")]:
                if not blank(row[f"{col}_n"]):
                    S.n(f"\\nRqOne{tag}{nm}{vn}N", row[f"{col}_n"], f"{src}#{item}/{col}_n",
                        f"{tlabel}: {item}; count, {vl}")
                if not is_den and not blank(row.get(f"{col}_pct", "")):
                    S.p(f"\\nRqOne{tag}{nm}{vn}Pct", row[f"{col}_pct"], f"{src}#{item}/{col}_pct",
                        f"{tlabel}: {item}; percent of view denominator, {vl}")

    table("T-RQ1a.csv", "Fam", "T-RQ1a paradigm family (per record, any listed)",
          lambda it: "Denom" if it.startswith("N (") else slug(it.split(" ")[0] if it.split(" ")[0].isupper() else it))
    table("T-RQ1b.csv", "Model", "T-RQ1b model family (per record, any listed)",
          lambda it: "Denom" if it.startswith("N (") else slug(it))
    table("T-RQ1c.csv", "Attr", "T-RQ1c language, modality, human comparison, codable",
          lambda it: "Denom" if it.startswith("N (") else slug(it))

    # n_models_stated
    rows = read_csv(base / "T-RQ1b_n_models_stated.csv")
    src = rel(base / "T-RQ1b_n_models_stated.csv")
    fm = {"n stated": ("NStated", f_int), "% of N stated": ("StatedPct", f_pct),
          "median": ("Median", lambda x: f_dec(x, 1)), "Q1": ("Qone", lambda x: f_dec(x, 1)),
          "Q3": ("Qthree", lambda x: f_dec(x, 1)), "max": ("Max", f_int)}
    for row in rows:
        nm, fn = fm[row["statistic"]]
        for col, vn, vl in [("A", "A", "View A"), ("B", "B", "View B"), ("S", "Strict", "Strict frame")]:
            S.add(f"\\nRqOneModels{nm}{vn}", fn(row[col]), f"{src}#{row['statistic']}/{col}",
                  f"T-RQ1b number of models stated per record (records that state a number): {row['statistic']}, {vl}")

    # T-RQ1d: period rows (family x period) and year totals
    rows = read_csv(base / "T-RQ1d.csv")
    src = rel(base / "T-RQ1d.csv")
    fams = [c for c in rows[0].keys() if c not in ("view", "bin_type", "bin", "total")]
    vname = {"A": "A", "B": "B", "S": "Strict"}
    for row in rows:
        vn = vname[row["view"]]
        if row["bin_type"] == "period":
            b = slug(row["bin"])
            for c in fams + ["total"]:
                S.n(f"\\nRqOneTime{vn}{b}{slug(c) if c != 'total' else 'Total'}", row[c],
                    f"{src}#{row['view']}/{row['bin']}/{c}",
                    f"T-RQ1d records by first paradigm family and period: view {row['view']}, period {row['bin']}, family {c}")
            den = m["denominators"][row["view"]]
            S.p(f"\\nRqOneTime{vn}{b}Pct", 100 * int(row["total"]) / den,
                f"{src}#{row['view']}/{row['bin']}/total / {mr}#denominators (computed)",
                f"Share of view {row['view']} records published in {row['bin']}")
        else:
            S.n(f"\\nRqOneYear{vn}{slug(row['bin'])}", row["total"], f"{src}#{row['view']}/{row['bin']}/total",
                f"T-RQ1d records in year {row['bin']} (2026 is a partial year), view {row['view']}")

    # T-RQ1e top 25 names
    rows = read_csv(base / "T-RQ1e.csv")
    src = rel(base / "T-RQ1e.csv")
    for row in rows:
        rk = slug(row["rank"])
        for col, nm, lab in [("A_n_records", "AN", "view A records"), ("A_pct", "APct", "percent of view A"),
                             ("B_n_records", "BN", "view B records"), ("S_n_records", "StrictN", "strict-frame records")]:
            f = S.p if col == "A_pct" else S.n
            f(f"\\nRqOneTop{rk}{nm}", row[col], f"{src}#rank {row['rank']}/{col}",
              f"T-RQ1e rank {row['rank']} normalised paradigm name '{row['paradigm_name_normalised']}': {lab}")
    e = m["T-RQ1e"]
    S.n("\\nRqOneNamesDistinct", e["distinct_names_A"], f"{mr}#T-RQ1e/distinct_names_A",
        "Distinct normalised paradigm names in view A")
    S.n("\\nRqOneNamesOnce", e["names_once_A"], f"{mr}#T-RQ1e/names_once_A",
        "Paradigm names occurring once in view A")
    S.p("\\nRqOneNamesOncePct", 100 * e["names_once_A"] / e["distinct_names_A"],
        f"{mr}#T-RQ1e names_once_A/distinct_names_A (computed)", "Percent of distinct names occurring once in view A")

    for i, (lang, n) in enumerate(m["languages_named_view_A_top"], start=1):
        S.n(f"\\nRqOneLang{slug(str(i))}N", n, f"{mr}#languages_named_view_A_top/{i}",
            f"Rank {i} named language in view A: {lang}; records")


def do_rq1_flag_error():
    p = ROOT / "runs/fulltext-pilot/rq1-flag-crosstab.md"
    txt = need(p).read_text(encoding="utf-8")
    r = rel(p)
    m = re.search(r"Records used:\s*(\d+)\s*\(reference YES (\d+), NO (\d+)\)", txt)
    assert m, "flag crosstab: records line not found"
    S.n("\\nRqOneFlagRefN", m.group(1), f"{r}#Records used", "Records in the flag error check (reference standard)")
    S.n("\\nRqOneFlagRefYes", m.group(2), f"{r}#Records used", "Reference YES records in the flag error check")
    S.n("\\nRqOneFlagRefNo", m.group(3), f"{r}#Records used", "Reference NO records in the flag error check")
    pats = [("FalseExcl", r"False exclusions \(reference YES, flag no\)"),
            ("YesUnclear", r"Reference YES flagged unclear"),
            ("FalseIncl", r"False inclusions \(reference NO, flag yes\)"),
            ("NoUnclear", r"Reference NO flagged unclear")]
    for nm, pat in pats:
        mm = re.search(pat + r":\s*(\d+)/(\d+) = ([\d.]+) \[([\d.]+), ([\d.]+)\]", txt)
        assert mm, f"flag crosstab: {nm} not found"
        k, n, est, lo, hi = mm.groups()
        S.n(f"\\nRqOneFlag{nm}K", k, f"{r}#{nm}", f"Flag error check {nm}: records with the event")
        S.n(f"\\nRqOneFlag{nm}Den", n, f"{r}#{nm}", f"Flag error check {nm}: denominator")
        S.p(f"\\nRqOneFlag{nm}Pct", 100 * int(k) / int(n), f"{r}#{nm} (k/n computed)",
            f"Flag error check {nm}: proportion, percent")
        S.p(f"\\nRqOneFlag{nm}Lo", 100 * float(lo), f"{r}#{nm}", f"Flag error check {nm}: Wilson 95% lower, percent")
        S.p(f"\\nRqOneFlag{nm}Hi", 100 * float(hi), f"{r}#{nm}", f"Flag error check {nm}: Wilson 95% upper, percent")


def do_semantic_and_cocitation():
    base = ROOT / "runs/rq1-semantic-map"
    st = read_json(base / "stability.json")
    r = rel(base / "stability.json")
    S.n("\\nRqOneSemBoot", st["n_boot"], f"{r}#n_boot", "Bootstrap resamples for cluster stability")
    S.n("\\nRqOneSemClusters", st["n_clusters_full"], f"{r}#n_clusters_full",
        "HDBSCAN clusters in the full semantic map (main setting)")
    S.n("\\nRqOneSemUnclustered", st["n_unclustered_full"], f"{r}#n_unclustered_full",
        "Records left unclustered (noise) in the main setting")
    for key, nm, lab in [("ARI_noise_as_label", "AriNoise", "adjusted Rand index vs full map, noise as a label"),
                         ("ARI_clustered_in_both", "AriBoth", "adjusted Rand index vs full map, records clustered in both")]:
        for st_key, snm in [("median", "Median"), ("q1", "Qone"), ("q3", "Qthree"), ("min", "Min"), ("max", "Max")]:
            S.d(f"\\nRqOneSem{nm}{snm}", st[key][st_key], f"{r}#{key}/{st_key}", f"Bootstrap {lab}: {st_key}")
    for st_key, snm in [("median", "Median"), ("q1", "Qone"), ("q3", "Qthree"), ("min", "Min"), ("max", "Max")]:
        S.d(f"\\nRqOneSemBootClusters{snm}", st["n_clusters_in_bootstrap"][st_key],
            f"{r}#n_clusters_in_bootstrap/{st_key}", f"Clusters found per bootstrap resample: {st_key}", k=1)
    S.d("\\nRqOneSemBootUniqueMedian", st["unique_records_per_resample"]["median"],
        f"{r}#unique_records_per_resample/median", "Unique records per bootstrap resample: median", k=1)

    sens = read_json(base / "sensitivity.json")
    sr = rel(base / "sensitivity.json")
    for i, row in enumerate(sens, start=1):
        key = slug(f"{row['min_cluster_size']}x{row['min_samples']}")
        k = f"min_cluster_size {row['min_cluster_size']}, min_samples {row['min_samples']}"
        S.n(f"\\nRqOneSemSens{key}Clusters", row["n_clusters"], f"{sr}#{k}/n_clusters",
            f"Semantic map sensitivity ({k}): clusters")
        S.n(f"\\nRqOneSemSens{key}Unclustered", row["n_unclustered"], f"{sr}#{k}/n_unclustered",
            f"Semantic map sensitivity ({k}): unclustered records")
        S.d(f"\\nRqOneSemSens{key}Ari", row["ARI_vs_main_noise_as_label"], f"{sr}#{k}/ARI_vs_main_noise_as_label",
            f"Semantic map sensitivity ({k}): adjusted Rand index vs main setting, noise as a label")

    cl = read_csv(base / "clusters.csv")
    cr = rel(base / "clusters.csv")
    for row in cl:
        c = row["cluster"]
        nm = "Unclustered" if c == "0" else slug(c)
        lab = "unclustered records" if c == "0" else f"cluster {c} (top terms: {row['top_terms']})"
        S.n(f"\\nRqOneSemCl{nm}N", row["n"], f"{cr}#cluster {c}/n", f"Semantic map {lab}: records")
        S.p(f"\\nRqOneSemCl{nm}Pct", row["pct_of_frame"], f"{cr}#cluster {c}/pct_of_frame",
            f"Semantic map {lab}: percent of view A")
        S.p(f"\\nRqOneSemCl{nm}FlagPct", row["flag_yes_share_pct"], f"{cr}#cluster {c}/flag_yes_share_pct",
            f"Semantic map {lab}: percent with coder flag yes")
        S.d(f"\\nRqOneSemCl{nm}Year", row["median_year"], f"{cr}#cluster {c}/median_year",
            f"Semantic map {lab}: median year", k=1)

    # co-citation
    p = ROOT / "runs/rq1-cocitation/metrics.json"
    m = read_json(p)
    r = rel(p)
    cv = m["coverage"]
    S.n("\\nRqOneCoFrame", m["frame_N"], f"{r}#frame_N", "Co-citation: records in the frame")
    S.n("\\nRqOneCoCovered", m["covered_records"], f"{r}#covered_records",
        "Co-citation: records with a resolvable reference list")
    S.p("\\nRqOneCoCoveredPct", 100 * m["covered_share"], f"{r}#covered_share",
        "Co-citation: percent of the frame with a resolvable reference list")
    S.n("\\nRqOneCoArxivOnly", cv["arxiv_only"], f"{r}#coverage/arxiv_only", "Co-citation: arXiv-only records (no reference list)")
    S.n("\\nRqOneCoNoRefs", cv["openalex_no_references"], f"{r}#coverage/openalex_no_references",
        "Co-citation: OpenAlex records without references")
    S.n("\\nRqOneCoRefs", m["distinct_references"], f"{r}#distinct_references", "Co-citation: distinct references")
    S.n("\\nRqOneCoTopN", m["top_n"], f"{r}#top_n", "Co-citation: top-N references taken by citing-record count")
    S.n("\\nRqOneCoKmin", m["K_min_citing_records"], f"{r}#K_min_citing_records",
        "Co-citation: minimum citing records for a node to be selected")
    S.n("\\nRqOneCoNodesSel", m["n_nodes_selected"], f"{r}#n_nodes_selected", "Co-citation: nodes selected")
    S.n("\\nRqOneCoEdgeMin", m["edge_min_cocitation"], f"{r}#edge_min_cocitation", "Co-citation: minimum co-citations for an edge")
    S.n("\\nRqOneCoNodes", m["n_nodes_in_graph"], f"{r}#n_nodes_in_graph", "Co-citation: nodes in the drawn graph")
    S.n("\\nRqOneCoEdges", m["n_edges"], f"{r}#n_edges", "Co-citation: edges in the graph")
    S.n("\\nRqOneCoIsolated", m["isolated_nodes_dropped"], f"{r}#isolated_nodes_dropped", "Co-citation: isolated nodes dropped")
    S.n("\\nRqOneCoClusters", m["n_clusters"], f"{r}#n_clusters", "Co-citation: Louvain clusters (main seed)")
    S.d("\\nRqOneCoModularity", m["modularity"], f"{r}#modularity", "Co-citation: modularity of the main partition")
    s = m["stability"]
    S.n("\\nRqOneCoSeeds", s["n_seeds"], f"{r}#stability/n_seeds", "Co-citation: Louvain seeds in the stability check")
    S.d("\\nRqOneCoModMin", s["modularity_min"], f"{r}#stability/modularity_min", "Co-citation: minimum modularity over seeds")
    S.d("\\nRqOneCoModMax", s["modularity_max"], f"{r}#stability/modularity_max", "Co-citation: maximum modularity over seeds")
    S.n("\\nRqOneCoClustersMin", s["n_clusters_min"], f"{r}#stability/n_clusters_min", "Co-citation: fewest clusters over seeds")
    S.n("\\nRqOneCoClustersMax", s["n_clusters_max"], f"{r}#stability/n_clusters_max", "Co-citation: most clusters over seeds")
    S.d("\\nRqOneCoAriMin", s["ari_min"], f"{r}#stability/ari_min", "Co-citation: minimum pairwise adjusted Rand index over seeds")
    S.d("\\nRqOneCoAriMedian", s["ari_median"], f"{r}#stability/ari_median", "Co-citation: median pairwise adjusted Rand index over seeds")
    S.d("\\nRqOneCoAriMax", s["ari_max"], f"{r}#stability/ari_max", "Co-citation: maximum pairwise adjusted Rand index over seeds")

    ccl = read_csv(ROOT / "runs/rq1-cocitation/clusters.csv")
    ccr = "runs/rq1-cocitation/clusters.csv"
    for row in ccl:
        c = row["cluster"]
        S.n(f"\\nRqOneCoCl{slug(c)}Nodes", row["n_nodes"], f"{ccr}#cluster {c}/n_nodes",
            f"Co-citation cluster {c} (top works: {row['label_top3']}): nodes")
        S.n(f"\\nRqOneCoCl{slug(c)}Edges", row["n_internal_edges"], f"{ccr}#cluster {c}/n_internal_edges",
            f"Co-citation cluster {c}: internal edges")
        S.n(f"\\nRqOneCoCl{slug(c)}Cites", row["total_citations_of_members"], f"{ccr}#cluster {c}/total_citations_of_members",
            f"Co-citation cluster {c}: citations of member works by frame records")


# --------------------------------------------------------------------------- 3. RQ2-RQ4 interim
RQ = ROOT / __import__("os").environ.get("RQ234_RUN", "runs/rq234-interim")  # CRP-S05: RQ234_RUN=runs/rq234-final for the final run
CODERS = [("claude", "Claude"), ("codex", "Codex")]
FITEM = {
    "f1": "exact model version (and query date for API models) stated",
    "f2": "decoding temperature stated",
    "f3": "identical prompt sampled repeatedly and the number stated",
    "f4": "complete prompt text available",
    "f5": "same item in two or more wordings, results compared",
    "f6": "order of answer options varied (na if free text)",
    "f7": "two or more temperature or sampling settings compared",
    "f8": "two snapshots or generations of one vendor model line compared",
    "f9": "novel or perturbed items used against memorisation, or tested explicitly",
    "f10": "statistical test or interval reported for the model effect or model-human difference",
    "f11": "preregistration cited",
    "f12": "link to code or data given",
}


def feat_name(feature: str) -> str:
    parts = feature.split("|")[1:]            # drop the rqN prefix
    return "".join(slug(x.replace("_", " ")) for x in parts)


def feat_meaning(feature: str) -> str:
    parts = feature.split("|")
    if parts[0] == "rq4" and parts[1] in FITEM:
        return f"item {parts[1]} ({FITEM[parts[1]]}) = {parts[2]}"
    return " / ".join(parts[1:])


def prevalence(csvname, prefix, area_label, label_fn, extras=False):
    rows = read_csv(RQ / csvname)
    src = rel(RQ / csvname)
    if extras:
        bsrc = rel(RQ / "nonresponse_bounds.csv")
        bnd = {(r["coder"], r["feature"]): r for r in read_csv(RQ / "nonresponse_bounds.csv")}
    for row in rows:
        feat = row["feature"]
        nm = feat_name(feat)
        passes = row.get("passes_v012_rule", "")
        agree = (f"agreement field {row['agreement_field']}: kappa {row['kappa']}, {row['percent_agreement']}% on "
                 f"{row['n_agreement']} pairs, v0.12 rule {'pass' if passes == 'True' else 'FAIL (coder-sensitivity display, not an uncertainty interval)'}"
                 ) if passes != "" else "agreement field not assessed against the rule"
        for cp, cn in CODERS:
            k = row[f"{cp}_k"]
            if blank(k):
                continue
            base = f"\\n{prefix}{nm}{cn}"
            lab = f"{area_label}: {label_fn(feat)}; {cn}"
            S.n(base + "N", row[f"{cp}_n_domain"], f"{src}#{feat}/{cp}_n_domain", f"{lab}: eligible respondents in the domain")
            S.n(base + "K", k, f"{src}#{feat}/{cp}_k", f"{lab}: studies with the feature (unweighted)")
            S.p(base + "Est", row[f"{cp}_est_pct"], f"{src}#{feat}/{cp}_est_pct",
                f"{lab}: design-weighted share of eligible studies, percent; {agree}")
            note = row.get(f"{cp}_note", "")
            cpv = row.get(f"{cp}_cp_unweighted_pct", "")
            if "zero-variance" in note and not blank(cpv):
                mm = re.fullmatch(r"\s*([\d.]+)\s*-\s*([\d.]+)\s*", cpv)
                assert mm, f"cannot parse exact interval {cpv!r}"
                lo, hi = mm.groups()
                S.p(base + "Lo", lo, f"{src}#{feat}/{cp}_cp_unweighted_pct", f"{lab}: exact unweighted lower bound, percent (zero-variance estimate)")
                S.p(base + "Hi", hi, f"{src}#{feat}/{cp}_cp_unweighted_pct", f"{lab}: exact unweighted upper bound, percent (zero-variance estimate)")
            else:
                S.p(base + "Lo", row[f"{cp}_lo_pct"], f"{src}#{feat}/{cp}_lo_pct", f"{lab}: 95% interval lower, percent")
                S.p(base + "Hi", row[f"{cp}_hi_pct"], f"{src}#{feat}/{cp}_hi_pct", f"{lab}: 95% interval upper, percent")
            if extras:
                b = bnd[(cp, feat)]      # KeyError = a prevalence row without bounds: stop rather than skip
                S.p(base + "BoundLo", b["bound_lo_pct"], f"{bsrc}#{cp}/{feat}/bound_lo_pct",
                    f"{lab}: nonresponse lower bound, percent (v0.9.1; unknown-status records ineligible, or eligible without the outcome)")
                S.p(base + "BoundHi", b["bound_hi_pct"], f"{bsrc}#{cp}/{feat}/bound_hi_pct",
                    f"{lab}: nonresponse upper bound, percent (v0.9.1; unknown-status records ineligible, or eligible with the outcome)")
                if passes != "":
                    S.s(base + "Pass", "pass" if passes == "True" else "fail", f"{src}#{feat}/passes_v012_rule",
                        f"{lab}: inter-coder agreement of the governing field under the v0.12 rule ({row['agreement_field']}: pass or fail)")


def do_rq234():
    prevalence("rq2.csv", "RqTwo", "RQ2 share of eligible studies with at least one row of the label",
               lambda f: " / ".join(f.split("|")[1:]))
    prevalence("rq3.csv", "RqThree", "RQ3 comparison basis", lambda f: " / ".join(f.split("|")[1:]), extras=True)
    prevalence("rq4.csv", "RqFour", "RQ4 reporting item or robustness check", feat_meaning, extras=True)
    do_paired_and_zero()

    # RQ2 rows by family (descriptive counts)
    rows = read_csv(RQ / "rq2-rows-by-family.csv")
    src = rel(RQ / "rq2-rows-by-family.csv")
    tot = {}
    for row in rows:
        cn = row["coder"].capitalize()
        nm = f"\\nRqTwoRows{cn}{slug(row['outcome_kind'])}{slug(row['derived_label'].replace('-', ' '))}{slug(row['paradigm_family'])}"
        S.n(nm, row["rows"], f"{src}#{row['coder']}/{row['outcome_kind']}/{row['derived_label']}/{row['paradigm_family']}",
            f"RQ2 unweighted rows ({row['coder']}): outcome kind {row['outcome_kind']}, label {row['derived_label']}, paradigm family {row['paradigm_family']}")
        key = (cn, row["outcome_kind"])
        tot[key] = tot.get(key, 0) + int(row["rows"])
    for (cn, kind), v in sorted(tot.items()):
        S.n(f"\\nRqTwoRows{cn}{slug(kind)}Total", v, f"{src}#{cn.lower()}/{kind} (sum of rows)",
            f"RQ2 unweighted rows ({cn.lower()}), outcome kind {kind}, all labels and families")

    # human sample size
    hn = read_json(RQ / "rq3-human-n.json")
    hr = rel(RQ / "rq3-human-n.json")
    for cp, cn in CODERS:
        for grp, gl in [("all_reported", "AllReported"), ("primary_type_own_sample", "OwnSample")]:
            g = hn[cp][grp]
            S.n(f"\\nRqThreeHumanN{cn}{gl}K", g["n"], f"{hr}#{cp}/{grp}/n", f"Studies reporting a human sample size ({cp}, {grp})")
            for key, nm in [("min", "Min"), ("q1", "Qone"), ("median", "Median"), ("q3", "Qthree"), ("max", "Max"),
                            ("weighted_median_point_only", "WeightedMedian")]:
                S.add(f"\\nRqThreeHumanN{cn}{gl}{nm}", f_int(g[key]) if float(g[key]).is_integer() else f_num1(g[key]),
                      f"{hr}#{cp}/{grp}/{key}",
                      f"Reported human sample size ({cp}, {grp}): {key}" + (" (point value only, no interval)" if key.startswith("weighted") else ""))

    # trend sensitivity (descriptive; no trend claimed)
    rows = read_csv(RQ / "rq4_trend.csv")
    src = rel(RQ / "rq4_trend.csv")
    nfit = {}
    for row in rows:
        cn = row["coder"].capitalize()
        if row["status"] != "fitted":
            continue
        nfit[cn] = nfit.get(cn, 0) + 1
        nm = f"\\nRqFourTrend{feat_name(row['feature'])}{cn}"
        lab = f"RQ4 sensitivity trend per publication year ({row['coder']}): {feat_meaning(row['feature'])}"
        S.d(nm + "Or", row["OR_per_year"], f"{src}#{row['coder']}/{row['feature']}/OR_per_year", f"{lab}; odds ratio per year (sensitivity analysis, no trend claimed)", k=2)
        S.d(nm + "Lo", row["or_lo"], f"{src}#{row['coder']}/{row['feature']}/or_lo", f"{lab}; 95% interval lower", k=2)
        S.d(nm + "Hi", row["or_hi"], f"{src}#{row['coder']}/{row['feature']}/or_hi", f"{lab}; 95% interval upper", k=2)
    for cn, v in nfit.items():
        S.n(f"\\nRqFourTrendFitted{cn}", v, f"{src}#{cn.lower()}/status=fitted (count)", f"RQ4 trend models fitted ({cn.lower()})")
    rows = read_csv(RQ / "trend_descriptive_only.csv")
    src = rel(RQ / "trend_descriptive_only.csv")
    cnt = {}
    for row in rows:
        cnt[row["coder"].capitalize()] = cnt.get(row["coder"].capitalize(), 0) + 1
    for cn, v in cnt.items():
        S.n(f"\\nRqFourTrendDescOnly{cn}", v, f"{src}#{cn.lower()} (row count)",
            f"RQ4 features below the 10 events / 10 non-events trend minimum ({cn.lower()}); descriptive only")

    # merge sensitivity (all estimands, key stats)
    rows = read_csv(RQ / "sensitivity_merge.csv")
    src = rel(RQ / "sensitivity_merge.csv")
    for row in rows:
        feat = row["feature"]
        cn = row["coder"].capitalize()
        if feat == "ELIGIBLE_SHARE":
            area, nm, lab = "Ft", "EligShare", "eligible share of the frame"
        elif feat.startswith("rq2"):
            area, nm, lab = "RqTwo", feat_name(feat), f"RQ2 {feat_meaning(feat)}"
        elif feat.startswith("rq4"):
            area, nm, lab = "RqFour", feat_name(feat), f"RQ4 {feat_meaning(feat)}"
        else:
            raise AssertionError(feat)
        if row["merged_est_pct"] == "":
            continue
        b = f"\\n{area}Merge{nm}{cn}"
        pre = f"Merged-strata sensitivity ({row['coder']}), {lab}"
        S.p(b + "Est", row["merged_est_pct"], f"{src}#{row['coder']}/{feat}/merged_est_pct", f"{pre}: estimate, percent")
        S.p(b + "Lo", row["merged_lo_pct"], f"{src}#{row['coder']}/{feat}/merged_lo_pct", f"{pre}: 95% interval lower, percent")
        S.p(b + "Hi", row["merged_hi_pct"], f"{src}#{row['coder']}/{feat}/merged_hi_pct", f"{pre}: 95% interval upper, percent")
        S.p(b + "Diff", row["diff_est_pct_points"], f"{src}#{row['coder']}/{feat}/diff_est_pct_points",
            f"{pre}: merged minus original estimate, percentage points")
        if not blank(row["ci_width_ratio_merged_over_orig"]):
            S.d(b + "WidthRatio", row["ci_width_ratio_merged_over_orig"], f"{src}#{row['coder']}/{feat}/ci_width_ratio_merged_over_orig",
                f"{pre}: interval width merged over original", k=2)


def do_paired_and_zero():
    """Paired like-for-like contrasts (descriptive, no test) and exact zero-event upper bounds."""
    rows = read_csv(RQ / "paired_contrasts.csv")
    src = rel(RQ / "paired_contrasts.csv")
    for r in rows:
        cn, cp = r["coder"].capitalize(), r["coder"]
        base = f"\\nPair{slug(r['contrast'])}{cn}"
        key = f"{cp}/{r['contrast']}"
        pre = f"Paired contrast ({cp}), {r['contrast']} (item A minus item B, same eligible studies; descriptive, no test)"
        S.n(base + "N", r["n_domain"], f"{src}#{key}/n_domain", f"{pre}: eligible studies")
        S.n(base + "Both", r["n_both"], f"{src}#{key}/n_both", f"{pre}: studies with both items (unweighted)")
        S.n(base + "AOnly", r["n_a_only"], f"{src}#{key}/n_a_only", f"{pre}: studies with item A only (unweighted)")
        S.n(base + "BOnly", r["n_b_only"], f"{src}#{key}/n_b_only", f"{pre}: studies with item B only (unweighted)")
        S.p(base + "AEst", r["a_est_pct"], f"{src}#{key}/a_est_pct", f"{pre}: item A design-weighted prevalence, percent")
        S.p(base + "BEst", r["b_est_pct"], f"{src}#{key}/b_est_pct", f"{pre}: item B design-weighted prevalence, percent")
        S.p(base + "Diff", r["diff_a_minus_b_pct_points"], f"{src}#{key}/diff_a_minus_b_pct_points", f"{pre}: difference A minus B, percentage points")
        S.p(base + "Lo", r["diff_lo_pct"], f"{src}#{key}/diff_lo_pct", f"{pre}: 95% interval of the difference, lower, percentage points")
        S.p(base + "Hi", r["diff_hi_pct"], f"{src}#{key}/diff_hi_pct", f"{pre}: 95% interval of the difference, upper, percentage points")
        S.p(base + "BoundLo", r["nr_bound_lo_pct"], f"{src}#{key}/nr_bound_lo_pct", f"{pre}: worst-case nonresponse lower bound of the difference, percentage points")
        S.p(base + "BoundHi", r["nr_bound_hi_pct"], f"{src}#{key}/nr_bound_hi_pct", f"{pre}: worst-case nonresponse upper bound of the difference, percentage points")
        S.s(base + "Pass", "pass" if r["both_items_pass_v012_rule"] == "True" else "fail", f"{src}#{key}/both_items_pass_v012_rule",
            f"{pre}: both underlying fields pass the v0.12 inter-coder rule (pass) or at least one fails (fail)")
    rows = read_csv(RQ / "zero_event_bounds.csv")
    src = rel(RQ / "zero_event_bounds.csv")
    area = {"rq2": "RqTwo", "rq3": "RqThree", "rq4": "RqFour"}
    for r in rows:
        cn, cp = r["coder"].capitalize(), r["coder"]
        base = f"\\nZeroEvt{area[r['feature'].split('|')[0]]}{feat_name(r['feature'])}{cn}"
        key = f"{cp}/{r['feature']}"
        pre = f"Zero events among eligible studies ({cp}), {r['feature']}"
        S.n(base + "N", r["n_domain"], f"{src}#{key}/n_domain", f"{pre}: eligible studies in the domain")
        S.p(base + "Hi", r["upper_cp_pct"], f"{src}#{key}/upper_cp_pct", f"{pre}: exact Clopper-Pearson 95% upper limit, unweighted, percent")
        S.p(base + "HiNeff", r["upper_cp_neff_pct"], f"{src}#{key}/upper_cp_neff_pct",
            f"{pre}: same limit with n replaced by the Kish effective sample size (sensitivity, approximation), percent")


def do_rq2_generation():
    """RQ2 rows by model generation: unweighted counts, descriptive only (no test, no weights, no interval)."""
    gen_word = {"G1": "GOne", "G2": "GTwo", "G3": "GThree", "unknown": "Unknown"}
    gen_text = {"G1": "G1 (pre-instruction-era and early instruction models)", "G2": "G2 (2023-era chat models)",
                "G3": "G3 (2024 and later)", "unknown": "unknown generation (no rule applies)"}
    summ = read_json(RQ / "rq2_generation_summary.json")
    ss = rel(RQ / "rq2_generation_summary.json")
    for cp, cn in CODERS:
        s = summ[cp]
        S.n(f"\\nRqTwoGen{cn}TotalRows", s["rows"], f"{ss}#{cp}/rows", f"RQ2 effect rows ({cp}), all outcome kinds, unweighted")
        S.n(f"\\nRqTwoGen{cn}TotalStudies", s["studies"], f"{ss}#{cp}/studies", f"Studies with at least one RQ2 effect row ({cp}), unweighted")
        for g, w in gen_word.items():
            S.n(f"\\nRqTwoGen{cn}Total{w}Rows", s["rows_per_generation"][g], f"{ss}#{cp}/rows_per_generation/{g}",
                f"RQ2 effect rows ({cp}) in {gen_text[g]}, all outcome kinds, unweighted count (descriptive only)")
            S.n(f"\\nRqTwoGen{cn}Total{w}Studies", s["studies_per_generation"][g], f"{ss}#{cp}/studies_per_generation/{g}",
                f"Studies with at least one RQ2 row in {gen_text[g]} ({cp}); a study can count in several generations, so not additive")
            S.n(f"\\nRqTwoGen{cn}NameOnly{w}Rows", s["rows_per_generation_name_rule_only"][g],
                f"{ss}#{cp}/rows_per_generation_name_rule_only/{g}",
                f"Sensitivity: RQ2 effect rows ({cp}) in {gen_text[g]} if the model name rule alone assigned the generation (release_date ignored)")
        S.p(f"\\nRqTwoGen{cn}UnknownShare", 100 * s["unknown_share"], f"{ss}#{cp}/unknown_share",
            f"Share of RQ2 effect rows ({cp}) with unknown model generation, percent of all rows (unweighted)")
        S.n(f"\\nRqTwoGen{cn}ReleaseDateRows", s["rows_by_source"].get("release_date", 0), f"{ss}#{cp}/rows_by_source/release_date",
            f"RQ2 effect rows ({cp}) whose generation came from the extractor's stated release year")
        S.n(f"\\nRqTwoGen{cn}ReleaseDateDisagree", s["release_date_rows_disagreeing_with_name_rule"],
            f"{ss}#{cp}/release_date_rows_disagreeing_with_name_rule",
            f"RQ2 effect rows ({cp}) where both exist and the stated release year gives a different generation from the name rule (diagnostic only; the name rule is used)")
    rows = read_csv(RQ / "rq2_by_generation.csv")
    src = rel(RQ / "rq2_by_generation.csv")
    for row in rows:
        cn = row["coder"].capitalize()
        w = gen_word[row["generation"]]
        lab = "All" if row["derived_label"] == "ALL" else slug(row["derived_label"].replace("-", " "))
        nm = f"\\nRqTwoGen{cn}{slug(row['outcome_kind'])}{lab}{w}"
        key = f"{row['coder']}/{row['outcome_kind']}/{row['derived_label']}/{row['generation']}"
        what = (f"RQ2 ({row['coder']}), outcome kind {row['outcome_kind']}, label {row['derived_label']}, {gen_text[row['generation']]}")
        S.n(nm + "Rows", row["rows"], f"{src}#{key}/rows", f"{what}: unweighted effect rows (descriptive only)")
        S.n(nm + "Studies", row["studies"], f"{src}#{key}/studies", f"{what}: studies with at least one such row (not additive across generations)")


def do_eligibility_and_nonresponse():
    rows = read_csv(RQ / "eligibility-estimates.csv")
    src = rel(RQ / "eligibility-estimates.csv")
    for row in rows:
        cp, cn = row["coder"], row["coder"].capitalize()
        pre = f"Eligible share of the frame ({cp})"
        for col, nm, f, lab in [
            ("n_analysed", "Analysed", S.n, "records analysed"),
            ("n_respondents", "Resp", S.n, "respondents (full text obtained)"),
            ("n_eligible_respondents", "EligResp", S.n, "eligible respondents"),
            ("n_unknown_status", "Unknown", S.n, "records with unknown status (no full text)"),
            ("est_share_of_frame_pct", "Est", S.p, "design-weighted eligible share, percent"),
            ("lo_pct", "Lo", S.p, "95% interval lower, percent"),
            ("hi_pct", "Hi", S.p, "95% interval upper, percent"),
            ("bound_all_unknown_ineligible_pct", "BoundLo", S.p, "bound if every unknown-status record is ineligible, percent"),
            ("bound_all_unknown_eligible_pct", "BoundHi", S.p, "bound if every unknown-status record is eligible, percent"),
        ]:
            f(f"\\nFtElig{nm}{cn}", row[col], f"{src}#{cp}/{col}", f"{pre}: {lab}")
        S.add(f"\\nFtEligNHat{cn}", f_num1(row["N_hat_eligible"]), f"{src}#{cp}/N_hat_eligible",
              f"{pre}: estimated number of eligible records in the frame (point estimate)")
        S.n(f"\\nFtFrame{cn}", row["frame_N"], f"{src}#{cp}/frame_N", "Frame size (liberal-eligible records)")

    allrows = read_csv(RQ / "eligibility.csv")
    src = rel(RQ / "eligibility.csv")
    tot = [r for r in allrows if r["stratum"] == "TOTAL"]
    assert len(tot) == 1, "eligibility.csv needs exactly one TOTAL row"
    tot = tot[0]
    rows = [r for r in allrows if r["stratum"] != "TOTAL"]
    S.n("\\nFtStrata", len(rows), f"{src}#row count excluding TOTAL", "Strata (paradigm family x period) in the sampling design")
    for col, nm, lab in [("n_analysed", "Analysed", "records analysed"), ("n_full_text", "FullText", "full texts obtained"),
                         ("n_no_open_copy", "NoOpenCopy", "no open copy"), ("N_h", "FrameN", "frame records")]:
        assert int(float(tot[col])) == sum(int(float(r[col])) for r in rows), f"TOTAL row disagrees with strata for {col}"
        S.n(f"\\nFtTot{nm}", tot[col], f"{src}#TOTAL/{col}", f"All strata: {lab}")
    for cp, cn in CODERS:
        for col, nm, lab in [("eligible", "Elig", "coded eligible"), ("ineligible", "Inelig", "coded ineligible"),
                             ("unclear", "Unclear", "coded unclear"), ("pending_extraction", "Pending", "pending extraction")]:
            assert int(float(tot[f"{cp}_{col}"])) == sum(int(float(r[f"{cp}_{col}"])) for r in rows)
            S.n(f"\\nFtTot{nm}{cn}", tot[f"{cp}_{col}"], f"{src}#TOTAL/{cp}_{col}", f"All strata ({cp}): {lab}")
        S.p(f"\\nFtTotIneligRate{cn}", 100 * float(tot[f"{cp}_ineligibility_rate"]), f"{src}#TOTAL/{cp}_ineligibility_rate",
            f"Unweighted ineligibility rate among analysed records with a full text ({cp}), percent")

    # nonresponse.md tables (no CSV exists for them): response counts and Wilson intervals; permutation p NOT read
    p = RQ / "nonresponse.md"
    txt = need(p).read_text(encoding="utf-8")
    r = rel(p)
    sections = re.split(r"\n## ", txt)
    want = {"By flag": "Flag", "By paradigm family": "Fam", "By year": "Year", "By venue type": "Venue"}
    found = set()
    for sec in sections:
        head = sec.split("\n", 1)[0]
        tag = next((v for k, v in want.items() if head.startswith(k)), None)
        if not tag:
            continue
        found.add(tag)
        for line in sec.splitlines():
            if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 6 or not re.fullmatch(r"\d+", cells[1]):
                continue
            label = cells[0]
            mm = re.fullmatch(r"([\d.]+) to ([\d.]+)", cells[5])
            assert mm, f"nonresponse interval not parsed: {cells[5]}"
            nm = slug(label.replace("<=", "upto "))
            pre = f"Nonresponse by {head.lower()}: {label}"
            S.n(f"\\nFtResp{tag}{nm}Analysed", cells[1], f"{r}#{head}/{label}/analysed", f"{pre}; records analysed")
            S.n(f"\\nFtResp{tag}{nm}Got", cells[2], f"{r}#{head}/{label}/respondents", f"{pre}; respondents (full text obtained)")
            S.p(f"\\nFtResp{tag}{nm}Pct", cells[4], f"{r}#{head}/{label}/response %", f"{pre}; response rate, percent")
            S.p(f"\\nFtResp{tag}{nm}Lo", mm.group(1), f"{r}#{head}/{label}/Wilson", f"{pre}; Wilson 95% lower, percent")
            S.p(f"\\nFtResp{tag}{nm}Hi", mm.group(2), f"{r}#{head}/{label}/Wilson", f"{pre}; Wilson 95% upper, percent")
    assert found == set(want.values()), f"nonresponse sections missing: {set(want.values()) - found}"


# --------------------------------------------------------------------------- 4. agreement
def kappa_val(x):
    return None if blank(x) else float(x)


def do_agreement():
    rows = read_csv(RQ / "agreement.csv")
    src = rel(RQ / "agreement.csv")
    for row in rows:
        nm = f"\\nAgreeInterim{slug(row['field'].replace('_', ' '))}"
        lab = f"Claude vs Codex agreement, {row['field']} ({row['level']})"
        if nm + "N" in S.names:
            nm = nm + slug(row["level"])
        key = f"{row['field']}/{row['level']}"
        S.n(nm + "N", row["n"], f"{src}#{key}/n", f"{lab}: units compared")
        S.p(nm + "Pct", row["percent_agreement"], f"{src}#{key}/percent_agreement", f"{lab}: percent agreement")
        kv = kappa_val(row["kappa"])
        if kv is None:
            S.s(nm + "Kappa", "NA", f"{src}#{key}/kappa", f"{lab}: kappa undefined (no variation); v0.12 rule basis {row['rule_basis']}, pass={row['passes_v012_rule']}")
        else:
            S.d(nm + "Kappa", kv, f"{src}#{key}/kappa", f"{lab}: Cohen kappa; v0.12 rule basis {row['rule_basis']}, pass={row['passes_v012_rule']}")

    for rdir, tag, lab in [("round1", "ExtOne", "extraction pilot round 1"),
                           ("round2-fresh", "ExtTwoFresh", "extraction pilot round 2, fresh records"),
                           ("round2-combined", "ExtTwoComb", "extraction pilot round 2, combined")]:
        p = ROOT / "runs/extraction-pilot" / rdir / "kappa.csv"
        rows = read_csv(p)
        src = rel(p)
        for row in rows:
            nm = f"\\nAgree{tag}{slug(row['field'].replace('_', ' '))}"
            key = f"{row['field']}"
            pre = f"{lab}, {row['field']} ({row['level']})"
            S.n(nm + "N", row["n"], f"{src}#{key}/n", f"{pre}: units compared")
            S.p(nm + "Pct", 100 * float(row["agreement"]), f"{src}#{key}/agreement", f"{pre}: percent agreement (file stores a fraction)")
            kv = kappa_val(row["kappa"])
            if kv is None:
                S.s(nm + "Kappa", "NA", f"{src}#{key}/kappa", f"{pre}: kappa undefined (no variation)")
            else:
                S.d(nm + "Kappa", kv, f"{src}#{key}/kappa", f"{pre}: Cohen kappa")


# --------------------------------------------------------------------------- 5. pilot side-by-side
PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]


def truth(x):
    return str(x).strip() == "True"


def do_pilot():
    base = ROOT / "runs/pilot-side-by-side"
    for tfile, tag, lab in [("table_a1.csv", "AOne", "A1 (preregistered, primary)"),
                            ("table_a2.csv", "ATwo", "A2 (post-results, not preregistered)")]:
        rows = read_csv(base / tfile)
        src = rel(base / tfile)
        models = sorted({r["model"] for r in rows})
        assert len(rows) == len(models) * len(PARADIGMS), "pilot grid is not complete"
        if tag == "AOne":
            S.n("\\nPilotModels", len(models), f"{src}#distinct model", "Open models in the pilot")
            S.n("\\nPilotParadigms", len(PARADIGMS), f"{src}#distinct paradigm", "Many Labs 1 effects in the pilot")
            S.n("\\nPilotGrids", len(rows), f"{src}#row count", "Model x paradigm grids")
            ks = {r["human_k"] for r in rows}
            assert len(ks) == 1
            S.n("\\nPilotHumanSites", int(float(ks.pop())), f"{src}#human_k", "Many Labs 1 sites per paradigm on the human side")
            S.n("\\nPilotLowValidityGrids", sum(truth(r["low_validity_overall"]) for r in rows), f"{src}#low_validity_overall (count True)",
                "Grids whose overall response validity is below 0.80")
            S.n("\\nPilotSTwoPositive", sum(truth(r["llm_S2_lower_gt0"]) for r in rows), f"{src}#llm_S2_lower_gt0 (count True)",
                "Grids whose S-squared interval lower bound exceeds 0 (factor shares reportable)")
            S.n("\\nPilotHumanSIncludesZero", sum(truth(r["human_S_interval_includes_0"]) for r in rows),
                f"{src}#human_S_interval_includes_0 (count True)", "Grids whose human spread interval includes 0")
        groups = [(p, [r for r in rows if r["paradigm"] == p]) for p in PARADIGMS] + [("All", rows)]
        for pname, g in groups:
            pk = "All" if pname == "All" else slug(pname)
            pl = "all 42 grids" if pname == "All" else f"paradigm {pname}"
            b = f"\\nPilot{tag}{pk}"
            ro = [r["rule_outcome"] for r in g]
            sv = [r["spread_vs_human"] for r in g]
            ags = [truth(r["sign_agrees_with_human"]) for r in g]
            exc = [truth(r["llm_mu_ci_excludes_0"]) for r in g]
            for key, val, mean in [
                ("Grids", len(g), "grids (models)"),
                ("Stable", ro.count("stable"), "grids labelled stable by the preregistered rule"),
                ("Fragile", ro.count("fragile"), "grids labelled fragile by the preregistered rule"),
                ("Neither", ro.count("neither"), "grids labelled neither stable nor fragile"),
                ("SignAgree", sum(ags), "grids whose point sign of the LLM mean effect equals the human sign"),
                ("SignAgreeCiExclZero", sum(a and e for a, e in zip(ags, exc)), "grids with sign agreement and the 95% interval of the LLM mean effect excluding 0"),
                ("SpreadLarger", sum(v == "larger" for v in sv), "grids where the LLM spread interval lies above the human spread interval (non-overlapping; names two sources: prompt perturbation vs site and sample differences)"),
                ("SpreadSmaller", sum(v == "smaller" for v in sv), "grids where the LLM spread interval lies below the human spread interval (non-overlapping)"),
                ("SpreadOverlap", sum(v.startswith("no statement") for v in sv), "grids where the LLM and human spread intervals overlap (no statement)"),
            ]:
                S.n(b + key, val, f"{src}#{pname}/{'rule_outcome' if key in ('Stable','Fragile','Neither') else 'columns'} (count)",
                    f"Pilot {lab}, {pl}: {mean}")
            assert len(g) == ro.count("stable") + ro.count("fragile") + ro.count("neither")
            assert len(g) == sum(v == "larger" for v in sv) + sum(v == "smaller" for v in sv) + sum(v.startswith("no statement") for v in sv)


def do_pilot_nd():
    """Near-deterministic split of the pilot variance shares: counts of grids, descriptive over cells."""
    p = ROOT / "runs/pilot-nd-split/summary.csv"
    src = rel(p)
    for r in read_csv(p):
        tag = {"A1": "AOne", "A2": "ATwo"}[r["scale"]]
        lab = {"A1": "A1 (preregistered, primary)", "A2": "A2 (post-results, not preregistered)"}[r["scale"]]
        for col, nm, mean in [
            ("grids", "Grids", "model x paradigm grids"),
            ("grids_nd_flagged", "GridsNd", "grids with a near-deterministic flag on any cell"),
            ("reportable", "Reportable", "grids with reportable factor shares (S-squared lower bound above 0)"),
            ("reportable_nd", "ReportableNd", "reportable grids with a near-deterministic flag"),
            ("reportable_not_nd", "ReportableNotNd", "reportable grids without a near-deterministic flag"),
            ("wording_dominated", "WordDom", "reportable grids with a wording share of 0.5 or more"),
            ("wording_dominated_nd", "WordDomNd", "wording-dominated grids with a near-deterministic flag"),
            ("wording_dominated_not_nd", "WordDomNotNd", "wording-dominated grids without a near-deterministic flag"),
        ]:
            S.n(f"\\nPilotNd{tag}{nm}", r[col], f"{src}#{r['scale']}/{col}",
                f"Pilot ND split {lab}: {mean} (descriptive over cells; shares are not variance components)")


# --------------------------------------------------------------------------- CRP-S04 B1, B3, B8 (added 2026-10-17)
def do_calibration():
    """B1: calibration of the stable / fragile rule against a zero-spread human-replica model (runs/pilot-rule-calibration)."""
    base = ROOT / "runs/pilot-rule-calibration"
    sm = read_csv(base / "summary.csv")
    src = rel(base / "summary.csv")
    cfg = read_json(base / "config.json")
    S.n("\\nCalReps", cfg["reps"], f"{rel(base / 'config.json')}#reps", "Monte-Carlo replicates per paradigm and variant in the rule calibration")
    S.n("\\nCalNPerArm", cfg["n_per_arm"], f"{rel(base / 'config.json')}#n_per_arm", "Responses per arm and cell in the rule calibration (pilot design)")
    for r in sm:
        p, v = r["paradigm"], r["variant"]
        tag = f"\\nCal{slug(p)}" + ("Emp" if v == "empirical" else "")
        lab = f"rule calibration {p}" + (" (empirical response shapes)" if v == "empirical" else " (normal responses; P1 binomial)")
        key = f"{src}#{p}/{v}"
        S.n(tag + "Cells", r["cells"], key + "/cells", f"{lab}: cells per grid")
        S.p(tag + "Fragile", 100 * float(r["P_fragile"]), key + "/P_fragile", f"{lab}: percent of replicates labelled fragile for a zero-spread model with the human pooled effect")
        S.p(tag + "FragileSe", 100 * float(r["P_fragile_se"]), key + "/P_fragile_se", f"{lab}: Monte-Carlo standard error of that percentage (percentage points)")
        S.p(tag + "Stable", 100 * float(r["P_stable"]), key + "/P_stable", f"{lab}: percent labelled stable")
        S.p(tag + "Neither", 100 * float(r["P_neither"]), key + "/P_neither", f"{lab}: percent labelled neither")
        S.d(tag + "MeanSigma", r["mean_sigma"], key + "/mean_sigma", f"{lab}: mean sign stability sigma")
        S.p(tag + "SigmaClause", 100 * float(r["P_sigma_lt_06"]), key + "/P_sigma_lt_06", f"{lab}: percent with sigma below 0.6")
        S.p(tag + "RangeClause", 100 * float(r["P_range_clause"]), key + "/P_range_clause", f"{lab}: percent with dbar-2S and dbar+2S on opposite sides of zero")
    hs = read_csv(base / "human_sites.csv")
    hsrc = rel(base / "human_sites.csv")
    for r in hs:
        p = r["paradigm"]
        tag = f"\\nCalHuman{slug(p)}"
        S.n(tag + "SitesAboveZero", r["n_sites_ci_above0"], f"{hsrc}#{p}/n_sites_ci_above0", f"Human ML1 {p}: sites whose 95% interval lies above 0")
        S.d(tag + "Sigma", r["sigma"], f"{hsrc}#{p}/sigma", f"Human ML1 {p}: sign stability of the 36 sites")
        S.s(tag + "Label", r["rule_table_a1"], f"{hsrc}#{p}/rule_table_a1", f"Human ML1 {p}: label of the preregistered rule with sites as cells (S^H and its upper bound from table_a1)")
        assert r["rule_table_a1"] == r["rule_moment"], (p, r["rule_table_a1"], r["rule_moment"])
    S.n("\\nCalHumanSites", hs[0]["k_sites"], f"{hsrc}#k_sites", "Human ML1 sites used as cells")
    for lab_ in ("fragile", "stable", "neither"):
        S.n(f"\\nCalHuman{lab_.capitalize()}Paradigms", sum(r["rule_table_a1"] == lab_ for r in hs), f"{hsrc}#rule_table_a1 (count)",
            f"Paradigms (of 7) whose 36 human sites are labelled {lab_} by the preregistered rule")
    cl = read_csv(base / "clause_split.csv")
    csrc = rel(base / "clause_split.csv")
    fr = [r for r in cl if r["rule_outcome"] == "fragile"]
    S.n("\\nCalObsFragile", len(fr), f"{csrc}#rule_outcome (count fragile)", "Observed A1 grids labelled fragile")
    S.n("\\nCalObsGrids", len(cl), f"{csrc}#row count", "Observed A1 grids")
    for c_, nm in (("sigma only", "SigmaOnly"), ("range only", "RangeOnly"), ("both", "Both")):
        S.n(f"\\nCalClause{nm}", sum(r["clause"] == c_ for r in fr), f"{csrc}#clause (fragile grids)", f"Fragile grids by rule clause: {c_}")
    f12 = [r for r in fr if r["paradigm"] in ("P1", "P2a", "P2b", "P2c", "P2d")]
    f34 = [r for r in fr if r["paradigm"] in ("P3", "P4")]
    S.n("\\nCalObsFragilePOneToTwo", len(f12), f"{csrc}#paradigm in P1,P2a-d", "Fragile grids among the 30 P1 and P2a-d grids")
    S.n("\\nCalObsGridsPOneToTwo", sum(r["paradigm"] in ("P1", "P2a", "P2b", "P2c", "P2d") for r in cl), f"{csrc}#paradigm in P1,P2a-d", "Grids for P1 and P2a-d")
    S.n("\\nCalObsFragilePThreeFour", len(f34), f"{csrc}#paradigm in P3,P4", "Fragile grids among the 12 P3 and P4 grids")
    S.n("\\nCalObsGridsPThreeFour", sum(r["paradigm"] in ("P3", "P4") for r in cl), f"{csrc}#paradigm in P3,P4", "Grids for P3 and P4")
    hi = read_csv(base / "sigma_ge_09.csv")
    hsrc2 = rel(base / "sigma_ge_09.csv")
    S.n("\\nCalSigmaHighGrids", len(hi), f"{hsrc2}#row count", "Grids with sign stability of 0.9 or more")
    S.n("\\nCalSigmaHighFragile", sum(r["rule_outcome"] == "fragile" for r in hi), f"{hsrc2}#rule_outcome", "Grids with sigma 0.9 or more that the rule labels fragile")
    S.n("\\nCalSigmaHighFragileRangeOnly", sum(r["rule_outcome"] == "fragile" and r["clause"] == "range only" for r in hi), f"{hsrc2}#clause",
        "Grids with sigma 0.9 or more that are fragile through the range clause alone")
    S.n("\\nCalSigmaHighStable", sum(r["rule_outcome"] == "stable" for r in hi), f"{hsrc2}#rule_outcome", "Grids with sigma 0.9 or more that the rule labels stable")


def do_placement():
    """B3: placement of the model spread against the human interval, sensitivity analyses (runs/pilot-placement-sensitivity)."""
    base = ROOT / "runs/pilot-placement-sensitivity"
    rows = read_csv(base / "placement_counts.csv")
    src = rel(base / "placement_counts.csv")
    keys = [("original", "Orig", "all grids, response format kept (as in the paper)"),
            ("(a) grids without", "NoNd", "grids without near-deterministic cells, response format kept"),
            ("(a') grids with", "WithNd", "grids with near-deterministic cells, response format kept"),
            ("(b) F0 cells only (F removed), all", "FZero", "format F0 cells only (8 or 16 cells), all grids"),
            ("(b) F0 cells only, grids without", "FZeroNoNd", "format F0 cells only, grids without near-deterministic cells"),
            ("(b') F1 cells only (F removed), all", "FOne", "format F1 cells only (8 or 16 cells), all grids"),
            ("(b') F1 cells only, grids without", "FOneNoNd", "format F1 cells only, grids without near-deterministic cells")]
    for prefix, tag, lab in keys:
        m = [r for r in rows if r["analysis"].startswith(prefix)]
        assert len(m) == 1, (prefix, len(m))
        r = m[0]
        for col, nm in (("n_grids", "Grids"), ("larger", "Larger"), ("overlap", "Overlap"), ("smaller", "Smaller")):
            S.n(f"\\nPlace{tag}{nm}", r[col], f"{src}#{r['analysis']}/{col}", f"Placement sensitivity, {lab}: {nm.lower()} (LLM spread interval vs human interval)")
        assert int(r["n_grids"]) == int(r["larger"]) + int(r["overlap"]) + int(r["smaller"])


def do_design():
    """B8: design weights, Kish effective sample sizes and unweighted counts beside the weighted shares (runs/rq234-design-diagnostics)."""
    base = ROOT / "runs/rq234-design-diagnostics"
    ds = read_csv(base / "design_summary.csv")
    src = rel(base / "design_summary.csv")
    for r in ds:
        c = r["coder"].capitalize()
        for col, nm, mean, fn in [
            ("n_respondents", "RespN", "respondents (analysed records with a full text and a usable extraction)", S.n),
            ("respondents_w_min", "RespWMin", "smallest respondent design weight", S.p),
            ("respondents_w_max", "RespWMax", "largest respondent design weight", S.p),
            ("respondents_kish_neff", "RespKish", "Kish effective sample size of the respondents", S.p),
            ("n_eligible", "EligN", "eligible studies", S.n),
            ("eligible_w_min", "EligWMin", "smallest design weight among eligible studies", S.p),
            ("eligible_w_max", "EligWMax", "largest design weight among eligible studies", S.p),
            ("eligible_kish_neff", "EligKish", "Kish effective sample size of the eligible studies", S.p),
            ("n_strata", "Strata", "sampling strata", S.n),
            ("n_estimation_groups", "Groups", "estimation groups after the v0.12.1 merge", S.n),
            ("groups_1_respondent", "GroupsOneResp", "estimation groups with a single respondent (no variance term)", S.n),
            ("df", "Df", "degrees of freedom of the t interval (sum of respondents minus 1 over groups)", S.n),
        ]:
            fn(f"\\nDesign{c}{nm}", r[col], f"{src}#{r['coder']}/{col}", f"Design diagnostics, {r['coder']}: {mean}")
        S.d(f"\\nDesign{c}TQuantile", r["t_quantile_975"], f"{src}#{r['coder']}/t_quantile_975", f"Design diagnostics, {r['coder']}: t quantile for the 95% interval", 3)
    hl = read_csv(base / "headline_prevalences.csv")
    hsrc = rel(base / "headline_prevalences.csv")
    tags = {"rq4|perturbation|wording": ("Wording", "wording perturbation"), "rq4|robustness_tested|yes": ("AnyJudged", "any of the judged perturbation types"),
            "rq4|f2|yes": ("FTwo", "temperature stated (f2)"), "rq4|f11|yes": ("FEleven", "preregistration cited (f11)"), "rq4|f12|yes": ("FTwelve", "code or data link (f12)")}
    for r in hl:
        t, lab = tags[r["key"]]
        c = r["coder"].capitalize()
        for col, nm, mean, fn in [("k", "K", "studies with the feature (unweighted)", S.n), ("n", "N", "eligible studies in the domain (unweighted)", S.n),
                                  ("unweighted_pct", "Unw", "unweighted share k/n", S.p), ("weighted_pct", "Wtd", "design-weighted share", S.p),
                                  ("domain_kish_neff", "Kish", "Kish effective sample size of the domain", S.p),
                                  ("logit_lo_pct", "LogitLo", "lower limit of the logit-scale 95% interval (B8, shares under 10%)", S.p),
                                  ("logit_hi_pct", "LogitHi", "upper limit of the logit-scale 95% interval (B8, shares under 10%)", S.p)]:
            fn(f"\\nDesign{c}{t}{nm}", r[col], f"{hsrc}#{r['key']}/{r['coder']}/{col}", f"Design diagnostics, {r['coder']}, {lab}: {mean}")
    vs = read_csv(base / "venue_sensitivity.csv")
    vsrc = rel(base / "venue_sensitivity.csv")
    for r in vs:
        t, lab = tags[r["key"]]
        c = r["coder"].capitalize()
        S.p(f"\\nDesign{c}{t}VenueWtd", r["venue_pct"], f"{vsrc}#{r['key']}/{r['coder']}/venue_pct", f"Venue sensitivity, {r['coder']}, {lab}: venue-adjusted weighted share")
    mx = max(abs(float(r["change_pp"])) for r in vs)
    S.p("\\nDesignVenueMaxChange", mx, f"{vsrc}#max|change_pp|", "Venue sensitivity: largest absolute change of a headline share (points), both coders")


# --------------------------------------------------------------------------- main
def write_outputs(interim: bool):
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% GENERATED by analysis/paper_numbers.py. Do not edit; rerun the script.",
        "% Each macro: value from a run output; the trailing comment names the source file and row/key.",
        f"% interim: {'true' if interim else 'false'} (data/processed/prisma-fulltext.json)",
        f"% macros: {len(S.rows)}",
    ]
    for name, value, src, _ in S.rows:
        lines.append(f"\\newcommand{{{name}}}{{{value}}} % src: {src}")
    OUT_TEX.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def esc(s):
        return str(s).replace("|", "\\|")

    def plain(v):
        return v.replace("\\ensuremath{-}", "-").replace("{,}", ",")

    idx = [
        "# Autonumbers index",
        "",
        "Generated by `analysis/paper_numbers.py` together with `paper/common/autonumbers.tex`. Do not edit.",
        f"Macros: {len(S.rows)}. Interim run: {'yes' if interim else 'no'}.",
        "Use the macro, never a typed number. The main file must load `common/autonumbers.tex` before the sections.",
        "Intervals are separate macros (`...Lo`, `...Hi`). Percentages carry no % sign. Counts show the thousands separator as `{,}` in the .tex file.",
        "`...Pass` macros hold `pass` or `fail` (v0.12 inter-coder rule of the governing field); `...BoundLo`/`...BoundHi` are nonresponse bounds (v0.9.1), not confidence limits; `nPair...` are descriptive paired differences with no test; `nZeroEvt...` are exact upper limits at zero events.",
        "Rows whose meaning says `FAIL` come from fields that failed the v0.12 inter-coder rule: show both coders, do not present the value as a single estimate with an uncertainty interval.",
        "No p-values and no LLM/human spread ratio are generated.",
        "",
        "| macro | value | source | meaning |",
        "|---|---|---|---|",
    ]
    for name, value, src, meaning in S.rows:
        idx.append(f"| `{esc(name)}` | {esc(plain(value))} | `{esc(src)}` | {esc(meaning)} |")
    OUT_IDX.write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")


def main():
    do_prisma()
    interim = do_fulltext_flag()
    do_rq1_tables()
    do_rq1_flag_error()
    do_semantic_and_cocitation()
    do_rq234()
    do_rq2_generation()
    do_eligibility_and_nonresponse()
    do_agreement()
    do_pilot()
    do_pilot_nd()
    do_calibration()
    do_placement()
    do_design()
    write_outputs(interim)
    print(f"wrote {rel(OUT_TEX)} and {rel(OUT_IDX)}: {len(S.rows)} macros; interim={interim}")


if __name__ == "__main__":
    main()
