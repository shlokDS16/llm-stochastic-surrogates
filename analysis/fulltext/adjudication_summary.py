"""Unblind the adjudication of the 20 sampled coder disagreements (protocol amendment v0.12 item 5) and summarise it.

    python -I analysis/fulltext/adjudication_summary.py [--run runs/rq234-final]

Reads <run>/adjudication-result.jsonl (the blinded Opus adjudicator's verdicts on values A and B) and <run>/adjudication-key.json
(which coder gave A and B; never shown to the adjudicator). Writes <run>/adjudication-summary.csv (one row per item, with the
coder whose value fits the rule) and adjudication-summary.json (counts by category, by coder favoured, by field group). The
dataset is not recoded (protocol).
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def group(field):
    if field.startswith("F.perturbations_tested"):
        return "perturbations"
    if field.startswith("F.robustness_outcome"):
        return "robustness outcome"
    if field.startswith("F.f"):
        return "reporting items f1-f12"
    return field.split("[")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/rq234-final")
    run = ROOT / ap.parse_args().run
    key = json.loads((run / "adjudication-key.json").read_text(encoding="utf-8"))["mapping"]
    res = [json.loads(l) for l in (run / "adjudication-result.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = []
    for r in res:
        fit = r["fits_rule"].strip()
        coder = key[r["id"]].get(fit) if fit in ("A", "B") else "neither"
        rows.append(dict(id=r["id"], order=r["order"], field=r["field"], item=r.get("item", ""), group=group(r["field"]),
                         category=r["category"], fits_rule_value=fit, favoured_coder=coder))
    with open(run / "adjudication-summary.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    out = dict(n=len(rows), by_category=dict(Counter(r["category"] for r in rows)),
               by_favoured_coder=dict(Counter(r["favoured_coder"] for r in rows)),
               by_group={g: dict(Counter(r["favoured_coder"] for r in rows if r["group"] == g)) for g in sorted({r["group"] for r in rows})},
               category_by_coder={c: dict(Counter(r["favoured_coder"] for r in rows if r["category"] == c)) for c in sorted({r["category"] for r in rows})})
    (run / "adjudication-summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
