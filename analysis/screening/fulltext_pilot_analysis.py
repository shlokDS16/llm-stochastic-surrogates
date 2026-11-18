"""Amendment v0.8 C: full-text reference pilot, error rates of each abstract-level rule.

    .venv/Scripts/python -I analysis/screening/fulltext_pilot_analysis.py [--confirmed data/processed/fulltext-pilot/confirm-sheet.csv]

Reference = the blind full-text reader's decision (YES / NO), replaced by Shlok's decision where he filled
`your_decision` in the confirm sheet. Records without an open full text or judged UNCLEAR are left out of the
error rates and counted. For each rule (strict, liberal, Claude non-EXCLUDE, OLMo non-EXCLUDE, Qwen non-EXCLUDE):
false exclusions = reference YES but the rule excludes; false inclusions = reference NO but the rule includes;
overall and per (Claude, OLMo) cell, with Wilson 95 percent intervals. Also: strict-vs-liberal discordant records,
and RQ1 codability among records with no INCLUDE vote. Writes runs/fulltext-pilot/report.md and results.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data/processed/fulltext-pilot"


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirmed", default=str(P / "confirm-sheet.csv"))
    a = ap.parse_args()
    samp = {json.loads(l)["id"]: json.loads(l) for l in (P / "sample.jsonl").read_text(encoding="utf-8").splitlines() if l}
    J = {}
    for f in sorted(P.glob("judgements-*.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                j = json.loads(l); J[j["id"]] = j
    conf = {}
    if Path(a.confirmed).exists():
        for row in csv.DictReader(open(a.confirmed, encoding="utf-8-sig")):
            v = (row.get("your_decision (YES/NO)") or "").strip().upper()
            if v in ("YES", "NO"):
                conf[row["pilot_id"]] = v
    v08 = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data/processed/screen/abstract-decisions-v08.jsonl").read_text(encoding="utf-8").splitlines() if l}
    rules = {
        "strict": lambda d: d["strict"] == "eligible",
        "liberal": lambda d: d["liberal"] == "eligible",
        "claude": lambda d: d["claude"] != "EXCLUDE",
        "olmo": lambda d: d["olmo"] != "EXCLUDE",
        "qwen": lambda d: d["qwen"] != "EXCLUDE",
    }
    rows, skipped = [], {"no_full_text": 0, "unclear": 0}
    for i, s in samp.items():
        j = J[i]
        ref = conf.get(j["pilot_id"], j["eligible"])
        if not j["full_text_obtained"]:
            skipped["no_full_text"] += 1; continue
        if ref not in ("YES", "NO"):
            skipped["unclear"] += 1; continue
        d = v08[i]
        rows.append(dict(id=i, pilot_id=j["pilot_id"], cell=f"{s['cell_claude']}/{s['cell_olmo']}", ref=ref,
                         confirmed=j["pilot_id"] in conf, no_include=("INCLUDE" not in (d["claude"], d["olmo"], d["qwen"])),
                         rq1=j.get("rq1_codable_from_abstract"), **{r: f(d) for r, f in rules.items()}))
    res = {"n_used": len(rows), "skipped": skipped, "n_confirmed_by_shlok": sum(r["confirmed"] for r in rows),
           "reference_yes": sum(r["ref"] == "YES" for r in rows), "rules": {}, "by_cell": {}}
    for name in rules:
        yes = [r for r in rows if r["ref"] == "YES"]; no = [r for r in rows if r["ref"] == "NO"]
        fe = sum(not r[name] for r in yes); fi = sum(r[name] for r in no)
        res["rules"][name] = dict(false_excl=fe, ref_yes=len(yes), fe_rate=round(fe / len(yes), 3) if yes else None,
                                  fe_ci=wilson(fe, len(yes)), false_incl=fi, ref_no=len(no),
                                  fi_rate=round(fi / len(no), 3) if no else None, fi_ci=wilson(fi, len(no)))
    cells = defaultdict(list)
    for r in rows:
        cells[r["cell"]].append(r)
    for c, rs in sorted(cells.items()):
        yes = [r for r in rs if r["ref"] == "YES"]
        res["by_cell"][c] = dict(n=len(rs), ref_yes=len(yes), **{f"fe_{n}": sum(not r[n] for r in yes) for n in ("strict", "liberal")})
    disc = [r for r in rows if r["strict"] != r["liberal"]]
    res["strict_vs_liberal_discordant"] = [dict(pilot_id=r["pilot_id"], ref=r["ref"], cell=r["cell"]) for r in disc]
    noinc = [r for r in rows if r["no_include"]]
    res["no_include_records"] = dict(n=len(noinc), ref_yes=sum(r["ref"] == "YES" for r in noinc),
                                     rq1_codable=sum(1 for r in noinc if r["rq1"]))
    s_fe, l_fe = res["rules"]["strict"], res["rules"]["liberal"]
    diff_pp = None if not s_fe["ref_yes"] else round(100 * (s_fe["false_excl"] - l_fe["false_excl"]) / s_fe["ref_yes"], 1)
    n_diff = s_fe["false_excl"] - l_fe["false_excl"]
    res["switch_rule"] = dict(diff_false_excl_pp=diff_pp, records_driving_difference=n_diff,
                              outcome=("report both side by side (difference rests on <= 2 records)" if n_diff <= 2 and (diff_pp or 0) > 10
                                       else "liberal becomes primary" if (diff_pp or 0) > 10 else "strict stays primary"))
    out = ROOT / "runs/fulltext-pilot"; out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    lines = ["# Full-text reference pilot (amendment v0.8 C): PILOT, not a validation", "",
             f"Used {res['n_used']} of 70 (no open full text {skipped['no_full_text']}, unclear {skipped['unclear']}); "
             f"reference YES {res['reference_yes']}; decisions confirmed by Shlok: {res['n_confirmed_by_shlok']}.", "",
             "| rule | false exclusions / reference YES | rate [Wilson 95%] | false inclusions / reference NO | rate [Wilson 95%] |", "|---|---|---|---|---|"]
    for n, r in res["rules"].items():
        lines.append(f"| {n} | {r['false_excl']}/{r['ref_yes']} | {r['fe_rate']} {r['fe_ci']} | {r['false_incl']}/{r['ref_no']} | {r['fi_rate']} {r['fi_ci']} |")
    lines += ["", "By cell (Claude/OLMo): " + "; ".join(f"{c}: n {v['n']}, YES {v['ref_yes']}, FE strict {v['fe_strict']}, FE liberal {v['fe_liberal']}" for c, v in res["by_cell"].items()),
              "", f"Strict vs liberal discordant records: {res['strict_vs_liberal_discordant']}",
              f"Records with no INCLUDE vote: {res['no_include_records']}",
              f"Switch rule (pre-set): {res['switch_rule']}"]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
