"""Recall of the final query (v0.7, run S2) on the held-out and third known-item sets, matched in the retrieved corpus by DOI,
arXiv identifier or title (first 60 normalised characters), as for the first set in research/protocol/known-item-recall.md.
Post-amendment, in-sample values.

    python analysis/search/known_item_recall_v07.py [--out runs/known-item-recall-v07]
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/known-item-recall-v07")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    recs = [json.loads(line) for line in open(ROOT / "data/processed/records.jsonl", encoding="utf-8")]
    dois = {(r.get("doi") or "").lower() for r in recs if r.get("doi")}
    arx = {(r.get("arxiv") or "").lower() for r in recs if r.get("arxiv")}
    titles = {norm(r.get("title"))[:60] for r in recs}
    res = {"corpus_records": len(recs)}
    lines = ["# Known-item recall of the final query (v0.7) on the held-out and third sets", "",
             f"Corpus: data/processed/records.jsonl ({len(recs)} records). Post-amendment, in-sample values.", ""]
    for name, f in (("holdout", "known-items-holdout-verified.json"), ("third", "known-items-third-verified.json")):
        items = json.loads((ROOT / "research/protocol" / f).read_text(encoding="utf-8"))
        found, missed = 0, []
        for it in items:
            d = (it.get("doi") or "").lower().replace("https://doi.org/", "")
            ax = (it.get("arxiv") or "").lower()
            t = norm(it.get("title"))[:60]
            how = "doi" if d and d in dois else "arxiv" if ax and ax in arx else "title" if t and t in titles else None
            if how:
                found += 1
            else:
                missed.append(it.get("title", ""))
        res[name] = {"verified": len(items), "found": found, "missed": missed}
        lines += [f"## {name}", f"Found {found} of {len(items)} verified items.", "Missed:"] + [f"- {m}" for m in missed] + [""]
    (out / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: (v if k == "corpus_records" else (v["found"], v["verified"])) for k, v in res.items()}))


if __name__ == "__main__":
    main()
