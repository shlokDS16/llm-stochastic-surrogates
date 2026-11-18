"""Derive RQ2 summary labels from the observable effect-row fields (amendment v0.12 item 1; brief v1.1 section 6).

    .venv/Scripts/python -I analysis/fulltext/derive_labels.py [--coder claude|codex|both] [--out runs/extraction-labels]

Committed before any main-sample analysis. Rules are transcribed from `research/protocol/fulltext-extraction-brief.md`
v1.1 section 6; where that text leaves a case undecided the script returns an explicit UNCLASSIFIED-* code instead of
choosing (counted and reported, never silently mapped):
- effect rows, model effect present but human effect absent: UNCLASSIFIED-MODEL-ONLY (v1.1 has no label for it);
- effect rows, both present but direction not reported: INSUFFICIENT (direction is an observable the rule needs).
"EXAGGERATED / ATTENUATED by the authors' test" cannot be derived because the form records only whether the authors
found a difference, not its sign; without a common-metric ratio such rows are SAME-DIRECTION-UNQUANTIFIED.
Output: `<out>/<coder>-effects.csv` (one row per effect row: order, study_id, pid, paradigm family, model, model family,
outcome_kind, observables, ratio, derived label, coder label, match) and `<out>/summary.json` (label counts and
derived-versus-coder agreement). Only records with eligibility YES and v1.1 rows (`outcome_kind` present) are used.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "data/processed/extraction"


def num(v) -> float | None:
    try:
        return float(str(v).strip().split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def low(v) -> str:
    return str(v).strip().lower() if v is not None else ""


def derive(r: dict, has_human_data: bool) -> tuple[str, float | None]:
    kind = low(r.get("outcome_kind"))
    if kind == "agreement":
        return "AGREEMENT-ONLY", None
    if kind == "accuracy":
        mvh = low(r.get("model_vs_human"))
        if mvh in ("above", "similar", "below"):
            return {"above": "ABOVE-HUMAN", "similar": "HUMAN-LEVEL", "below": "BELOW-HUMAN"}[mvh], None
        return ("INSUFFICIENT" if has_human_data else "NO-HUMAN-REFERENCE"), None
    if kind != "effect":
        return "UNCLASSIFIED-NO-KIND", None
    m, h, d = low(r.get("model_effect_present")), low(r.get("human_effect_present")), low(r.get("direction"))
    if h == "no_human_reference":
        return "NO-HUMAN-REFERENCE", None
    if m not in ("yes", "no") or h not in ("yes", "no"):
        return "INSUFFICIENT", None
    if m == "no" and h == "no":
        return "NO-EFFECT", None
    if m == "yes" and d == "opposite":
        return "DIFFERENT", None
    if h == "yes" and m == "no":
        return "SUPER-NORMATIVE", None
    if m == "yes" and h == "no":
        return "UNCLASSIFIED-MODEL-ONLY", None
    if d != "same":
        return "INSUFFICIENT", None
    me, he = num(r.get("model_es")), num(r.get("human_es"))
    if r.get("es_metric") and me is not None and he not in (None, 0.0):
        ratio = abs(me / he)
        if ratio > 2:
            return "EXAGGERATED", ratio
        if ratio >= 0.5:
            return "HUMAN-LIKE", ratio
        return "ATTENUATED", ratio
    return "SAME-DIRECTION-UNQUANTIFIED", None


def rows_for(coder: str):
    for f in sorted((EXT / coder).glob("[0-9][0-9][0-9].json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if low(d.get("eligibility", {}).get("decision")) != "yes":
            continue
        fam_p = {p.get("pid"): p.get("family") for p in d.get("C", {}).get("paradigms", [])}
        fam_m = {m.get("name"): m.get("family") for m in d.get("B", {}).get("models", [])}
        types = [low(t) for t in d.get("D", {}).get("types", [])]
        has_h = any(t and t != "none" for t in types) or low(d.get("D", {}).get("primary_type")) not in ("", "none")
        for r in d.get("E", {}).get("effects", []):
            if "outcome_kind" not in r:
                continue
            lab, ratio = derive(r, has_h)
            pid = str(r.get("pid") or "")
            # composite rows ("P1+P2+P3": a result the authors pooled over paradigms) keep the joined families
            pfam = fam_p.get(pid) or "+".join(sorted({fam_p.get(p) or "?" for p in pid.split("+")}))
            yield dict(order=d.get("order") or int(f.stem), study_id=d.get("study_id"), pid=r.get("pid"),
                       paradigm_family=pfam, model=r.get("model"),
                       model_family=r.get("model_family") or fam_m.get(r.get("model")),
                       outcome_kind=low(r.get("outcome_kind")), model_effect_present=low(r.get("model_effect_present")),
                       human_effect_present=low(r.get("human_effect_present")), direction=low(r.get("direction")),
                       model_vs_human=low(r.get("model_vs_human")), es_metric=r.get("es_metric"),
                       ratio=None if ratio is None else round(ratio, 3), derived_label=lab,
                       coder_label=str(r.get("label") or "").upper(), match=lab == str(r.get("label") or "").upper())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", default="both", choices=["claude", "codex", "both"])
    ap.add_argument("--out", default="runs/extraction-labels")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for coder in (["claude", "codex"] if a.coder == "both" else [a.coder]):
        rows = list(rows_for(coder))
        if not rows:
            continue
        with (out / f"{coder}-effects.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        summary[coder] = {"rows": len(rows), "records": len({r["order"] for r in rows}),
                          "derived": dict(Counter(r["derived_label"] for r in rows)),
                          "derived_equals_coder_label": sum(r["match"] for r in rows)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
