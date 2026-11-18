"""Fetch OpenAlex `referenced_works` for the OpenAlex records of the liberal frame (resumable cache).

    .venv/Scripts/python.exe -I analysis/rq1/fig4_fetch_refs.py [--limit N]

Batched list calls (`filter=openalex:W1|W2|...`, 50 IDs per call). Cache: data/processed/references/frame-refs.jsonl
({"id","referenced_works":[...],"returned":bool}); IDs OpenAlex does not return (merged or deleted) are cached
with returned=false. Only IDs not yet cached are fetched, so re-running resumes.
Second pass (same script, same cache style): data/processed/references/ref-meta.jsonl holds first author, year and
title for the references that the figure script needs to label (`--meta ID_FILE` is not used; the figure script calls
fetch_meta()).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/search"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from openalex_search import get, key  # noqa: E402
import rq1_common as C  # noqa: E402

API = "https://api.openalex.org/works"
REFS = ROOT / "data/processed/references/frame-refs.jsonl"
META = ROOT / "data/processed/references/ref-meta.jsonl"
BATCH = 50


def _cache(path: Path) -> dict:
    out = {}
    if path.exists():
        for l in path.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                out[r["id"]] = r
    return out


def fetch_refs(ids: list[str], limit: int | None = None, log=print) -> dict:
    REFS.parent.mkdir(parents=True, exist_ok=True)
    cache = _cache(REFS)
    todo = [i for i in ids if i not in cache]
    if limit:
        todo = todo[:limit]
    log(f"refs: {len(ids)} OpenAlex frame IDs; {len(cache)} cached; {len(todo)} to fetch")
    k = key()
    with REFS.open("a", encoding="utf-8") as out:
        for b in range(0, len(todo), BATCH):
            chunk = todo[b:b + BATCH]
            params = {"filter": "openalex:" + "|".join(i.rsplit("/", 1)[1] for i in chunk), "per-page": str(BATCH),
                      "select": "id,referenced_works", "api_key": k}
            got = {w["id"]: w.get("referenced_works") or [] for w in get(f"{API}?{urllib.parse.urlencode(params)}")["results"]}
            for i in chunk:
                row = {"id": i, "referenced_works": got.get(i, []), "returned": i in got}
                cache[i] = row
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            log(f"  refs {b + len(chunk)}/{len(todo)}")
    return cache


def fetch_meta(ids: list[str], log=print) -> dict:
    cache = _cache(META)
    todo = [i for i in ids if i not in cache]
    log(f"meta: {len(ids)} reference IDs; {len(cache)} cached; {len(todo)} to fetch")
    k = key()
    with META.open("a", encoding="utf-8") as out:
        for b in range(0, len(todo), BATCH):
            chunk = todo[b:b + BATCH]
            params = {"filter": "openalex:" + "|".join(i.rsplit("/", 1)[1] for i in chunk), "per-page": str(BATCH),
                      "select": "id,display_name,publication_year,authorships,cited_by_count,doi,locations", "api_key": k}
            got = {}
            for w in get(f"{API}?{urllib.parse.urlencode(params)}")["results"]:
                au = (w.get("authorships") or [])
                first = au[0]["author"]["display_name"] if au and au[0].get("author") else None
                urls = [(l.get("landing_page_url") or "") for l in (w.get("locations") or [])]
                arx = next((re.search(r"arxiv\.org/abs/([^\s?#]+)", u).group(1) for u in urls if "arxiv.org/abs/" in u), None)
                got[w["id"]] = {"id": w["id"], "first_author": first, "n_authors": len(au), "year": w.get("publication_year"),
                                "title": w.get("display_name"), "cited_by_count": w.get("cited_by_count"), "doi": w.get("doi"),
                                "arxiv_id": arx, "n_zenodo_loc": sum(("zenodo" in u.lower() or "10.5281" in u) for u in urls),
                                "n_dagstuhl_loc": sum(("dagstuhl" in u.lower() or "10.4230" in u) for u in urls), "returned": True}
            for i in chunk:
                row = got.get(i, {"id": i, "returned": False})
                cache[i] = row
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
    return cache


ARXIV = ROOT / "data/processed/references/arxiv-meta.jsonl"


def fetch_arxiv(arxiv_ids: list[str], log=print) -> dict:
    """First author, title and year of the first version from the arXiv abstract page's citation_* meta tags (the
    export API answered 429 here), cached; used only for OpenAlex records whose metadata shows the DOI-conflation
    signature (see fig4_cocitation.py). One page per ID, 2 s apart."""
    import html
    import time
    import urllib.request
    cache = _cache(ARXIV)
    todo = [i for i in arxiv_ids if i not in cache]
    log(f"arxiv: {len(arxiv_ids)} IDs; {len(cache)} cached; {len(todo)} to fetch")
    with ARXIV.open("a", encoding="utf-8") as out:
        for i in todo:
            req = urllib.request.Request(f"https://arxiv.org/abs/{i}", headers={"User-Agent": "crp-review-fig4"})
            with urllib.request.urlopen(req, timeout=60) as r:
                page = r.read().decode("utf-8", "replace")

            def tag(name):
                return [html.unescape(m) for m in re.findall(r'<meta name="%s" content="([^"]*)"' % name, page)]

            t, au, d = tag("citation_title"), tag("citation_author"), tag("citation_date")
            row = {"id": i, "first_author": (au[0].split(",")[1].strip() + " " + au[0].split(",")[0].strip()) if au and "," in au[0] else (au[0] if au else None),
                   "title": " ".join(t[0].split()) if t else None, "year": int(d[0][:4]) if d else None}
            cache[i] = row
            out.write(json.dumps(row, ensure_ascii=False) + chr(10))
            out.flush()
            time.sleep(2)
    return cache


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    rows, views, _ = C.load_frame(need_years=False)
    ids = [i for i in views["A"] if i.startswith("https://openalex.org/")]
    fetch_refs(ids, a.limit)


if __name__ == "__main__":
    main()
