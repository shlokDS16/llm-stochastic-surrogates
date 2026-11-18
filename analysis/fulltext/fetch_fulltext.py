"""Fetch open full texts for the analysed full-text sample (amendment v0.9.1) and convert them to markdown.

    .venv/Scripts/python -I analysis/fulltext/fetch_fulltext.py [--max-order 150]

Reads `data/processed/fulltext-sample/sample.jsonl` (records with `analysed` true, in `order`). For each record it
collects candidate PDF URLs, in this order: OpenAlex best_oa_location and every location with a pdf_url; the arXiv
PDF when any location or the DOI points to arXiv; Semantic Scholar `openAccessPdf` and its arXiv id (by DOI). The
first URL that returns a real PDF (magic bytes %PDF) is kept. The PDF goes to `research/sources/pdfs/fulltext/` and
its markdown (markitdown CLI) to `research/sources/md/fulltext/`, both named `<order:03d>_<short id>`.
Writes `data/processed/fulltext/reading-list.jsonl` (one row per record, in order). Resumable: records whose PDF
and markdown already exist are not fetched again. Records without an open copy get status `no_open_copy` and are
candidates for the VIT eGateway list (research/USER-ACTIONS.md); a reader agent may still find a copy by search.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/search"))
from openalex_search import get, key  # noqa: E402

API = "https://api.openalex.org/works"
S2 = "https://api.semanticscholar.org/graph/v1/paper/DOI:{}?fields=openAccessPdf,externalIds"
SAMPLE = ROOT / "data/processed/fulltext-sample/sample.jsonl"
OUT = ROOT / "data/processed/fulltext/reading-list.jsonl"
PDFS = ROOT / "research/sources/pdfs/fulltext"
MDS = ROOT / "research/sources/md/fulltext"
MARKITDOWN = r"C:\Users\Shlok\AppData\Roaming\Python\Python314\Scripts\markitdown.exe"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-review-fetcher (academic, non-commercial)"}
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}|[a-z\-]+/[0-9]{7})", re.I)


OSF_RE = re.compile(r"10\.312(?:34|19|35)/osf\.io/([a-z0-9]+)", re.I)
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?{}"
ARXIV_API = "http://export.arxiv.org/api/query?{}"


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def europepmc(doi: str) -> list[str]:
    q = urllib.parse.urlencode({"query": f'DOI:"{doi}"', "format": "json", "resultType": "core"})
    try:
        with urllib.request.urlopen(urllib.request.Request(EPMC.format(q), headers=UA), timeout=30) as r:
            res = json.load(r)["resultList"]["result"]
    except Exception:  # noqa: BLE001 - best-effort fallback
        return []
    out = []
    for hit in res[:1]:
        if hit.get("pmcid"):
            out.append(f"jats:{hit['pmcid']}")
        for u in (hit.get("fullTextUrlList") or {}).get("fullTextUrl", []):
            if u.get("documentStyle") == "pdf" and u.get("availabilityCode") in ("OA", "F"):
                out.append(u["url"])
    return out


def arxiv_by_title(title: str) -> str | None:
    words = norm(title).split()[:12]
    if len(words) < 3:
        return None
    q = urllib.parse.urlencode({"search_query": "ti:" + " AND ti:".join(words), "max_results": "5"})
    try:
        with urllib.request.urlopen(urllib.request.Request(ARXIV_API.format(q), headers=UA), timeout=30) as r:
            feed = r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None
    finally:
        time.sleep(3)  # arXiv API etiquette
    for entry in feed.split("<entry>")[1:]:
        t = re.search(r"<title>(.*?)</title>", entry, re.S)
        i = re.search(r"<id>http://arxiv\.org/abs/([^<v]+)", entry)
        if t and i and norm(t.group(1)) == norm(title):  # exact normalised title match only
            return i.group(1)
    return None


def short(i: str) -> str:
    return i.rsplit("/", 1)[-1].replace(":", "_")


def openalex_meta(ids: list[str], k: str) -> dict:
    out = {}
    for b in range(0, len(ids), 50):
        chunk = ids[b:b + 50]
        params = {"filter": "openalex:" + "|".join(short(i) for i in chunk), "per-page": "50", "api_key": k,
                  "select": "id,doi,title,publication_year,primary_location,best_oa_location,locations,type"}
        for w in get(f"{API}?{urllib.parse.urlencode(params)}")["results"]:
            out[w["id"]] = w
    return out


def candidates(rec: dict, w: dict | None) -> tuple[list[str], str | None, str | None]:
    urls, arxiv, doi = [], None, None
    if rec["id"].startswith("arxiv:"):
        arxiv = rec["id"].split(":", 1)[1]
    if w:
        doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
        locs = [w.get("best_oa_location")] + list(w.get("locations") or [])
        for loc in locs:
            if not loc:
                continue
            if loc.get("pdf_url"):
                urls.append(loc["pdf_url"])
            for u in (loc.get("landing_page_url"), loc.get("pdf_url")):
                m = ARXIV_RE.search(u or "")
                if m and not arxiv:
                    arxiv = m.group(1)
        doi = doi or rec.get("doi")
        if doi and doi.lower().startswith("10.48550/arxiv."):
            arxiv = arxiv or doi.split("arxiv.", 1)[1]
    doi = doi or rec.get("doi")
    if doi and not arxiv:
        try:
            req = urllib.request.Request(S2.format(urllib.parse.quote(doi)), headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                s2 = json.load(r)
            arxiv = (s2.get("externalIds") or {}).get("ArXiv") or arxiv
            if (s2.get("openAccessPdf") or {}).get("url"):
                urls.append(s2["openAccessPdf"]["url"])
        except Exception:  # noqa: BLE001 - S2 is a best-effort fallback (rate limits, unknown DOIs)
            pass
        time.sleep(1.1)
    if doi:
        m = OSF_RE.match(doi)
        if m:  # PsyArXiv, OSF Preprints, SocArXiv: the OSF download endpoint serves the PDF
            urls.append(f"https://osf.io/{m.group(1)}/download")
        urls.extend(europepmc(doi))
    if not arxiv and not urls and rec.get("title"):
        arxiv = arxiv_by_title(rec["title"])
    if arxiv:
        urls.insert(0, f"https://arxiv.org/pdf/{arxiv}")
    seen, uniq = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq, arxiv, doi


def jats_to_md(pmcid: str, md: Path) -> bool:
    """Europe PMC JATS XML -> plain markdown (section titles as headings, paragraphs, table cells kept as text)."""
    u = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            x = r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return False
    x = re.sub(r"<title>(.*?)</title>", lambda m: "\n\n## " + m.group(1) + "\n\n", x, flags=re.S)
    x = re.sub(r"</(p|tr|caption|ref)>", "\n\n", x)
    x = re.sub(r"</t[dh]>", " | ", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = re.sub(r"\n{3,}", "\n\n", x)
    md.write_text(f"<!-- source: Europe PMC {pmcid} JATS XML -->\n" + x, encoding="utf-8")
    return md.stat().st_size > 2000


def download(url: str, dest: Path) -> bool:
    if url.startswith("jats:"):
        return False
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read(60_000_000)
    except Exception:  # noqa: BLE001 - any failure means try the next candidate
        return False
    if not data.startswith(b"%PDF"):
        return False
    dest.write_bytes(data)
    return True


def to_md(pdf: Path, md: Path) -> bool:
    with md.open("w", encoding="utf-8") as f:
        p = subprocess.run([MARKITDOWN, str(pdf)], stdout=f, stderr=subprocess.DEVNULL, timeout=300)
    return p.returncode == 0 and md.stat().st_size > 2000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-order", type=int, default=150)
    a = ap.parse_args()
    PDFS.mkdir(parents=True, exist_ok=True)
    MDS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    recs = sorted((json.loads(l) for l in SAMPLE.read_text(encoding="utf-8").splitlines() if l.strip()),
                  key=lambda r: r["order"])
    recs = [r for r in recs if r["analysed"] and r["order"] <= a.max_order]
    titles = {}
    with (ROOT / "data/processed/records.jsonl").open(encoding="utf-8") as f:
        want = {r["id"] for r in recs}
        for line in f:
            d = json.loads(line)
            if d["id"] in want:
                titles[d["id"]] = (d.get("title"), d.get("year"), d.get("venue"), d.get("doi"))
    meta = openalex_meta([r["id"] for r in recs if r["id"].startswith("https://openalex.org/")], key())
    prev = {}
    if OUT.exists():
        prev = {d["id"]: d for d in map(json.loads, OUT.read_text(encoding="utf-8").splitlines())}
    rows = []
    for r in recs:
        stem = f"{r['order']:03d}_{short(r['id'])}"
        pdf, md = PDFS / f"{stem}.pdf", MDS / f"{stem}.md"
        t, y, v, d0 = titles.get(r["id"], (None, None, None, None))
        if md.exists() and r["id"] in prev and prev[r["id"]]["status"] == "ok":
            rows.append(prev[r["id"]])
            continue
        urls, arxiv, doi = candidates({**r, "title": t, "doi": d0}, meta.get(r["id"]))
        doi = doi or d0
        got = next((u for u in urls if download(u, pdf)), None)
        ok_md = bool(got) and to_md(pdf, md)
        if not ok_md:
            jats = next((u for u in urls if u.startswith("jats:")), None)
            if jats and jats_to_md(jats[5:], md):
                got, ok_md = jats, True
        row = dict(order=r["order"], id=r["id"], stratum=r["stratum"], flag=r["flag"], title=t, year=y, venue=v,
                   doi=doi, arxiv=arxiv, candidates=urls, source_url=got,
                   status="ok" if ok_md else ("pdf_no_text" if got else "no_open_copy"),
                   pdf=str(pdf.relative_to(ROOT)) if pdf.exists() else None, md=str(md.relative_to(ROOT)) if ok_md else None,
                   md_chars=md.stat().st_size if ok_md else None)
        rows.append(row)
        print(f"{r['order']:3d} {row['status']:13s} {(t or '')[:70]}", flush=True)
        OUT.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
    OUT.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
    from collections import Counter
    print(Counter(x["status"] for x in rows))


if __name__ == "__main__":
    main()
