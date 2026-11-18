"""Generate paper/acme/tables/tab-validation.tex (Table 5, validation designs with study counts and a synthesis column).

Study counts and shares are read from runs/rq234-final/rq2.csv (outcome kinds and derived labels against human data). Each cell is
checked against the matching \\NUM key built by analysis/acme/make_autonumbers.py (_section5_numbers), so the table and the text
cannot disagree. Rule of the review (Section 3): a field that met the agreement rule carries a 95 percent design-based interval;
a field that failed it is shown as a pass-specific value without an interval (marked with a dagger).
The Human comparator, Metric and Synthesis columns are descriptive text of the designs; they hold no number.

Usage:  python analysis/acme/make_tab_validation.py [--out paper/acme/tables/tab-validation.tex]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()
from make_autonumbers import NUMBERS  # noqa: E402  (importing runs every reconciliation assert of the number blocks)

SRC = "runs/rq234-final/rq2.csv"
PASSES = (("claude", "p1"), ("codex", "p2"))  # column prefixes in the run file; first and second coding pass

# (group heading or None, row key in rq2.csv, NUM prefix, design, human comparator, metric, synthesis)
G_EFF, G_ACC, G_AGR, G_NONE = ("Effect rows: a manipulation-induced effect compared with the human effect",
                               "Accuracy rows: performance against a normative key, compared with human performance",
                               "Agreement rows: item-level correspondence with human responses",
                               "Rows without a usable human comparison")
ROWS = [
    (G_EFF, "rq2|effect|ANY", "val.eff.any", "Any effect contrast against a human effect",
     "Human effect", "Direction, ratio, authors' test",
     "Shows that the manipulation moves the simulator, not yet by how much."),
    (None, "rq2|effect|SAME-DIRECTION-UNQUANTIFIED", "val.eff.sdu", "Direction only",
     "Human effect", "Sign, or non-significant model-human test",
     "Necessary and weak: no magnitude, no uncertainty; a non-rejection is not equivalence."),
    (None, "rq2|effect|HUMAN-LIKE", "val.eff.hl", "Ratio of effects inside a fixed band",
     "Human effect size, same metric", "Ratio between 0.5 and 2",
     "Quantifies magnitude; compares two point estimates, and the band is a convention."),
    (None, "rq2|effect|EXAGGERATED", "val.eff.exa", "Ratio above the band, or larger by the authors' test",
     "Human effect size, same metric", "Ratio above 2, or test",
     "Detects over-reaction; needs both effects as numbers or a test."),
    (None, "rq2|effect|ATTENUATED", "val.eff.att", "Ratio below the band",
     "Human effect size, same metric", "Ratio below 0.5",
     "Detects under-reaction; needs both effects as numbers."),
    (None, "rq2|effect|SUPER-NORMATIVE", "val.eff.sup", "Human effect present, model effect absent",
     "Human effect", "Significance of the model effect",
     "Depends on the power of the model test, which the authors set."),
    (None, "rq2|effect|DIFFERENT", "val.eff.dif", "Effect in the opposite direction",
     "Human effect", "Sign and significance",
     "A clear failure on direction; silent on degree."),
    (G_ACC, "rq2|accuracy|ANY", "val.acc.any", "Any accuracy row against a human comparison",
     "Human accuracy, same key", "Accuracy, authors' test",
     "Compares levels, not the manipulation effect or the error pattern."),
    (None, "rq2|accuracy|BELOW-HUMAN", "val.acc.blw", "Simulator below human accuracy",
     "Human accuracy", "Authors' test or statement", "A difference in level, not a mismatch of effects."),
    (None, "rq2|accuracy|HUMAN-LEVEL", "val.acc.hum", "Simulator at human accuracy",
     "Human accuracy", "Authors' test or statement", "Equal accuracy does not imply equal response patterns."),
    (None, "rq2|accuracy|ABOVE-HUMAN", "val.acc.abv", "Simulator above human accuracy",
     "Human accuracy", "Authors' test or statement", "Departs from humans toward the normative answer."),
    (G_AGR, "rq2|agreement|ANY", "val.agr.any", "Item-level agreement with human responses",
     "Human item means or labels", "Correlation, similarity score",
     "Validates the ranking of stimuli; never read as the same effect."),
    (G_NONE, "rq2|effect|NO-HUMAN-REFERENCE", "val.eff.nor", "Effect rows with no human reference",
     "None", "None", "No validation claim is possible."),
    (None, "rq2|effect|INSUFFICIENT", "val.eff.ins", "Effect rows without usable effect sizes",
     "Human data exist", "Not reported", "The comparison cannot be reconstructed from the paper."),
]


def esc(s: str) -> str:
    return s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def cell(r: dict[str, str], pre: str, col: str, p: str) -> str:
    k, n = int(r[f"{col}_k"]), int(r[f"{col}_n_domain"])
    est, lo, hi = (f"{float(r[f'{col}_{x}_pct']):.1f}" for x in ("est", "lo", "hi"))
    assert NUMBERS[f"{pre}.{p}"].value == est and NUMBERS[f"{pre}.{p}k"].value == str(k), (pre, p)
    if r["passes_v012_rule"] == "True":
        assert NUMBERS[f"{pre}.{p}lo"].value == lo and NUMBERS[f"{pre}.{p}hi"].value == hi, (pre, p)
        return f"{k}/{n} ({est}; {lo} to {hi})"
    assert f"{pre}.{p}lo" not in NUMBERS, pre  # a failed field carries no interval key
    return f"{k}/{n} ({est})$^{{\\dagger}}$"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "paper" / "acme" / "tables" / "tab-validation.tex")
    args = ap.parse_args()
    with (ROOT / SRC).open(encoding="utf-8", newline="") as f:
        rq2 = {r["feature"]: r for r in csv.DictReader(f)}
    L = [
        "% GENERATED by analysis/acme/make_tab_validation.py from runs/rq234-final/rq2.csv. Do not edit by hand; rerun the script.",
        "% Cells: k/n studies (design-weighted percent; 95 percent design-based interval where the label field met the agreement rule).",
        r"{\footnotesize\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.05}",
        r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.16\textwidth}"
        r">{\raggedright\arraybackslash}p{0.10\textwidth}"
        r">{\raggedright\arraybackslash}p{0.12\textwidth}"
        r">{\raggedright\arraybackslash}p{0.11\textwidth}"
        r">{\raggedright\arraybackslash}p{0.11\textwidth}"
        r">{\raggedright\arraybackslash}p{0.26\textwidth}@{}}",
        r"\toprule",
        r"Validation design & Human comparator & Metric & Studies, first pass & Studies, second pass & Synthesis \\",
        r"\midrule",
    ]
    first = True
    for grp, key, pre, design, comp, metric, syn in ROWS:
        if grp:
            if not first:
                L.append(r"\addlinespace[2pt]")
            L.append(rf"\multicolumn{{6}}{{@{{}}l}}{{\textit{{{esc(grp)}}}}} \\")
            first = False
        r = rq2[key]
        cells = [cell(r, pre, col, p) for col, p in PASSES]
        L.append(" & ".join([esc(design), esc(comp), esc(metric), *cells, esc(syn)]) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}}", ""]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    rc.write_source_recorded([args.out], "analysis/acme/make_tab_validation.py", _REC)
    print(f"wrote {args.out} ({len(ROWS)} rows)")


if __name__ == "__main__":
    main()
