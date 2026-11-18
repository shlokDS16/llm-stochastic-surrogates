"""Union raw search files, deduplicate, and check known-item recall (protocol sections 5 and 6).

    python -I analysis/search/build_records.py --run-id S1

Inputs: `data/raw/search/*-<run>.jsonl` (OpenAlex works; other sources normalised to the same keys).
Outputs:
  data/processed/records.jsonl          one deduplicated record per line
  research/protocol/prisma-counts.json  identified / duplicates removed / unique, per source
  research/protocol/known-item-recall.md
Deduplication order: DOI, then arXiv ID, then normalised title + publication year.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def norm_title(t: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = sorted((i, w) for w, idx in inv.items() for i in idx)
    return " ".join(w for _, w in pos)


def arxiv_of(w: dict) -> str:
    for loc in [w.get("primary_location") or {}] + (w.get("locations") or []):
        url = ((loc or {}).get("landing_page_url") or "") + " " + ((loc or {}).get("pdf_url") or "")
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", url)
        if m:
            return m.group(1)
    doi = (w.get("doi") or "").lower()
    m = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", doi)
    return m.group(1) if m else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    a = ap.parse_args()
    files = sorted((ROOT / "data/raw/search").glob(f"*-{a.run_id}*.jsonl"))
    if not files:
        raise SystemExit(f"no raw files for run {a.run_id}")
    by_key: dict[str, dict] = {}
    counts = {"identified": {}, "duplicates_removed": 0}
    for f in files:
        src = f.name.split("-")[0]
        n = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            w = json.loads(line)
            n += 1
            doi = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            ax = arxiv_of(w)
            tkey = f"{norm_title(w.get('title'))}|{w.get('publication_year')}"
            keys = [k for k in (f"doi:{doi}" if doi else "", f"arxiv:{ax}" if ax else "", f"t:{tkey}") if k]
            hit = next((by_key[k] for k in keys if k in by_key), None)
            if hit:
                counts["duplicates_removed"] += 1
                hit["sources"] = sorted(set(hit["sources"]) | {src})
                for k in keys:
                    by_key.setdefault(k, hit)
                continue
            rec = {"id": w.get("id"), "doi": doi, "arxiv": ax, "title": w.get("title"),
                   "year": w.get("publication_year"), "date": w.get("publication_date"),
                   "type": w.get("type"), "language": w.get("language"),
                   "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                   "abstract": abstract(w.get("abstract_inverted_index")) or w.get("_abstract", ""),
                   "cited_by": w.get("cited_by_count"), "query": w.get("_query"), "sources": [src]}
            for k in keys:
                by_key[k] = rec
        counts["identified"][f.stem] = n
    recs = list({id(r): r for r in by_key.values()}.values())
    counts["unique"] = len(recs)
    out = ROOT / "data/processed/records.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    (ROOT / "research/protocol/prisma-counts.json").write_text(json.dumps(counts, indent=1), encoding="utf-8")

    known = json.loads((ROOT / "research/protocol/known-items.json").read_text(encoding="utf-8"))
    titles = {norm_title(r["title"]) for r in recs}
    dois = {r["doi"] for r in recs if r["doi"]}
    axs = {r["arxiv"] for r in recs if r["arxiv"]}
    lines = ["# Known-item recall", "", f"Run {a.run_id}; {len(recs)} unique records.", "",
             "| Known item | Found by | Note |", "|---|---|---|"]
    found = 0
    for k in known:
        how = ("doi" if k["doi"] and k["doi"].lower() in dois else
               "arxiv" if k["arxiv"] and k["arxiv"] in axs else
               "title" if norm_title(k["title"]) in titles else "")
        found += bool(how)
        lines.append(f"| {k['first_author']} {k['year']}: {k['title'][:70]} | {how or 'MISSED'} | {k['family']} |")
    lines += ["", f"Recall: {found}/{len(known)} = {found / len(known):.2f} (target >= 0.90; borderline items included)."]
    (ROOT / "research/protocol/known-item-recall.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(counts), f"recall {found}/{len(known)}")


if __name__ == "__main__":
    main()
