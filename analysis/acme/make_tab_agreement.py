"""Generate paper/acme/tables/tab-agreement.tex (Supplement Table, key `s-agreement`): every agreement statistic collected.

Sources (all read here, none typed):
  runs/extraction-pilot/round1|round2-fresh|round2-old|round2-combined/kappa.csv   extraction pilots (percent as a proportion, kappa)
  runs/rq234-final/agreement.csv                                                   full sample: percent, kappa, rule basis, rule outcome
  data/processed/screen/title-agreement.json, abstract-agreement.json, abstract-agreement-v08.json   screening passes
Each value that the text quotes through a \\NUM key is checked against that key (rm.*, sp.*, au.*, val.*), so the table and the text cannot
disagree. The rule (amendment v0.12 item 3) belongs to the full sample: kappa at least 0.6 when every category holds at least 5 records in
each pass, otherwise percent agreement at least 0.80; the file carries the basis and the outcome and this script prints them as stored.
No file holds an interval for an agreement statistic, so the table shows none. Procedure nouns only (decision D-AI): "pass".

Usage:  python analysis/acme/make_tab_agreement.py [--out paper/acme/tables/tab-agreement.tex]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()
from make_autonumbers import NUMBERS  # noqa: E402  (importing runs every reconciliation assert of the number blocks)

PILOTS = [  # (directory, header used in the table)
    ("round1", "Pilot 1"),
    ("round2-fresh", "Pilot 2 fresh"),
    ("round2-old", "Pilot 2 old"),
    ("round2-combined", "Pilot 2 combined"),
]
FULL = "runs/rq234-final/agreement.csv"
SCREEN = "data/processed/screen/"
ALIAS = {"E.label (coder-assigned)": "E.label"}  # the pilot files name the coder-assigned label without the suffix
GROUPS = [  # (heading, predicate on the normalised field name)
    ("Eligibility and venue", lambda f: f == "eligibility.decision" or f.startswith("A.")),
    ("Human reference", lambda f: f.startswith("D.")),
    ("Paradigm family", lambda f: f.startswith("C.")),
    ("Outcomes", lambda f: f.startswith("E.")),
    ("Reporting items", lambda f: f.startswith("F.")),
]
WORDS = {2: "two", 4: "four", 5: "five", 8: "eight"}


def q(x: str | float, nd: int) -> str:
    """Round half up from the stored decimal string (the rule the number keys use)."""
    return str(Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def num(key: str) -> str:
    assert key in NUMBERS, f"missing NUM key {key}"
    return NUMBERS[key].value


def esc(s: str) -> str:
    return s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def field_tex(f: str) -> str:
    """Field name in typewriter with break points after '_', '[' and '.'."""
    t = esc(f).replace(r"\_", r"\_\allowbreak ").replace("[", r"[\allowbreak ").replace(".", r".\allowbreak ")
    return rf"\texttt{{{t}}}"


def read_csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "paper" / "acme" / "tables" / "tab-agreement.tex")
    args = ap.parse_args()

    # ------------------------------------------------------------------ read
    full_rows = read_csv(FULL)
    full = {ALIAS.get(r["field"], r["field"]): r for r in full_rows}
    assert len(full) == len(full_rows), "duplicate field in agreement.csv"
    pilot: dict[str, dict[str, dict[str, str]]] = {}
    for d, _ in PILOTS:
        rows = read_csv(f"runs/extraction-pilot/{d}/kappa.csv")
        pilot[d] = {ALIAS.get(r["field"], r["field"]): r for r in rows}
        assert len(pilot[d]) == len(rows), d
        extra = set(pilot[d]) - set(full)
        assert not extra, (d, extra)  # every pilot field also exists in the full sample

    # ------------------------------------------------------------------ assertions against \NUM keys
    def pil(d: str, f: str) -> dict[str, str]:
        return pilot[d][f]

    def pk(d: str, f: str) -> str:  # pilot kappa, two decimals
        return q(pil(d, f)["kappa"], 2)

    assert num("rm.cp1N") == str(pil("round1", "eligibility.decision")["n"])
    assert pk("round1", "eligibility.decision") == num("rm.cp1Elig")
    assert pk("round1", "C.family_presence (pooled)") == num("rm.cp1Fam")
    assert pk("round1", "E.model_effect_present") == num("rm.cp1Mod")
    assert pk("round2-fresh", "F.f4") == num("rm.cp2FreshF4")
    assert pk("round2-fresh", "C.family_presence (pooled)") == num("rm.cp2FreshFam")
    assert pk("round2-fresh", "E.outcome_kind") == num("rm.cp2FreshKind")
    assert pk("round2-fresh", "E.label") == num("rm.cp2FreshLab")
    assert WORDS[int(pil("round2-fresh", "eligibility.decision")["n"])] == num("rm.cp2FreshN")
    assert WORDS[int(pil("round2-old", "eligibility.decision")["n"])] == num("rm.cp2OldN")
    assert pk("round2-combined", "F.f4") == num("rm.cp2CombF4")
    assert pk("round2-combined", "C.family_presence (pooled)") == num("rm.cp2CombFam")
    assert pk("round2-combined", "E.outcome_kind") == num("rm.cp2CombKind")
    assert pk("round2-combined", "E.label") == num("rm.cp2CombLab")

    def fk(f: str) -> str:
        return full[f]["kappa"]

    def fp(f: str) -> str:
        return full[f]["percent_agreement"]

    # full sample: eligibility and the counts of fields passing, failing and passing on percent alone
    assert q(fk("eligibility.decision"), 2) == num("rm.fsElK") and fp("eligibility.decision") == num("rm.fsElPct")
    tested = [r for f, r in full.items() if f not in ("eligibility.decision", "A.peer_reviewed")]
    assert len(tested) == int(num("rm.fsFields"))
    n_pass = sum(r["passes_v012_rule"] == "True" for r in tested)
    fails = [r for r in tested if r["passes_v012_rule"] == "False"]
    assert n_pass == int(num("rm.fsPass")) and len(fails) == int(num("rm.fsFail"))
    fk_fail = [float(r["kappa"]) for r in fails if r["kappa"] != ""]
    assert q(min(fk_fail), 2) == num("rm.fsFailKlo") and q(max(fk_fail), 2) == num("rm.fsFailKhi")
    pct_only = [r for r in tested if r["passes_v012_rule"] == "True" and r["rule_basis"].startswith("percent")
                and r["kappa"] != "" and float(r["kappa"]) < float(num("rm.ruleK"))]
    assert WORDS[len(pct_only)] == num("rm.fsPctPass"), len(pct_only)
    assert fk("F.f1") == num("rm.fsF1K") and fp("F.f1") == num("rm.fsF1Pct")
    # reporting items quoted in Sections 4 to 6 (au.* and sp.*) and in Section 5 (val.*)
    AU = {"au.any": "F.robustness_tested (robustness_outcome != na)", "au.code": "F.f12", "au.nov": "F.f9", "au.ord": "F.f6",
          "au.out": "F.robustness_outcome", "au.prereg": "F.f11", "au.rep": "F.f3", "au.smp": "F.f7", "au.snap": "F.f8", "au.wrd": "F.f5",
          "au.pc": "F.perturbations_tested[contamination]", "au.pd": "F.perturbations_tested[decoding]",
          "au.po": "F.perturbations_tested[option_order]", "au.ps": "F.perturbations_tested[seeds]",
          "au.pv": "F.perturbations_tested[model_version]", "au.pw": "F.perturbations_tested[wording]",
          "val.kind": "E.outcome_kind", "val.label": "E.derived_label (script)"}
    for pre, f in AU.items():
        assert num(f"{pre}.agree") == fp(f) and num(f"{pre}.kappa") == fk(f), (pre, f)
    for pre, f in {"sp.f1": "F.f1", "sp.f2": "F.f2", "sp.f4": "F.f4", "sp.f6na": "F.f6"}.items():
        assert num(f"{pre}.agree") == fp(f) and num(f"{pre}.kappa") == fk(f), (pre, f)
        assert num(f"{pre}.rule") == ("met" if full[f]["passes_v012_rule"] == "True" else "failed"), (pre, f)
    assert num("val.kind.nkeys") == full["E.outcome_kind"]["n"]
    judged = [f"F.perturbations_tested[{t}]" for t in ("option_order", "response_format", "seeds", "model_version")]
    assert all(full[f]["passes_v012_rule"] == "False" for f in judged) and WORDS[len(judged)] == num("au.nJudgedFail")
    kk = [float(full[f]["kappa"]) for f in judged]
    assert q(min(kk), 2) == num("au.pert.failKlo") and q(max(kk), 2) == num("au.pert.failKhi")
    ot = [f for f in full if f.startswith("E.outcome_types[") and full[f]["passes_v012_rule"] == "False"]
    ko = [float(full[f]["kappa"]) for f in ot]
    assert q(min(ko), 2) == num("val.met.failKlo") and q(max(ko), 2) == num("val.met.failKhi")
    dt = [float(r["kappa"]) for f, r in full.items() if f.startswith("D.types[") and r["kappa"] != ""]
    assert q(min(dt), 3) == num("val.ref.kappaMin")

    # screening passes
    ti = json.loads((ROOT / SCREEN / "title-agreement.json").read_text(encoding="utf-8"))
    ab = json.loads((ROOT / SCREEN / "abstract-agreement.json").read_text(encoding="utf-8"))
    a8 = json.loads((ROOT / SCREEN / "abstract-agreement-v08.json").read_text(encoding="utf-8"))
    kp = a8["kappa_pairwise"]
    SCR = [  # (label, n, kappa, NUM key checked)
        ("Title stage, pass 1 with pass 2, three labels", ti["n"], ti["kappa_3class"], "rm.kTitle"),
        ("Title stage, pass 1 with pass 2, exclusion against any other label", ti["n"], ti["kappa_exclude_vs_not"], "rm.kTitleEx"),
        ("Abstract stage, pass 1 with pass 2, three labels", ab["n"], kp["claude-olmo"], "rm.kAbs12"),
        ("Abstract stage, pass 1 with pass 3, three labels", a8["n"], kp["claude-qwen"], "rm.kAbs13"),
        ("Abstract stage, pass 2 with pass 3, three labels", a8["n"], kp["olmo-qwen"], "rm.kAbs23"),
        ("Abstract stage, passes 1 to 3 (Fleiss), three labels", a8["n"], a8["fleiss_kappa_3class"], "rm.kFleiss"),
        ("Abstract stage, pass 1 with pass 2, exclusion against any other label", ab["n"], ab["kappa_exclude_vs_not"], "rm.kAbsEx"),
    ]
    assert ab["kappa_3class"] == kp["claude-olmo"]  # the two files agree on pass 1 with pass 2
    assert ti["n"] == int(num("rm.nUnique").replace(",", "")) and ab["n"] == a8["n"] == int(num("rm.nStage2").replace(",", ""))
    for _, _, k, key in SCR:
        assert str(k) == num(key), (key, k, num(key))

    # ------------------------------------------------------------------ build the rows
    def pcell(d: str, f: str) -> str:
        r = pilot[d].get(f)
        if r is None:
            return ""
        k = "--" if r["kappa"] == "" else q(r["kappa"], 3)
        return f"{k}; {q(Decimal(r['agreement']) * 100, 1)}; {r['n']}"

    L = [
        "% GENERATED by analysis/acme/make_tab_agreement.py from the extraction-pilot kappa.csv files, runs/rq234-final/agreement.csv and",
        "% data/processed/screen/*-agreement*.json. Do not edit by hand; rerun the script. Body rows of a longtable (caption, label and header: floats.tex).",
        "% Pilot cells: kappa; percent agreement; units. Full-sample cells: units, percent, kappa, rule basis, rule outcome (as stored in the file).",
    ]
    order: list[str] = []
    for head, pred in GROUPS:
        fs = [f for f in full if pred(f)]
        assert fs, head
        order += fs
        L.append(rf"\multicolumn{{10}}{{@{{}}l}}{{\emph{{{head}}}}}\\")
        for f in fs:
            r = full[f]
            basis = "kappa" if r["rule_basis"].startswith("kappa") else "percent"
            assert r["rule_basis"].startswith(("kappa", "percent")), r["rule_basis"]
            res = "pass" if r["passes_v012_rule"] == "True" else "fail"
            kap = "--" if r["kappa"] == "" else q(r["kappa"], 3)
            cells = [field_tex(f), *(pcell(d, f) for d, _ in PILOTS), r["n"], r["percent_agreement"], kap, basis, res]
            L.append(" & ".join(cells) + r" \\")
        L.append(r"\addlinespace[2pt]")
    assert sorted(order) == sorted(full), "a field of agreement.csv is not in any group"
    L.append(r"\multicolumn{10}{@{}l}{\emph{Screening passes: kappa between passes}}\\")
    for lab, n, k, _ in SCR:
        L.append(" & ".join([esc(lab), "", "", "", "", f"{n:,}", "--", q(k, 3), "--", "none"]) + r" \\")
    L += [
        r"\midrule",
        r"\multicolumn{10}{@{}p{14.4cm}}{\scriptsize\emph{Notes.} Pilot cells give kappa, percent agreement and the number of units; a blank cell means the field was not in the "
        r"instructions of that round, and a dash marks an undefined kappa (one category only). The full-sample rule of amendment v0.12 sets a field as met "
        r"when kappa reaches \NUM{rm.ruleK} with at least \NUM{rm.ruleCat} records in every category of each pass, otherwise when percent agreement reaches "
        r"\NUM{rm.rulePct} as a proportion; \NUM{rm.fsPass} of the \NUM{rm.fsFields} tested fields pass and \NUM{rm.fsFail} fail, and the eligibility and venue "
        r"rows lie outside that count. The pilot columns and the screening rows report values only. No source file holds an interval for an agreement "
        r"statistic, so none is shown. Units: group E rows are matched on paradigm family and model family; group F rows use the studies that both passes "
        r"judged eligible; pooled rows pool over families or perturbation types. "
        r"Sources: runs/extraction-pilot/round1, round2-fresh, round2-old and round2-combined (kappa.csv); runs/rq234-final/agreement.csv; "
        r"data/processed/screen/title-agreement.json, abstract-agreement.json and abstract-agreement-v08.json.}\\",
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    rc.write_source_recorded([args.out], "analysis/acme/make_tab_agreement.py", _REC)
    print(f"wrote {args.out} ({len(full)} field rows, {len(SCR)} screening rows, {len(PILOTS)} pilot rounds)")


if __name__ == "__main__":
    main()
