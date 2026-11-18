"""Included-studies table and ESM_1 (revision-list item A2).  CPU only, no LLM, deterministic.

Run:  .venv/Scripts/python.exe -I analysis/fulltext/included_studies.py [--out runs/included-studies]

Reads (never edits)
  data/processed/fulltext-sample/sample.jsonl        150 analysed records (analysed == true), stratum
  data/processed/fulltext/reading-list.jsonl         title, year, venue, DOI, arXiv id, full-text status
  data/processed/prisma-fulltext.json                counts used as a cross-check
  data/processed/extraction/{claude,codex}/NNN.json  eligibility and blocks A-F per coder
  paper/common/references.bib                        only to report which inc<NNN> keys exist

Writes
  runs/included-studies/{config.json,log.txt,git_sha.txt,included-studies.csv}
  paper/tables/T-included.tex                        longtable of the included studies
  paper/esm/ESM_1-analysed-records.csv, paper/esm/ESM_1-README.md

Inclusion in the table: "YES" in the Claude or the Codex coding (raw decisions, no override).
Orders 17 and 54 are abstract-only and counted as excluded in the main analysis
(analysis/fulltext/rq234_analysis.py OVERRIDE_INELIGIBLE); order 54 (Claude U, Codex Y) is therefore in the table
with a dagger, order 17 (Claude U, Codex N) is not.  The table and ESM report the raw coder decisions.
The "primary coder" of a table row is Claude if Claude coded the record YES, otherwise Codex.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODERS = ("claude", "codex")
FAMILY_ORDER = ["HB", "JDM", "RE", "TOM", "MEM", "LANG", "LEARN", "NUM", "MOR", "DEV", "OTH"]
PERT_CODE = {"wording": "W", "option_order": "O", "decoding": "D", "model_version": "V", "contamination": "C",
             "response_format": "F", "persona": "P", "seeds": "S", "language": "L", "other": "X"}
HUMAN_SHORT = {"none": "none", "own_sample": "own", "published_norms": "norms", "crowd_norms": "crowd",
               "replication_dataset": "repl.", "": "n/c"}
BASE_FAMILY = [("chatgpt", "GPT"), ("gpt", "GPT"), ("deepseek", "DeepSeek"), ("gemma", "Gemma"), ("gemini", "Gemini"), ("flan", "Flan-T5"),
               ("chatglm", "ChatGLM"), ("olmo", "OLMo"), ("qwen", "Qwen"), ("llama", "Llama"), ("mistral", "Mistral"),
               ("mixtral", "Mistral"), ("claude", "Claude"), ("granite", "Granite"), ("phi", "Phi"), ("falcon", "Falcon"),
               ("vicuna", "Vicuna"), ("palm", "PaLM"), ("grok", "Grok"), ("perplexity", "Perplexity")]
ABSTRACT_ONLY = {17, 54}  # counted as excluded in the main analysis (E5 abstract-only), see rq234_analysis.py
TEX_SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
               "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}

log = logging.getLogger("included_studies")


def tex(s: str) -> str:
    return "".join(TEX_SPECIAL.get(ch, ch) for ch in str(s))


def jl(p: Path):
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def low(v) -> str:
    return str(v).strip().lower() if v is not None else ""


def code(dec: str | None) -> str:
    """YES/NO/UNCLEAR -> Y/N/U ; None (no full text) -> '-'."""
    return {"YES": "Y", "NO": "N", "UNCLEAR": "U"}.get(str(dec).upper(), "-") if dec else "-"


def load():
    sample = [s for s in jl(ROOT / "data/processed/fulltext-sample/sample.jsonl") if s.get("analysed")]
    reading = {r["order"]: r for r in jl(ROOT / "data/processed/fulltext/reading-list.jsonl")}
    ext = {c: {} for c in CODERS}
    for c in CODERS:
        for f in sorted((ROOT / "data/processed/extraction" / c).glob("[0-9][0-9][0-9].json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            ext[c][int(f.stem)] = d
    prisma = json.loads((ROOT / "data/processed/prisma-fulltext.json").read_text(encoding="utf-8"))
    bib = (ROOT / "paper/common/references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"^@\w+\{(inc\d{3})\s*,", bib, flags=re.M))
    return sample, reading, ext, prisma, keys


def effect_rows(d: dict | None) -> int:
    """Rows counted as in derive_labels.rows_for: effects entries carrying an outcome_kind."""
    if not d:
        return 0
    return sum(1 for r in d.get("E", {}).get("effects", []) if "outcome_kind" in r and low(r.get("outcome_kind")))


def first_family(d: dict | None) -> str:
    if not d:
        return ""
    for p in d.get("C", {}).get("paradigms", []):
        if p.get("family"):
            return p["family"]
    return ""


def model_names(d: dict | None) -> list[str]:
    out = []
    if not d:
        return out
    for m in d.get("B", {}).get("models", []):
        fam = (m.get("family") or "").strip()
        name = (m.get("name") or "").strip()
        lab = fam
        if fam.lower() in ("", "other"):
            lab = next((b for k, b in BASE_FAMILY if name.lower().startswith(k)), None)
            if lab is None:
                lab = re.split(r"[\s(,/]|-(?=\d)", name)[0][:14]
        if lab.lower() in [m.lower() for m in out]:
            continue
        if lab and lab not in out:
            out.append(lab)
    return out


def perts(d: dict | None) -> list[str]:
    if not d:
        return []
    return [low(t) for t in d.get("F", {}).get("perturbations_tested", []) if low(t)]


def build(sample, reading, ext):
    rows = []
    for s in sorted(sample, key=lambda s: s["order"]):
        o = s["order"]
        rd = reading[o]
        cl, cx = ext["claude"].get(o), ext["codex"].get(o)
        a = {}
        for d in (cl, cx):
            if d and d.get("A"):
                for k, v in d["A"].items():
                    a.setdefault(k, v) if v not in (None, "") else None
        ft = rd.get("status") == "ok" and bool(rd.get("md_chars"))
        dec = {c: (ext[c][o]["eligibility"]["decision"] if ft and o in ext[c] else None) for c in CODERS}
        fc = {c: (ext[c][o]["eligibility"].get("failed_criterion") if ft and o in ext[c] else None) for c in CODERS}
        r = dict(order=o, openalex_id=s["id"], doi=rd.get("doi") or a.get("doi") or "", arxiv_id=rd.get("arxiv") or a.get("arxiv_id") or "",
                 title=rd.get("title") or a.get("title") or "", first_author=a.get("first_author") or "",
                 year=rd.get("year") or a.get("year") or "", venue=rd.get("venue") or a.get("venue") or "",
                 stratum=s["stratum"], fulltext_obtained="yes" if ft else "no",
                 claude_decision=dec["claude"] or "no_full_text", claude_failed_criterion=fc["claude"] or "",
                 codex_decision=dec["codex"] or "no_full_text", codex_failed_criterion=fc["codex"] or "",
                 main_analysis_status=("excluded: abstract-only (E5, pending human confirmation)" if o in ABSTRACT_ONLY and ft else ""),
                 bib_key=f"inc{o:03d}", _cl=cl if ft else None, _cx=cx if ft else None)
        r["in_table"] = "yes" if "YES" in dec.values() else "no"
        prim = cl if dec["claude"] == "YES" else cx
        sec = cx if prim is cl else cl
        fam = first_family(prim) or first_family(sec)
        r["family"] = fam if fam else "OTH"
        r["family_note"] = "" if fam else "no family coded; shown as OTH"
        mods = model_names(prim) or model_names(sec)
        r["models"] = mods
        r["human"] = low((prim or {}).get("D", {}).get("primary_type")) if prim else ""
        r["n_rows_claude"], r["n_rows_codex"] = effect_rows(cl if ft else None), effect_rows(cx if ft else None)
        r["perts"] = perts(prim)
        r["codes"] = {c: code(dec[c]) for c in CODERS}
        rows.append(r)
    return rows


def models_cell(mods: list[str]) -> str:
    if not mods:
        return "n/c"
    shown = ", ".join(tex(m) for m in mods[:3])
    return shown + (f" +{len(mods) - 3}" if len(mods) > 3 else "")


def write_table(rows, path: Path, keys_missing: list[str]) -> None:
    inc = [r for r in rows if r["in_table"] == "yes"]
    inc.sort(key=lambda r: (FAMILY_ORDER.index(r["family"]) if r["family"] in FAMILY_ORDER else 99, int(r["year"] or 0), r["order"]))
    cap = (r"Studies coded eligible by at least one coder (the primary or the second coder) among the 150 analysed records, "
           r"ordered by first paradigm family and year. The same list with identifiers is in Online Resource ESM\_1. "
           "Family: HB heuristics and biases, JDM judgement and decision making, RE reasoning, TOM theory of mind, MEM memory, "
           "LANG psycholinguistics, LEARN learning, NUM numerical cognition, MOR moral judgement, DEV development, OTH other. "
           
           f"{len(inc)} studies.")
    L = []
    L.append("% generated by analysis/fulltext/included_studies.py; do not edit by hand")
    L.append("% needs \\usepackage{booktabs,longtable}; place with \\tabIncluded (a longtable, not a float)")
    L.append("\\begingroup\\footnotesize\\setlength{\\tabcolsep}{2.5pt}\\renewcommand{\\arraystretch}{0.9}")
    L.append("\\begin{longtable}{@{}l l >{\\raggedright\\arraybackslash}p{0.12\\textwidth} l c l c@{}}")  # 0.20 overflowed the sn-jnl text width (CRP-S05)
    L.append(f"\\caption{{{cap}}}\\label{{tab:included}}\\\\")
    head = ("Study & Family & Models & Human & Rows & Perturbations & C/X \\\\")
    L += ["\\toprule", head, "\\midrule", "\\endfirsthead",
          "\\multicolumn{7}{@{}l}{\\tablename\\ \\thetable\\ (continued)}\\\\", "\\toprule", head, "\\midrule", "\\endhead",
          "\\midrule \\multicolumn{7}{r@{}}{\\emph{continued on the next page}}\\\\ \\bottomrule \\endfoot",
          "\\bottomrule",
          "\\multicolumn{7}{@{}p{\\dimexpr\\textwidth-5pt\\relax}}{\\footnotesize Notes. Models: model families as coded (the model name when the family "
          "is not standard), at most three, then the number of further families; n/c = not coded. "
          "Human: primary human comparison coded for the study (none; own = own human sample; norms = published norms; crowd = crowd norms; repl. = replication dataset). "
          "Rows: effect, accuracy or agreement rows extracted, primary/second coder. "
          "Perturbations run by the study (primary coder if it coded the study eligible, otherwise second coder): "
          "W wording, O option order, D decoding, V model version, C contamination check, F response format, P persona, "
          "S seeds, L language, X other; a dash = none. "
          "C/X: eligibility in the primary and second codings, Y eligible, N not eligible, U unclear. "
          "$^\\dagger$ Counted as excluded in the main analysis (abstract-only; pending human confirmation).}\\\\",
          "\\endlastfoot"]
    prev = None
    for r in inc:
        if prev is not None and r["family"] != prev:
            L.append("\\midrule")
        prev = r["family"]
        dag = "$^\\dagger$" if r["order"] in ABSTRACT_ONLY else ""
        pt = "".join(PERT_CODE.get(p, "X") for p in sorted(set(r["perts"]), key=lambda p: list(PERT_CODE).index(p) if p in PERT_CODE else 99))
        L.append(" & ".join([f"\\citet{{inc{r['order']:03d}}}{dag}", tex(r["family"]), models_cell(r["models"]),
                             tex(HUMAN_SHORT.get(r["human"], r["human"])),
                             f"{r['n_rows_claude']}/{r['n_rows_codex']}", pt or "--",
                             f"{r['codes']['claude']}/{r['codes']['codex']}"]) + " \\\\")
    L.append("\\end{longtable}")
    L.append("\\endgroup")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    log.info("T-included.tex: %d studies; family counts %s", len(inc), dict(Counter(r["family"] for r in inc)))


ESM_COLS = ["order", "openalex_id", "doi", "arxiv_id", "title", "first_author", "year", "venue", "stratum", "fulltext_obtained",
            "claude_decision", "claude_failed_criterion", "codex_decision", "codex_failed_criterion",
            "in_included_table", "main_analysis_status", "bib_key"]
ESM_COLS += [f"claude_f{i}" for i in range(1, 13)] + ["claude_perturbations"]
ESM_COLS += [f"codex_f{i}" for i in range(1, 13)] + ["codex_perturbations"]


def write_esm(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ESM_COLS)
        w.writeheader()
        for r in rows:
            out = {k: r.get(k, "") for k in ESM_COLS}
            out["in_included_table"] = r["in_table"]
            for c, d in (("claude", r["_cl"]), ("codex", r["_cx"])):
                if d is not None and d["eligibility"]["decision"] == "YES":
                    for i in range(1, 13):
                        out[f"{c}_f{i}"] = d.get("F", {}).get(f"f{i}", "")
                    out[f"{c}_perturbations"] = ";".join(perts(d))
            w.writerow(out)
    log.info("ESM_1 csv: %d rows", len(rows))


README = """# ESM_1: the 150 analysed records

One row per analysed record (the first 150 records of the stratified full-text sample, in sample order). UTF-8 CSV, comma separated, header row.

Sources: `data/processed/fulltext-sample/sample.jsonl` (order, OpenAlex id, stratum), `data/processed/fulltext/reading-list.jsonl` (title, year, venue, DOI, arXiv id, full-text status), `data/processed/extraction/{claude,codex}/NNN.json` (eligibility and items). Generated by `analysis/fulltext/included_studies.py`, run `runs/included-studies/`.

| Column | Meaning |
|---|---|
| order | Position in the analysed sample (1-150); the bibliography key of an included study is `inc` plus this number in three digits |
| openalex_id | OpenAlex work id (or `arxiv:` id for preprints without an OpenAlex id) |
| doi | DOI from the reading list, otherwise from the extraction; empty if none |
| arxiv_id | arXiv identifier, empty if none |
| title | Title as held in the reading list |
| first_author | First author as coded by the extractor from the full text. Empty where no full text was obtained (the record file holds no author field) |
| year | Publication year |
| venue | Venue as held in the reading list or, if empty there, as coded from the full text |
| stratum | Sampling stratum `family|period` (paradigm-family label of the sampling frame, `none` = no family; period 2018-2023, 2024 or 2025-2026) |
| fulltext_obtained | `yes` if a full text was retrieved and read, `no` otherwise (48 records) |
| claude_decision, codex_decision | Eligibility decision of each coder: `YES`, `NO`, `UNCLEAR`, or `no_full_text` |
| claude_failed_criterion, codex_failed_criterion | Exclusion criterion of a `NO` decision (e.g. benchmark-only, neural-only, not-llm, not-english, questionnaire-only, other); empty otherwise |
| in_included_table | `yes` if at least one coder decided `YES` (the studies listed in Table `tab:included`) |
| main_analysis_status | `excluded: abstract-only ...` for orders 17 and 54, which the main analysis counts as ineligible although a coder said UNCLEAR or YES (abstract-only evidence, pending human confirmation); empty otherwise |
| bib_key | Bibliography key of the record (`incNNN`) |
| claude_f1 ... claude_f12 | For records the coder decided `YES`: the twelve reporting items of the RQ4 audit as coded (`yes`, `no` or `na`, as defined in the coding form); empty otherwise |
| claude_perturbations | Perturbation types the study ran, as coded, semicolon separated (wording, option_order, decoding, model_version, contamination, response_format, persona, seeds, language, other); empty if none or not eligible |
| codex_f1 ... codex_f12, codex_perturbations | The same for the Codex coder |

Codings are the extractors' raw values; no adjudication has been applied. Counts in the paper use the rules described in the Methods (abstract-only override for orders 17 and 54).
"""


def sha_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/included-studies")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=[
        logging.FileHandler(out / "log.txt", mode="w", encoding="utf-8"), logging.StreamHandler(sys.stdout)])

    sample, reading, ext, prisma, keys = load()
    assert len(sample) == 150, len(sample)
    rows = build(sample, reading, ext)
    inc = [r for r in rows if r["in_table"] == "yes"]
    missing = sorted(f"inc{r['order']:03d}" for r in inc if f"inc{r['order']:03d}" not in keys)
    log.info("analysed %d; full text %d; extracted claude %d codex %d; included (YES in either) %d",
             len(rows), sum(r["fulltext_obtained"] == "yes" for r in rows), len(ext["claude"]), len(ext["codex"]), len(inc))
    log.info("prisma-fulltext.json cross-check: fulltext_assessed %s (extracted here %d)", prisma.get("fulltext_assessed"), len(ext["claude"]))
    log.info("decision counts claude %s codex %s", dict(Counter(r["claude_decision"] for r in rows)), dict(Counter(r["codex_decision"] for r in rows)))
    log.info("bib keys present for %d of %d included; missing %d", len(inc) - len(missing), len(inc), len(missing))

    write_table(rows, ROOT / "paper/tables/T-included.tex", missing)
    write_esm(rows, ROOT / "paper/esm/ESM_1-analysed-records.csv")
    (ROOT / "paper/esm/ESM_1-README.md").write_text(README, encoding="utf-8")

    # run-directory copy and config
    flat = [{k: v for k, v in r.items() if not k.startswith("_")} for r in inc]
    with (out / "included-studies.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order", "family", "models", "human", "rows_claude", "rows_codex", "perturbations", "claude", "codex", "bib_key_in_bib"])
        for r in sorted(flat, key=lambda r: r["order"]):
            w.writerow([r["order"], r["family"], ";".join(r["models"]), r["human"], r["n_rows_claude"], r["n_rows_codex"],
                        ";".join(r["perts"]), r["codes"]["claude"], r["codes"]["codex"], "no" if f"inc{r['order']:03d}" in missing else "yes"])
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:  # noqa: BLE001
        sha = f"unknown ({e!r})"
    (out / "git_sha.txt").write_text(sha + "\n", encoding="utf-8")
    cfg = dict(run="included-studies", script="analysis/fulltext/included_studies.py", git_sha=sha, seed=None,
               note="deterministic, no randomness", python=sys.version.split()[0],
               inclusion_rule="YES in Claude or Codex raw decision", abstract_only_orders=sorted(ABSTRACT_ONLY),
               n_analysed=len(rows), n_included=len(inc), n_bib_keys_missing=len(missing), bib_keys_missing=missing,
               inputs={p: sha_of(ROOT / p) for p in ["data/processed/fulltext-sample/sample.jsonl", "data/processed/fulltext/reading-list.jsonl",
                                                     "data/processed/prisma-fulltext.json"]},
               outputs=["paper/tables/T-included.tex", "paper/esm/ESM_1-analysed-records.csv", "paper/esm/ESM_1-README.md"])
    (out / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    log.info("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
