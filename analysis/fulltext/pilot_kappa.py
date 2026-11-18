"""Extraction-form pilot: agreement between Claude Sonnet and Codex per categorical field (protocol section 7).

    .venv/Scripts/python -I analysis/fulltext/pilot_kappa.py --orders 1 2 4 ... [--run runs/extraction-pilot]

Inputs: `data/processed/extraction/{claude,codex}/<order:03d>.json` (brief v1.0). Outputs in the run directory:
`kappa.csv` (field, level, n, percent agreement, Cohen's kappa, categories seen), `disagreements.md` (every
disagreeing value with both codes), `config.json` (inputs with sha256). Kappa is a reliability diagnostic, not
validity; fields with kappa < 0.6 are redefined once and re-piloted, or dropped from quantitative synthesis.

Levels: `study` fields use every pilot record both coders judged; YES-only fields use records both coded YES.
Effect rows are matched on (paradigm family, model family): each coder's rows are mapped to the family of their
paradigm (section C) and of their model (section B); per key the modal value is taken; kappa on keys both coded.
Family presence (C) and perturbation types (F) are scored as one binary item per study x category (pooled).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "data/processed/extraction"
FAMILIES = ["HB", "JDM", "RE", "TOM", "MEM", "LANG", "LEARN", "NUM", "MOR", "DEV", "OTH"]
PERTS = ["wording", "option_order", "response_format", "decoding", "seeds", "model_version", "contamination",
         "persona", "language", "other"]


def kappa(a: list, b: list) -> tuple[float | None, float]:
    n = len(a)
    if n == 0:
        return None, float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (None if pe == 1 else (po - pe) / (1 - pe)), po


def norm(v):
    return str(v).strip().lower() if v is not None else "null"


def effect_keys(d: dict) -> dict:
    fam_p = {p.get("pid"): p.get("family") for p in d.get("C", {}).get("paradigms", [])}
    fam_m = {m.get("name"): m.get("family") for m in d.get("B", {}).get("models", [])}
    out: dict = {}
    for r in d.get("E", {}).get("effects", []):
        mf = r.get("model_family") or fam_m.get(r.get("model")) or next((f for n, f in fam_m.items() if n and r.get("model")
                                                 and (n in r["model"] or r["model"] in n)), "other")
        out.setdefault((fam_p.get(r.get("pid"), "?"), mf), []).append(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", nargs="+", type=int, required=True)
    ap.add_argument("--run", default="runs/extraction-pilot")
    a = ap.parse_args()
    run = ROOT / a.run
    run.mkdir(parents=True, exist_ok=True)
    pairs, cfg = {}, {}
    for o in a.orders:
        f1, f2 = EXT / "claude" / f"{o:03d}.json", EXT / "codex" / f"{o:03d}.json"
        if f1.exists() and f2.exists():
            pairs[o] = (json.loads(f1.read_text(encoding="utf-8")), json.loads(f2.read_text(encoding="utf-8")))
            for f in (f1, f2):
                cfg[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    rows, dis = [], []

    def add(field, level, items):  # items: list of (unit, value_claude, value_codex)
        k, po = kappa([x[1] for x in items], [x[2] for x in items])
        cats = sorted(set(x[1] for x in items) | set(x[2] for x in items))
        rows.append(dict(field=field, level=level, n=len(items), agreement=round(po, 3) if items else None,
                         kappa=None if k is None else round(k, 3), categories="|".join(cats)))
        dis.extend(f"- {field} [{u}]: claude={x} codex={y}" for u, x, y in items if x != y)

    add("eligibility.decision", "study", [(o, norm(c["eligibility"]["decision"]), norm(x["eligibility"]["decision"]))
                                          for o, (c, x) in pairs.items()])
    yes = {o: p for o, p in pairs.items() if all(norm(d["eligibility"]["decision"]) == "yes" for d in p)}
    add("A.peer_reviewed", "study", [(o, norm(c["A"].get("peer_reviewed")), norm(x["A"].get("peer_reviewed")))
                                     for o, (c, x) in pairs.items()])
    add("D.primary_type", "yes-both", [(o, norm(c["D"].get("primary_type")), norm(x["D"].get("primary_type")))
                                       for o, (c, x) in yes.items()])
    for i in range(1, 13):
        add(f"F.f{i}", "yes-both", [(o, norm(c["F"].get(f"f{i}")), norm(x["F"].get(f"f{i}"))) for o, (c, x) in yes.items()])
    add("F.robustness_outcome", "yes-both", [(o, norm(c["F"].get("robustness_outcome")),
                                              norm(x["F"].get("robustness_outcome"))) for o, (c, x) in yes.items()])
    fam = lambda d: {p.get("family") for p in d["C"].get("paradigms", [])}  # noqa: E731
    add("C.family_presence (pooled)", "yes-both x family",
        [(f"{o}:{f}", str(f in fam(c)), str(f in fam(x))) for o, (c, x) in yes.items() for f in FAMILIES])
    pt = lambda d: set(d["F"].get("perturbations_tested") or [])  # noqa: E731
    add("F.perturbations_tested (pooled)", "yes-both x type",
        [(f"{o}:{t}", str(t in pt(c)), str(t in pt(x))) for o, (c, x) in yes.items() for t in PERTS])
    matched, unmatched = {}, 0
    for o, (c, x) in yes.items():
        kc, kx = effect_keys(c), effect_keys(x)
        unmatched += len(set(kc) ^ set(kx))
        for key in set(kc) & set(kx):
            matched[(o, key)] = (kc[key], kx[key])
    for fld in ("outcome_kind", "basis", "model_effect_present", "human_effect_present", "direction",
                "model_vs_human", "authors_comparison", "label"):
        mode = lambda rs: Counter(norm(r.get(fld)) for r in rs).most_common(1)[0][0]  # noqa: E731
        add(f"E.{fld}", "matched (paradigm family x model family)",
            [(f"{o}:{k[0]}/{k[1]}", mode(rc), mode(rx)) for (o, k), (rc, rx) in matched.items()])
    import csv
    with (run / "kappa.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (run / "disagreements.md").write_text(
        f"# Disagreements (pilot orders {sorted(pairs)}; both YES: {sorted(yes)}; effect keys matched "
        f"{len(matched)}, unmatched {unmatched})\n\n" + "\n".join(dis) + "\n", encoding="utf-8")
    (run / "config.json").write_text(json.dumps({"orders": a.orders, "pairs": sorted(pairs), "yes_both": sorted(yes),
                                                 "matched_effect_keys": len(matched),
                                                 "unmatched_effect_keys": unmatched, "inputs": cfg}, indent=1),
                                     encoding="utf-8")
    for r in rows:
        print(f"{r['field']:34s} n={r['n']:3d} agree={r['agreement']} kappa={r['kappa']}")


if __name__ == "__main__":
    main()
