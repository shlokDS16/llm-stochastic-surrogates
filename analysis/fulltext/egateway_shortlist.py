"""Rank the records without a full text for a 10-paper eGateway shortlist (Shlok, 2026-10-17: access for about 10 only).

    .venv/Scripts/python.exe -I analysis/fulltext/egateway_shortlist.py

Inputs: data/processed/fulltext/missing-fulltext.csv (48 records, groups A eGateway / B open repository), the interim design
(runs/rq234-interim snapshot via rq234_analysis, Claude coder), records.jsonl (OpenAlex cited_by).
Ranking (fixed here, before any new text is read):
  1. RQ1 abstract flag yes first, then unclear, then no (a flagged record is the likeliest to be eligible and so to inform RQ2-RQ4);
  2. within a flag level, the largest current design weight of the record's estimation group (N_g / r_g): one more respondent
     there lowers the largest weights most and raises the effective sample size most;
  3. then OpenAlex citations (impact), then order.
Output: runs/egateway-shortlist/ranked.csv and shortlist.md (top 10 of group A, plus the group-B rank for information).
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rq234_analysis as R  # noqa: E402

FLAG_RANK = {"yes": 0, "unclear": 1, "no": 2}


def main():
    src = ROOT / "runs/rq234-interim"
    snap = src / "input-snapshot"
    sample = R.jl(ROOT / "data/processed/fulltext-sample/sample.jsonl")
    reading = {r["order"]: r for r in R.jl(ROOT / "data/processed/fulltext/reading-list.jsonl")}
    ids = {s["id"] for s in sample}
    records = {r["id"]: r for r in R.jl(ROOT / "data/processed/records.jsonl") if r["id"] in ids}
    ext = {c: {} for c in R.CODERS}
    for c in R.CODERS:
        for f in sorted((snap / c).glob("[0-9][0-9][0-9].json")):
            ext[c][int(f.stem)] = json.loads(f.read_text(encoding="utf-8"))
    units = R.build_units(sample, reading, records, ext)
    d = R.Design(units, "claude", [])
    by_order = {u["order"]: u for u in units}
    with open(ROOT / "data/processed/fulltext/missing-fulltext.csv", encoding="utf-8-sig", newline="") as fh:
        miss = list(csv.DictReader(fh))
    rows = []
    for m in miss:
        o = int(m["order"])
        u = by_order[o]
        g = d.grp[u["stratum"]]
        rec = records.get(u["id"], {})
        rows.append(dict(order=o, group=m["group"], publisher=m["publisher"], doi=m["doi"], title=m["title"], stratum=u["stratum"],
                         rq1_flag=str(u["flag"]).lower(), est_group=g, N_g=d.Ng[g], r_g=d.rg[g],
                         group_weight=round(d.Ng[g] / d.rg[g], 1) if d.rg[g] else None,
                         weight_if_added=round(d.Ng[g] / (d.rg[g] + 1), 1),
                         cited_by=rec.get("cited_by") or 0, year=u["year"]))
    rows.sort(key=lambda r: (FLAG_RANK.get(r["rq1_flag"], 3), -(r["group_weight"] or 1e9), -r["cited_by"], r["order"]))
    for i, r in enumerate(rows, 1):
        r["rank_all"] = i
    out = ROOT / "runs/egateway-shortlist"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "ranked.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    a = [r for r in rows if r["group"].startswith("A")]
    md = ["# eGateway shortlist (10 of the 20 paywalled records)\n",
          "Rule (fixed before reading): RQ1 abstract flag yes > unclear > no; then the largest current design weight of the record's "
          "estimation group (N_g / r_g, Claude coding, interim design); then OpenAlex citations.\n",
          "| rank | order | publisher | DOI | title | RQ1 flag | group weight now -> if added | citations |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(a[:10], 1):
        md.append(f"| {i} | {r['order']} | {r['publisher']} | {r['doi']} | {r['title']} | {r['rq1_flag']} | {r['group_weight']} -> "
                  f"{r['weight_if_added']} | {r['cited_by']} |")
    md += ["", f"Not shortlisted (stay nonresponse): {len(a) - 10} paywalled records and {len(rows) - len(a)} group-B records."]
    (out / "shortlist.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
