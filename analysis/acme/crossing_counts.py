"""Counts and agreement for the crossing coding (X1 crossed, X2 decomposed, X3 interaction).

    python analysis/acme/crossing_counts.py

Reads data/processed/crossing/<pass>/<order>.json for every pass directory present (claude, codex, ...).
Writes runs/crossing/counts.csv (one row per pass) and, when two or more passes exist, runs/crossing/agreement.csv
(one row per pass pair and field: studies coded by both, percent agreement, Cohen's kappa).
Coding brief: research/protocol/crossing-coding-brief.md.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/processed/crossing"
OUT = ROOT / "runs/crossing"

X1_LEVELS = ["yes", "partial", "no", "not_reported"]
X2_LEVELS = ["yes", "no", "not_reported"]
X3_LEVELS = ["yes", "no", "not_reported"]


def load_pass(d: Path) -> dict[int, dict]:
    out = {}
    for f in sorted(d.glob("[0-9]*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        out[int(rec["order"])] = rec
    return out


def value(rec: dict, key: str) -> str:
    return str(rec.get(key, {}).get("value", "not_reported"))


def non_r_crossed(rec: dict) -> bool:
    """X1 yes with at least two crossed sources other than repeated draws (R)."""
    if value(rec, "X1") != "yes":
        return False
    return len([s for s in rec["X1"].get("sources_crossed", []) if s != "R"]) >= 2


def counts_row(name: str, recs: dict[int, dict]) -> dict:
    n = len(recs)
    row: dict = {"pass": name, "n": n}
    for key, levels in (("X1", X1_LEVELS), ("X2", X2_LEVELS), ("X3", X3_LEVELS)):
        c = Counter(value(r, key) for r in recs.values())
        for lv in levels:
            row[f"{key}_{lv}"] = c.get(lv, 0)
        other = sum(v for k, v in c.items() if k not in levels)
        if other:
            row[f"{key}_other"] = other
    row["X1_yes_ge2_sources_excl_R"] = sum(non_r_crossed(r) for r in recs.values())
    row["X2_variance_share"] = sum("variance_share" in r["X2"].get("x2_types", []) for r in recs.values())
    row["X2_anova_or_mixed"] = sum("anova_or_mixed_term" in r["X2"].get("x2_types", []) for r in recs.values())
    row["X2_effect_change"] = sum("effect_change" in r["X2"].get("x2_types", []) for r in recs.values())
    row["multi_source_varied_ge2"] = sum(len(r.get("sources_varied", [])) >= 2 for r in recs.values())
    return row


def kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if math.isclose(pe, 1.0):
        return float("nan")
    return (po - pe) / (1 - pe)


def agreement_rows(pa: str, ra: dict, pb: str, rb: dict) -> list[dict]:
    common = sorted(set(ra) & set(rb))
    fields = {
        "X1": lambda r: value(r, "X1"),
        "X1_crossed_yes_vs_other": lambda r: "yes" if value(r, "X1") == "yes" else "other",
        "X2": lambda r: value(r, "X2"),
        "X3": lambda r: value(r, "X3"),
    }
    rows = []
    for name, fn in fields.items():
        a = [fn(ra[o]) for o in common]
        b = [fn(rb[o]) for o in common]
        agree = 100 * sum(x == y for x, y in zip(a, b)) / len(common) if common else float("nan")
        k = kappa(a, b)
        rows.append({"pass_a": pa, "pass_b": pb, "field": name, "n_common": len(common),
                     "percent_agreement": round(agree, 1), "kappa": "" if math.isnan(k) else round(k, 3)})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, 0) for k in keys})


def main() -> None:
    passes = {d.name: load_pass(d) for d in sorted(SRC.iterdir()) if d.is_dir() and any(d.glob("[0-9]*.json"))}
    if not passes:
        raise SystemExit(f"no pass directories with JSON under {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "counts.csv", [counts_row(n, r) for n, r in passes.items()])
    print("wrote", OUT / "counts.csv", {n: len(r) for n, r in passes.items()})
    if len(passes) >= 2:
        rows = []
        for (pa, ra), (pb, rb) in itertools.combinations(passes.items(), 2):
            rows += agreement_rows(pa, ra, pb, rb)
        write_csv(OUT / "agreement.csv", rows)
        print("wrote", OUT / "agreement.csv")


if __name__ == "__main__":
    main()
