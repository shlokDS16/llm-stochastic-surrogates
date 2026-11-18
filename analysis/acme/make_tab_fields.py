"""Generate paper/acme/tables/tab-fields.tex (coded fields that the paper analyses: definition, admissible values, level; the outcome field flagged).

The row texts condense the frozen coding briefs; each row names the brief it comes from and the script checks, before writing, that
  * the field key occurs in that brief (or in research/protocol/extraction-template.json for the full-text fields),
  * every admissible value (and every label) occurs in that brief's text,
  * the twelve reporting items f1 to f12 are all present and their number equals the \\NUM key rm.nItems (paper/acme/autonumbers.tex).
Briefs read (all under research/protocol/):
  rq1-abstract-coding-brief.md   abstract-level coding of the liberal frame (level: record)
  fulltext-extraction-brief.md   full-text eligibility and extraction (level: record for eligibility, study or effect row otherwise)
  extraction-form.md             sections E and F (item wording)
  crossing-coding-brief.md       crossing recode, fields X1 to X3 (level: study)
Levels: record = a screened record (abstract coding of the frame; eligibility judgement of each analysed record); study = an eligible study read in full;
effect row = one paradigm-by-model row inside a study (the form's section E), summarised to studies by the analysis scripts.  Beyond the record/study
split of the brief, the effect-row level is named because the outcome field lives there.
Fields coded but not analysed in the main text (left to the supplement) are listed in LEFT_TO_SUPPLEMENT and written as a comment into the table file.
No AI tool is named in the exhibit.  Mismatches in the checks stop the script (nothing is repaired by hand).

Usage (project root):  .venv/Scripts/python.exe -I analysis/acme/make_tab_fields.py [--out paper/acme/tables/tab-fields.tex]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402

ROOT = rc.ROOT
P = ROOT / "research" / "protocol"
SRC = {"abs": P / "rq1-abstract-coding-brief.md", "ft": P / "fulltext-extraction-brief.md", "form": P / "extraction-form.md",
       "x": P / "crossing-coding-brief.md", "tmpl": P / "extraction-template.json"}
AUTO = ROOT / "paper" / "acme" / "autonumbers.tex"

FAM = "HB, JDM, RE, TOM, MEM, LANG, LEARN, NUM, MOR, DEV, OTH"
HUM = "none, own_sample, published_norms, replication_dataset, crowd_norms"
YNN = "yes, no, na"
# (group, source key, key in source, field, definition, values, level, flag)
ROWS = [
    ("Abstract coding of the liberal frame (all records, title and abstract only)", None, None, None, None, None, None, None),
    ("abs", "meets_criteria_on_abstract", "Abstract flag", "Model tested on a cognitive task, new results", "yes, no, unclear", "record"),
    ("abs", "family", "Paradigm family", "Family of each paradigm named; the first sets strata", FAM, "record"),
    ("abs", "model_families", "Model family", "Families of the models named", "GPT, Claude, Gemini, Llama, Mistral, Qwen, OLMo, other", "record"),
    ("abs", "models", "Model names", "Model names as written", "list of names; empty if none named", "record"),
    ("abs", "languages", "Task languages", "Task-item languages, if stated", "list of languages; empty if not stated", "record"),
    ("abs", "modality", "Modality", "Stimulus modality stated", "text, image+text, not_stated", "record"),
    ("Full-text coding (every analysed record, then eligible studies)", None, None, None, None, None, None, None),
    ("ft", "eligibility.decision", "Eligibility", "Meets the six inclusion criteria", "YES, NO, UNCLEAR", "record"),
    ("ft", "types", "Human comparison", "Every human comparison used", HUM, "study"),
    ("ft", "primary_type", "Primary comparison", "Comparison the main results rest on", HUM, "study"),
    ("ft", "human_n", "Human sample size", "Human participants, if stated", "integer, null", "study"),
    ("ft", "outcome_types", "Outcome types", "Every kind of outcome reported", "accuracy, bias_magnitude, effect_size, choice_distribution, human_correlation, other", "study"),
    ("ft", "outcome_kind", "Outcome kind", "Kind of result; fixes the fields that apply", "effect, accuracy, agreement", "effect row", True),
    ("ft", "model_effect_present", "Effect fields", "Model effect, human effect, direction and model versus human, coded in each effect row", "yes, no, not_reported, na; no_human_reference; same, opposite, not_applicable; above, similar, below, not_compared", "effect row"),
    ("ft", "label", "Derived label", "Derived by script from the fields above", "ABOVE-HUMAN, HUMAN-LEVEL, BELOW-HUMAN, AGREEMENT-ONLY, NO-EFFECT, DIFFERENT, SUPER-NORMATIVE, EXAGGERATED, HUMAN-LIKE, ATTENUATED, SAME-DIRECTION-UNQUANTIFIED, INSUFFICIENT, NO-HUMAN-REFERENCE", "effect row"),
    ("Reporting items (each yes, no or na)", None, None, None, None, None, None, None),
    ("form", "f1", "f1 Version, date", "Exact model version, and query date for hosted models", YNN, "study"),
    ("form", "f2", "f2 Decoding", "Temperature or greedy decoding stated for every model", YNN, "study"),
    ("form", "f3", "f3 Repeats", "Identical prompt sampled more than once, number stated", YNN, "study"),
    ("form", "f4", "f4 Prompts", "Complete prompt text for every condition available", YNN, "study"),
    ("form", "f5", "f5 Wording", "Same item in two or more wordings, results compared", YNN, "study"),
    ("form", "f6", "f6 Option order", "Option order randomized or counterbalanced; na if none listed", YNN, "study"),
    ("form", "f7", "f7 Temperature", "Two or more temperature settings run and compared", YNN, "study"),
    ("form", "f8", "f8 Versions", "Two snapshots or generations of one model line compared", YNN, "study"),
    ("form", "f9", "f9 Contamination", "Novel or perturbed items, or an explicit test", YNN, "study"),
    ("form", "f10", "f10 Test", "Test or interval for the model effect or the difference", YNN, "study"),
    ("form", "f11", "f11 Registration", "Preregistration cited", YNN, "study"),
    ("form", "f12", "f12 Code or data", "Link to code or data given", YNN, "study"),
    ("ft", "perturbations_tested", "Perturbations tested", "Every perturbation run and reported", "wording, option_order, response_format, decoding, seeds, model_version, contamination, persona, language, other", "study"),
    ("ft", "robustness_outcome", "Robustness outcome", "Fate of the main result under the first six perturbations", "survived, weakened, reversed, mixed, na, not_reported", "study"),
    ("Crossing recode of the eligible studies", None, None, None, None, None, None, None),
    ("x", "sources_varied", "Sources varied", "Sources of simulation uncertainty that the study varies", "M model, W wording, O order, T temperature, P persona, R repeated draws, X other", "study"),
    ("x", "X1", "X1 Crossed", "Two or more sources in a full factorial crossing", "yes, partial, no, not_reported", "study"),
    ("x", "X2", "X2 Decomposed", "Variance share, model term or change quantified", "yes, no, not_reported", "study"),
    ("x", "X3", "X3 Interaction", "A source-by-source interaction estimated or shown", "yes, no, not_reported", "study"),
]

LEFT_TO_SUPPLEMENT = (
    "Left to the supplement (coded, not analysed in the main text): bibliographic fields (identifiers, title, venue, year, first-author field, country, "
    "peer-review status); model details (exact version, access, tuning stage, parameter count, release and query dates, counts of models and families); "
    "paradigm details (name, source paper, item origin, item count, languages and modality at full text, contamination risk); human population and "
    "effect metric; the basis, authors' comparison, effect-size and agreement-value fields and headline of each effect row; coder notes; abstract-level "
    "number of models stated, human-comparison statement, codability and failed criterion; crossing details (sources crossed, decomposition types and "
    "sources, interaction pairs, evidence strings)."
)


def tex(s: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$")):
        s = s.replace(a, b)
    return s


def values_cell(v: str) -> str:
    return tex(v).replace("+", "$+$")


def verify(rows, tr: rc.Tracker) -> list[str]:
    text = {k: tr.add(p).read_text(encoding="utf-8") for k, p in SRC.items()}
    errs: list[str] = []
    for r in rows:
        if r[1] is None:
            continue
        src, key, field, _, vals = r[0], r[1], r[2], r[3], r[4]
        body = text[src]
        if src == "ft":
            body = body + text["tmpl"]
        if src == "form":
            body = body  # f-items are numbered 1..12 in section F of the form
            m = int(key[1:])
            if not re.search(rf"^{m}\. ", body, re.M):
                errs.append(f"{key}: item {m} not found in extraction-form.md section F")
            continue
        base = key.split(".")[-1]
        if base not in body:
            errs.append(f"{field}: key '{key}' not found in {SRC[src].name}")
        if vals.startswith("list") or vals == "integer, null":
            toks = []
        elif src == "x" and key == "sources_varied":
            toks = []
            for part in vals.split(","):
                code, word = part.strip().split(" ", 1)
                if not re.search(rf"\| {code} \| ", body) or word.split()[0] not in body.lower():
                    errs.append(f"{field}: source '{part.strip()}' not found in {SRC[src].name}")
        else:
            toks = [t.strip() for t in re.split(r"[,;]\s*", vals)]
        for t in toks:
            if t not in body:
                errs.append(f"{field}: value '{t}' not found in {SRC[src].name}")
    return errs


def build(tr: rc.Tracker) -> str:
    rows = []
    for r in ROWS:
        if r[1] is None:
            rows.append(("group", r[0]))
        else:
            rows.append(r)
    entries = [r for r in ROWS if r[1] is not None]
    # normalise tuple shape: (src, key, field, definition, values, level[, flag])
    errs = verify(entries, tr)
    items = [e for e in entries if e[0] == "form"]
    auto = tr.add(AUTO).read_text(encoding="utf-8")
    m = re.search(r"NUM:rm\.nItems\\endcsname\{([^}]*)\}", auto)
    words = {"twelve": 12}
    if not m or words.get(m.group(1), m.group(1)) != len(items):
        errs.append(f"number of reporting items {len(items)} vs rm.nItems {m.group(1) if m else None}")
    flagged = [e for e in entries if len(e) == 7 and e[6]]
    if [e[2] for e in flagged] != ["Outcome kind"]:
        errs.append(f"outcome field flag: expected exactly the outcome kind row, got {[e[2] for e in flagged]}")
    if errs:
        raise SystemExit("make_tab_fields: checks failed\n  " + "\n  ".join(errs))
    L = [
        "% GENERATED by analysis/acme/make_tab_fields.py from research/protocol/{rq1-abstract-coding-brief,fulltext-extraction-brief,extraction-form,crossing-coding-brief}.md. Do not edit by hand.",
        "% " + LEFT_TO_SUPPLEMENT,
        r"{\scriptsize\setlength{\tabcolsep}{2.5pt}\renewcommand{\arraystretch}{0.96}",
        r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.5cm}>{\raggedright\arraybackslash}p{4.55cm}>{\raggedright\arraybackslash}p{5.4cm}>{\raggedright\arraybackslash}p{1.45cm}>{\raggedright\arraybackslash}p{1.1cm}@{}}",
        r"\toprule",
        r"Field & Definition & Admissible values & Level & Flag \\",
        r"\midrule",
    ]
    first = True
    for r in rows:
        if r[0] == "group":
            if not first:
                L.append(r"\addlinespace[2pt]")
            L.append(r"\multicolumn{5}{@{}l}{\textit{" + tex(r[1]) + r"}} \\")
            L.append(r"\addlinespace[1pt]")
            first = False
            continue
        src, key, field, definition, vals, level = r[:6]
        flag = len(r) == 7 and r[6]
        fcell = r"\textbf{" + tex(field) + "}" if flag else tex(field)
        if src == "ft" and key == "label":
            definition = definition + "; labels " + vals
        if src == "form" or key == "label":
            L.append(rf"{fcell} & \multicolumn{{2}}{{>{{\raggedright\arraybackslash}}p{{10.12cm}}}}{{{tex(definition)}}} & {level} & \\")
        else:
            L.append(f"{fcell} & {tex(definition)} & {values_cell(vals)} & {level} & {'flagged' if flag else ''} \\\\")
    L += [r"\bottomrule", r"\end{tabular}}"]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "paper" / "acme" / "tables" / "tab-fields.tex")
    a = ap.parse_args()
    tr = rc.Tracker()
    text = build(tr)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    n = sum(1 for r in ROWS if r[1] is not None)
    rc.write_source([a.out], "analysis/acme/make_tab_fields.py", P, tr, extra={"n_fields": n, "left_to_supplement": LEFT_TO_SUPPLEMENT})
    print(f"wrote {a.out}; {n} fields; checks passed")


if __name__ == "__main__":
    main()
