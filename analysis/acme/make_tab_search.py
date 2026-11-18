"""Generate paper/acme/tables/tab-search.tex (search strategy by source and sub-query, PRISMA-S items 1, 8, 9, 10).

Rows: OpenAlex sub-queries B1 to B10 and the arXiv query, from run S2 of research/protocol/search-log.md (query v0.7).  For each row: source and
block, search date (heading of the run), the query terms, the count announced by the interface, the count returned (fetched), the retrieval cap
and the language filter.  The OpenAlex model block (shared by B1 to B10) is printed once in a spanning row.  Returned counts are taken from the log and
compared with research/protocol/prisma-counts.json (identified.*), and the sum of announced minus returned with the \\NUM key rm.nOaNotReturned
of paper/acme/autonumbers.tex; the arXiv cognition terms are compared with the union of the OpenAlex blocks.  Mismatches are printed, written to
tab-search.tex.source.json and never repaired by hand (exit status 2 with --strict).  No AI tool is named: the exhibit gives the query, not the
screening procedure.

Retrieval cap and language are read from the code that ran the search: analysis/search/openalex_search.py (cursor paging until exhausted, 50 records per
page, no language filter in the request; the 'language' field is only selected) and analysis/search/arxiv_search.py (all pages, 500 per request).

Usage (project root):  .venv/Scripts/python.exe -I analysis/acme/make_tab_search.py [--out paper/acme/tables/tab-search.tex] [--strict]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402

ROOT = rc.ROOT
LOG = ROOT / "research" / "protocol" / "search-log.md"
PC = ROOT / "research" / "protocol" / "prisma-counts.json"
AUTO = ROOT / "paper" / "acme" / "autonumbers.tex"
OA_CODE = ROOT / "analysis" / "search" / "openalex_search.py"
AX_CODE = ROOT / "analysis" / "search" / "arxiv_search.py"


def tex(s: str) -> str:
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$")):
        s = s.replace(a, b)
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    return s


def num(n: int) -> str:
    return f"{n:,}".replace(",", "{,}")


def split_terms(block: str, prefix: str = "") -> list[str]:
    terms = [t.strip() for t in re.split(r"\s+OR\s+", block.strip())]
    return [t[len(prefix):] if prefix and t.startswith(prefix) else t for t in terms]


def parse_log(txt: str):
    s2 = txt[txt.index("## OpenAlex run S2"):]
    oa_head = re.match(r"## OpenAlex run S2, query (v[\d.]+) \((\d{4}-\d{2}-\d{2})T", s2)
    ax_i = s2.index("## arXiv run S2")
    oa_part, ax_part = s2[:ax_i], s2[ax_i:]
    ax_head = re.match(r"## arXiv run S2 \((\d{4}-\d{2}-\d{2})T", ax_part)
    assert oa_head and ax_head
    rows = []
    for m in re.finditer(r"^\| (B\d+) \| (\d+) \| (\d+) \| `(.+)` \|$", oa_part, re.M):
        rows.append({"block": m.group(1), "announced": int(m.group(2)), "returned": int(m.group(3)), "query": m.group(4)})
    q = re.search(r"^Query: `(.+)`$", ax_part, re.M).group(1)
    tot = re.search(r"Total reported: (\d+); fetched: (\d+)", ax_part)
    return {"version": oa_head.group(1), "oa_date": oa_head.group(2), "ax_date": ax_head.group(1), "rows": rows,
            "ax_query": q, "ax_announced": int(tot.group(1)), "ax_returned": int(tot.group(2))}


def split_query(q: str, prefix: str = ""):
    m = re.match(r"^\((.+?)\) AND \((.+)\)(?: AND submittedDate:\[.*\])?$", q)
    assert m, q[:80]
    return split_terms(m.group(1), prefix), split_terms(m.group(2), prefix)


def build(tr: rc.Tracker):
    log = parse_log(tr.add(LOG).read_text(encoding="utf-8"))
    pc = tr.json(PC)
    auto = tr.add(AUTO).read_text(encoding="utf-8")
    issues: list[str] = []
    rows = log["rows"]
    assert [r["block"] for r in rows] == [f"B{i}" for i in range(1, 11)]
    models = None
    out_rows = []
    all_cog: list[str] = []
    for r in rows:
        a, b = split_query(r["query"])
        models = models or a
        if a != models:
            issues.append(f"MISMATCH model block of {r['block']} differs from B1")
        r["terms"] = b
        all_cog += b
        pcv = pc["identified"][f"openalex-S2-{r['block']}"]
        if pcv != r["returned"]:
            issues.append(f"MISMATCH {r['block']}: returned {r['returned']} in search-log.md vs {pcv} in prisma-counts.json")
    if pc["identified"]["arxiv-S2"] != log["ax_returned"]:
        issues.append(f"MISMATCH arXiv returned {log['ax_returned']} in search-log.md vs {pc['identified']['arxiv-S2']} in prisma-counts.json")
    if log["ax_announced"] != log["ax_returned"]:
        issues.append(f"NOTE arXiv announced {log['ax_announced']} and returned {log['ax_returned']}")
    nnr = sum(r["announced"] - r["returned"] for r in rows)
    m = re.search(r"NUM:rm\.nOaNotReturned\\endcsname\{([^}]*)\}", auto)
    if not m or int(m.group(1)) != nnr:
        issues.append(f"MISMATCH announced minus returned over B1-B10 = {nnr} vs autonumbers.tex rm.nOaNotReturned = {m.group(1) if m else None}")
    ax_models, ax_cog = split_query(log["ax_query"], "abs:")
    oa_union = list(dict.fromkeys(all_cog))
    if set(ax_cog) != set(oa_union):
        issues.append(f"MISMATCH arXiv cognition terms differ from the union of B1-B10: only arXiv {sorted(set(ax_cog)-set(oa_union))}; "
                      f"only OpenAlex {sorted(set(oa_union)-set(ax_cog))}")
    # cap and language from the code that ran the search
    oa_code, ax_code = tr.add(OA_CODE).read_text(encoding="utf-8"), tr.add(AX_CODE).read_text(encoding="utf-8")
    assert '"per-page": "100" if select == SELECT_LIGHT else "50"' in oa_code and "cursor" in oa_code and "language" in oa_code
    assert '"max_results": 500' in ax_code and "while total is None or start < total" in ax_code
    assert "lang" not in oa_code.split("def url_for")[1].split("def _net_wait")[0].replace("language,", "")  # no language parameter in the request
    meta = {"version": log["version"], "oa_date": log["oa_date"], "ax_date": log["ax_date"], "n_rows": len(rows) + 1,
            "announced_minus_returned": nnr, "issues": issues}

    def terms_cell(ts: list[str]) -> str:
        return "; ".join(tex(t) for t in ts)

    L = [
        "% GENERATED by analysis/acme/make_tab_search.py from research/protocol/search-log.md (run S2) and research/protocol/prisma-counts.json. Do not edit by hand.",
        "% Terms inside a block are joined by OR in the query; the model block joins to every OpenAlex block with AND.",
        r"{\footnotesize\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.05}",
        r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{1.95cm}p{1.45cm}>{\raggedright\arraybackslash}p{6.3cm}rrp{0.8cm}p{1.3cm}@{}}",
        r"\toprule",
        r"Source, block & Search date & Terms of the cognition block (joined by OR) & Announced & Returned & Cap & Language \\",
        r"\midrule",
        r"\multicolumn{7}{@{}p{15.0cm}@{}}{\scriptsize\emph{OpenAlex model block, joined by AND to each cognition block below:} " + terms_cell(models) + r". Retrieval cap: none; every page was fetched, 50 records per page for OpenAlex and 500 per request for arXiv} \\",
        r"\addlinespace[2pt]",
    ]
    for r in rows:
        L.append(f"OpenAlex {r['block']} & {log['oa_date']} & {{\\scriptsize {terms_cell(r['terms'])}}} & {num(r['announced'])} & {num(r['returned'])} & "
                 f"none & no filter \\\\")
        L.append(r"\addlinespace[2pt]")
    L += [r"\midrule",
          f"arXiv & {log['ax_date']} & {{\\scriptsize Union of the cognition terms of B1 to B10, searched in the abstract field and joined by OR; model block of "
          f"{len(ax_models)} terms: {terms_cell(ax_models)}; submitted 2026-06-01 to 2026-10-16}} & {num(log['ax_announced'])} & {num(log['ax_returned'])} & "
          f"none & no filter \\\\",
          r"\bottomrule", r"\end{tabular}}"]
    return "\n".join(L) + "\n", meta, log


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "paper" / "acme" / "tables" / "tab-search.tex")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    tr = rc.Tracker()
    text, meta, _ = build(tr)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    rc.write_source([a.out], "analysis/acme/make_tab_search.py", PC, tr, extra=meta)
    print(f"wrote {a.out}; rows {meta['n_rows']}; mismatches/notes {len(meta['issues'])}")
    for s in meta["issues"]:
        print("  ", s)
    if a.strict and any(s.startswith("MISMATCH") for s in meta["issues"]):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
