"""arXiv API search for recent preprints (protocol section 4, source 2).

    python -I analysis/search/arxiv_search.py --run-id S1 --since 2026-06-01

Same blocks A AND B as the OpenAlex search, on title and abstract (`ti:` / `abs:` fields), restricted
to submissions since --since (OpenAlex indexing lag). Writes OpenAlex-shaped records to
`data/raw/search/arxiv-<run>.jsonl` and appends the query to `research/protocol/search-log.md`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NS = {"a": "http://www.w3.org/2005/Atom"}
A = ['"large language model"', '"language model"', 'LLM', 'GPT', 'ChatGPT', 'LLaMA', 'Claude', 'Gemini']
def _v05_terms() -> list[str]:
    """Block B terms of the current protocol (v0.7), taken from the OpenAlex script so both sources match."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("oa", ROOT / "analysis/search/openalex_search.py")
    oa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oa)
    terms: list[str] = []
    for part in oa.B_PARTS_V07:
        terms += [t.strip() for t in part.split(" OR ") if t.strip() not in terms]
    return terms


B = _v05_terms()


def block(terms: list[str]) -> str:
    return "(" + " OR ".join(f"abs:{t}" for t in terms) + ")"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--since", required=True, help="YYYY-MM-DD")
    a = ap.parse_args()
    since = dt.date.fromisoformat(a.since).strftime("%Y%m%d") + "0000"
    until = dt.date.today().strftime("%Y%m%d") + "2359"
    q = f"{block(A)} AND {block(B)} AND submittedDate:[{since} TO {until}]"
    out = ROOT / "data/raw/search" / f"arxiv-{a.run_id}.jsonl"
    n, start, total = 0, 0, None
    with out.open("w", encoding="utf-8") as fh:
        while total is None or start < total:
            url = ("http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
                {"search_query": q, "start": start, "max_results": 500,
                 "sortBy": "submittedDate", "sortOrder": "descending"}))
            for attempt in range(5):
                try:
                    with urllib.request.urlopen(url, timeout=90) as r:
                        root = ET.fromstring(r.read())
                    break
                except Exception:  # noqa: BLE001 - arXiv returns transient 5xx; back off and retry
                    time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit(f"arXiv API failed at start={start}")
            total = int(root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults").text)
            entries = root.findall("a:entry", NS)
            if not entries:
                break
            for e in entries:
                aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.rsplit("/abs/", 1)[-1])
                title = re.sub(r"\s+", " ", e.find("a:title", NS).text).strip()
                summ = re.sub(r"\s+", " ", e.find("a:summary", NS).text).strip()
                pub = e.find("a:published", NS).text[:10]
                rec = {"id": f"arxiv:{aid}", "doi": f"https://doi.org/10.48550/arxiv.{aid}", "title": title,
                       "publication_year": int(pub[:4]), "publication_date": pub, "type": "preprint",
                       "primary_location": {"landing_page_url": f"https://arxiv.org/abs/{aid}",
                                            "source": {"display_name": "arXiv"}},
                       "abstract_inverted_index": None, "_abstract": summ, "_query": "arxiv"}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
            start += len(entries)
            time.sleep(3)  # arXiv API etiquette: one request every 3 seconds
    with (ROOT / "research/protocol/search-log.md").open("a", encoding="utf-8") as fh:
        fh.write(f"\n## arXiv run {a.run_id} ({dt.datetime.now().isoformat(timespec='seconds')})\n"
                 f"Endpoint `export.arxiv.org/api/query`, abstract field, submitted {a.since} to today.\n\n"
                 f"Query: `{q}`\n\nTotal reported: {total}; fetched: {n}. Raw file: `{out.relative_to(ROOT).as_posix()}`.\n")
    print(f"arXiv: total={total} fetched={n}")


if __name__ == "__main__":
    main()
