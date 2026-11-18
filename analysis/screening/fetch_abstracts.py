"""Fetch OpenAlex abstracts for the stage-2 input (title-stage survivors).

    .venv/Scripts/python -I analysis/screening/fetch_abstracts.py [--input data/processed/screen/stage2-input.jsonl]

The S2 search used the light select (no abstracts), so stage 2 needs a second pass. One list call
per 100 OpenAlex IDs (`filter=openalex:W1|W2|...`), abstract rebuilt from `abstract_inverted_index`.
Results are cached in `data/processed/abstracts.jsonl` ({"id","abstract"}; abstract null when
OpenAlex has none), so the script is resumable and only fetches IDs not yet cached. arXiv records
already carry their abstract and are skipped. Finally writes the abstract into the input file
in place (records that already have one keep it).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/search"))
from openalex_search import get, key  # noqa: E402

API = "https://api.openalex.org/works"
CACHE = ROOT / "data/processed/abstracts.jsonl"


def rebuild(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/processed/screen/stage2-input.jsonl")
    a = ap.parse_args()
    inp = ROOT / a.input
    recs = [json.loads(l) for l in inp.read_text(encoding="utf-8").splitlines() if l.strip()]
    cache = {}
    if CACHE.exists():
        cache = {r["id"]: r["abstract"] for r in map(json.loads, CACHE.read_text(encoding="utf-8").splitlines()) if r}
    todo = [r["id"] for r in recs if r["id"].startswith("https://openalex.org/") and not r.get("abstract")
            and r["id"] not in cache]
    print(f"{len(recs)} records; {len(todo)} OpenAlex IDs to fetch; {len(cache)} cached")
    k = key()
    with CACHE.open("a", encoding="utf-8") as out:
        for b in range(0, len(todo), 100):
            ids = todo[b:b + 100]
            params = {"filter": "openalex:" + "|".join(i.rsplit("/", 1)[1] for i in ids),
                      "per-page": "100", "select": "id,abstract_inverted_index", "api_key": k}
            got = {w["id"]: rebuild(w.get("abstract_inverted_index"))
                   for w in get(f"{API}?{urllib.parse.urlencode(params)}")["results"]}
            for i in ids:  # IDs OpenAlex did not return (merged or deleted works) are cached as null
                cache[i] = got.get(i)
                out.write(json.dumps({"id": i, "abstract": cache[i]}, ensure_ascii=False) + "\n")
            out.flush()
            print(f"  {b + len(ids)}/{len(todo)}", flush=True)
    for r in recs:
        if not r.get("abstract") and cache.get(r["id"]):
            r["abstract"] = cache[r["id"]]
    inp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    n = sum(bool(r.get("abstract")) for r in recs)
    print(f"with abstract: {n}/{len(recs)} ({100 * n / len(recs):.1f} percent)")


if __name__ == "__main__":
    main()
