"""Amendment v0.9 item 3: validate the RQ1 coder's `meets_criteria_on_abstract` flag on the full-text pilot.

    .venv/Scripts/python -I analysis/screening/rq1_pilot_crosstab.py

Reference = full-text eligibility (reader decision, replaced by Shlok's confirm-sheet decision). Uses the pilot
records with an open full text and a YES/NO reference. Reports the cross-tab reference x liberal rule x coder flag,
by (Claude, OLMo) cell and by the coder's paradigm family, and the flag's false exclusions (reference YES, flag
"no") and false inclusions (reference NO, flag "yes"), with Wilson intervals; "unclear" is shown separately.
Writes runs/fulltext-pilot/rq1-flag-crosstab.md. The flag is not tuned afterwards (v0.9).
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data/processed/fulltext-pilot"


def wilson(k, n, z=1.96):
    if n == 0:
        return "n/a"
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} = {p:.2f} [{c - h:.2f}, {c + h:.2f}]"


def main() -> None:
    samp = {json.loads(l)["id"]: json.loads(l) for l in (P / "sample.jsonl").read_text(encoding="utf-8").splitlines() if l}
    J = {}
    for f in sorted(P.glob("judgements-*.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                j = json.loads(l); J[j["id"]] = j
    conf = {r["pilot_id"]: (r.get("your_decision (YES/NO)") or "").strip().upper()
            for r in csv.DictReader(open(P / "confirm-sheet.csv", encoding="utf-8-sig"))}
    v08 = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data/processed/screen/abstract-decisions-v08.jsonl").read_text(encoding="utf-8").splitlines() if l}
    rq1 = {}
    for f in sorted((ROOT / "data/processed/rq1").glob("rq1-batch-*.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l); rq1[r["id"]] = r
    rows = []
    for i, s in samp.items():
        j = J[i]
        ref = conf.get(j["pilot_id"]) if conf.get(j["pilot_id"]) in ("YES", "NO") else j["eligible"]
        if not j["full_text_obtained"] or ref not in ("YES", "NO") or i not in rq1:
            continue
        fams = sorted({p["family"] for p in rq1[i]["paradigms"]}) or ["none"]
        rows.append(dict(pid=j["pilot_id"], ref=ref, cell=f"{s['cell_claude']}/{s['cell_olmo']}", liberal=v08[i]["liberal"],
                         flag=rq1[i]["meets_criteria_on_abstract"], fam=fams[0]))
    yes = [r for r in rows if r["ref"] == "YES"]; no = [r for r in rows if r["ref"] == "NO"]
    out = ["# RQ1 coder flag against the full-text reference (v0.9 item 3; pilot, 53 records max)", "",
           f"Records used: {len(rows)} (reference YES {len(yes)}, NO {len(no)}).", "",
           "## Cross-tab: reference x liberal rule x coder flag", "",
           "| reference | liberal | flag yes | flag unclear | flag no |", "|---|---|---|---|---|"]
    for ref in ("YES", "NO"):
        for lib in ("eligible", "excluded_tiebreak"):
            c = Counter(r["flag"] for r in rows if r["ref"] == ref and r["liberal"] == lib)
            out.append(f"| {ref} | {lib} | {c['yes']} | {c['unclear']} | {c['no']} |")
    out += ["", "## Flag error rates (Wilson 95%)",
            f"- False exclusions (reference YES, flag no): {wilson(sum(r['flag'] == 'no' for r in yes), len(yes))}",
            f"- Reference YES flagged unclear: {wilson(sum(r['flag'] == 'unclear' for r in yes), len(yes))}",
            f"- False inclusions (reference NO, flag yes): {wilson(sum(r['flag'] == 'yes' for r in no), len(no))}",
            f"- Reference NO flagged unclear: {wilson(sum(r['flag'] == 'unclear' for r in no), len(no))}",
            "", "## By (Claude, OLMo) cell: reference YES/NO and flag yes/unclear/no", ""]
    for cell in sorted({r["cell"] for r in rows}):
        rs = [r for r in rows if r["cell"] == cell]
        out.append(f"- {cell}: " + ", ".join(f"{ref}: " + "/".join(str(sum(1 for r in rs if r['ref'] == ref and r['flag'] == f)) for f in ("yes", "unclear", "no")) for ref in ("YES", "NO")))
    out += ["", "## By coder paradigm family (first family; 'none' = no paradigm named)", ""]
    for fam in sorted({r["fam"] for r in rows}):
        rs = [r for r in rows if r["fam"] == fam]
        out.append(f"- {fam}: n {len(rs)}, reference YES {sum(r['ref'] == 'YES' for r in rs)}, flag yes {sum(r['flag'] == 'yes' for r in rs)}")
    dest = ROOT / "runs/fulltext-pilot/rq1-flag-crosstab.md"
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
