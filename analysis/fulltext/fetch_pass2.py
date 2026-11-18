"""Second fetch pass for analysed records left at `no_open_copy` by fetch_fulltext.py (open repositories it misses).

    .venv/Scripts/python -I analysis/fulltext/fetch_pass2.py

Zenodo (DOI 10.5281/zenodo.N: files from the records API), OSF Preprints / PsyArXiv (DOI 10.31234|10.31219|10.31235:
primary file from the OSF v2 API, long timeout), figshare (DOI 10.6084/m9.figshare.N: files from the figshare API),
and an arXiv retry when an arXiv id is known. Updates `data/processed/fulltext/reading-list.jsonl` in place
(status, source_url, md, md_chars; `pass` = 2) and writes the PDFs/markdown like the first pass.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_fulltext import MDS, OUT, PDFS, ROOT, UA, download, short, to_md  # noqa: E402

OSF_RE = re.compile(r"10\.312(?:34|19|35)/osf\.io/([a-z0-9_]+)", re.I)


def getjson(url: str, timeout: int = 90):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.load(r)
    except Exception:  # noqa: BLE001
        return None


def candidates(r: dict) -> list[str]:
    doi, out = (r.get("doi") or "").lower(), []
    m = re.match(r"10\.5281/zenodo\.(\d+)", doi)
    if m:
        rec = getjson(f"https://zenodo.org/api/records/{m.group(1)}")
        for f in (rec or {}).get("files", []):
            if f.get("key", "").lower().endswith(".pdf"):
                out.append(f["links"]["self"])
    m = OSF_RE.match(doi)
    if m:
        pid = m.group(1)
        pre = getjson(f"https://api.osf.io/v2/preprints/{pid}/?embed=primary_file", timeout=120)
        try:
            out.append(pre["data"]["embeds"]["primary_file"]["data"]["links"]["download"])
        except (TypeError, KeyError):
            out.append(f"https://osf.io/download/{pid.split('_')[0]}/")
    m = re.match(r"10\.6084/m9\.figshare\.(\d+)", doi)
    if m:
        rec = getjson(f"https://api.figshare.com/v2/articles/{m.group(1)}")
        out += [f["download_url"] for f in (rec or {}).get("files", []) if f.get("name", "").lower().endswith(".pdf")]
    if r.get("arxiv"):
        out.append(f"https://arxiv.org/pdf/{r['arxiv']}")
    return out


def main() -> None:
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        if r["status"] == "ok":
            continue
        stem = f"{r['order']:03d}_{short(r['id'])}"
        pdf, md = PDFS / f"{stem}.pdf", MDS / f"{stem}.md"
        urls = candidates(r)
        got = next((u for u in urls if download(u, pdf)), None)
        if got and to_md(pdf, md):
            r.update(status="ok", source_url=got, pdf=str(pdf.relative_to(ROOT)), md=str(md.relative_to(ROOT)),
                     md_chars=md.stat().st_size)
        r["pass"] = 2
        print(f"{r['order']:3d} {r['status']:13s} {len(urls)} candidates  {(r['title'] or '')[:60]}", flush=True)
        OUT.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
    from collections import Counter
    print(Counter(x["status"] for x in rows))


if __name__ == "__main__":
    main()
