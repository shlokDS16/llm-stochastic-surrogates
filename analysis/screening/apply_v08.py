"""Amendment v0.8: third rater (Qwen2.5-7B) on stage-2 disagreements; strict and liberal eligibility.

    .venv/Scripts/python -I analysis/screening/apply_v08.py

Reads abstract-decisions.jsonl (Claude, OLMo, v0.4 decision) and abstract.local-qwen.jsonl (Qwen labels on all
stage-2 records). Writes abstract-decisions-v08.jsonl with, per record: claude, olmo, qwen, the v0.4 decision and
  strict  : excluded_abstract (v0.4 double-exclude) | eligible | excluded_tiebreak
            eligible = v0.4 double-include, or (disagreement record with >= 2 of 3 raters non-EXCLUDE and >= 1 INCLUDE)
  liberal : same but eligible = >= 2 of 3 non-EXCLUDE (MAYBE counts)
and abstract-agreement-v08.json (counts under both rules, pairwise and Fleiss kappa over all stage-2 records).
"""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCR = ROOT / "data/processed/screen"
L = ["INCLUDE", "MAYBE", "EXCLUDE"]


def jl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss(rows):
    n, m = len(rows), 3
    p_j = Counter(x for r in rows for x in r)
    pe = sum((p_j[k] / (n * m)) ** 2 for k in L)
    pi = [(sum(c * c for c in Counter(r).values()) - m) / (m * (m - 1)) for r in rows]
    po = sum(pi) / n
    return (po - pe) / (1 - pe)


def main() -> None:
    dec = jl(SCR / "abstract-decisions.jsonl")
    qwen = {r["id"]: r["label"] for r in jl(SCR / "abstract.local-qwen.jsonl")}
    missing = [d["id"] for d in dec if d["id"] not in qwen]
    if missing:
        raise SystemExit(f"{len(missing)} stage-2 records lack a Qwen label (run the Qwen rater to completion)")
    out = []
    for d in dec:
        c, o, q = d["claude"], d["local"], qwen[d["id"]]
        votes = [c, o, q]
        non_ex = sum(v != "EXCLUDE" for v in votes)
        if d["decision"] == "excluded_abstract":
            strict = liberal = "excluded_abstract"
        elif d["decision"] == "full_text":
            strict = liberal = "eligible"
        else:
            strict = "eligible" if non_ex >= 2 and "INCLUDE" in votes else "excluded_tiebreak"
            liberal = "eligible" if non_ex >= 2 else "excluded_tiebreak"
        out.append(dict(id=d["id"], claude=c, olmo=o, qwen=q, decision_v04=d["decision"], strict=strict, liberal=liberal))
    (SCR / "abstract-decisions-v08.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out), encoding="utf-8")
    raters = {"claude": [x["claude"] for x in out], "olmo": [x["olmo"] for x in out], "qwen": [x["qwen"] for x in out]}
    stats = {
        "n": len(out),
        "strict": Counter(x["strict"] for x in out), "liberal": Counter(x["liberal"] for x in out),
        "qwen_labels": Counter(raters["qwen"]),
        "qwen_labels_on_disagreements": Counter(x["qwen"] for x in out if x["decision_v04"] == "full_text_disagreement"),
        "kappa_pairwise": {f"{a}-{b}": round(kappa(list(zip(raters[a], raters[b]))), 3) for a, b in combinations(raters, 2)},
        "fleiss_kappa_3class": round(fleiss([(x["claude"], x["olmo"], x["qwen"]) for x in out]), 3),
    }
    (SCR / "abstract-agreement-v08.json").write_text(json.dumps(stats, indent=1, default=dict), encoding="utf-8")
    print(json.dumps(stats, default=dict))


if __name__ == "__main__":
    main()
