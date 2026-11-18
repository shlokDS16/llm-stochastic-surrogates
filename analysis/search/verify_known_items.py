"""Verify each known item's DOI (Crossref) or arXiv ID (arXiv API) and compare titles.

    python -I analysis/search/verify_known_items.py

Writes `research/protocol/known-items-verified.json` with status verified / title-mismatch /
not-found per item.
"""
from __future__ import annotations

import difflib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = {"User-Agent": "CRP-review/0.1 (mailto:shlok.goenka2023@vitstudent.ac.in)"}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def fetch(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001 - recorded as not-found with the reason
        return str(e).encode()


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="research/protocol/known-items.json")
    ap.add_argument("--out", default="research/protocol/known-items-verified.json")
    a = ap.parse_args()
    items = json.loads((ROOT / a.items).read_text(encoding="utf-8"))
    for it in items:
        if it["doi"]:
            raw = fetch(f"https://api.crossref.org/works/{urllib.parse.quote(it['doi'])}")
            try:
                msg = json.loads(raw)["message"]
                found = (msg.get("title") or [""])[0]
                it["registered_year"] = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            except Exception:  # noqa: BLE001
                found = ""
        else:
            raw = fetch(f"http://export.arxiv.org/api/query?id_list={it['arxiv']}")
            m = re.search(rb"<entry>.*?<title>(.*?)</title>", raw or b"", re.S)
            found = re.sub(r"\s+", " ", m.group(1).decode()) if m else ""
        ratio = difflib.SequenceMatcher(None, norm(found), norm(it["title"])).ratio() if found else 0
        it["found_title"] = found
        it["title_similarity"] = round(ratio, 3)
        it["status"] = "verified" if ratio >= 0.85 else ("title-mismatch" if found else "not-found")
        print(f"{it['status']:<15} {ratio:.2f}  {it['first_author']:<16} {it['doi'] or it['arxiv']}")
        time.sleep(1)
    (ROOT / a.out).write_text(
        json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
