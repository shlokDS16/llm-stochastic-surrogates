"""Arm L records -> exact outcomes and effects at each analysis temperature (CPU).

    .venv/Scripts/python.exe -I analysis/acme/armL_outcomes.py [--runs runs/acme-L] [--out runs/acme-L/outcomes]

Outcome per prompt (canonical direction, compute-plan 4.2): P1 P(sure option); AF P(anti-speech answer: Yes to forbid, No to allow);
NR P(Yes to the US question), x1 marginalised exactly over the first answer; P3 E[rating] with 9 = definitely go (reversed scale
mapped r -> 10 - r); QA E[agreement] with 9 = strongly agree; P2a-d E[log x] over x > 0; P4 E[log(1 + x)] over x >= 0.
Each outcome is the readout renormalised over valid answers; `valid` is the mass of valid answers (rule: a model-item pair is
flagged when valid < 0.9 on more than 5 percent of its prompts). Effect = outcome(x1) - outcome(x0) per (model, item, W, O, variant, T).
Writes outcomes.csv (one row per prompt and T) and effects.csv.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import numtree  # noqa: E402

TEMPS = ("0.3", "0.7", "1.0", "1.5")
# rating direction: forward scale value r -> canonical. P3 forward: 9 = definitely go; QA forward (ML1): 1 = strongly agree.
RATING_FORWARD_CANON = {"P3": lambda r: r, "QA": lambda r: 10 - r}
RATING_REVERSED_CANON = {"P3": lambda r: 10 - r, "QA": lambda r: r}


def path_mass(paths, T):
    return {L: sum(math.exp(sum(t / float(T) - l for t, l in zip(p["tgt_logits"], p["lse"][T]))) for p in ps) for L, ps in paths.items()}


def binary(paths, T, target):
    m = path_mass(paths, T)
    tot = sum(m.values())
    return (m[target] / tot if tot > 0 else None), tot


def outcome(rec, T):
    it = rec["item"]
    if rec["readout"] == "choice":
        return binary(rec["paths"], T, rec["sure_label"])
    if it == "AF":
        return binary(rec["paths"], T, "Yes" if rec["x"] == 1 else "No")
    if it == "NR":
        if rec["x"] == 1:
            p1, v1 = binary(rec["first"], T, "Yes")
            py, vy = binary(rec["cond"]["Yes"], T, "Yes")
            pn, vn = binary(rec["cond"]["No"], T, "Yes")
            if None in (p1, py, pn):
                return None, 0.0
            return p1 * py + (1 - p1) * pn, v1 * (p1 * vy + (1 - p1) * vn)
        return binary(rec["paths"], T, "Yes")
    if rec["readout"] == "rating" and "paths" in rec:   # primary: answer paths (amendment A-L3)
        mass = {int(L): v for L, v in path_mass(rec["paths"], T).items()}
        tot = sum(mass.values())
        f = (RATING_REVERSED_CANON if rec["O"] == "reversed" else RATING_FORWARD_CANON)[it]
        return (sum(f(r) * m for r, m in mass.items()) / tot if tot > 0 else None), tot
    if rec["readout"] == "rating":
        ids = {int(k.strip()): set() for k in rec["digit_ids"]}
        for k, t in rec["digit_ids"].items():
            ids[int(k.strip())].add(t)
        pos = {t: i for i, t in enumerate(rec["cand_ids"])}
        lse = rec["lse"][T]
        mass = {r: sum(math.exp(rec["cand_logits"][pos[t]] / float(T) - lse) for t in ts) for r, ts in ids.items()}
        tot = sum(mass.values())
        f = (RATING_REVERSED_CANON if rec["O"] == "reversed" else RATING_FORWARD_CANON)[it]
        return (sum(f(r) * m for r, m in mass.items()) / tot if tot > 0 else None), tot
    if rec["readout"] == "number":
        d = numtree.distribution(rec["tree"], float(T))
        if it == "P4":
            v = {x: m for x, m in d["values"].items() if x >= 0}
            g = lambda x: math.log1p(x)
        else:
            v = {x: m for x, m in d["values"].items() if x > 0}
            g = math.log
        tot = sum(v.values())
        # valid = mass on a numeric answer (0.9 rule); coverage = resolved share (plan's 0.5 flag); y over resolved numbers
        return (sum(g(x) * m for x, m in v.items()) / tot if tot > 0 else None), d["numeric_mass"]
    raise KeyError(it)


def main():
    import csv
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/acme-L")
    ap.add_argument("--out")
    a = ap.parse_args()
    runs = ROOT / a.runs
    out = Path(a.out) if a.out else runs / "outcomes"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in sorted(runs.glob("*/*.jsonl")):
        for line in f.open(encoding="utf8"):
            rec = json.loads(line)
            for T in TEMPS:
                y, v = outcome(rec, T)
                row = dict(model=rec["model"], item=rec["item"], W=rec["W"], O=rec["O"], x=rec["x"], variant=rec["variant"], T=T, y=y, valid=v,
                           coverage=None, y_lb=None)
                if rec["readout"] == "number":   # coverage and a lower-bound imputation (open prefixes valued at their digits)
                    d = numtree.distribution(rec["tree"], float(T))
                    row["coverage"] = d["resolved"] / d["numeric_mass"] if d["numeric_mass"] else 0.0
                    lo = 0 if rec["item"] == "P4" else 1e-300
                    g = math.log1p if rec["item"] == "P4" else math.log
                    allv = {}
                    for src in (d["values"], d["open_prefixes"]):
                        for x, m in src.items():
                            if x >= 0 and (x > 0 or rec["item"] == "P4"):
                                allv[x] = allv.get(x, 0.0) + m
                    t = sum(allv.values())
                    row["y_lb"] = sum(g(x) * m for x, m in allv.items()) / t if t > 0 else None
                rows.append(row)
    with (out / "outcomes.csv").open("w", newline="", encoding="utf8") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    idx = {(r["model"], r["item"], r["W"], r["O"], r["variant"], r["T"], r["x"]): r for r in rows}
    eff = []
    for (m, it, W, O, var, T, x), r1 in idx.items():
        if x != 1:
            continue
        r0 = idx.get((m, it, W, O, var, T, 0))
        if r0 is None:
            continue
        d = None if r1["y"] is None or r0["y"] is None else r1["y"] - r0["y"]
        eff.append(dict(model=m, item=it, W=W, O=O, variant=var, T=T, delta=d, y1=r1["y"], y0=r0["y"], valid1=r1["valid"], valid0=r0["valid"]))
    with (out / "effects.csv").open("w", newline="", encoding="utf8") as fo:
        w = csv.DictWriter(fo, fieldnames=list(eff[0]))
        w.writeheader()
        w.writerows(eff)
    print(f"{len(rows)} outcome rows, {len(eff)} effects -> {out}")


if __name__ == "__main__":
    main()
