"""Split records into screening batches and merge classifier outputs (protocol amendment v0.4).

    python -I analysis/screening/batches.py split --stage title --size 1500
    python -I analysis/screening/batches.py merge --stage title
    python -I analysis/screening/batches.py merge --stage abstract

split: writes `data/processed/screen/<stage>-batch-NN.tsv` (id <TAB> text) for the Claude classifier.
       Title stage: text = title. Abstract stage: text = title || abstract (first 1,500 characters).
merge: reads Claude labels `data/processed/screen/<stage>-batch-NN.claude.jsonl`
       ({"id","label","code"} per line) and the local labels `<stage>.local.jsonl`, applies the
       stage rule, writes `<stage>-decisions.jsonl`, the next stage's input, and agreement counts.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCR = ROOT / "data/processed/screen"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def split(stage: str, size: int) -> None:
    src = ROOT / ("data/processed/records.jsonl" if stage == "title" else "data/processed/screen/stage2-input.jsonl")
    recs = load_jsonl(src)
    SCR.mkdir(parents=True, exist_ok=True)
    # Incremental: records already placed in an earlier batch are skipped, numbering continues,
    # so records added by a later download (or a resumed one) never get screened twice.
    old = sorted(SCR.glob(f"{stage}-batch-*.tsv"))
    seen = {l.split("\t", 1)[0] for f in old for l in f.read_text(encoding="utf-8").splitlines() if l}
    recs = [r for r in recs if r["id"] not in seen]
    first = len(old) + 1
    for k in range(0, len(recs), size):
        lines = []
        for r in recs[k:k + size]:
            text = (r.get("title") or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")
            if stage == "abstract":
                text += " || " + (r.get("abstract") or "")[:1500].replace("\t", " ").replace("\r", " ").replace("\n", " ")
            lines.append(f"{r['id']}\t{text}")
        (SCR / f"{stage}-batch-{first + k // size:02d}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(recs)} new records -> {-(-len(recs) // size)} new batches (from {first:02d}); {len(seen)} already batched")


def kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def merge(stage: str) -> None:
    claude = {r["id"]: r["label"] for f in sorted(SCR.glob(f"{stage}-batch-*.claude.jsonl")) for r in load_jsonl(f)}
    local = {r["id"]: r["label"] for r in load_jsonl(SCR / f"{stage}.local.jsonl")}
    src = ROOT / ("data/processed/records.jsonl" if stage == "title" else "data/processed/screen/stage2-input.jsonl")
    recs = {r["id"]: r for r in load_jsonl(src)}
    if stage == "title":
        # Amendment v0.6: the Claude title classifier returns only the IDs it does not exclude;
        # every other record is a Claude EXCLUDE. Batches it never returned would silently become
        # excludes, so every batch must have an output file.
        n_batches = len(list(SCR.glob("title-batch-*.tsv")))
        n_out = len(list(SCR.glob("title-batch-*.claude.jsonl")))
        if n_out != n_batches:
            raise SystemExit(f"Claude outputs for {n_out} of {n_batches} title batches; refusing to merge")
        # Coverage check: a screener that silently skipped part of its file would show 300-line
        # blocks with no kept record. Warn so those blocks can be re-screened.
        for f in sorted(SCR.glob("title-batch-*.tsv")):
            ids = [l.split("\t", 1)[0] for l in f.read_text(encoding="utf-8").splitlines() if l]
            kept = {r["id"] for r in load_jsonl(f.with_suffix(".claude.jsonl"))}
            empty = [b for b in range(0, len(ids), 300) if not kept & set(ids[b:b + 300])]
            if empty:
                print(f"WARNING {f.name}: no kept records in lines {[e + 1 for e in empty]} (+300); re-screen?")
        claude = {i: claude.get(i, "EXCLUDE") for i in recs}
    missing = [i for i in recs if i not in claude or i not in local]
    if missing:
        raise SystemExit(f"{len(missing)} records lack a label from one classifier, e.g. {missing[:3]}")
    dec, nxt = [], []
    for i, r in recs.items():
        a, b = claude[i], local[i]
        if stage == "title":
            keep = not (a == "EXCLUDE" and b == "EXCLUDE")
            d = "to_stage2" if keep else "excluded_title"
        else:
            d = ("excluded_abstract" if a == b == "EXCLUDE" else
                 "full_text" if a == b == "INCLUDE" else "full_text_disagreement")
            keep = d != "excluded_abstract"
        dec.append({"id": i, "claude": a, "local": b, "decision": d})
        if keep:
            nxt.append(r)
    (SCR / f"{stage}-decisions.jsonl").write_text("".join(json.dumps(x) + "\n" for x in dec), encoding="utf-8")
    nxt_file = SCR / ("stage2-input.jsonl" if stage == "title" else "fulltext-input.jsonl")
    nxt_file.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in nxt), encoding="utf-8")
    pairs = [(claude[i], local[i]) for i in recs]
    stats = {"stage": stage, "n": len(recs), "decisions": Counter(x["decision"] for x in dec),
             "claude": Counter(claude[i] for i in recs), "local": Counter(local[i] for i in recs),
             "kappa_3class": round(kappa(pairs), 3),
             "kappa_exclude_vs_not": round(kappa([(a == "EXCLUDE", b == "EXCLUDE") for a, b in pairs]), 3)}
    (SCR / f"{stage}-agreement.json").write_text(json.dumps(stats, indent=1, default=dict), encoding="utf-8")
    print(json.dumps(stats, default=dict))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split"); s.add_argument("--stage", required=True); s.add_argument("--size", type=int, default=1500)
    m = sub.add_parser("merge"); m.add_argument("--stage", required=True)
    a = ap.parse_args()
    split(a.stage, a.size) if a.cmd == "split" else merge(a.stage)


if __name__ == "__main__":
    main()
