"""Generate paper/acme/autonumbers.tex from NUMBERS (stub, CRP-S08 skeleton 2026-11-06).

Every number in the ACME manuscript enters LaTeX through \\NUM{key} (paper/acme/macros.tex), which reads a macro defined here.
This stub holds no numbers. A real build fills NUMBERS from files under runs/ (never typed by hand), e.g.

    NUMBERS["n.records.identified"] = Entry(value="...", src="runs/<id>/<file>#<field>")

Rules (blueprint section 7, number integrity):
  * value is the final LaTeX string (thousands separators, intervals, signs already formatted by the producer);
  * src names the run file and the field the value was read from; a missing src is refused;
  * keys use letters, digits, '.', ':' and '-' only (they become \\csname NUM:<key>\\endcsname);
  * the output is deterministic (sorted keys) so a rebuild produces a byte-identical file.

Usage:  python analysis/acme/make_autonumbers.py [--out paper/acme/autonumbers.tex]
"""
from __future__ import annotations

import argparse
import csv
import re  # also used by _section2_numbers
from dataclasses import dataclass
from pathlib import Path

KEY_RE = re.compile(r"^[A-Za-z0-9.:-]+$")
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "paper" / "acme" / "autonumbers.tex"
SCRIPT = "analysis/acme/make_autonumbers.py"


@dataclass(frozen=True)
class Entry:
    value: str  # LaTeX string, already formatted
    src: str    # run file and field, e.g. "runs/acme-G1b/results.csv#power"


# Dictionary-driven list. Empty at skeleton time: no numbers yet.
NUMBERS: dict[str, Entry] = {}


# --------------------------------------------------------------------------------------------------------------------------
# Section 2 (02-background.tex): design constants and human-scale constants. No model outcome appears here.
# Values that live in a machine-readable file are read from it at build time (and checked); the rest are design constants
# quoted from the frozen preregistration with the line they come from.
# --------------------------------------------------------------------------------------------------------------------------
def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _arml_scales() -> list[dict[str, str]]:
    import csv
    with (ROOT / "runs/human-ml1-acme/arml_scales.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _section2_numbers() -> dict[str, Entry]:
    import ast
    out: dict[str, Entry] = {}
    scales = _arml_scales()
    ks = {r["k_sites"] for r in scales}
    if len(ks) != 1:
        raise ValueError(f"sites differ across items in arml_scales.csv: {ks}")
    out["n.sites"] = Entry(ks.pop(), "runs/human-ml1-acme/arml_scales.csv#k_sites (identical for all items)")
    cp = [float(r["se_single_sd_units"]) for r in scales]
    out["cp.min"] = Entry(f"{min(cp):.2f}", "runs/human-ml1-acme/arml_scales.csv#se_single_sd_units (minimum over the items)")
    out["cp.max"] = Entry(f"{max(cp):.2f}", "runs/human-ml1-acme/arml_scales.csv#se_single_sd_units (maximum over the items)")
    out["n.items"] = Entry("ten" if len(scales) == 10 else str(len(scales)),
                           "runs/human-ml1-acme/arml_scales.csv (rows); research/relaunch/PREREG-acme.md#L67")
    # roster: models.yaml entries that are not precision controls
    rows = [ln for ln in _read("analysis/acme/models.yaml").splitlines()
            if ln.startswith("  ") and not ln.lstrip().startswith("#") and ":" in ln and "{repo:" in ln]
    roster = [ln for ln in rows if "control: true" not in ln]
    out["n.models"] = Entry(str(len(roster)), "analysis/acme/models.yaml (entries without control: true); research/relaunch/PREREG-acme.md#L74")
    gs = _read("analysis/acme/gstudy.py")
    temps = ast.literal_eval(re.search(r"^TEMPERATURES = (\(.*\))", gs, re.M).group(1))
    out["n.temps"] = Entry(str(len(temps)), "analysis/acme/gstudy.py#TEMPERATURES; research/relaunch/PREREG-acme.md#L79")
    labels = [f"{t:.1f}" for t in temps]
    out["temps.levels"] = Entry(", ".join(labels[:-1]) + " and " + labels[-1],
                                "analysis/acme/gstudy.py#TEMPERATURES; research/relaunch/PREREG-acme.md#L79")
    if 1.0 not in temps:
        raise ValueError("reference temperature 1.0 missing from TEMPERATURES")
    out["temp.ref"] = Entry("1.0", "analysis/acme/gstudy.py#TEMPERATURES (1.0 is the model's own distribution); PREREG-acme.md#L88")
    out["boot.B"] = Entry(re.search(r"^DEFAULT_B = (\d+)", gs, re.M).group(1),
                          "analysis/acme/gstudy.py#DEFAULT_B; research/relaunch/PREREG-acme.md#L108")
    # design constants quoted from the frozen preregistration
    out["n.wordings"] = Entry("ten", "research/relaunch/PREREG-acme.md#L76 (W0-W9) and #L157 (10 wordings)")
    out["n.effects"] = Entry("seven", "research/relaunch/PREREG-acme.md#L67 (ten items, P2a-d one anchoring effect); research/relaunch/ACME-BLUEPRINT.md#L223 (M4)")
    out["n.orders.max"] = Entry("2", "research/relaunch/PREREG-acme.md#L78 (P1, P3, QA, AF, NR have two orders)")
    out["n.items.twoorder"] = Entry("5", "research/relaunch/PREREG-acme.md#L157 (5 two-order items) and #L78")
    out["n.items.oneorder"] = Entry("5", "research/relaunch/PREREG-acme.md#L157 (5 one-order items) and #L78")
    # human between-site spread on Delta's scale (erratum E5): items whose 95% interval reaches zero
    with (ROOT / "runs/human-ml1-acme/SH_sd_units.csv").open(encoding="utf-8", newline="") as f:
        sh = list(csv.DictReader(f))
    n0 = sum(float(r["S_sd_lo"]) == 0.0 for r in sh)
    words = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    out["sh.items.lo0"] = Entry(words[n0], "runs/human-ml1-acme/SH_sd_units.csv#S_sd_lo (count of items with lower bound 0)")
    return out


NUMBERS.update(_section2_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 3 (03-review-method.tex): counts of the review of manuscript v3, read from the review ledgers and runs.
# Every value is read from a file at build time; counts that must reconcile are checked here, so a mismatch stops the build.
# Keys carry the prefix rm. (review method). No model or tool name is stored in any src string of this block.
# --------------------------------------------------------------------------------------------------------------------------
def _json(rel: str):
    import json
    return json.loads(_read(rel))


def _csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _n(v: int | float) -> str:
    """Integer with a thousands comma."""
    return f"{int(v):,}"


def _r2(x: str) -> str:
    """Two decimals, rounding half up from the stored 3-decimal string (0.725 -> 0.73)."""
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _cp_interval(k: int, n: int) -> tuple[float, float]:
    """Exact (Clopper-Pearson) 95 percent interval by bisection on the binomial tail."""
    from math import comb

    def cdf(x: int, p: float) -> float:  # P(X <= x)
        return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(x + 1))

    def solve(f, lo=0.0, hi=1.0):
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
        return (lo + hi) / 2

    lower = 0.0 if k == 0 else solve(lambda p: 0.025 - (1 - cdf(k - 1, p)))   # P(X >= k) = 0.025, increasing in p
    upper = 1.0 if k == n else solve(lambda p: cdf(k, p) - 0.025)               # P(X <= k) = 0.025, decreasing in p
    return lower, upper


def _section3_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 12: "twelve"}
    cnt = "runs/rq1-fig1-prisma/counts.json"
    c = _json(cnt)
    pc = _json("research/protocol/prisma-counts.json")
    ag = _json("data/processed/screen/abstract-agreement-v08.json")
    ta = _json("data/processed/screen/title-agreement.json")

    # ---- search and flow (Fig 2, Table 3) ------------------------------------------------------------------------------
    blocks = c["openalex_by_block"]
    assert sum(blocks.values()) == c["openalex_total"]
    assert c["openalex_total"] + c["arxiv"] == c["identified_total"]
    assert c["identified_total"] - c["duplicates_removed"] == c["unique"]
    assert c["unique"] - c["title_excluded"] == c["stage2"]
    assert c["stage2"] - c["abstract_both_exclude"] == pc["full_text_input"] == c["both_include"] + c["disagree_or_maybe"]
    assert ag["liberal"]["eligible"] + ag["liberal"]["excluded_tiebreak"] == pc["full_text_input"]
    assert ag["strict"]["eligible"] + ag["strict"]["excluded_tiebreak"] == pc["full_text_input"]
    assert c["liberal_eligible"] == ag["liberal"]["eligible"] == c["rq1_coded_frame"] and c["strict_eligible"] == ag["strict"]["eligible"]
    out["rm.nSubq"] = Entry(words[len(blocks)], f"{cnt}#openalex_by_block (number of sub-queries B1-B10)")
    for key, field in [("rm.nOpenalex", "openalex_total"), ("rm.nArxiv", "arxiv"), ("rm.nIdent", "identified_total"),
                       ("rm.nDup", "duplicates_removed"), ("rm.nUnique", "unique"), ("rm.nTitleExcl", "title_excluded"),
                       ("rm.nStage2", "stage2"), ("rm.nAbsExcl", "abstract_both_exclude"), ("rm.nBothIncl", "both_include"),
                       ("rm.nSplit", "disagree_or_maybe"), ("rm.nLiberal", "liberal_eligible"), ("rm.nStrict", "strict_eligible"),
                       ("rm.nLiberalExcl", "tiebreak_excluded")]:
        out[key] = Entry(_n(c[field]), f"{cnt}#{field}")
    out["rm.nFtCand"] = Entry(_n(pc["full_text_input"]), "research/protocol/prisma-counts.json#full_text_input")
    out["rm.nStrictExcl"] = Entry(_n(ag["strict"]["excluded_tiebreak"]), "data/processed/screen/abstract-agreement-v08.json#strict.excluded_tiebreak")
    # records the OpenAlex interface announced but did not return (search log, run S2 table: count minus fetched)
    log = _read("research/protocol/search-log.md")
    s2 = log.split("## OpenAlex run S2")[1].split("Raw files")[0]
    rows = re.findall(r"^\| (B\d+) \| (\d+) \| (\d+) \|", s2, re.M)
    assert len(rows) == len(blocks) and sum(int(r[2]) for r in rows) == c["openalex_total"]
    out["rm.nOaNotReturned"] = Entry(_n(sum(int(r[1]) - int(r[2]) for r in rows)),
                                     "research/protocol/search-log.md (run S2 table: announced count minus fetched, summed over B1-B10)")
    f = c["flag"]
    out["rm.nFlagYes"] = Entry(_n(f["yes"]), f"{cnt}#flag.yes")
    out["rm.nFlagUnclear"] = Entry(_n(f["unclear"]), f"{cnt}#flag.unclear")
    out["rm.nFlagNo"] = Entry(_n(f["no"]), f"{cnt}#flag.no")

    # ---- full-text sample (Fig 2) ---------------------------------------------------------------------------------------
    ft = c["fulltext"]
    alloc = _csv("data/processed/fulltext-sample/allocation.csv")
    assert sum(int(r["n_h_drawn"]) for r in alloc) == c["sample_drawn"] and sum(int(r["n_h_in_first_150"]) for r in alloc) == c["sample_analysed"]
    assert sum(int(r["N_h"]) for r in alloc) == c["liberal_eligible"]
    out["rm.nStrata"] = Entry(str(len(alloc)), "data/processed/fulltext-sample/allocation.csv (rows)")
    out["rm.nDrawn"] = Entry(str(c["sample_drawn"]), f"{cnt}#sample_drawn")
    out["rm.nAnalysed"] = Entry(str(c["sample_analysed"]), f"{cnt}#sample_analysed")
    out["rm.nFT"] = Entry(str(ft["fulltext_assessed"]), f"{cnt}#fulltext.fulltext_assessed")
    out["rm.nNoFT"] = Entry(str(ft["fulltext_not_retrievable"]), f"{cnt}#fulltext.fulltext_not_retrievable")
    out["rm.nFTExcl"] = Entry(str(ft["excluded_fulltext_total"]), f"{cnt}#fulltext.excluded_fulltext_total")
    out["rm.nElig1"] = Entry(str(ft["included_rq2_rq4"]), f"{cnt}#fulltext.included_rq2_rq4")
    out["rm.nElig2"] = Entry(str(c["fulltext_second_coding_included"]), f"{cnt}#fulltext_second_coding_included")
    assert ft["fulltext_assessed"] + ft["fulltext_not_retrievable"] == c["sample_analysed"]
    assert ft["fulltext_assessed"] - ft["excluded_fulltext_total"] == ft["included_rq2_rq4"]
    st = _json("runs/rq234-final/config.json")["reading_list_status"]
    lib = st["egateway_obtained"] + st["egateway_obtained_partial"]
    assert st["ok"] + lib == ft["fulltext_assessed"] and st["no_open_copy"] == ft["fulltext_not_retrievable"]
    out["rm.nOpenFT"] = Entry(str(st["ok"]), "runs/rq234-final/config.json#reading_list_status.ok")
    out["rm.nLibFT"] = Entry(words[lib], "runs/rq234-final/config.json#reading_list_status (library-service copies, complete plus partial)")
    # response and nonresponse bounds on the eligible share of the frame (first coding pass)
    nr = _csv("runs/rq234-final/eligibility-estimates.csv")[0]
    assert nr["coder"] == "claude" and int(nr["n_eligible_respondents"]) == ft["included_rq2_rq4"]
    for key, fld in [("rm.eligShare", "est_share_of_frame_pct"), ("rm.eligShareLo", "lo_pct"), ("rm.eligShareHi", "hi_pct"),
                     ("rm.eligBoundLo", "bound_all_unknown_ineligible_pct"), ("rm.eligBoundHi", "bound_all_unknown_eligible_pct")]:
        out[key] = Entry(f"{float(nr[fld]):.1f}", f"runs/rq234-final/eligibility-estimates.csv#{fld} (first coding pass)")
    nrm = _read("runs/rq234-final/nonresponse.md")
    m = re.search(r"\| claude \| rq4/f2/yes \| 80 \| 31 \| [\d.]+ \| [\d.]+ \| ([\d.]+) \| ([\d.]+) \|", nrm)
    out["rm.tempBoundLo"] = Entry(m.group(1), "runs/rq234-final/nonresponse.md (row rq4/f2/yes, first coding pass: bound, lower)")
    out["rm.tempBoundHi"] = Entry(m.group(2), "runs/rq234-final/nonresponse.md (row rq4/f2/yes, first coding pass: bound, upper)")
    z = _read("runs/rq234-final/zero_event_bounds.md")
    for coder, key, which in [("claude", "rm.essElig1", "first"), ("codex", "rm.essElig2", "second")]:
        mm = re.search(rf"\| {coder} \| rq\d/[^|]+ \| \d+ \| 0 \| [\d.]+ \| [\d.]+ \| ([\d.]+) \|", z)
        out[key] = Entry(mm.group(1), f"runs/rq234-final/zero_event_bounds.md#n_eff_kish (eligible studies, {which} coding pass)")

    # ---- screening agreement ---------------------------------------------------------------------------------------------
    kp = ag["kappa_pairwise"]
    out["rm.kTitle"] = Entry(f"{ta['kappa_3class']:.3f}", "data/processed/screen/title-agreement.json#kappa_3class")
    out["rm.kTitleEx"] = Entry(f"{ta['kappa_exclude_vs_not']:.3f}", "data/processed/screen/title-agreement.json#kappa_exclude_vs_not")
    out["rm.kAbs12"] = Entry(f"{kp['claude-olmo']:.3f}", "data/processed/screen/abstract-agreement-v08.json#kappa_pairwise (pass 1 with pass 2)")
    out["rm.kAbs13"] = Entry(f"{kp['claude-qwen']:.3f}", "data/processed/screen/abstract-agreement-v08.json#kappa_pairwise (pass 1 with pass 3)")
    out["rm.kAbs23"] = Entry(f"{kp['olmo-qwen']:.3f}", "data/processed/screen/abstract-agreement-v08.json#kappa_pairwise (pass 2 with pass 3)")
    out["rm.kFleiss"] = Entry(f"{ag['fleiss_kappa_3class']:.2f}", "data/processed/screen/abstract-agreement-v08.json#fleiss_kappa_3class")
    aj = _json("data/processed/screen/abstract-agreement.json")
    out["rm.kAbsEx"] = Entry(f"{aj['kappa_exclude_vs_not']:.2f}", "data/processed/screen/abstract-agreement.json#kappa_exclude_vs_not (passes 1 and 2)")
    loc = aj["local"]
    out["rm.pctExcl2"] = Entry(str(round(100 * loc["EXCLUDE"] / aj["n"])),
                               "data/processed/screen/abstract-agreement.json#local.EXCLUDE / n (share of stage-2 records labelled exclude by pass 2)")

    # ---- reference pilot on 70 disagreement records ----------------------------------------------------------------------
    rp = _json("runs/fulltext-pilot/results.json")
    r_s, r_l = rp["rules"]["strict"], rp["rules"]["liberal"]
    pil_src = "runs/fulltext-pilot/results.json"
    out["rm.pilN"] = Entry(str(rp["n_used"] + rp["skipped"]["no_full_text"] + rp["skipped"]["unclear"]), f"{pil_src}#n_used + skipped")
    out["rm.pilUsed"] = Entry(str(rp["n_used"]), f"{pil_src}#n_used")
    out["rm.pilRef"] = Entry(str(rp["reference_yes"]), f"{pil_src}#reference_yes")
    out["rm.pilRefNo"] = Entry(str(r_s["ref_no"]), f"{pil_src}#rules.strict.ref_no")
    out["rm.pilConf"] = Entry(str(rp["n_confirmed_by_shlok"]), f"{pil_src}#n_confirmed_by_shlok (decisions confirmed by the first author)")
    pt = re.sub(r"\s+", " ", _read("research/protocol/protocol.md"))
    mb = re.search(r"approved the reader's (\d+) YES/NO decisions in bulk \(reported in the methods as bulk confirmation, not row-by-row\); (\d+) UNCLEAR rows", pt)
    assert mb, "pilot confirmation split not found in protocol.md"
    nb, ni = int(mb.group(1)), int(mb.group(2))
    assert nb + ni == rp["n_confirmed_by_shlok"]
    out["rm.pilBulk"] = Entry(str(nb), "research/protocol/protocol.md (v0.8 pilot confirmation: decisions approved in bulk, not row by row)")
    out["rm.pilIndiv"] = Entry(["none", "one", "two", "three", "four", "five"][ni], "research/protocol/protocol.md (v0.8 pilot confirmation: rows decided one by one)")
    out["rm.pilStrictFE"] = Entry(f"{r_s['false_excl']}", f"{pil_src}#rules.strict.false_excl")
    out["rm.pilStrictRate"] = Entry(f"{r_s['fe_rate']:.3f}", f"{pil_src}#rules.strict.fe_rate")
    out["rm.pilStrictCI"] = Entry(f"{r_s['fe_ci'][0]:.3f} to {r_s['fe_ci'][1]:.3f}", f"{pil_src}#rules.strict.fe_ci")
    out["rm.pilLibFE"] = Entry(f"{r_l['false_excl']}", f"{pil_src}#rules.liberal.false_excl")
    out["rm.pilLibRate"] = Entry(f"{r_l['fe_rate']:.3f}", f"{pil_src}#rules.liberal.fe_rate")
    out["rm.pilLibCI"] = Entry(f"{r_l['fe_ci'][0]:.3f} to {r_l['fe_ci'][1]:.3f}", f"{pil_src}#rules.liberal.fe_ci")
    out["rm.pilLibFI"] = Entry(str(r_l["false_incl"]), f"{pil_src}#rules.liberal.false_incl")
    out["rm.pilStrictFI"] = Entry(str(r_s["false_incl"]), f"{pil_src}#rules.strict.false_incl")
    sw = rp["switch_rule"]
    # design counts quoted in the prose (sources, passes, rules, sets, periods, items), derived from the files that define them
    out["rm.nSources"] = Entry(words[sum(1 for k in ("openalex_total", "arxiv") if c.get(k))], f"{cnt}#openalex_total, arxiv (sources that returned records)")
    out["rm.nScreenPasses"] = Entry(words[sum(1 for k in ta if k in ("claude", "local"))],
                                    "data/processed/screen/title-agreement.json (label sets of the two title-stage passes)")
    out["rm.nRules"] = Entry(words[sum(1 for k in ("strict", "liberal") if k in ag)], "data/processed/screen/abstract-agreement-v08.json#strict, liberal (decision rules)")
    periods = {r["stratum"].split("|")[1] for r in alloc} - {"all"}
    out["rm.nPeriods"] = Entry(words[len(periods)], "data/processed/fulltext-sample/allocation.csv#stratum (distinct publication periods)")
    nitems = re.search(r"## F\. Reporting quality and robustness \((\d+) items", _read("research/protocol/extraction-form.md"))
    out["rm.nItems"] = Entry(words[int(nitems.group(1))], "research/protocol/extraction-form.md (section F, number of reporting items)")
    out["rm.nCodingPasses"] = Entry(words[len(_json("runs/rq234-final/config.json")["records_per_status"])],
                                    "runs/rq234-final/config.json#records_per_status (coding passes)")
    out["rm.pilNoText"] = Entry(str(rp["skipped"]["no_full_text"]), f"{pil_src}#skipped.no_full_text")
    # protocol constants quoted from the frozen protocol text (amendments v0.8 and v0.12, whitespace-normalised before matching)
    prot = " ".join(_read("research/protocol/protocol.md").split())
    sm = re.search(r"exceeds the liberal rule's by more than (\d+) percentage points the liberal rule becomes primary, unless the difference rests on one or (\w+) records", prot)
    num_words = {"two": "two", "three": "three"}
    out["rm.switchPP"] = Entry(words[int(sm.group(1))], "research/protocol/protocol.md (amendment v0.8 item C, switch rule: percentage-point margin)")
    out["rm.switchRecs"] = Entry(num_words[sm.group(2)], "research/protocol/protocol.md (amendment v0.8 item C, switch rule: records that may drive the difference)")
    rm_ = re.search(r"kappa >= (0\.\d+) when every category has at least (\d+) records in each coder's coding, otherwise if percent agreement >= (0\.\d+)", prot)
    out["rm.ruleK"] = Entry(rm_.group(1), "research/protocol/protocol.md (amendment v0.12 item 3, reporting rule: kappa threshold)")
    out["rm.ruleCat"] = Entry(words[int(rm_.group(2))], "research/protocol/protocol.md (amendment v0.12 item 3: minimum records per category)")
    out["rm.rulePct"] = Entry(rm_.group(3), "research/protocol/protocol.md (amendment v0.12 item 3: observed-agreement threshold, as a proportion)")
    out["rm.pilDiffPP"] = Entry(f"{sw['diff_false_excl_pp']:.1f}", f"{pil_src}#switch_rule.diff_false_excl_pp")
    out["rm.pilDriveRecs"] = Entry(words[sw["records_driving_difference"]], f"{pil_src}#switch_rule.records_driving_difference")

    # ---- known-item recall ------------------------------------------------------------------------------------------------
    kr = _json("runs/known-item-recall-v07/summary.json")
    first = re.search(r"Recall: (\d+)/(\d+)", _read("research/protocol/known-item-recall.md"))
    sets = {"S1": (int(first.group(1)), int(first.group(2))),
            "HO": (kr["holdout"]["found"], kr["holdout"]["verified"]),
            "TH": (kr["third"]["found"], kr["third"]["verified"])}
    for tag, (k, n) in sets.items():
        src = ("research/protocol/known-item-recall.md#Recall" if tag == "S1" else
               f"runs/known-item-recall-v07/summary.json#{'holdout' if tag == 'HO' else 'third'}")
        out[f"rm.rec{tag}k"], out[f"rm.rec{tag}n"] = Entry(str(k), src), Entry(str(n), src)
    out["rm.nKnownSets"] = Entry(words[len(sets)], "research/protocol/known-item-recall.md; runs/known-item-recall-v07/summary.json (known-item sets)")
    for tag, rel in [("HO", "research/protocol/query-recall-holdout.md"), ("TH", "research/protocol/query-recall-third.md")]:
        mm = re.search(r"^\| v0\.6 [^|]*\|[^|]*\| (\d+) / (\d+) \|", _read(rel), re.M)
        out[f"rm.rec6{tag}k"] = Entry(mm.group(1), f"{rel} (row v0.6)")
        out[f"rm.rec6{tag}n"] = Entry(mm.group(2), f"{rel} (row v0.6)")
        if tag == "TH":
            lo, hi = _cp_interval(int(mm.group(1)), int(mm.group(2)))
            out["rm.rec6THlo"] = Entry(f"{lo:.2f}", f"{rel} (row v0.6), Clopper-Pearson 95 percent interval computed in make_autonumbers.py")
            out["rm.rec6THhi"] = Entry(f"{hi:.2f}", f"{rel} (row v0.6), Clopper-Pearson 95 percent interval computed in make_autonumbers.py")
    ks = " ".join(_read("research/protocol/screening/abstract-claude-summary.md").split())
    mm = re.search(r"overall (\d+) present, (\d+) retained", ks)
    tl = re.search(r"Lost at the title stage: (.*?); lost at stage 2", ks).group(1)
    sl = re.search(r"lost at stage 2 \(.*?\): (.*?)\. Recovery", ks).group(1)
    ks_src = "research/protocol/screening/abstract-*-summary.md (known items through both stages)"
    out["rm.retPresent"] = Entry(mm.group(1), ks_src)
    out["rm.retKept"] = Entry(mm.group(2), ks_src)
    out["rm.lostTitle"] = Entry(words[tl.count("et al.")], ks_src + ", title-stage losses")
    out["rm.lostAbs"] = Entry(words[sl.count("et al.")], ks_src + ", stage-2 losses")
    assert int(mm.group(1)) - int(mm.group(2)) == tl.count("et al.") + sl.count("et al.")

    # ---- coding pilot (extraction instructions 1.0 and 1.1) -----------------------------------------------------------------
    def kap(run: str, field: str) -> dict[str, str]:
        for r in _csv(f"runs/extraction-pilot/{run}/kappa.csv"):
            if r["field"] == field:
                return r
        raise KeyError((run, field))

    r1 = kap("round1", "eligibility.decision")
    out["rm.cp1N"] = Entry(r1["n"], "runs/extraction-pilot/round1/kappa.csv#n (eligibility.decision)")
    out["rm.cp1Elig"] = Entry(_r2(r1['kappa']), "runs/extraction-pilot/round1/kappa.csv#kappa (eligibility.decision)")
    out["rm.cp1Fam"] = Entry(_r2(kap('round1', 'C.family_presence (pooled)')['kappa']), "runs/extraction-pilot/round1/kappa.csv#kappa (C.family_presence)")
    out["rm.cp1Mod"] = Entry(_r2(kap('round1', 'E.model_effect_present')['kappa']), "runs/extraction-pilot/round1/kappa.csv#kappa (E.model_effect_present)")
    fld = {"Kind": "E.outcome_kind", "Lab": "E.label", "Fam": "C.family_presence (pooled)", "F4": "F.f4"}
    for run, tag in [("round2-fresh", "Fresh"), ("round2-combined", "Comb")]:
        for k, field in fld.items():
            out[f"rm.cp2{tag}{k}"] = Entry(_r2(kap(run, field)['kappa']), f"runs/extraction-pilot/{run}/kappa.csv#kappa ({field})")
    out["rm.cp2FreshN"] = Entry(words[int(kap("round2-fresh", "E.outcome_kind")["n"])], "runs/extraction-pilot/round2-fresh/kappa.csv#n (records)")
    out["rm.cp2OldN"] = Entry(words[int(kap("round2-old", "D.primary_type")["n"])], "runs/extraction-pilot/round2-old/kappa.csv#n (records recoded)")

    # ---- full-sample agreement between the two coding passes -------------------------------------------------------------------
    ar = _csv("runs/rq234-final/agreement.csv")
    ag_src = "runs/rq234-final/agreement.csv"
    el = next(r for r in ar if r["field"] == "eligibility.decision")
    out["rm.fsElPct"] = Entry(el["percent_agreement"], f"{ag_src}#percent_agreement (eligibility.decision)")
    out["rm.fsElK"] = Entry(f"{float(el['kappa']):.2f}", f"{ag_src}#kappa (eligibility.decision)")
    used = [r for r in ar if r["field"] not in ("eligibility.decision", "A.peer_reviewed")]
    fail = [r for r in used if r["passes_v012_rule"] == "False"]
    out["rm.fsFields"] = Entry(str(len(used)), f"{ag_src} (rows other than eligibility.decision and A.peer_reviewed)")
    out["rm.fsFail"] = Entry(str(len(fail)), f"{ag_src}#passes_v012_rule == False")
    out["rm.fsPass"] = Entry(str(len(used) - len(fail)), f"{ag_src}#passes_v012_rule == True")
    fk = sorted(float(r["kappa"]) for r in fail if r["kappa"])
    out["rm.fsFailKlo"] = Entry(f"{fk[0]:.2f}", f"{ag_src}#kappa (minimum over failing fields)")
    out["rm.fsFailKhi"] = Entry(f"{fk[-1]:.2f}", f"{ag_src}#kappa (maximum over failing fields)")
    pr = [r for r in used if r["passes_v012_rule"] == "True" and r["rule_basis"].startswith("percent") and r["kappa"] and float(r["kappa"]) < 0.6]
    out["rm.fsPctPass"] = Entry(words[len(pr)], f"{ag_src} (passing on the percent rule with kappa below 0.6)")
    f1 = next(r for r in ar if r["field"] == "F.f1")
    out["rm.fsF1K"] = Entry(f"{float(f1['kappa']):.3f}", f"{ag_src}#kappa (F.f1)")
    out["rm.fsF1Pct"] = Entry(f1["percent_agreement"], f"{ag_src}#percent_agreement (F.f1)")
    ak = _json("runs/rq234-final/adjudication-key.json")
    asm = _json("runs/rq234-final/adjudication-summary.json")
    adj_src = "runs/rq234-final/adjudication-summary.json"
    out["rm.adjPool"] = Entry(str(ak["pool_size"]), "runs/rq234-final/adjudication-key.json#pool_size")
    out["rm.adjN"] = Entry(str(asm["n"]), f"{adj_src}#n")
    bc, bf = asm["by_category"], asm["by_favoured_coder"]
    out["rm.adjInc"] = Entry(str(bc["inconsistent application"]), f"{adj_src}#by_category.inconsistent application")
    out["rm.adjDef"] = Entry(str(bc["unresolved definition"]), f"{adj_src}#by_category.unresolved definition")
    out["rm.adjAmb"] = Entry(str(bc["genuine source ambiguity"]), f"{adj_src}#by_category.genuine source ambiguity")
    out["rm.adjFav1"] = Entry(str(bf["claude"]), f"{adj_src}#by_favoured_coder (first coding pass)")
    out["rm.adjFav2"] = Entry(str(bf["codex"]), f"{adj_src}#by_favoured_coder (second coding pass)")
    out["rm.adjFavNone"] = Entry(str(bf["neither"]), f"{adj_src}#by_favoured_coder (neither)")
    return out


NUMBERS.update(_section3_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 4 (04-state-of-art-specification.tex): RQ1, how simulated participants are specified. Keys carry the prefix sp.
# Two evidence bases: (i) abstract-level coding of the liberal frame (complete for the frame, no sampling), read from the RQ1
# tables and the coded batch files; (ii) design-weighted full-text estimates of the reporting items, read from the final
# estimate files. Counts that must reconcile are asserted, so a mismatch stops the build. No model or tool name is stored in
# any src string of this block; "first pass" and "second pass" name the two independent coding passes.
# --------------------------------------------------------------------------------------------------------------------------
def rq1_model_family_by_bin(scheme: str = "year") -> list[dict]:
    """Records of the liberal frame naming each model family, by publication bin (long format; one row per bin x family).

    scheme "year": bins 2018-2021 (pooled), 2022, ..., 2026 (partial year); scheme "period": the three sampling periods of
    the review design. A record that names several families enters several rows, so rows do not sum to the bin total.
    family "none named" counts records whose abstract names no model family. Used by _section4_numbers and by the Fig 3
    panel (b) script, so that text and figure share one source (data/processed/rq1/ via analysis/rq1/rq1_common.py).
    """
    import sys
    sys.path.insert(0, str(ROOT / "analysis" / "rq1"))
    import rq1_common as C  # noqa: E402
    rows, _views, _manifest = C.load_frame()
    if scheme == "year":
        bin_of = lambda y: "2018-2021" if y <= 2021 else str(y)  # noqa: E731
    elif scheme == "period":
        bin_of = C.period_of
    else:
        raise ValueError(scheme)
    totals: dict[str, int] = {}
    counts: dict[tuple[str, str], int] = {}
    for r in rows.values():
        b = bin_of(int(r["year"]))
        totals[b] = totals.get(b, 0) + 1
        fams = set(r["model_families"]) or {"none named"}
        for f in fams:
            counts[(b, f)] = counts.get((b, f), 0) + 1
    out = []
    for b in sorted(totals):
        for f in C.MODEL_FAMILIES + ["none named"]:
            k = counts.get((b, f), 0)
            out.append({"bin": b, "n_records": totals[b], "family": f, "n_named": k, "share_pct": 100.0 * k / totals[b]})
    return out


def _section4_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    pct1 = lambda k, n: f"{100.0 * k / n:.1f}"  # noqa: E731
    t1 = "runs/rq1-tables"

    def item(table: str, label_start: str) -> dict[str, str]:
        hits = [r for r in _csv(f"{t1}/{table}.csv") if r["item"].startswith(label_start)]
        assert len(hits) == 1, (table, label_start, len(hits))
        return hits[0]

    c = _json("runs/rq1-fig1-prisma/counts.json")
    nA = int(item("T-RQ1a", "N (denominator)")["A_n"])
    nB = int(item("T-RQ1a", "N (denominator)")["B_n"])
    assert nA == c["rq1_coded_frame"] == c["liberal_eligible"] and nB == c["flag"]["yes"]
    out["sp.nFrame"] = Entry(_n(nA), "runs/rq1-tables/T-RQ1a.csv#A_n (denominator); runs/rq1-fig1-prisma/counts.json#rq1_coded_frame")
    out["sp.nFlagged"] = Entry(_n(nB), "runs/rq1-tables/T-RQ1a.csv#B_n (denominator); runs/rq1-fig1-prisma/counts.json#flag.yes")

    # ---- volume and period shares (Fig 3 panel a) --------------------------------------------------------------------------
    ym = _json("runs/rq1-fig2-years/metrics.json")["total_by_year"]["A"]
    assert sum(ym.values()) == nA
    drows = [r for r in _csv(f"{t1}/T-RQ1d.csv") if r["view"] == "A"]
    for r in drows:
        if r["bin_type"] == "year":
            assert int(r["total"]) == ym[r["bin"]], r["bin"]
    for y in ("2018", "2021", "2023", "2024", "2025", "2026"):
        out[f"sp.y{y}"] = Entry(_n(ym[y]), f"runs/rq1-fig2-years/metrics.json#total_by_year.A.{y}; runs/rq1-tables/T-RQ1d.csv (year rows)")
    per = {r["bin"]: r for r in drows if r["bin_type"] == "period"}
    assert sum(int(r["total"]) for r in per.values()) == nA
    fam_cols = ["HB", "JDM", "RE", "TOM", "MEM", "LANG", "LEARN", "NUM", "MOR", "DEV", "OTH", "none"]
    for r in per.values():
        assert sum(int(r[f]) for f in fam_cols) == int(r["total"])
    e, l = per["2018-2023"], per["2025-2026"]
    src_p = "runs/rq1-tables/T-RQ1d.csv (period rows, view A)"
    out["sp.nEarly"] = Entry(_n(int(e["total"])), src_p)
    out["sp.pctEarly"] = Entry(pct1(int(e["total"]), nA), src_p + "; share of the frame")
    out["sp.nLate"] = Entry(_n(int(l["total"])), src_p)
    out["sp.pctLate"] = Entry(pct1(int(l["total"]), nA), src_p + "; share of the frame")
    out["sp.langEarlyN"] = Entry(e["LANG"], src_p + "#LANG (2018-2023)")
    out["sp.jdmLateN"] = Entry(l["JDM"], src_p + "#JDM (2025-2026)")
    out["sp.noneLateN"] = Entry(l["none"], src_p + "#none (2025-2026)")
    assert int(e["LANG"]) == max(int(e[f]) for f in fam_cols if f != "none")
    assert int(l["JDM"]) == max(int(l[f]) for f in fam_cols if f != "none")

    # ---- paradigm families and names (T-RQ1a, T-RQ1e, metrics) ---------------------------------------------------------------
    for tag, lab in [("lang", "LANG"), ("jdm", "JDM"), ("num", "NUM"), ("dev", "DEV")]:
        r = item("T-RQ1a", lab + " ")
        out[f"sp.fam.{tag}.n"] = Entry(r["A_n"], f"runs/rq1-tables/T-RQ1a.csv#A_n ({lab})")
        out[f"sp.fam.{tag}.pct"] = Entry(f"{float(r['A_pct']):.1f}", f"runs/rq1-tables/T-RQ1a.csv#A_pct ({lab})")
    r = item("T-RQ1a", "None named")
    out["sp.fam.none.n"] = Entry(r["A_n"], "runs/rq1-tables/T-RQ1a.csv#A_n (None named)")
    out["sp.fam.none.pct"] = Entry(f"{float(r['A_pct']):.1f}", "runs/rq1-tables/T-RQ1a.csv#A_pct (None named)")
    m = _json(f"{t1}/metrics.json")["T-RQ1e"]
    nn, once = int(m["distinct_names_A"]), int(m["names_once_A"])
    out["sp.nNames"] = Entry(_n(nn), f"{t1}/metrics.json#T-RQ1e.distinct_names_A")
    out["sp.nNamesOnce"] = Entry(_n(once), f"{t1}/metrics.json#T-RQ1e.names_once_A")
    out["sp.pctNamesOnce"] = Entry(pct1(once, nn), f"{t1}/metrics.json#T-RQ1e.names_once_A / distinct_names_A")
    top = _csv(f"{t1}/T-RQ1e.csv")[0]
    assert top["rank"] == "1"
    out["sp.topNameN"] = Entry(top["A_n_records"], f"{t1}/T-RQ1e.csv#A_n_records (rank 1)")

    # ---- administration as stated in the abstract (T-RQ1c) --------------------------------------------------------------------
    for key, lab in [("modText", "Modality: text"), ("modImg", "Modality: image+text"), ("modNone", "Modality: not stated"),
                     ("langNone", "Language: not stated"), ("langEn", "Language: English"), ("langZh", "Language: Chinese")]:
        r = item("T-RQ1c", lab)
        out[f"sp.{key}.n"] = Entry(_n(int(r["A_n"])), f"{t1}/T-RQ1c.csv#A_n ({lab})")
        out[f"sp.{key}.pct"] = Entry(f"{float(r['A_pct']):.1f}", f"{t1}/T-RQ1c.csv#A_pct ({lab})")
    cod = item("T-RQ1c", "RQ1 codable")
    hm = _json("runs/rq1-fig5-heatmap/metrics.json")["marginals"]
    assert int(cod["A_n"]) == hm["A"]["paradigm_and_model_named"] and int(cod["B_n"]) == hm["B"]["paradigm_and_model_named"]
    out["sp.nBoth.n"] = Entry(_n(int(cod["A_n"])), f"{t1}/T-RQ1c.csv#A_n (RQ1 codable); runs/rq1-fig5-heatmap/metrics.json#marginals.A")
    out["sp.nBoth.pct"] = Entry(f"{float(cod['A_pct']):.1f}", f"{t1}/T-RQ1c.csv#A_pct (RQ1 codable)")
    out["sp.nBothB.pct"] = Entry(f"{float(cod['B_pct']):.1f}", f"{t1}/T-RQ1c.csv#B_pct (RQ1 codable)")

    # ---- model families named, and how often a model count is stated (T-RQ1b) -------------------------------------------------
    for tag, lab in [("gpt", "GPT"), ("claude", "Claude"), ("gemini", "Gemini"), ("llama", "Llama"), ("qwen", "Qwen"),
                     ("mistral", "Mistral"), ("olmo", "OLMo"), ("other", "other"), ("none", "None named")]:
        r = item("T-RQ1b", lab)
        out[f"sp.mf.{tag}.n"] = Entry(_n(int(r["A_n"])), f"{t1}/T-RQ1b.csv#A_n ({lab})")
        out[f"sp.mf.{tag}.pct"] = Entry(f"{float(r['A_pct']):.1f}", f"{t1}/T-RQ1b.csv#A_pct ({lab})")
    ns = {r["statistic"]: r for r in _csv(f"{t1}/T-RQ1b_n_models_stated.csv")}
    out["sp.nm.n"] = Entry(_n(int(ns["n stated"]["A"])), f"{t1}/T-RQ1b_n_models_stated.csv#A (n stated)")
    out["sp.nm.pct"] = Entry(f"{float(ns['% of N stated']['A']):.1f}", f"{t1}/T-RQ1b_n_models_stated.csv#A (% of N stated)")
    out["sp.nm.med"] = Entry(f"{float(ns['median']['A']):.0f}", f"{t1}/T-RQ1b_n_models_stated.csv#A (median)")
    out["sp.nm.q1"] = Entry(f"{float(ns['Q1']['A']):.0f}", f"{t1}/T-RQ1b_n_models_stated.csv#A (Q1)")
    out["sp.nm.q3"] = Entry(f"{float(ns['Q3']['A']):.0f}", f"{t1}/T-RQ1b_n_models_stated.csv#A (Q3)")
    out["sp.nm.max"] = Entry(ns["max"]["A"], f"{t1}/T-RQ1b_n_models_stated.csv#A (max)")

    # ---- model families named over time (Fig 3 panel b), recomputed from the coded batch files and reconciled -------------------
    byyear = rq1_model_family_by_bin("year")
    byper = rq1_model_family_by_bin("period")
    tb = {"GPT": "gpt", "Claude": "claude", "Gemini": "gemini", "Llama": "llama", "Mistral": "mistral", "Qwen": "qwen", "OLMo": "olmo",
          "other": "other", "none named": "none"}
    for rows_, name in ((byyear, "year"), (byper, "period")):
        for fam, tag in tb.items():
            tot = sum(r["n_named"] for r in rows_ if r["family"] == fam)
            assert str(tot) == out[f"sp.mf.{tag}.n"].value.replace(",", ""), (name, fam, tot)
        assert sum(r["n_records"] for r in rows_ if r["family"] == "GPT") == nA
    pl = {"2018-2023": "Early", "2024": "Mid", "2025-2026": "Late"}
    for r in byper:
        if r["family"] in ("GPT", "Claude", "Gemini", "Llama", "Qwen", "none named"):
            out[f"sp.mfp.{tb[r['family']]}{pl[r['bin']]}"] = Entry(
                f"{r['share_pct']:.1f}",
                "data/processed/rq1/rq1-batch-*.jsonl and data/processed/records.jsonl (year), liberal frame via "
                f"analysis/rq1/rq1_common.py; records naming the family over records in period {r['bin']}")

    # ---- design-weighted full-text estimates: documentation items f1, f2, f4 and the not-applicable share of f6 -----------------
    rq4 = {r["feature"]: r for r in _csv("runs/rq234-final/rq4.csv")}
    nr = {(r["coder"], r["feature"]): r for r in _csv("runs/rq234-final/nonresponse_bounds.csv")}
    md = _read("runs/rq234-final/rq4.md")
    f4src = "runs/rq234-final/rq4.csv"
    for fn, val, tag in [("f1", "yes", "f1"), ("f2", "yes", "f2"), ("f4", "yes", "f4"), ("f6", "na", "f6na")]:
        r = rq4[f"rq4|{fn}|{val}"]
        for pidx, col, who in ((1, "claude", "first"), (2, "codex", "second")):
            est, lo, hi = (float(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
            k, n = int(r[f"{col}_k"]), int(r[f"{col}_n_domain"])
            out[f"sp.{tag}.p{pidx}"] = Entry(f"{est:.1f}", f"{f4src}#est_pct (feature {fn}/{val}, {who} pass)")
            out[f"sp.{tag}.p{pidx}k"] = Entry(str(k), f"{f4src}#k ({fn}/{val}, {who} pass)")
            if fn == "f2":  # only f2 meets the agreement rule among these four items, so only f2 carries an interval
                out[f"sp.{tag}.p{pidx}lo"] = Entry(f"{lo:.1f}", f"{f4src}#lo_pct ({fn}/{val}, {who} pass)")
                out[f"sp.{tag}.p{pidx}hi"] = Entry(f"{hi:.1f}", f"{f4src}#hi_pct ({fn}/{val}, {who} pass)")
                assert f"{est:.1f} ({lo:.1f} to {hi:.1f}) | {k}/{n}" in md, (fn, who)  # reconcile with the rendered table
            b = nr[(col, f"rq4|{fn}|{val}")]
            out[f"sp.{tag}.b{pidx}lo"] = Entry(f"{float(b['bound_lo_pct']):.1f}", f"runs/rq234-final/nonresponse_bounds.csv#bound_lo_pct ({fn}/{val}, {who} pass)")
            out[f"sp.{tag}.b{pidx}hi"] = Entry(f"{float(b['bound_hi_pct']):.1f}", f"runs/rq234-final/nonresponse_bounds.csv#bound_hi_pct ({fn}/{val}, {who} pass)")
            assert int(b["k"]) == k
        out[f"sp.{tag}.kappa"] = Entry(f"{float(r['kappa']):.3f}", f"{f4src}#kappa ({fn})")
        out[f"sp.{tag}.agree"] = Entry(f"{float(r['percent_agreement']):.1f}", f"{f4src}#percent_agreement ({fn})")
        out[f"sp.{tag}.rule"] = Entry("met" if r["passes_v012_rule"] == "True" else "failed", f"{f4src}#passes_v012_rule ({fn})")
    assert out["sp.f2.rule"].value == "met" and out["sp.f4.rule"].value == "failed" and out["sp.f6na.rule"].value == "failed"
    # year trend of the documentation item f2, fitted per pass (sensitivity analysis; no direction is claimed)
    tr = {(r["coder"], r["feature"]): r for r in _csv("runs/rq234-final/rq4_trend.csv")}
    for pidx, col, who in ((1, "claude", "first"), (2, "codex", "second")):
        t = tr[(col, "rq4|f2|yes")]
        assert t["status"] == "fitted"
        for key, fld in (("", "OR_per_year"), ("lo", "or_lo"), ("hi", "or_hi")):
            out[f"sp.f2.or{pidx}{key}"] = Entry(f"{float(t[fld]):.2f}", f"runs/rq234-final/rq4_trend.csv#{fld} (f2, {who} pass)")
    return out


NUMBERS.update(_section4_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 5 (05-state-of-art-validation.tex): outcome kinds and labels against human data (RQ2), human reference types, human
# sample sizes and metric types (RQ3 of the review), design-weighted over eligible studies, one value per coding pass.
# Keys carry the prefix val. Rule: a field that met the agreement rule carries an interval (keys p1lo, p1hi, p2lo, p2hi); a field
# that failed it carries pass-specific values only. Every value is checked against the rendered table of the same run.
# No tool or model name is stored in any src string of this block.
# --------------------------------------------------------------------------------------------------------------------------
def _section5_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    d = "runs/rq234-final"
    f1 = lambda x: f"{float(x):.1f}"  # noqa: E731
    passes = ((1, "claude", "first"), (2, "codex", "second"))
    rq2 = {r["feature"]: r for r in _csv(f"{d}/rq2.csv")}
    rq3 = {r["feature"]: r for r in _csv(f"{d}/rq3.csv")}
    md2, md3 = _read(f"{d}/rq2.md").splitlines(), _read(f"{d}/rq3.md").splitlines()
    nb = {(r["coder"], r["feature"]): r for r in _csv(f"{d}/nonresponse_bounds.csv")}

    def row_line(md: list[str], start: str) -> str:
        hits = [ln for ln in md if ln.startswith(start)]
        assert len(hits) == 1, (start, len(hits))
        return hits[0]

    def put(prefix: str, r: dict[str, str], src: str, line: str, want_rule: bool | None, bound: bool = False) -> None:
        rule = r["passes_v012_rule"] == "True"
        if want_rule is not None:
            assert rule == want_rule, (prefix, r["feature"], rule)
        for pidx, col, who in passes:
            est, lo, hi = (float(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
            k, n = int(r[f"{col}_k"]), int(r[f"{col}_n_domain"])
            assert f"{k}/{n}" in line and f"{f1(est)} ({f1(lo)} to {f1(hi)})" in line, (prefix, who, line)  # reconcile with table
            out[f"{prefix}.p{pidx}"] = Entry(f1(est), f"{src}#est_pct ({who} pass)")
            out[f"{prefix}.p{pidx}k"] = Entry(str(k), f"{src}#k ({who} pass)")
            if rule:
                out[f"{prefix}.p{pidx}lo"] = Entry(f1(lo), f"{src}#lo_pct ({who} pass)")
                out[f"{prefix}.p{pidx}hi"] = Entry(f1(hi), f"{src}#hi_pct ({who} pass)")
            if bound:
                b = nb[(col, r["feature"])]
                assert int(b["k"]) == k
                out[f"{prefix}.b{pidx}lo"] = Entry(f1(b["bound_lo_pct"]), f"{d}/nonresponse_bounds.csv#bound_lo_pct ({who} pass)")
                out[f"{prefix}.b{pidx}hi"] = Entry(f1(b["bound_hi_pct"]), f"{d}/nonresponse_bounds.csv#bound_hi_pct ({who} pass)")

    # ---- eligible base and the agreement rule for the two fields behind the outcome rows --------------------------------------
    for pidx, col, who in passes:
        ns = {int(r[f"{col}_n_domain"]) for r in list(rq2.values()) + list(rq3.values())}
        assert ns == {int(NUMBERS[f"rm.nElig{pidx}"].value)}, (who, ns)  # same eligible base as Section 3
    kind, lab = rq2["rq2|effect|ANY"], rq2["rq2|effect|SUPER-NORMATIVE"]
    assert kind["agreement_field"] == "E.outcome_kind" and kind["passes_v012_rule"] == "True"
    assert lab["agreement_field"].startswith("E.derived_label") and lab["passes_v012_rule"] == "False"
    out["val.kind.kappa"] = Entry(f"{float(kind['kappa']):.3f}", f"{d}/rq2.csv#kappa (E.outcome_kind)")
    out["val.kind.agree"] = Entry(f1(kind["percent_agreement"]), f"{d}/rq2.csv#percent_agreement (E.outcome_kind)")
    out["val.label.kappa"] = Entry(f"{float(lab['kappa']):.3f}", f"{d}/rq2.csv#kappa (E.derived_label)")
    out["val.label.agree"] = Entry(f1(lab["percent_agreement"]), f"{d}/rq2.csv#percent_agreement (E.derived_label)")
    assert kind["n_agreement"] == lab["n_agreement"]
    out["val.kind.nkeys"] = Entry(kind["n_agreement"], f"{d}/rq2.csv#n_agreement (matched keys)")

    # ---- outcome kinds and derived labels (RQ2 tables) ---------------------------------------------------------------------
    eff = {"ANY": "any", "SAME-DIRECTION-UNQUANTIFIED": "sdu", "HUMAN-LIKE": "hl", "EXAGGERATED": "exa", "ATTENUATED": "att",
           "SUPER-NORMATIVE": "sup", "DIFFERENT": "dif", "NO-HUMAN-REFERENCE": "nor", "INSUFFICIENT": "ins",
           "UNCLASSIFIED-MODEL-ONLY": "mo"}
    acc = {"ANY": "any", "ABOVE-HUMAN": "abv", "HUMAN-LEVEL": "hum", "BELOW-HUMAN": "blw", "NO-HUMAN-REFERENCE": "nor",
           "INSUFFICIENT": "ins"}
    for kindname, tags, pre in (("effect", eff, "eff"), ("accuracy", acc, "acc"), ("agreement", {"ANY": "any"}, "agr")):
        for label, tag in tags.items():
            r = rq2[f"rq2|{kindname}|{label}"]
            put(f"val.{pre}.{tag}", r, f"{d}/rq2.csv ({kindname}/{label})", row_line(md2, f"| {kindname} | {label} |"),
                True if tag == "any" else False)

    # ---- unweighted row counts per outcome kind (descriptive) ---------------------------------------------------------------
    rows = _csv(f"{d}/rq2-rows-by-family.csv")
    for pidx, col, who in passes:
        for kindname, pre in (("effect", "eff"), ("accuracy", "acc"), ("agreement", "agr")):
            tot = sum(int(r["rows"]) for r in rows if r["coder"] == col and r["outcome_kind"] == kindname)
            out[f"val.rows.{pre}.p{pidx}"] = Entry(_n(tot), f"{d}/rq2-rows-by-family.csv#rows ({kindname}, {who} pass, summed over families)")

    # ---- human reference types (all fields met the agreement rule, so every share carries an interval) ----------------------
    for pre, typ in (("none", "none"), ("own", "own_sample"), ("norms", "published_norms"), ("crowd", "crowd_norms")):
        r = rq3[f"rq3|types_any|{typ}"]
        put(f"val.ref.{pre}", r, f"{d}/rq3.csv (types_any/{typ})", row_line(md3, f"| types_any/{typ} |"), True)
        r = rq3[f"rq3|primary_type|{typ}"]
        put(f"val.prim.{pre}", r, f"{d}/rq3.csv (primary_type/{typ})", row_line(md3, f"| primary_type/{typ} |"), True)
    r = rq3["rq3|types_any|replication_dataset"]
    assert r["claude_k"] == "0" and r["codex_k"] == "0"
    for pidx, col, who in passes:
        out[f"val.ref.repl.p{pidx}k"] = Entry(r[f"{col}_k"], f"{d}/rq3.csv#k (types_any/replication_dataset, {who} pass)")
        out[f"val.ref.repl.n{pidx}"] = Entry(r[f"{col}_n_domain"], f"{d}/rq3.csv#n_domain (types_any/replication_dataset, {who} pass)")
        lo_, hi_ = r[f"{col}_cp_unweighted_pct"].split("-")
        assert float(lo_) == 0.0
        out[f"val.ref.repl.ub{pidx}"] = Entry(f1(hi_), f"{d}/rq3.csv#cp_unweighted_pct (types_any/replication_dataset, {who} pass; exact upper bound)")
    out["val.ref.kappaMin"] = Entry(
        f"{min(float(rq3[f'rq3|types_any|{t}']['kappa']) for t in ('none', 'own_sample', 'published_norms', 'crowd_norms')):.3f}",
        f"{d}/rq3.csv#kappa (types_any fields with a kappa; the replication-dataset field has none because both passes agree on zero)")

    # ---- human sample size -------------------------------------------------------------------------------------------------
    put("val.hn", rq3["rq3|human_n|reported"], f"{d}/rq3.csv (human_n/reported)", row_line(md3, "| human_n/reported |"), True, bound=True)
    hn = _json(f"{d}/rq3-human-n.json")
    fmt = lambda v: str(int(v)) if float(v) == int(v) else f"{float(v):.1f}"  # noqa: E731
    for pidx, col, who in passes:
        a, o = hn[col]["all_reported"], hn[col]["primary_type_own_sample"]
        assert a["n"] == int(out[f"val.hn.p{pidx}k"].value)
        s = f"{d}/rq3-human-n.json ({who} pass)"
        for key in ("min", "q1", "median", "q3", "max"):
            out[f"val.hn.{key}.p{pidx}"] = Entry(fmt(a[key]) if key != "max" else _n(a[key]), f"{s}#all_reported.{key}")
        out[f"val.hn.own.med.p{pidx}"] = Entry(fmt(o["median"]), f"{s}#primary_type_own_sample.median")
        out[f"val.hn.own.n.p{pidx}"] = Entry(str(o["n"]), f"{s}#primary_type_own_sample.n")

    # ---- metric types ------------------------------------------------------------------------------------------------------
    met = {"acc": ("accuracy", True), "cor": ("human_correlation", True), "es": ("effect_size", False), "bias": ("bias_magnitude", False),
           "choice": ("choice_distribution", False), "oth": ("other", False)}
    for pre, (typ, rule) in met.items():
        put(f"val.met.{pre}", rq3[f"rq3|outcome_types|{typ}"], f"{d}/rq3.csv (outcome_types/{typ})",
            row_line(md3, f"| outcome_types/{typ} |"), rule)
    fk = [float(rq3[f"rq3|outcome_types|{t}"]["kappa"]) for _, (t, rule) in met.items() if not rule]
    out["val.met.failKlo"] = Entry(f"{min(fk):.2f}", f"{d}/rq3.csv#kappa (outcome_types fields that failed the rule; minimum)")
    out["val.met.failKhi"] = Entry(f"{max(fk):.2f}", f"{d}/rq3.csv#kappa (outcome_types fields that failed the rule; maximum)")
    assert len(fk) == 4
    return out


NUMBERS.update(_section5_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 6 (06-uncertainty-audit.tex): practice audit of the sources of simulator uncertainty (RQ3), design-weighted over eligible
# studies, one value per coding pass, from runs/rq234-final (rq4.csv and its rendered table rq4.md, nonresponse_bounds.csv,
# rq4_trend.csv, trend_descriptive_only.csv, nonresponse.md). Keys carry the prefix au. Rule: a field that met the agreement rule
# carries an interval (keys p1lo, p1hi, p2lo, p2hi); a field that failed it carries pass-specific values only. Every value is
# checked against the rendered table of the same run, and every comparison that the prose states is asserted below.
# Items already used by Sections 3 to 5 (sp.f1, sp.f2, sp.f6na, rm.ess*) are reused and not rebuilt. No tool or model name is
# stored in any src string of this block.
# --------------------------------------------------------------------------------------------------------------------------
def _section6_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    d = "runs/rq234-final"
    f1 = lambda x: f"{float(x):.1f}"  # noqa: E731
    passes = ((1, "claude", "first"), (2, "codex", "second"))
    rq4 = {r["feature"]: r for r in _csv(f"{d}/rq4.csv")}
    nb = {(r["coder"], r["feature"]): r for r in _csv(f"{d}/nonresponse_bounds.csv")}
    md = _read(f"{d}/rq4.md").splitlines()
    vals: dict[tuple[str, int], tuple[float, float, float, float, float]] = {}  # (prefix, pass) -> est, lo, hi, logit lo, logit hi

    def row_line(label: str) -> str:
        hits = [ln for ln in md if ln.startswith(f"| {label} |")]
        assert len(hits) == 1, (label, len(hits))
        return hits[0]

    def put(prefix: str, feature: str, want_rule: bool, interval: bool = False, bounds: bool = False, logit: bool = False,
            denom: bool = False) -> None:
        r = rq4[f"rq4|{feature}"]
        rule = r["passes_v012_rule"] == "True"
        assert rule == want_rule, (prefix, feature, rule)
        line = row_line(feature.replace("|", "/"))
        src = f"{d}/rq4.csv (rq4|{feature})"
        for pidx, col, who in passes:
            est, lo, hi = (float(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
            ll, lh = float(r[f"{col}_lo_logit_pct"]), float(r[f"{col}_hi_logit_pct"])
            k, n = int(r[f"{col}_k"]), int(r[f"{col}_n_domain"])
            assert f"{f1(est)} ({f1(lo)} to {f1(hi)})" in line and f"{k}/{n}" in line, (prefix, who, line)  # reconcile with table
            vals[(prefix, pidx)] = (est, lo, hi, ll, lh)
            out[f"{prefix}.p{pidx}"] = Entry(f1(est), f"{src}#est_pct ({who} pass)")
            out[f"{prefix}.p{pidx}k"] = Entry(str(k), f"{src}#k ({who} pass)")
            if denom:
                out[f"{prefix}.n{pidx}"] = Entry(str(n), f"{src}#n_domain ({who} pass)")
            if interval:
                assert rule, prefix  # an interval is printed only for a field that met the agreement rule
                out[f"{prefix}.p{pidx}lo"] = Entry(f1(lo), f"{src}#lo_pct ({who} pass)")
                out[f"{prefix}.p{pidx}hi"] = Entry(f1(hi), f"{src}#hi_pct ({who} pass)")
            if logit:
                out[f"{prefix}.p{pidx}llo"] = Entry(f1(ll), f"{src}#lo_logit_pct ({who} pass)")
                out[f"{prefix}.p{pidx}lhi"] = Entry(f1(lh), f"{src}#hi_logit_pct ({who} pass)")
            if bounds:
                b = nb[(col, f"rq4|{feature}")]
                assert int(b["k"]) == k
                out[f"{prefix}.b{pidx}lo"] = Entry(f1(b["bound_lo_pct"]), f"{d}/nonresponse_bounds.csv#bound_lo_pct ({who} pass)")
                out[f"{prefix}.b{pidx}hi"] = Entry(f1(b["bound_hi_pct"]), f"{d}/nonresponse_bounds.csv#bound_hi_pct ({who} pass)")
                vals[(prefix + ".b", pidx)] = (float(b["bound_lo_pct"]), float(b["bound_hi_pct"]), 0.0, 0.0, 0.0)
        out[f"{prefix}.kappa"] = Entry(f"{float(r['kappa']):.3f}", f"{src}#kappa")
        out[f"{prefix}.agree"] = Entry(f1(r["percent_agreement"]), f"{src}#percent_agreement")

    for pidx, col, who in passes:  # same eligible base as Sections 3 to 5
        assert {int(r[f"{col}_n_domain"]) for r in rq4.values() if r["feature"].startswith(("rq4|f1|", "rq4|perturbation|"))} \
            == {int(NUMBERS[f"rm.nElig{pidx}"].value)}

    # ---- documentation items not already reported in Section 4: code or data link, preregistration -------------------------------
    put("au.code", "f12|yes", True, interval=True, bounds=True)
    put("au.prereg", "f11|yes", True, interval=True, bounds=True, logit=True)
    # ---- variation items ---------------------------------------------------------------------------------------------------------
    put("au.rep", "f3|yes", True, interval=True, bounds=True)       # identical prompt sampled repeatedly
    put("au.wrd", "f5|yes", False)                                  # wording varied and compared
    put("au.ord", "f6_applicable|yes", False, denom=True)           # option order varied, studies that list their options
    put("au.smp", "f7|yes", True, interval=True)                    # two or more sampling settings compared
    put("au.snap", "f8|yes", False)                                 # two or more snapshots of one model line compared
    put("au.nov", "f9|yes", True, interval=True)                    # novel or perturbed items against memorisation
    # ---- perturbation types (the first six are judged for the outcome of a robustness check) ------------------------------------
    put("au.any", "robustness_tested|yes", True, interval=True, bounds=True)
    put("au.pw", "perturbation|wording", True, interval=True, bounds=True)
    put("au.po", "perturbation|option_order", False)
    put("au.pd", "perturbation|decoding", True, interval=True)
    put("au.ps", "perturbation|seeds", False)
    put("au.pv", "perturbation|model_version", False)
    put("au.pc", "perturbation|contamination", False)
    assert rq4["rq4|perturbation|response_format"]["passes_v012_rule"] == "False"
    judged_fail = ("option_order", "response_format", "seeds", "model_version")
    kf = [float(rq4[f"rq4|perturbation|{t}"]["kappa"]) for t in judged_fail]
    assert "six-type robustness judgement" in "\n".join(md)  # the outcome is judged on six perturbation types
    out["au.nJudged"] = Entry("six", f"{d}/rq4.md (header: six-type robustness judgement); types listed in protocol v0.12 (rq4 outcome field)")
    assert len(judged_fail) == 4
    out["au.nJudgedFail"] = Entry("four", f"{d}/rq4.csv#passes_v012_rule (perturbation types option_order, response_format, seeds, model_version)")
    out["au.pert.failKlo"] = Entry(f"{min(kf):.2f}", f"{d}/rq4.csv#kappa (judged perturbation types that failed the rule; minimum)")
    out["au.pert.failKhi"] = Entry(f"{max(kf):.2f}", f"{d}/rq4.csv#kappa (judged perturbation types that failed the rule; maximum)")

    # unweighted share of the wording perturbation (descriptive; the weighted share is lower because of the weights)
    for pidx, col, who in passes:
        k, n = int(rq4["rq4|perturbation|wording"][f"{col}_k"]), int(rq4["rq4|perturbation|wording"][f"{col}_n_domain"])
        out[f"au.pw.u{pidx}"] = Entry(f"{100.0 * k / n:.1f}", f"{d}/rq4.csv#k / n_domain (perturbation|wording, {who} pass; unweighted)")
        assert 100.0 * k / n > vals[("au.pw", pidx)][0]

    # ---- outcome of the robustness check among studies that ran a judged type --------------------------------------------------
    for tag, lab in (("sur", "survived"), ("wea", "weakened"), ("mix", "mixed"), ("rev", "reversed")):
        put(f"au.out.{tag}", f"robustness_outcome_among_tested|{lab}", False, denom=True)
    for pidx, col, who in passes:
        assert out[f"au.out.sur.n{pidx}"].value == rq4["rq4|robustness_tested|yes"][f"{col}_k"]  # denominator = studies that tested
    o = rq4["rq4|robustness_outcome_among_tested|survived"]
    assert o["agreement_field"] and o["passes_v012_rule"] == "False"
    out["au.out.kappa"] = Entry(f"{float(o['kappa']):.3f}", f"{d}/rq4.csv#kappa (robustness outcome)")
    out["au.out.agree"] = Entry(f1(o["percent_agreement"]), f"{d}/rq4.csv#percent_agreement (robustness outcome)")

    # ---- statements that the prose makes about these values (all asserted) ----------------------------------------------------
    V = lambda p, i, j=0: vals[(p, i)][j]  # noqa: E731
    overlap = lambda a, b: a[1] <= b[2] and b[1] <= a[2]  # noqa: E731  (t-interval rows: est, lo, hi)
    f2 = {i: tuple(float(rq4["rq4|f2|yes"][f"{c}_{x}_pct"]) for x in ("est", "lo", "hi")) for i, c, _ in passes}
    f2l = {i: float(rq4["rq4|f2|yes"][f"{c}_lo_logit_pct"]) for i, c, _ in passes}
    f2b = {i: float(nb[(c, "rq4|f2|yes")]["bound_lo_pct"]) for i, c, _ in passes}
    for i in (1, 2):
        assert overlap(f2[i], vals[("au.code", i)][:3]), i                                   # temperature and code link overlap
        pr = vals[("au.prereg", i)]
        assert pr[1] == 0.0                                                                  # t interval truncated at zero
        assert pr[2] < f2[i][1] and pr[2] < V("au.code", i, 1)                               # t interval below temperature and code link
        assert pr[4] < f2l[i] and pr[4] < V("au.code", i, 3)                                 # logit interval below both
        assert vals[("au.prereg.b", i)][1] > f2b[i] and vals[("au.prereg.b", i)][1] > vals[("au.code.b", i)][0]  # bounds overlap
        assert vals[("au.any.b", i)][0] < 50.0 < vals[("au.any.b", i)][1] and V("au.any", i, 1) < 50.0 < V("au.any", i, 2)
        assert overlap(vals[("au.pw", i)][:3], vals[("au.pd", i)][:3])                       # wording and decoding intervals overlap
        assert V("au.pc", i) < V("au.nov", i)                                                # contamination perturbation below the item
        assert V("au.rep", i) > max(V(p, i) for p in ("au.smp", "au.snap", "au.nov", "au.wrd"))  # repeated sampling is the largest
    assert V("au.any", 1) > 50.0 > V("au.any", 2)                                            # either side of one half
    assert V("au.pw", 1) > V("au.pd", 1) and V("au.pd", 2) > V("au.pw", 2)                   # the passes order wording and decoding differently
    assert V("au.out.mix", 1) == max(V(f"au.out.{t}", 1) for t in ("sur", "wea", "mix", "rev"))   # first pass: mixed is largest
    assert V("au.out.wea", 2) == max(V(f"au.out.{t}", 2) for t in ("sur", "wea", "mix", "rev"))   # second pass: weakened is largest
    assert out["au.out.rev.p1k"].value == "2" and out["au.out.rev.p2k"].value == "2"

    # ---- year trends (sensitivity fits per pass) -------------------------------------------------------------------------------
    tr = _csv(f"{d}/rq4_trend.csv")
    desc = _csv(f"{d}/trend_descriptive_only.csv")
    for pidx, col, who in passes:
        fit = [r for r in tr if r["coder"] == col and r["status"] == "fitted"]
        dsc = [r for r in tr if r["coder"] == col and r["status"] == "descriptive_only"]
        assert len(dsc) == len([r for r in desc if r["coder"] == col])
        out[f"au.tr.fit{pidx}"] = Entry(str(len(fit)), f"{d}/rq4_trend.csv#status=fitted ({who} pass)")
        out[f"au.tr.desc{pidx}"] = Entry(str(len(dsc)), f"{d}/rq4_trend.csv#status=descriptive_only ({who} pass); trend_descriptive_only.csv")
        excl = sorted(r["feature"] for r in fit if float(r["or_hi"]) < 1 or float(r["or_lo"]) > 1)
        out[f"au.tr.excl{pidx}"] = Entry(str(len(excl)), f"{d}/rq4_trend.csv#or_lo, or_hi (fits whose interval excludes one, {who} pass)")
        if pidx == 1:
            assert excl == []
        else:
            assert excl == ["rq4|perturbation|option_order", "rq4|perturbation|wording", "rq4|robustness_tested|yes"], excl
        for tag, feat in (("any", "robustness_tested|yes"), ("wrd", "perturbation|wording"), ("ord", "perturbation|option_order")):
            t = next(r for r in fit if r["feature"] == f"rq4|{feat}")
            for key, fld in (("", "OR_per_year"), ("lo", "or_lo"), ("hi", "or_hi")):
                out[f"au.tr.{tag}.p{pidx}{key}"] = Entry(f"{float(t[fld]):.2f}", f"{d}/rq4_trend.csv#{fld} ({feat}, {who} pass)")
    assert out["au.tr.fit1"].value == "20" and out["au.tr.fit2"].value == "23"
    assert all(">= 10 events and >= 10 non-events" in r["rule"] for r in desc)  # the fitting threshold stated in the prose
    out["au.tr.minEvents"] = Entry("ten", f"{d}/trend_descriptive_only.csv#rule (v0.12.1 item 2: at least 10 events and 10 non-events)")

    # ---- response by publication year (nonresponse that a trend in weighted shares would inherit) --------------------------------
    nrm = _read(f"{d}/nonresponse.md")
    yr = {m.group(1): m for m in re.finditer(r"^\| (<=2023|2024|2025|2026) \| (\d+) \| (\d+) \| (\d+) \| ([\d.]+) \|", nrm, re.M)}
    assert set(yr) == {"<=2023", "2024", "2025", "2026"}
    lo_, hi_ = min(yr.values(), key=lambda m: float(m.group(5))), max(yr.values(), key=lambda m: float(m.group(5)))
    assert lo_.group(1) == "2025" and hi_.group(1) == "<=2023"
    for tag, m in (("lo", lo_), ("hi", hi_)):
        s = f"{d}/nonresponse.md (by year, row {m.group(1)})"
        out[f"au.resp.{tag}.pct"] = Entry(m.group(5), s + "#response %")
        out[f"au.resp.{tag}.k"] = Entry(m.group(3), s + "#respondents")
        out[f"au.resp.{tag}.n"] = Entry(m.group(2), s + "#analysed")
        assert int(m.group(3)) + int(m.group(4)) == int(m.group(2))
    return out


NUMBERS.update(_section6_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Crossing recode (Sections 3 and 6): counts of studies that cross, vary or decompose the sources of simulation uncertainty, and the
# agreement between the two coding passes. Keys carry the prefix cx. Source files: runs/crossing/counts.csv (one row per pass) and
# runs/crossing/agreement.csv (one row per field), written by analysis/acme/crossing_counts.py from data/processed/crossing/<pass>/
# under research/protocol/crossing-coding-brief.md. Pass 1 is the first pass and pass 2 the second, as in the other sections.
# Counts are unweighted counts of the eligible studies of the first extraction pass; intervals are exact (Clopper-Pearson).
# --------------------------------------------------------------------------------------------------------------------------
def _crossing_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    d = "runs/crossing"
    counts = {r["pass"]: r for r in _csv(f"{d}/counts.csv")}
    assert set(counts) == {"claude", "codex"}, sorted(counts)
    from decimal import Decimal, ROUND_HALF_UP
    f1 = lambda x: str(Decimal(repr(float(x))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))  # noqa: E731  (half up, audit C9)
    passes = ((1, "claude", "first"), (2, "codex", "second"))
    for pidx, col, who in passes:
        r = counts[col]
        n = int(r["n"])
        out[f"cx.n.p{pidx}"] = Entry(str(n), f"{d}/counts.csv#n ({who} pass)")
        # category counts of each field reconcile with the number of studies coded
        assert sum(int(r[f"X1_{k}"]) for k in ("yes", "partial", "no", "not_reported")) == n, (col, "X1")
        assert sum(int(r[f"X2_{k}"]) for k in ("yes", "no", "not_reported")) == n, (col, "X2")
        assert sum(int(r[f"X3_{k}"]) for k in ("yes", "no", "not_reported")) == n, (col, "X3")
        fields = {
            "x1yes": "X1_yes",                    # fully cross two or more sources
            "x1part": "X1_partial",               # two or more sources vary, not fully crossed
            "x1exr": "X1_yes_ge2_sources_excl_R",  # fully crossed, at least two sources other than repeated draws
            "multi": "multi_source_varied_ge2",   # two or more sources varied
            "x2yes": "X2_yes",                    # any quantification of a source (share, test term or change)
            "anova": "X2_anova_or_mixed",         # an ANOVA, regression or mixed-model term of a source
            "effch": "X2_effect_change",          # a quantified change of the outcome across levels of a source
            "vshare": "X2_variance_share",        # a variance share or component per source
            "x3yes": "X3_yes",                    # an interaction between sources estimated or shown
        }
        for key, column in fields.items():
            k = int(r[column])
            lo, hi = _cp_interval(k, n)
            out[f"cx.{key}.p{pidx}k"] = Entry(str(k), f"{d}/counts.csv#{column} ({who} pass)")
            out[f"cx.{key}.p{pidx}"] = Entry(f1(100 * k / n), f"{d}/counts.csv#{column} / #n, percent ({who} pass)")
            out[f"cx.{key}.p{pidx}lo"] = Entry(f1(100 * lo), f"{d}/counts.csv#{column}, exact lower bound, percent ({who} pass)")
            out[f"cx.{key}.p{pidx}hi"] = Entry(f1(100 * hi), f"{d}/counts.csv#{column}, exact upper bound, percent ({who} pass)")
    c1, c2 = counts["claude"], counts["codex"]
    # statements the prose makes
    assert int(c1["X2_variance_share"]) <= 1 and int(c2["X2_variance_share"]) <= 1, "text says at most one study reports a variance share"
    assert int(c1["X1_yes"]) > int(c2["X1_yes"]) and int(c1["X2_anova_or_mixed"]) < int(c2["X2_anova_or_mixed"])
    assert int(c1["X1_partial"]) < int(c2["X1_partial"]), "text: the second pass codes more designs as partly crossed"
    for c in (c1, c2):
        # text: a change of the outcome is the usual form of quantification; two or more sources vary in at least half of the studies
        assert 2 * int(c["X2_effect_change"]) > int(c["X2_yes"]), c["pass"]
        assert 2 * int(c["multi_source_varied_ge2"]) >= int(c["n"]), c["pass"]
    ag ={r["field"]: r for r in _csv(f"{d}/agreement.csv") if (r["pass_a"], r["pass_b"]) == ("claude", "codex")}
    assert set(ag) == {"X1", "X1_crossed_yes_vs_other", "X2", "X3"}, sorted(ag)
    out["cx.agr.n"] = Entry(ag["X1"]["n_common"], f"{d}/agreement.csv#n_common (studies coded by both passes)")
    for key, field in (("x1", "X1"), ("x1y", "X1_crossed_yes_vs_other"), ("x2", "X2"), ("x3", "X3")):
        assert ag[field]["n_common"] == ag["X1"]["n_common"]
        out[f"cx.agr.{key}.pct"] = Entry(f1(ag[field]["percent_agreement"]), f"{d}/agreement.csv#percent_agreement ({field})")
        out[f"cx.agr.{key}.kappa"] = Entry(f"{float(ag[field]['kappa']):.3f}", f"{d}/agreement.csv#kappa ({field})")
    kap = {k: float(v["kappa"]) for k, v in ag.items()}
    assert min(kap, key=kap.get) == "X2" and max(kap, key=kap.get) == "X3", kap  # text: kappa runs from the X2 value to the X3 value
    # agreement rule of Section 3 (kappa >= 0.6 with five or more records per category, else observed agreement >= 0.80)
    for field in ("X1", "X2"):
        assert float(ag[field]["kappa"]) < 0.6 and float(ag[field]["percent_agreement"]) < 80, field
    for field in ("X1_crossed_yes_vs_other", "X3"):
        assert float(ag[field]["kappa"]) < 0.6 and float(ag[field]["percent_agreement"]) >= 80, field
    return out


NUMBERS.update(_crossing_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 7, subsections 7.1 to 7.5 (07-benchmark.tex): design, human reference, roster, readout and estimator verification.
# Keys carry the prefix bm. (benchmark). No model outcome is read here: nothing under runs/acme-L/ is opened. Sources are the frozen
# preregistration and its addenda, the human-data runs, the roster files, the wording check, the truncation calibration on pilot
# prompts, and the synthetic gates G1 and G1b. Values that live in a machine-readable file are read from it and checked against
# the text of the preregistration where the plan states them. S7PRE_RAW keeps the unformatted values for the table scripts.
# --------------------------------------------------------------------------------------------------------------------------
S7PRE_RAW: dict = {}
_WORDS = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
          11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen"}


def _fx(x: float | str, nd: int) -> str:
    """Fixed decimals, half up, from the shortest repr of the float (0.0295 -> 0.03)."""
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def _sg(x: float | str, nd: int) -> str:
    """Like _fx, but a negative number is returned as a LaTeX math minus for running text."""
    s = _fx(x, nd)
    return f"$-{s[1:]}$" if s.startswith("-") else s


def _rx(text: str, pattern: str, what: str) -> re.Match:
    m = re.search(pattern, text, re.M | re.S)
    assert m, f"pattern for {what} not found: {pattern}"
    return m


def roster() -> list[dict[str, str]]:
    """The model roster of analysis/acme/models.yaml (precision controls included, flagged), with the licence from MODELS.jsonl."""
    import json
    lic = {}
    for ln in _read("runs/models/MODELS.jsonl").splitlines():
        d = json.loads(ln)
        lic[d["slug"]] = d
    rows = []
    for ln in _read("analysis/acme/models.yaml").splitlines():
        m = re.match(r"^  ([\w.\-]+):\s*\{(.*)\}", ln)
        if not m or ln.lstrip().startswith("#"):
            continue
        slug, body = m.groups()
        d = {kv.group(1): kv.group(2).strip() for kv in re.finditer(r"(\w+):\s*([^,]+?)(?:,|$)", body)}
        d["slug"] = slug
        d["control"] = "true" if d.get("control") == "true" else "false"
        if d["control"] == "false":
            j = lic[slug]
            assert j["repo"] == d["repo"] and j["revision"] == d["revision"], slug  # pinned revision agrees with MODELS.jsonl
            assert len(j["license"]) == 1
            d["licence"] = j["license"][0].replace("license:", "")
        rows.append(d)
    return rows


def _section7pre_numbers() -> dict[str, Entry]:
    import json
    import hashlib
    from datetime import datetime
    out: dict[str, Entry] = {}
    pre = _read("research/relaunch/PREREG-acme.md")
    err = _read("research/relaunch/PREREG-acme-ERRATA.md")
    expl = _read("research/relaunch/EXPLORATORY-acme.md")
    P = "research/relaunch/PREREG-acme.md"

    # ---- preregistration: frozen commit, hash, date, multiplicity, amendment counts -------------------------------------------------
    out["bm.prereg.commit"] = Entry(_rx(err, r"The frozen file \(([0-9a-f]{7}),", "freeze commit").group(1),
                                    "research/relaunch/PREREG-acme-ERRATA.md#header (freeze commit)")
    recorded = _rx(_read("research/relaunch/PREREG-acme.sha256"), r"^([0-9a-f]{64})\s", "recorded sha256").group(1)
    actual = hashlib.sha256(pre.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    assert recorded == actual, "PREREG-acme.md changed since the recorded freeze hash"
    out["bm.prereg.sha12"] = Entry(recorded[:12], "research/relaunch/PREREG-acme.sha256 (equals the LF-normalised SHA-256 of PREREG-acme.md, checked at build)")
    fr = _rx(pre, r"^FROZEN: (\d{4}-\d{2}-\d{2}) ", "freeze date").group(1)
    d = datetime.strptime(fr, "%Y-%m-%d")
    out["bm.prereg.date"] = Entry(f"{d.day} {d.strftime('%B %Y')}", f"{P}#FROZEN line")
    # OSF registration (decision D0032; date_registered from the OSF API, UTC); must not precede the freeze
    d32 = [json.loads(l) for l in _read("research/ledgers/decisions.jsonl").splitlines() if '"D0032"' in l]
    assert len(d32) == 1 and "https://osf.io/t82jc" in d32[0]["decision"]
    od = datetime.strptime(_rx(d32[0]["decision"], r"date_registered (\d{4}-\d{2}-\d{2})T", "OSF date").group(1), "%Y-%m-%d")
    assert od >= d
    out["bm.osf.date"] = Entry(f"{od.day} {od.strftime('%B %Y')}", "research/ledgers/decisions.jsonl#D0032 (OSF API date_registered, UTC)")
    mreg = _rx(err, r"At registration, Arm L outputs existed for (\d+) of the (\d+) models and had only\s+been hashed", "outputs at registration")
    out["bm.osf.armL.k"] = Entry(mreg.group(1), "research/relaunch/PREREG-acme-ERRATA.md#registration record (Arm L models with hashed output at registration)")
    out["bm.osf.armL.n"] = Entry(mreg.group(2), "research/relaunch/PREREG-acme-ERRATA.md#registration record (models in the design)")
    hashes = re.findall(r"^- `[^`]+`: [0-9a-f]{64}$", pre.split("## 9. Hashes")[1], re.M)
    assert len(hashes) == 15
    out["bm.prereg.nhash"] = Entry(str(len(hashes)), f"{P}#section 9 (files with a recorded SHA-256)")
    n_al = len(re.findall(r"^- \*\*A-L\d", pre, re.M))
    assert n_al == 6
    out["bm.prereg.nAL"] = Entry(_WORDS[n_al], f"{P}#section 1 (amendments A-L1 to A-L6)")
    n_er = len(re.findall(r"^## E\d", err, re.M))
    assert n_er >= 5   # errata are append-only; the count is read, not fixed
    out["bm.prereg.nErr"] = Entry(_WORDS[n_er], f"research/relaunch/PREREG-acme-ERRATA.md (errata E1 to E{n_er}; '## E' headings)")
    out["bm.alpha"] = Entry(_rx(pre, r"Holm over 3, α = (0\.05)", "alpha").group(1), f"{P}#section 5 (Holm over 3, alpha)")
    out["bm.holm.k"] = Entry(_WORDS[int(_rx(pre, r"Holm over (\d),", "Holm family").group(1))], f"{P}#section 5")
    nums = [int(x) for x in re.findall(r"^(\d+)\. ", expl, re.M)]
    assert nums == list(range(1, 13)), nums  # items 1-6 of the addendum and items 7-12 of amendment X2
    out["bm.expl.n"] = Entry(_WORDS[len(nums)], "research/relaunch/EXPLORATORY-acme.md (numbered items 1 to 12, amendments X1 and X2)")

    # ---- design constants ------------------------------------------------------------------------------------------------------------
    g1b = _json("runs/acme-G1b/run.json")
    sh = g1b["config"]["shapes"]
    nm, nw = int(NUMBERS["n.models"].value), 10
    n2, n1, nt = sh["two_order_items"], sh["one_order_items"], sh["temperatures"]
    assert (sh["models"], sh["wordings"]) == (nm, nw) and n2 == int(NUMBERS["n.items.twoorder"].value) and n1 == int(NUMBERS["n.items.oneorder"].value)
    assert nt == int(NUMBERS["n.temps"].value)
    cells = nm * nw * (2 * n2 + n1)
    out["bm.cells.T1"] = Entry(_n(cells), "runs/acme-G1b/run.json#config.shapes (14 x 10 x (5 two-order x 2 + 5 one-order)); PREREG section 2")
    out["bm.cells.all"] = Entry(_n(cells * nt), "as bm.cells.T1 times the number of temperatures")
    tn = _read("analysis/acme/numtree.py")
    cap = int(_rx(tn, r"max_exp=(\d+)", "tree cap").group(1))
    assert f"{cap} expansions" in pre
    out["bm.tree.cap"] = Entry(_n(cap), f"analysis/acme/numtree.py#expand_trees(max_exp); {P}#A-L2")
    stop = _rx(tn, r"stop_unresolved=0\.0?(\d+)", "unresolved stop").group(1).lstrip("0") or "0"
    assert f"unresolved mass at most {stop} percent" in pre
    out["bm.tree.stop"] = Entry(stop, f"analysis/acme/numtree.py#expand_trees(stop_unresolved); {P}#A-L2")
    mp = _rx(tn, r"min_prob=1e-(\d+)", "tree min_prob").group(1)
    mc = _rx(tn, r"min_child=1e-(\d+)", "tree min_child").group(1)
    th = _rx(tn, r"thresh=(\d+)\.0", "tree thresh").group(1)
    pre1 = re.sub(r"\s+", " ", pre)
    assert f"best open node below 1e-{mp}" in pre1 and f"within {th} nats" in pre1 and f"above 1e-{mc} absolute" in pre1
    out["bm.tree.minp"] = Entry(f"10^{{-{mp}}}", f"analysis/acme/numtree.py#expand_trees(min_prob); {P}#A-L2 (best open node)")
    out["bm.tree.minchild"] = Entry(f"10^{{-{mc}}}", f"analysis/acme/numtree.py#expand_trees(min_child); {P}#A-L2 (child kept above)")
    out["bm.tree.thresh"] = Entry(th, f"analysis/acme/numtree.py#expand_trees(thresh); {P}#A-L2 (within 12 nats of the best token)")
    cal = _json("runs/acme-tree-calib/summary.json")["summary"][str(cap)]
    mae_r, mae_l = _fx(cal["mae_resolved"], 3), _fx(cal["mae_lb"], 3)
    assert f"= {mae_r} log units for resolved-only" in pre and f"and {mae_l} for y_lb (n = {cal['n']}" in pre
    out["bm.tree.mae"] = Entry(mae_r, "runs/acme-tree-calib/summary.json#summary.1024.mae_resolved (pilot prompts only)")
    out["bm.tree.maelb"] = Entry(mae_l, "runs/acme-tree-calib/summary.json#summary.1024.mae_lb (pilot prompts only)")
    out["bm.tree.ncal"] = Entry(str(cal["n"]), "runs/acme-tree-calib/summary.json#summary.1024.n")
    vm = _rx(pre, r"valid mass < (0\.9) on more than (\d) percent of its prompts", "valid-mass rule")
    out["bm.vm.thr"] = Entry(vm.group(1), f"{P}#section 7 (valid-mass rule)")
    out["bm.vm.frac"] = Entry(vm.group(2), f"{P}#section 7 (valid-mass rule)")
    out["bm.vm.s1"] = Entry(_rx(pre, r"Sensitivity S1: threshold (0\.5)", "S1").group(1), f"{P}#section 7 (S1)")
    g3 = _rx(pre, r"at least (\d+) models and (\d+) of 10 items", "G3")
    out["bm.g3.models"] = Entry(g3.group(1), f"{P}#section 6 (G3)")
    out["bm.g3.items"] = Entry(g3.group(2), f"{P}#section 6 (G3)")
    g4 = _rx(pre, r"slope in \[(0\.9), (1\.1)\] and SD of the\s+z-scores .*? at most (1\.3)", "G4")
    out["bm.g4.lo"], out["bm.g4.hi"], out["bm.g4.z"] = (Entry(g4.group(i), f"{P}#section 6 (G4)") for i in (1, 2, 3))
    cs = _read("analysis/acme/config_S.yaml")
    out["bm.s.draws"] = Entry(_rx(cs, r"^  n: (\d+)$", "Arm S draws").group(1), "analysis/acme/config_S.yaml#design.n")
    ws = re.findall(r"^  - (W\d)$", cs.split("temps:")[0].split("wordings:")[1], re.M)
    out["bm.s.nw"] = Entry(_WORDS[len(ws)], "analysis/acme/config_S.yaml#design.wordings")
    tl = re.findall(r"^  - (\d\.\d)$", cs.split("temps:")[1].split("orders_P1")[0], re.M)
    out["bm.s.temps"] = Entry(" and ".join(tl), "analysis/acme/config_S.yaml#design.temps")
    assert (len(ws), tl) == (4, ["0.7", "1.0"])
    ras = _read("analysis/acme/run_armS.py")
    s2 = _rx(ras, r'"S2new": dict\(F="F1", temps=\[(1\.0)\], n=(\d+)', "Arm S stage S2")
    cplan = _read("research/relaunch/compute-plan.md")
    assert f"F1 reasoning format, T = {s2.group(1)}, n = {s2.group(2)}" in cplan
    out["bm.s2.temp"] = Entry(s2.group(1), "analysis/acme/run_armS.py#STAGES.S2new.temps; research/relaunch/compute-plan.md (S2 row)")
    out["bm.s2.draws"] = Entry(s2.group(2), "analysis/acme/run_armS.py#STAGES.S2new.n; research/relaunch/compute-plan.md (S2 row)")
    pm = _rx(cplan, r"\| Pilot design \| (\d+) models, 4 wordings", "pilot roster size")
    assert "pilot's greedy answers" in re.sub(r"\s+", " ", pre)   # PREREG section 0: the smoke test compared readouts with the pilot's answers
    out["bm.pilot.models"] = Entry(_WORDS[int(pm.group(1))], "research/relaunch/compute-plan.md (Pilot design row: 6 models, W0-W3, 76,800 responses); PREREG-acme.md section 0")
    est = _read("analysis/pilot/estimators.py")
    out["sh.K"] = Entry(_rx(est, r"def split_half_var\([^)]*K=(\d+)", "split-half K").group(1), "analysis/pilot/estimators.py#split_half_var(K); erratum E5 (K = 200)")
    gst = _read("analysis/acme/gstudy.py")
    dt = _rx(gst, r"def dstudy_min_design\(components, target=(0\.\d+)", "D-study target").group(1)
    assert f"0.1 ML1-SD" in _read("research/relaunch/PREREG-acme-ERRATA.md") and dt == "0.1"
    out["bm.dstudy.target"] = Entry(dt, "analysis/acme/gstudy.py#dstudy_min_design(target); research/relaunch/PREREG-acme-ERRATA.md E6 item 3")

    # ---- wordings, decoys and the equivalence check --------------------------------------------------------------------------------
    man = _json("analysis/acme/prompts/MANIFEST.json")
    files = man.get("files", man)
    dec = [k for k in files if k.startswith("decoys/")]
    items = {k.split("/")[1].split("_")[0] for k in dec}
    assert len(dec) == 20 and len(items) == 10
    out["bm.decoys.per"] = Entry(_WORDS[len(dec) // len(items)], "analysis/acme/prompts/MANIFEST.json (decoy files per item)")
    sc = _json("runs/acme-equivalence/scores.json")
    A, B = sc["judgeA"], sc["judgeB"]
    assert A["decoy_detected"] == B["decoy_detected"] == sc["n_decoy"] == 20 and A["paraphrase_equivalent"] == B["paraphrase_equivalent"] == sc["n_paraphrase"] == 90
    assert sc["flagged_total"] == 0 and sc["n_pairs"] == 110
    out["bm.eq.pairs"] = Entry(str(sc["n_pairs"]), "runs/acme-equivalence/scores.json#n_pairs")
    out["bm.eq.para"] = Entry(str(sc["n_paraphrase"]), "runs/acme-equivalence/scores.json#n_paraphrase")
    out["bm.eq.decoy"] = Entry(str(sc["n_decoy"]), "runs/acme-equivalence/scores.json#n_decoy (both judges detected all)")
    out["bm.eq.flag"] = Entry(str(sc["flagged_total"]), "runs/acme-equivalence/scores.json#flagged_total")
    kj = _json("runs/acme-equivalence/key.json")
    low = {}
    for jn in ("A", "B"):
        rows = [json.loads(l) for l in (ROOT / f"runs/acme-equivalence/judge_{jn}.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]
        low[jn] = sum(1 for r in rows if kj[r["id"]]["kind"] == "paraphrase" and int(r["confidence"]) < 5)
    assert low == {"A": 7, "B": 0}, low
    out["bm.eq.lowconf"] = Entry(_WORDS[low["A"]], "runs/acme-equivalence/judge_A.jsonl#confidence (paraphrase pairs below 5; key.json#kind); judge B gave none")

    # ---- human reference -------------------------------------------------------------------------------------------------------------
    bt = {}
    for rel in ("runs/human-ml1/benchmark_table.csv", "runs/human-ml1-acme/benchmark_table.csv"):
        for r in _csv(rel):
            bt[(r["paradigm"], r["metric"])] = r
    zero_pub = sorted(i for i in ("P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR") if float(bt[(i, "primary")]["S_H"]) == 0.0)
    assert zero_pub == ["AF", "NR", "P3"], zero_pub
    out["bm.sh.zero.pub"] = Entry(_WORDS[len(zero_pub)], "runs/human-ml1/benchmark_table.csv and runs/human-ml1-acme/benchmark_table.csv#S_H (primary rows equal to 0)")
    shu = {r["item"]: r for r in _csv("runs/human-ml1-acme/SH_sd_units.csv")}
    assert sorted(i for i, r in shu.items() if float(r["S_sd_lo"]) == 0.0) == ["AF", "NR", "P1", "P3"]
    assert all(float(r["S_sd"]) > 0 for r in shu.values())
    out["bm.sh.pos"] = Entry(_WORDS[len(shu)], "runs/human-ml1-acme/SH_sd_units.csv#S_sd (all items positive)")
    p1 = bt[("P1", "primary")]
    out["bm.p1.tau"] = Entry(_fx(p1["tau"], 2), "runs/human-ml1/benchmark_table.csv#tau (P1 primary)")
    out["bm.p1.tau.hi"] = Entry(_fx(p1["tau_hi"], 2), "runs/human-ml1/benchmark_table.csv#tau_hi (P1 primary)")
    af, afc = bt[("AF", "primary")], bt[("AF", "check_ml1_published_yes_coding")]
    cs_af = {r["item"]: r for r in _csv("runs/human-ml1-acme/canonical_signs.csv")}["AF"]
    assert cs_af["canonical_sign"] == "-1" and float(af["mu"]) < 0
    for tag, fld in (("mu", "mu"), ("lo", "mu_lo"), ("hi", "mu_hi")):
        out[f"bm.af.{tag}"] = Entry(_sg(af[fld], 2), f"runs/human-ml1-acme/benchmark_table.csv#{fld} (AF primary)")
    out["bm.af.tau"] = Entry(_fx(af["tau"], 2), "runs/human-ml1-acme/benchmark_table.csv#tau (AF primary)")
    out["bm.af.tau.hi"] = Entry(_fx(af["tau_hi"], 2), "runs/human-ml1-acme/benchmark_table.csv#tau_hi (AF primary)")
    out["bm.af.pub.tau"] = Entry(_fx(afc["tau"], 2), "runs/human-ml1-acme/benchmark_table.csv#tau (AF, published coding)")
    out["bm.af.pub.tau.lo"] = Entry(_fx(afc["tau_lo"], 2), "runs/human-ml1-acme/benchmark_table.csv#tau_lo (AF, published coding)")
    out["bm.af.pub.tau.hi"] = Entry(_fx(afc["tau_hi"], 2), "runs/human-ml1-acme/benchmark_table.csv#tau_hi (AF, published coding)")
    pc = _json("runs/human-ml1-acme/published_comparison.json")["AF"]["published"]
    out["bm.af.pub.d"] = Entry(_fx(pc["d"], 2), "runs/human-ml1-acme/published_comparison.json#AF.published.d")

    # ---- roster ------------------------------------------------------------------------------------------------------------------------
    ros = [r for r in roster() if r["control"] == "false"]
    ctl = [r for r in roster() if r["control"] == "true"]
    assert len(ros) == nm and len(ctl) == 1
    nf4 = [r for r in ros if r["quant"] == "nf4_saved"]
    bf = [r for r in ros if r["quant"] == "bf16"]
    assert len(nf4) + len(bf) == nm
    sz = [float(r["params_b"]) for r in ros]
    out["bm.models.nf4"] = Entry(_WORDS[len(nf4)], "analysis/acme/models.yaml#quant (nf4_saved, controls excluded)")
    out["bm.models.bf16"] = Entry(_WORDS[len(bf)], "analysis/acme/models.yaml#quant (bf16, controls excluded)")
    out["bm.models.fam"] = Entry(_WORDS[len({r["family"] for r in ros})], "analysis/acme/models.yaml#family")
    out["bm.size.min"] = Entry(_fx(min(sz), 2), "analysis/acme/models.yaml#params_b (minimum)")
    out["bm.size.max"] = Entry(_fx(max(sz), 1), "analysis/acme/models.yaml#params_b (maximum)")
    out["bm.bf16.max"] = Entry(_fx(max(float(r["params_b"]) for r in bf), 2), "analysis/acme/models.yaml#params_b (largest bf16 model)")
    out["bm.nf4.min"] = Entry(_fx(min(float(r["params_b"]) for r in nf4), 2), "analysis/acme/models.yaml#params_b (smallest NF4 model)")
    assert max(float(r["params_b"]) for r in bf) < min(float(r["params_b"]) for r in nf4)  # precision is confounded with size
    qw = [r for r in ros if r["family"] == "Qwen2.5"]
    out["bm.qwen.n"] = Entry(_WORDS[len(qw)], "analysis/acme/models.yaml#family=Qwen2.5")
    lics = [r["licence"] for r in ros]
    assert set(lics) == {"apache-2.0", "mit"}
    out["bm.lic.apache"] = Entry(_WORDS[lics.count("apache-2.0")], "runs/models/MODELS.jsonl#license (apache-2.0)")
    out["bm.lic.mit"] = Entry(_WORDS[lics.count("mit")], "runs/models/MODELS.jsonl#license (mit)")

    # ---- gate G1 (synthetic, pooled level) -----------------------------------------------------------------------------------------
    r1 = _json("runs/acme-G1/run.json")
    vt = _read("runs/acme-G1/VERDICT.md")
    g1 = {}
    for tag, fn, var in (("first", "results.csv", "as_written"), ("a", "results_A1.csv", "A1")):
        P_ = [r for r in _csv(f"runs/acme-G1/{fn}") if r["level"] == "pooled_mean"]
        assert len(P_) == 63 and {r["variant"] for r in P_} == {var} and {int(r["reps"]) for r in P_} == {r1["cfg"]["reps"]}
        cov = [float(r["coverage"]) for r in P_]
        zero = [r for r in P_ if r["true_is_zero"] == "True"]
        rk = [float(r["rank_correct_rate"]) for r in P_ if r["rank_applicable"] == "True"]
        g1[tag] = {"bias": max(abs(float(r["bias"])) for r in P_), "cov": sum(0.90 <= c <= 0.98 for c in cov), "n": len(P_),
                   "fp": max(float(r["false_positive_rate"]) for r in zero), "nzero": len(zero), "rank": min(rk), "nrank": len(rk)}
    # reconcile with the rendered verdict table (generated by simulate_G1.py): rows `as_written` and `A1`
    row_first = _rx(vt, r"^\| `as_written` \| (\w+) \| FAIL \((\d+)/63\) \| (\w+) \| (\w+) \| \*\*(\w+)\*\* \|", "G1 first row")
    row_a = _rx(vt, r"^\| `A1` \| (\w+) \| PASS \((\d+)/63\) \| (\w+) \| (\w+) \| \*\*(\w+)\*\* \|", "G1 A1 row")
    assert row_first.group(5) == "FAIL" and row_a.group(5) == "PASS"
    assert int(row_first.group(2)) == g1["first"]["cov"] and int(row_a.group(2)) == g1["a"]["cov"]
    assert row_first.group(1, 3, 4) == ("FAIL", "FAIL", "PASS") and row_a.group(1, 3, 4) == ("PASS", "PASS", "PASS")
    assert f"worst b/W bias -{_fx(g1['first']['bias'], 3)}" in vt and f"worst b/W bias +{_fx(g1['a']['bias'], 3)}" in vt
    assert f"worst d/W {_fx(g1['a']['fp'], 3)}" in vt and g1["a"]["rank"] == 1.0 == g1["first"]["rank"]
    crit = _rx(pre, r"\|bias\| of each share ≤ (0\.02); coverage of the 95 percent interval between (0\.90) and (0\.98) in at least "
                    r"(\d+) percent of\s+scenario-components; false-positive rate .*? ≤ (0\.05) .*? in at least (\d+) percent", "G1 criteria")
    c_bias, c_lo, c_hi, c_cov, c_fp, c_rank = crit.groups()[0], crit.groups()[1], crit.groups()[2], crit.groups()[3], crit.groups()[4], crit.groups()[5]
    import math as _m
    need = _m.ceil(int(c_cov) / 100 * g1["a"]["n"])
    S7PRE_RAW["g1"] = {**g1, "need": need, "crit": {"bias": c_bias, "lo": c_lo, "hi": c_hi, "cov": c_cov, "fp": c_fp, "rank": c_rank}}
    out["bm.g1.reps"] = Entry(_n(r1["cfg"]["reps"]), "runs/acme-G1/run.json#cfg.reps")
    out["bm.g1.B"] = Entry(_n(r1["cfg"]["B"]), "runs/acme-G1/run.json#cfg.B")
    out["bm.g1.nscen"] = Entry(_WORDS[len(r1["cfg"]["scenarios"])], "runs/acme-G1/run.json#cfg.scenarios")
    out["bm.g1.ncomp"] = Entry(str(g1["a"]["n"]), "runs/acme-G1/results_A1.csv (rows at level pooled_mean)")
    out["bm.g1.crit.bias"] = Entry(c_bias, f"{P}#section 6 (G1 criterion C1)")
    out["bm.g1.crit.lo"], out["bm.g1.crit.hi"] = Entry(c_lo, f"{P}#section 6 (C2)"), Entry(c_hi, f"{P}#section 6 (C2)")
    out["bm.g1.crit.cov"] = Entry(c_cov, f"{P}#section 6 (C2)")
    out["bm.g1.crit.fp"] = Entry(c_fp, f"{P}#section 6 (C3)")
    out["bm.g1.crit.rank"] = Entry(c_rank, f"{P}#section 6 (C4)")
    out["bm.g1.nzero"] = Entry(str(g1["a"]["nzero"]), "runs/acme-G1/results_A1.csv (pooled rows with true_is_zero)")
    out["bm.g1.first.cov"] = Entry(str(g1["first"]["cov"]), "runs/acme-G1/results.csv#coverage (pooled rows in 0.90 to 0.98)")
    out["bm.g1.first.bias"] = Entry(_fx(g1["first"]["bias"], 3), "runs/acme-G1/results.csv#bias (largest absolute, pooled rows)")
    out["bm.g1.first.fp"] = Entry(_fx(g1["first"]["fp"], 2), "runs/acme-G1/results.csv#false_positive_rate (largest, pooled zero rows)")
    out["bm.g1.a.cov"] = Entry(str(g1["a"]["cov"]), "runs/acme-G1/results_A1.csv#coverage (pooled rows in 0.90 to 0.98)")
    out["bm.g1.a.bias"] = Entry(_fx(g1["a"]["bias"], 3), "runs/acme-G1/results_A1.csv#bias (largest absolute, pooled rows)")
    out["bm.g1.a.fp"] = Entry(_fx(g1["a"]["fp"], 3), "runs/acme-G1/results_A1.csv#false_positive_rate (largest, pooled zero rows)")
    out["bm.g1.a.rank"] = Entry(_fx(g1["a"]["rank"], 3), "runs/acme-G1/results_A1.csv#rank_correct_rate (lowest, applicable rows)")
    out["bm.g1.first.nviol"] = Entry(_rx(vt, r"\| C3 false positives \|[^\n]*\| (\d+) of 19 violate; worst a/M 1\.000", "first C3").group(1),
                                     "runs/acme-G1/VERDICT.md (variant as_written, C3 row: components violating)")

    # ---- gate G1b (synthetic; generated tables of VERDICT.md only, reconciled with the result files) ------------------------------
    gv = _read("runs/acme-G1b/VERDICT.md").split("## Diagnostics")[0]
    reps = g1b["config"]["reps"]
    lim = g1b["config"]["pass_max"]
    assert _fx(lim, 4) in gv
    rates = {}
    for h in ("H1", "H2", "H3"):
        m = _rx(gv, rf"^\| {h} \| (\d+) \| (\d+) \| ([\d.]+) \| [\d.]+ \| 0\.0695 \| \*\*PASS\*\* \|", f"G1b null row {h}")
        k, n = int(m.group(2)), int(m.group(1))
        df = _csv(f"runs/acme-G1b/results_{h}_null.csv")
        pcol = f"p_{h}"
        assert len(df) == n == reps[f"{h}_null"] and sum(float(r[pcol]) < 0.05 for r in df) == k
        pa = _rx(gv, rf"^\| {h} \| [^\n]*? \| (\d+) \| ([\d.]+) \| [\d.]+ \|$", f"G1b power row {h}")
        dfa = _csv(f"runs/acme-G1b/results_{h}_alt.csv")
        assert len(dfa) == int(pa.group(1)) == reps[f"{h}_alt"]
        ka = sum(float(r[pcol]) < 0.05 for r in dfa)
        assert abs(ka / len(dfa) - float(pa.group(2))) < 5e-4
        rates[h] = {"k": k, "n": n, "rate": k / n, "ka": ka, "na": len(dfa)}
        out[f"bm.g1b.{h}.k"] = Entry(str(k), f"runs/acme-G1b/VERDICT.md (type-I table, {h} rejections); results_{h}_null.csv#{pcol}")
        out[f"bm.g1b.{h}.rate"] = Entry(_fx(k / n, 3), f"runs/acme-G1b/VERDICT.md (type-I table, {h} rejection rate)")
        out[f"bm.g1b.{h}.pow"] = Entry(_fx(ka / len(dfa), 3), f"runs/acme-G1b/VERDICT.md (power table, {h}); results_{h}_alt.csv#{pcol}")
    S7PRE_RAW["g1b"] = {"rates": rates, "lim": lim}
    # erratum E2.3 and E6.4: two H3 null replicates have p = 0.05 exactly; counted as rejections the rate is 27/500, whose exact
    # upper 95 percent bound exceeds the limit
    from scipy.stats import beta as _beta
    h3p = [float(r["p_H3"]) for r in _csv("runs/acme-G1b/results_H3_null.csv")]
    ties = sum(abs(p - 0.05) < 1e-12 for p in h3p)
    k_tie = rates["H3"]["k"] + ties
    assert (ties, k_tie, len(h3p)) == (2, 27, 500)
    ub = float(_beta.ppf(0.95, k_tie + 1, len(h3p) - k_tie))
    assert ub > lim
    out["bm.g1b.H3.ties"] = Entry(_WORDS[ties], "runs/acme-G1b/results_H3_null.csv#p_H3 (replicates with p = 0.05 exactly); ERRATA E2 item 3")
    out["bm.g1b.H3.k.tie"] = Entry(str(k_tie), "runs/acme-G1b/results_H3_null.csv#p_H3 (p <= 0.05 counted as rejection); ERRATA E2 item 3")
    out["bm.g1b.H3.rate.tie"] = Entry(_fx(k_tie / len(h3p), 3), "as bm.g1b.H3.k.tie divided by the number of null replicates")
    out["bm.g1b.H3.ub"] = Entry(_fx(ub, 3), "scipy.stats.beta.ppf(0.95, k+1, n-k) with k = bm.g1b.H3.k.tie, n = 500 (exact one-sided upper 95 percent bound); ERRATA E6 item 4")
    out["bm.g1b.n"] = Entry(str(reps["H1_null"]), "runs/acme-G1b/run.json#config.reps (null replicates per hypothesis)")
    out["bm.g1b.na"] = Entry(str(reps["H1_alt"]), "runs/acme-G1b/run.json#config.reps (alternative replicates per hypothesis)")
    out["bm.g1b.B"] = Entry(_n(g1b["config"]["B"]), "runs/acme-G1b/run.json#config.B")
    out["bm.g1b.lim"] = Entry(_fx(lim, 4), "runs/acme-G1b/run.json#config.pass_max")
    out["bm.g1b.cp"] = Entry(_fx(g1b["config"]["c_p"], 1), "runs/acme-G1b/run.json#config.c_p")
    nul = _rx(pre, r"H1, pooled wording share \(W \+ M×W\) = T share = (0\.25) in every item; H3, M×W share\s+= W share = (0\.30), residual (0\.40)", "G1b nulls")
    out["bm.g1b.h1null"], out["bm.g1b.h3null"], out["bm.g1b.h3res"] = (Entry(nul.group(i), f"{P}#section 6 (G1b boundary nulls)") for i in (1, 2, 3))
    h2n = _csv("runs/acme-G1b/results_H2_null.csv")
    hold, tests = sum(int(float(r["H2_n_hold"])) for r in h2n), sum(int(float(r["H2_k"])) for r in h2n)
    assert (hold, tests) == (8, 5000) and rates["H2"]["k"] == 0
    out["bm.g1b.h2.item.k"] = Entry(str(hold), "runs/acme-G1b/results_H2_null.csv#H2_n_hold (summed)")
    out["bm.g1b.h2.item.n"] = Entry(_n(tests), "runs/acme-G1b/results_H2_null.csv#H2_k (summed)")
    out["bm.g1b.h2.item.rate"] = Entry(_fx(hold / tests, 4), "runs/acme-G1b/results_H2_null.csv#H2_n_hold / H2_k")
    msd = sum(float(r["H2_mean_median_sd"]) for r in h2n) / len(h2n)
    out["bm.g1b.h2.msd"] = Entry(_fx(msd, 3), "runs/acme-G1b/results_H2_null.csv#H2_mean_median_sd (mean over replicates)")
    out["bm.g1b.h2.alt"] = Entry(_fx(2 * g1b["config"]["c_p"], 1), "runs/acme-G1b/run.json#config.c_p (alternative: twice the null)")
    return out


NUMBERS.update(_section7pre_numbers())


def _human_pooled_numbers() -> dict[str, Entry]:
    """Pooled human effect on Delta's scale (erratum E6 item 2), ML1-SD units, 2 decimals. Human data only."""
    out: dict[str, Entry] = {}
    f = "runs/human-ml1-acme/pooled_sd_units.csv"
    rows = _csv(f)
    assert [r["item"] for r in rows] == ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR"]
    for r in rows:
        assert r["orientation_ok"] == "True", r["item"]
        for k, col in (("mu", "mu_sd"), ("lo", "mu_sd_lo"), ("hi", "mu_sd_hi")):
            out[f"hp.{r['item']}.{k}"] = Entry(_sg(r[col], 2), f"{f}#{col} (REML mean of site raw differences / sd_within; Wald 95 percent)")
    return out


NUMBERS.update(_human_pooled_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 7 verification results (D0034, E7): gates G3 and G4 on the full data and the two readout diagnostics. Every value is
# read from the gate and diagnostic outputs (audited, runs/gate-audits/G3G4-AUDIT.md).
# --------------------------------------------------------------------------------------------------------------------------
def _verification_numbers() -> dict[str, Entry]:
    import json
    out: dict[str, Entry] = {}
    g3f = "runs/acme-L/outcomes/G3.json"
    g3 = _json(g3f)
    out["vf.g3.pairs"] = Entry(str(g3["n_pairs"]), f"{g3f}#n_pairs")
    out["vf.g3.excl"] = Entry(str(g3["n_excluded"]), f"{g3f}#n_excluded")
    out["vf.g3.a"] = Entry(_WORDS[g3["G3_reading_a"]["models_valid_on_8plus_items"]], f"{g3f}#G3_reading_a.models_valid_on_8plus_items")
    out["vf.g3.b"] = Entry(_WORDS[g3["G3_reading_b"]["items_with_10plus_valid_models"]], f"{g3f}#G3_reading_b.items_with_10plus_valid_models")
    assert g3["G3_pass"] is False
    for tag, d in (("main", "runs/acme-L/G4"), ("sampledSE", "runs/acme-L/G4-alt-sampledSE"), ("noexcl", "runs/acme-L/G4-alt-noexcl")):
        g4 = _json(f"{d}/G4.json")
        assert g4["G4_complete"] and not g4["models_incomplete"]
        out[f"vf.g4.{tag}.pass"] = Entry(_WORDS[len(g4["models_pass"])], f"{d}/G4.json#models_pass (count)")
        out[f"vf.g4.{tag}.fail"] = Entry(_WORDS[len(g4["models_fail"])], f"{d}/G4.json#models_fail (count)")
    out["vf.g4.cells"] = Entry(_n(_json("runs/acme-L/G4/G4.json")["n_cells"]), "runs/acme-L/G4/G4.json#n_cells")
    for r in _csv("runs/acme-L/G4/pooled_type.csv"):
        out[f"vf.g4.pool.{r['type']}.slope"] = Entry(_fx(r["slope"], 3), f"runs/acme-L/G4/pooled_type.csv#slope ({r['type']})")
        if r["type"] != "numeric":
            out[f"vf.g4.pool.{r['type']}.zsd"] = Entry(_fx(r["z_sd"], 2), f"runs/acme-L/G4/pooled_type.csv#z_sd ({r['type']})")
    # Defect 1: valid mass above 1 in the rating/choice readouts; path-pass vs single-pass gap
    import csv as _c
    n_rows = n1 = n1001 = 0
    with open(ROOT / "runs/acme-L/outcomes/outcomes.csv", encoding="utf-8") as f:
        for r in _c.DictReader(f):
            n_rows += 1
            if r["valid"] and float(r["valid"]) > 1.0:
                n1 += 1
                n1001 += float(r["valid"]) > 1.001
    out["vf.d1.rows"] = Entry(_n(n_rows), "runs/acme-L/outcomes/outcomes.csv (rows)")
    out["vf.d1.gt1"] = Entry(_n(n1), "runs/acme-L/outcomes/outcomes.csv#valid (> 1.0)")
    out["vf.d1.gt1001"] = Entry(_n(n1001), "runs/acme-L/outcomes/outcomes.csv#valid (> 1.001)")
    pcf = "runs/acme-L/diagnostics/pass_consistency_summary.json"
    pc = _json(pcf)
    lg = pc["logit_gap_T1"]
    out["vf.d1.gap.med"], out["vf.d1.gap.p95"], out["vf.d1.gap.max"] = (Entry(_fx(lg[k], nd), f"{pcf}#logit_gap_T1.{k}") for k, nd in (("median_abs", 3), ("p95_abs", 2), ("max_abs", 1)))
    b1, b03 = pc["by_T"]["1.0"], pc["by_T"]["0.3"]
    out["vf.d1.dy.med"] = Entry(_fx(b1["dy_median_abs"], 3), f"{pcf}#by_T.1.0.dy_median_abs")
    out["vf.d1.dy.p95"] = Entry(_fx(b1["dy_p95_abs"], 2), f"{pcf}#by_T.1.0.dy_p95_abs")
    out["vf.d1.dy.max"] = Entry(_fx(b1["dy_max_abs"], 1), f"{pcf}#by_T.1.0.dy_max_abs")
    out["vf.d1.vmax.T1"] = Entry(_fx(b1["valid_path_max"], 2), f"{pcf}#by_T.1.0.valid_path_max")
    out["vf.d1.vmax.T03"] = Entry(_fx(b03["valid_path_max"], 2), f"{pcf}#by_T.0.3.valid_path_max")
    out["vf.d1.vsingle.max"] = Entry(_fx(max(pc["by_T"][t]["valid_single_max"] for t in pc["by_T"]), 5), f"{pcf}#by_T.*.valid_single_max (max)")
    # Defect 2: verbal multipliers on P2b
    mf = "runs/acme-L/diagnostics/multiplier_share.csv"
    ms = _csv(mf)
    p2b = sorted((float(r["share"]) for r in ms if r["item"] == "P2b" and r["share"]), reverse=True)
    other = max(float(r["share"]) for r in ms if r["item"] != "P2b" and r["share"])
    out["vf.d2.p2b.max"] = Entry(_fx(p2b[0], 2), f"{mf}#share (P2b, max over models)")
    out["vf.d2.p2b.n10"] = Entry(_WORDS[sum(x >= 0.10 for x in p2b)], f"{mf}#share (P2b, models with share >= 0.10)")
    out["vf.d2.other.max"] = Entry(_fx(other, 2), f"{mf}#share (P2a, P2c, P2d, P4: max over models)")
    cells = _csv("runs/acme-L/G4/cells.csv")
    ex = [r for r in cells if (r["model"], r["item"], r["W"], r["T"]) == ("olmo2-7b-instruct", "P2b", "W1", "0.7")]
    assert len(ex) == 1
    out["vf.d2.ex.dL"] = Entry(_sg(ex[0]["dL"], 1), "runs/acme-L/G4/cells.csv#dL (olmo2-7b-instruct, P2b, W1, T 0.7)")
    out["vf.d2.ex.dS"] = Entry(_sg(ex[0]["dS"], 2), "runs/acme-L/G4/cells.csv#dS (olmo2-7b-instruct, P2b, W1, T 0.7)")
    # rosters per item (D0034)
    for r in _csv("runs/acme-L/rosters.csv"):
        for k in ("validmass_only", "per_model", "per_type"):
            out[f"vf.roster.{k.replace('_', '')}.{r['item']}"] = Entry(r[k], f"runs/acme-L/rosters.csv#{k} ({r['item']})")
    return out


NUMBERS.update(_verification_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Section 7 results (CRP-S09, post-outcome, descriptive; spec research/relaunch/acme-gates/S7-REWRITE-SPEC.md, errata E7 to E7b).
# Keys: rt.* route table (columns a, b, c, eS = (e)-Arm S, eL = (e)-Arm L; sensitivities under rt.sens.*), hy.* hypotheses as
# estimates (hypotheses_estimates.csv; the p-values of hypotheses.json are never read, audit C3), ys.* human yardsticks,
# syn.* synthetic check of the sampled-arm estimator. Shares are the untruncated mean-square shares, two decimals.
# Groups: M; O = O + MxO; W; MW = MxW; WO = WxO + MxWxO; T = every component that contains T; res; draw (Arm S E2 only).
# --------------------------------------------------------------------------------------------------------------------------
RT_DIR = "runs/acme-gstudy/route-table"
RT_COLS = {"(a)": ("a", "E2"), "(b)": ("b", "A1"), "(c)": ("c", "A1"), "(e)-ArmS": ("eS", "E2"), "(e)-ArmL": ("eL", "A1")}
CR_ITEMS = ["AF", "NR", "P1", "P3", "QA"]
NUM_ITEMS = ["P2a", "P2b", "P2c", "P2d", "P4"]
THR_E7A = 0.06


def _grp(comp: str) -> str:
    if comp.startswith("res"):
        return "res"
    if comp == "draw":
        return "draw"
    if comp in ("O", "MO"):
        return "O"
    if comp in ("WO", "MWO"):
        return "WO"
    if "T" in comp:
        return "T"
    return comp  # M, W, MW


def _route_groups(rows: list[dict[str, str]], column: str, basis: str) -> dict[tuple[str, str], float]:
    """Sum of untruncated shares per (item, group) for one route-table column (main decomposition, all temperatures)."""
    out: dict[tuple[str, str], float] = {}
    for r in rows:
        if r["column"] != column or r["basis"] != basis or r["analysis"] not in ("A1-S", "4facet") or not r["component"]:
            continue
        key = (r["item"], _grp(r["component"]))
        out[key] = out.get(key, 0.0) + float(r["share"])
    return out


def _comp_shares(rows: list[dict[str, str]], column: str, basis: str) -> dict[tuple[str, str], float]:
    d = {}
    for r in rows:
        if r["column"] == column and r["basis"] == basis and r["analysis"] in ("A1-S", "4facet") and r["component"] and r["component"] != "draw":
            d[(r["item"], "res" if r["component"].startswith("res") else r["component"])] = float(r["share"])
    return d


def _section7res_numbers() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    rtf = f"{RT_DIR}/route_table.csv"
    rows = _csv(rtf)
    # roster sizes (words) per column and item
    seen = set()
    for r in rows:
        if r["column"] in RT_COLS and r["n_models"] and (r["column"], r["item"]) not in seen:
            seen.add((r["column"], r["item"]))
            c = RT_COLS[r["column"]][0]
            out[f"rt.{c}.n.{r['item']}"] = Entry(_WORDS[int(float(r["n_models"]))], f"{rtf}#n_models (column {r['column']}, item {r['item']})")
    nw = {r["n_wordings"] for r in rows if r["column"] in ("(a)", "(e)-ArmS", "(e)-ArmL") and r["n_wordings"]}
    assert nw == {"4.0"}, nw
    out["rt.a.nw"] = Entry("four", f"{rtf}#n_wordings (columns (a), (e)-Arm S, (e)-Arm L)")
    out["rt.thr"] = Entry(_fx(THR_E7A, 2), "research/relaunch/PREREG-acme-ERRATA.md E7a item 3 (differences under this value are not interpreted)")
    groups: dict[str, dict[tuple[str, str], float]] = {}
    for col, (c, basis) in RT_COLS.items():
        g = _route_groups(rows, col, basis)
        groups[c] = g
        for (item, grp), v in g.items():
            out[f"rt.{c}.{grp}.{item}"] = Entry(_sg(v, 2), f"{rtf}#share (column {col}, basis {basis}, item {item}, group {grp} = sum of components)")

    for c, g in groups.items():
        for item in {i for i, _ in g}:
            if (item, "M") in g and (item, "O") in g:
                out[f"rt.{c}.MplusO.{item}"] = Entry(_sg(g[(item, "M")] + g[(item, "O")], 2), f"{rtf}#share (column {c}, item {item}, groups M + O = sum of components)")

    def _rng(c: str, grp: str, items: list[str], tag: str, absolute: bool = False) -> None:
        vals = [groups[c][(i, grp)] for i in items if (i, grp) in groups[c]]
        what = f"{rtf}#share (column {c}, group {grp}, items {'/'.join(items)}"
        if absolute:
            out[f"rt.{c}.{grp}.{tag}.maxabs"] = Entry(_fx(max(abs(v) for v in vals), 2), what + "; maximum of absolute values)")
        else:
            out[f"rt.{c}.{grp}.{tag}.min"] = Entry(_sg(min(vals), 2), what + "; minimum)")
            out[f"rt.{c}.{grp}.{tag}.max"] = Entry(_sg(max(vals), 2), what + "; maximum)")

    for c in ("a", "b", "eS", "eL"):
        for grp in ("T", "O", "MW"):
            _rng(c, grp, CR_ITEMS, "cr")
        _rng(c, "W", CR_ITEMS, "cr", absolute=True)
    _rng("a", "MW", NUM_ITEMS, "num")
    # Section 8 (uncertainty budget): model share over the four items where it leads (P1, QA, AF, NR), column (b); Arm S draw noise, column (a), E2
    _rng("b", "M", ["P1", "QA", "AF", "NR"], "four")
    _rng("a", "draw", CR_ITEMS, "cr")
    # width of the leave-one-wording-out range of the model share and the model-by-wording share, column (a), E2
    lw = {}
    for r in rows:
        if r["column"] == "(a)" and r["basis"] == "E2" and r["component"] in ("M", "MW") and r["item"] in CR_ITEMS:
            lw[(r["component"], r["item"])] = float(r["lowo_max"]) - float(r["lowo_min"])
    for comp in ("M", "MW"):
        vals = [lw[(comp, i)] for i in CR_ITEMS]
        what = f"{rtf}#lowo_max-lowo_min (column (a), E2, component {comp}, five choice and rating items"
        out[f"rt.a.lowo.{comp}.min"] = Entry(_fx(min(vals), 2), what + "; minimum)")
        out[f"rt.a.lowo.{comp}.max"] = Entry(_fx(max(vals), 2), what + "; maximum)")
    # column (e): agreement of the Arm S (E2) and Arm L (A1) shares, component by component
    S, L = _comp_shares(rows, "(e)-ArmS", "E2"), _comp_shares(rows, "(e)-ArmL", "A1")
    cr_pairs = {k: S[k] - L[k] for k in S if k in L and k[0] in CR_ITEMS}
    over = sorted(k for k, d in cr_pairs.items() if abs(d) >= THR_E7A)
    assert over == [("P3", "MW"), ("P3", "W")], over  # the text names exactly these two; a change stops the build
    base = f"{rtf}#share (columns (e)-Arm S E2 and (e)-Arm L A1, matched item x component, five choice and rating items"
    out["rt.e.agree.n"] = Entry(str(len(cr_pairs)), base + "; count of pairs)")
    out["rt.e.agree.within"] = Entry(str(len(cr_pairs) - len(over)), base + f"; count with absolute difference below {THR_E7A})")
    out["rt.e.agree.P3.W"] = Entry(_fx(abs(cr_pairs[("P3", "W")]), 2), base + "; |difference|, P3, W)")
    out["rt.e.agree.P3.MW"] = Entry(_fx(abs(cr_pairs[("P3", "MW")]), 2), base + "; |difference|, P3, MW)")
    # the same agreement on the E1 basis (draw noise not a component; the like-for-like basis for an exact readout, E7a item 2)
    S1 = _comp_shares(rows, "(e)-ArmS", "E1")
    cr1 = {k: S1[k] - L[k] for k in S1 if k in L and k[0] in CR_ITEMS}
    over1 = sorted(k for k, d in cr1.items() if abs(d) >= THR_E7A)
    base1 = base.replace("(e)-Arm S E2", "(e)-Arm S E1")
    out["rt.e1.agree.n"] = Entry(str(len(cr1)), base1 + "; count of pairs)")
    out["rt.e1.agree.within"] = Entry(str(len(cr1) - len(over1)), base1 + f"; count with absolute difference below {THR_E7A})")
    out["rt.e1.agree.over"] = Entry(", ".join(f"{i} {c}" for i, c in over1) or "none", base1 + "; pairs at or above the threshold)")
    out["rt.e1.agree.maxabs"] = Entry(_fx(max(abs(v) for v in cr1.values()), 2), base1 + "; largest |difference|)")
    p2c = {k: S[k] - L[k] for k in S if k in L and k[0] == "P2c"}
    out["rt.e.agree.P2c.max"] = Entry(_fx(max(abs(v) for v in p2c.values()), 2), base.replace("five choice and rating items", "item P2c") + "; largest |difference|)")
    # prompt identity across the arms (column (e))
    pif = "runs/acme-gstudy/A1-route-e-armL/prompt_identity.csv"
    pi = _csv(pif)
    out["rt.pi.groups"] = Entry(str(len(pi)), f"{pif} (rows = item x wording groups)")
    out["rt.pi.mismatch"] = Entry(_WORDS[sum(r["match"] != "True" for r in pi)], f"{pif}#match (rows not True)")
    # sensitivities against column (a), E2, choice and rating items (E7 item 4)
    sf = f"{RT_DIR}/sens_table.csv"
    srows = _csv(sf)
    comp_a = _comp_shares(rows, "(a)", "E2")
    for k in "abcde":
        sname = f"S-{k}"
        sr = [dict(r, column=sname) for r in srows if r["sens"] == sname]
        comp_s = _comp_shares(sr, sname, "E2")
        diff = {kk: comp_s[kk] - comp_a[kk] for kk in comp_s if kk in comp_a and kk[0] in CR_ITEMS}
        big = [kk for kk, d in diff.items() if abs(d) >= THR_E7A]
        out[f"rt.sens.{k}.pairs"] = Entry(str(len(diff)), f"{sf}#share against {rtf} (S-{k} vs column (a), E2, matched item x component, five choice and rating items)")
        out[f"rt.sens.{k}.big"] = Entry(_WORDS[len(big)], f"{sf}#share (pairs differing from column (a) by {THR_E7A} or more)")
        if k == "c":
            out["rt.sens.c.big.res"] = Entry(_WORDS[sum(kk[1] == "res" for kk in big)], f"{sf}#share (S-c pairs differing by {THR_E7A} or more that are residual terms)")
        gs = _route_groups(sr, sname, "E2")
        for (item, grp), v in gs.items():
            if item in CR_ITEMS and grp in ("M", "O"):
                out[f"rt.sens.{k}.{grp}.{item}"] = Entry(_sg(v, 2), f"{sf}#share (S-{k}, E2, item {item}, group {grp} = sum of components)")
        ns = {r["item"]: r["n_models"] for r in sr if r["n_models"]}
        if k == "b":
            out["rt.sens.b.n.P1"] = Entry(_WORDS[int(float(ns["P1"]))], f"{sf}#n_models (S-b, P1)")
        if k == "a":
            vals = [int(float(ns[i])) for i in CR_ITEMS]
            out["rt.sens.a.n.min"] = Entry(_WORDS[min(vals)], f"{sf}#n_models (S-a, five choice and rating items; minimum)")
            out["rt.sens.a.n.max"] = Entry(_WORDS[max(vals)], f"{sf}#n_models (S-a, five choice and rating items; maximum)")
        if k == "e":
            assert {float(r["n_wordings"]) for r in sr if r["n_wordings"]} == {3.0}
    sdf = "runs/acme-S-gstudy/sens-S-d/summary.json"
    sd = _json(sdf)["items"]
    for item in ("P1", "AF", "NR"):
        out[f"rt.sens.d.clip.{item}"] = Entry(_fx(sd[item]["clip_rate"], 2), f"{sdf}#items.{item}.clip_rate")
    # hypotheses as estimates (E7 item 5); the p-values of hypotheses.json are never read
    hf = f"{RT_DIR}/hypotheses_estimates.csv"
    bmap = {"E2": "E2", "E1": "E1", "A1": "A1", "setup_sd_raw": "raw", "setup_sd_drawcorr": "dc", "A1_lb95_onesided": "lb"}
    for r in _csv(hf):
        c = RT_COLS[r["column"]][0]
        h = r["hypothesis"].replace("_analogue", "a")
        pre = f"hy.{c}.{h}.{bmap[r['basis']]}.{r['item_set'].replace('_', '')}"
        what = f"{hf}#{{}} (column {r['column']}, {r['hypothesis']}, basis {r['basis']}, item set {r['item_set']})"
        out[f"{pre}.k"] = Entry(_WORDS[int(r["k_items"])], what.format("k_items"))
        if h == "H2":
            out[f"{pre}.n"] = Entry(_WORDS[int(float(r["estimate"]))], what.format("estimate (count of items)"))
            continue
        out[f"{pre}.est"] = Entry(_sg(r["estimate"], 2), what.format("estimate"))
        if r["lo"]:
            out[f"{pre}.lo"] = Entry(_sg(r["lo"], 2), what.format("lo"))
            out[f"{pre}.hi"] = Entry(_sg(r["hi"], 2), what.format("hi"))
        else:
            out[f"{pre}.lowomin"] = Entry(_sg(r["lowo_min"], 2), what.format("lowo_min"))
            out[f"{pre}.lowomax"] = Entry(_sg(r["lowo_max"], 2), what.format("lowo_max"))
    # yardsticks at T = 1.0, ML1-SD units: median over models of the set-up SD against c_p, S_H and |pooled human effect|
    for tag, d in (("b", "runs/acme-gstudy/A1-route-b-pertype"), ("a", "runs/acme-S-gstudy/route-a-yardsticks/raw"),
                   ("ad", "runs/acme-S-gstudy/route-a-yardsticks/drawcorr")):
        yf = f"{d}/yardsticks.csv"
        for r in _csv(yf):
            if r["model"] != "__median__":
                continue
            it, y = r["item"], r["yardstick"]
            src = f"{yf}#{{}} (model __median__, item {it}, yardstick {y})"
            out[f"ys.{tag}.{it}.sd"] = Entry(_fx(r["setup_sd"], 2), src.format("setup_sd"))
            if r["setup_lo"]:
                out[f"ys.{tag}.{it}.sdlo"] = Entry(_fx(r["setup_lo"], 2), src.format("setup_lo"))
                out[f"ys.{tag}.{it}.sdhi"] = Entry(_fx(r["setup_hi"], 2), src.format("setup_hi"))
            yk = {"c_p": "cp", "S_H": "sh", "pooled_abs": "pool"}[y]
            out[f"ys.{tag}.{it}.r{yk}"] = Entry(_fx(r["ratio"], 1), src.format("ratio (set-up SD / yardstick)"))
            if tag == "b":
                out[f"ys.{yk}.{it}.est"] = Entry(_fx(r["y_est"], 2), src.format("y_est"))
                if r["y_lo"]:
                    out[f"ys.{yk}.{it}.lo"] = Entry(_fx(r["y_lo"], 2), src.format("y_lo"))
                    out[f"ys.{yk}.{it}.hi"] = Entry(_fx(r["y_hi"], 2), src.format("y_hi"))
    # frozen intervals of selected column (b) shares (underpowered), and ranges of the ratios to S_H over the choice and rating items
    for r in rows:
        if r["column"] == "(b)" and r["basis"] == "A1" and r["analysis"] == "4facet" and r["component"] in ("M", "MW") and r["item"] in CR_ITEMS:
            what = f"{rtf}#{{}} (column (b), A1, item {r['item']}, component {r['component']})"
            out[f"rt.b.int.{r['component']}.{r['item']}.lo"] = Entry(_sg(r["share_lo"], 2), what.format("share_lo"))
            out[f"rt.b.int.{r['component']}.{r['item']}.hi"] = Entry(_sg(r["share_hi"], 2), what.format("share_hi"))
    ybf = "runs/acme-gstudy/A1-route-b-pertype/yardsticks.csv"
    yb = [r for r in _csv(ybf) if r["model"] == "__median__"]
    rsh = [float(r["ratio"]) for r in yb if r["yardstick"] == "S_H" and r["item"] in CR_ITEMS]
    out["ys.b.rsh.cr.min"] = Entry(_fx(min(rsh), 1), f"{ybf}#ratio (S_H, five choice and rating items; minimum)")
    out["ys.b.rsh.cr.max"] = Entry(_fx(max(rsh), 1), f"{ybf}#ratio (S_H, five choice and rating items; maximum)")
    # guards for the qualitative statements of section 7.10 (the text names these items; a change in the files stops the build)
    sep_pool = {(r["item"], r["position"]) for r in yb if r["yardstick"] == "pooled_abs" and r["separated"] == "True"}
    assert sep_pool == {("P1", "below"), ("P2c", "below"), ("QA", "above")}, sep_pool
    assert {r["item"] for r in yb if r["yardstick"] == "S_H" and r["sh_lo_zero"] == "True"} == {"AF", "NR", "P1", "P3"}
    assert {r["item"] for r in yb if r["yardstick"] == "c_p" and r["separated"] != "True"} == {"P3"}
    # H2-type counts on the choice and rating items only (red-team M-1, CRP-S09 2026-11-08): the plan's six-item count includes P2c, which is not interpreted
    cpb = {r["item"]: r for r in yb if r["yardstick"] == "c_p"}
    cpr = [cpb[i] for i in CR_ITEMS]
    out["ys.b.cr.k"] = Entry(_WORDS[len(cpr)], f"{ybf}#item (yardstick c_p, five choice and rating items)")
    out["ys.b.cr.exceed.n"] = Entry(_WORDS[sum(r["position"] == "above" for r in cpr)], f"{ybf}#position (c_p, five choice and rating items; count 'above', median set-up SD over c_p)")
    out["ys.b.cr.lb.n"] = Entry(_WORDS[sum(r["separated"] == "True" for r in cpr)], f"{ybf}#separated (c_p, five choice and rating items; count True, one-sided lower bound over c_p)")
    # design constants of the route table quoted in the text (each from the file or erratum that fixes it)
    out["rt.floor"] = Entry("three", "runs/acme-S-gstudy/route-a/README.md (decomposability floor: >= 3 models on the roster); PREREG-acme-ERRATA.md E7")
    out["rt.tref"] = Entry("1.0", "PREREG-acme-ERRATA.md E7 item 6 (yardstick comparison on T = 1.0 cells)")
    out["rt.sens.a.rule"] = Entry("0.8 and 0.2", "runs/acme-S-gstudy/sens-S-a/README.md (loose roster: validity 0.8, gap 0.2)")
    out["rt.sens.d.clipbound"] = Entry("12", "runs/acme-S-gstudy/sens-S-d/README.md (logit clipped to +-12, PREREG S4)")
    out["syn.crit.bias"] = Entry("0.02", "PREREG-acme-ERRATA.md E7 item 3 (|bias| <= 0.02 on every share)")
    out["syn.crit.lo"], out["syn.crit.hi"] = Entry("0.90", "PREREG-acme-ERRATA.md E7 item 3 (coverage 0.90-0.98)"), Entry("0.98", "PREREG-acme-ERRATA.md E7 item 3 (coverage 0.90-0.98)")
    # synthetic check of the sampled-arm estimator (E7 item 3, E7a)
    synd = "runs/acme-S-gstudy/synthetic"
    sm = _json(f"{synd}/summary.json")
    out["syn.e2.maxbias"] = Entry(_fx(sm["G_E2"]["max_abs_bias"], 4), f"{synd}/summary.json#G_E2.max_abs_bias")
    out["syn.e2.cells"] = Entry(str(sm["G_E2"]["cells"]), f"{synd}/summary.json#G_E2.cells")
    out["syn.e2.gt02"] = Entry(str(sm["G_E2"]["n_abs_bias_gt_0p02"]), f"{synd}/summary.json#G_E2.n_abs_bias_gt_0p02")
    cc = sm["C_coverage_corrected"]
    out["syn.cov.min"] = Entry(_fx(cc["min"], 3), f"{synd}/summary.json#C_coverage_corrected.min")
    out["syn.cov.max"] = Entry(_fx(cc["max"], 3), f"{synd}/summary.json#C_coverage_corrected.max")
    out["syn.cov.cells"] = Entry(str(cc["cells"]), f"{synd}/summary.json#C_coverage_corrected.cells")
    out["syn.cov.inrange"] = Entry(_fx(100 * cc["frac_cells_in_0p90_0p98"], 0), f"{synd}/summary.json#C_coverage_corrected.frac_cells_in_0p90_0p98 (percent)")
    out["syn.e1.maxbias"] = Entry(_fx(sm["G_E1"]["max_abs_bias"], 1), f"{synd}/summary.json#G_E1.max_abs_bias")
    nwc = _csv(f"{synd}/nw_check.csv")
    for nwv, tag in (("4", "four"), ("12", "twelve")):
        out[f"syn.nw.{tag}.e2"] = Entry(_fx(max(float(r["max_abs_bias"]) for r in nwc if r["n_w"] == nwv and r["basis"] == "E2"), 3),
                                        f"{synd}/nw_check.csv#max_abs_bias (n_w {nwv}, E2, maximum over items and scenarios)")
    return out


NUMBERS.update(_section7res_numbers())


# --------------------------------------------------------------------------------------------------------------------------
# Writer clean-up numbers (CRP-S09 writer, 2026-11-08): metric strings (Section 5), software environment and prompt manifest
# (Supplement S2), near-deterministic share of the binary Arm L prompts (Section 7.3, Supplement S3)
# Each value is read from a file under runs/ or data/processed/ at build time.
# --------------------------------------------------------------------------------------------------------------------------
ND_THRESHOLD = 0.99   # EXPLORATORY-acme.md item 8: near-deterministic cell = maximum option probability above 0.99
ND_ITEMS = ("P1", "AF", "NR")   # binary items: the maximum option probability is max(y, 1 - y)


def nd_shares() -> dict[tuple[str, str], tuple[int, int]]:
    """(model, item) -> (near-deterministic prompts, prompts) for the main variant at the four analysis temperatures."""
    out: dict[tuple[str, str], list[int]] = {}
    for r in _csv("runs/acme-L/outcomes/outcomes.csv"):
        if r["item"] not in ND_ITEMS or r["variant"] != "main" or r["y"] in ("", "nan"):
            continue
        y = float(r["y"])
        k = (r["model"], r["item"])
        cell = out.setdefault(k, [0, 0])
        cell[1] += 1
        cell[0] += int(max(y, 1.0 - y) > ND_THRESHOLD)
    return {k: (v[0], v[1]) for k, v in out.items()}


def _writer_cleanup_numbers() -> dict[str, Entry]:
    import glob
    import json

    out: dict[str, Entry] = {}
    # Section 5: free-text metric strings of the first coding pass
    n_str, strings = 0, set()
    for f in sorted(glob.glob(str(ROOT / "data/processed/extraction/claude/*.json"))):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        if j["eligibility"]["decision"] != "YES":
            continue
        m = j["D"].get("metric")
        if m and m != "not_reported":
            n_str += 1
            strings.add(" ".join(str(m).lower().split()))
    assert n_str > 0
    src = "data/processed/extraction/claude/*.json#D.metric (eligible studies of the first pass; strings compared after lower-casing and white-space normalization)"
    out["val.met.str.n"] = Entry(str(n_str), src + ", count")
    out["val.met.str.d"] = Entry(str(len(strings)), src + ", distinct strings")

    # Supplement S2: software environment and prompt manifest, identical in the run metadata of every model
    metas = [json.loads(Path(f).read_text(encoding="utf-8")) for f in sorted(glob.glob(str(ROOT / "runs/acme-L/*/meta*.json")))]
    assert metas
    for field, key in (("torch", "bm.env.torch"), ("transformers", "bm.env.tf"), ("gpu", "bm.env.gpu"), ("manifest_sha256", "bm.env.manifest12")):
        vals = {m[field] for m in metas}
        assert len(vals) == 1, (field, vals)
        v = vals.pop()
        out[key] = Entry(v[:12] if field == "manifest_sha256" else v, f"runs/acme-L/*/meta*.json#{field} (one value in all {len(metas)} metadata files)")
    starts = sorted(m["started"][:10] for m in metas)
    out["bm.env.first"] = Entry(starts[0], "runs/acme-L/*/meta*.json#started (earliest)")
    out["bm.env.last"] = Entry(starts[-1], "runs/acme-L/*/meta*.json#started (latest)")

    # Section 7.3 and Supplement S3: near-deterministic share of the binary prompts
    nd = nd_shares()
    per_model: dict[str, list[int]] = {}
    for (mdl, _it), (k, n) in nd.items():
        c = per_model.setdefault(mdl, [0, 0])
        c[0] += k
        c[1] += n
    shares = {m: c[0] / c[1] for m, c in per_model.items()}
    lo, hi = min(shares, key=shares.get), max(shares, key=shares.get)
    srcnd = "runs/acme-L/outcomes/outcomes.csv#y (binary items P1, AF, NR; variant main; four temperatures; near-deterministic = max(y, 1 - y) > 0.99)"
    out["bm.nd.thr"] = Entry(f"{ND_THRESHOLD:.2f}", "research/relaunch/EXPLORATORY-acme.md item 8 (maximum option probability above 0.99)")
    out["bm.nd.min"] = Entry(f"{100 * shares[lo]:.0f}", srcnd + ", smallest model share, percent")
    out["bm.nd.max"] = Entry(f"{100 * shares[hi]:.0f}", srcnd + ", largest model share, percent")
    out["bm.nd.n"] = Entry(str(len(shares)), srcnd + ", models")
    # The NF4 precision-control keys (bm.prec.*) were removed after the red-team review of 2026-11-08: the analysis (analysis/acme/precision_control.py) is
    # post-outcome and not in the plan or the errata, and it is not reported in the paper.
    return out


NUMBERS.update(_writer_cleanup_numbers())


def render(numbers: dict[str, Entry]) -> str:
    lines = [
        f"% GENERATED by {SCRIPT}. Do not edit by hand; rerun the script.",
        "% Each line defines \\csname NUM:<key>\\endcsname; the manuscript reads it with \\NUM{<key>}.",
        "% The trailing comment names the run file and field the value came from.",
        f"% macros: {len(numbers)}",
    ]
    for key in sorted(numbers):
        entry = numbers[key]
        if not KEY_RE.match(key):
            raise ValueError(f"bad key {key!r}: use letters, digits, '.', ':' and '-' only")
        if not entry.src.strip():
            raise ValueError(f"key {key!r} has no src: every number needs a run file and field")
        if any(ch in entry.value for ch in "%\n"):
            raise ValueError(f"value of {key!r} contains '%' or a newline")
        lines.append(f"\\expandafter\\newcommand\\csname NUM:{key}\\endcsname{{{entry.value}}} % src: {entry.src}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    text = render(NUMBERS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.out} ({len(NUMBERS)} macros)")


if __name__ == "__main__":
    main()
