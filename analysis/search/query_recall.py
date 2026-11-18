"""Known-item recall and corpus size for candidate query versions, before any full download.

    python -I analysis/search/query_recall.py

For each query version and sub-query, one OpenAlex request with the search plus
`filter=doi:<known DOIs>` returns how many verified known items the query retrieves, and one
request without the DOI filter returns the corpus size. arXiv-only known items are matched through
their DataCite DOIs (10.48550/arXiv.<id>). Writes `research/protocol/query-recall.md`.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("oa", ROOT / "analysis/search/openalex_search.py")
oa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oa)

B_NARROW = [
    '"cognitive bias" OR "cognitive biases" OR "heuristics and biases" OR "decision heuristics" OR '
    '"theory of mind" OR "false belief" OR "false-belief" OR "anchoring effect" OR "anchoring bias" OR '
    '"framing effect" OR "framing effects"',
    '"judgment and decision making" OR "judgement and decision making" OR "decision bias" OR '
    '"decision biases" OR "human judgment" OR "risky choice" OR "risk preference" OR '
    '"conjunction fallacy" OR "base rate" OR "base-rate" OR "cognitive reflection"',
    oa.B_PARTS[2],  # Wason, syllogism, working memory, psycholinguistics, garden path, priming
    oa.B_PARTS[3],  # moral judgment, cognitive psychology/science, machine psychology, developmental
    oa.B_PARTS[4] + ' OR "moral dilemma" OR "moral dilemmas" OR "trolley problem" OR "sunk cost" OR '
    '"gambler\'s fallacy" OR "Many Labs" OR "replication of classic" OR "human-like reasoning"',
]
# v0.5b: phrases added after the first known-item check (Takemoto 2024, Cui 2025, Hong 2024 missed).
# This is the version adopted in openalex_search.py as B_PARTS_V05.
B_NARROW_B = oa.B_PARTS_V05


def known_dois(path: Path) -> list[str]:
    items = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for it in items:
        if it.get("status") != "verified":
            continue
        out.append(it["doi"].lower() if it["doi"] else f"10.48550/arxiv.{it['arxiv']}")
    return out


def count(q: str, k: str, doi_filter: str | None) -> int:
    url = oa.url_for(q, "*", k).replace("per-page=50", "per-page=1")
    if doi_filter:
        url = url.replace("filter=from_publication_date", f"filter=doi:{doi_filter},from_publication_date")
    return oa.get(url)["meta"]["count"]


def ids_retrieved(q: str, k: str, doi_filter: str) -> set[str]:
    url = oa.url_for(q, "*", k).replace("per-page=50", "per-page=100")
    url = url.replace("filter=from_publication_date", f"filter=doi:{doi_filter},from_publication_date")
    return {(w.get("doi") or "").lower().replace("https://doi.org/", "") for w in oa.get(url)["results"]}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="research/protocol/known-items-verified.json")
    ap.add_argument("--out", default="research/protocol/query-recall.md")
    a = ap.parse_args()
    k = oa.key()
    dois = known_dois(ROOT / a.items)
    dfilt = "|".join(dois)
    # How many known items OpenAlex indexes at all (denominator for recall).
    indexed = oa.get(oa.API + f"?filter=doi:{dfilt}&per-page=100&select=doi&api_key={k}")["results"]
    indexed_set = {(w.get("doi") or "").lower().replace("https://doi.org/", "") for w in indexed}
    versions = {
        "v0.3 A AND B (broad B)": [f"({oa.A}) AND ({b})" for b in oa.B_PARTS],
        "v0.1 A AND B AND C": [f"({oa.A}) AND ({b}) AND ({oa.C})" for b in oa.B_PARTS],
        "v0.5 A AND B-narrow": [f"({oa.A}) AND ({b})" for b in B_NARROW],
        "v0.5b A AND B-narrow plus added phrases": [f"({oa.A}) AND ({b})" for b in B_NARROW_B],
        "v0.6 A AND (broad B plus protocol families)": [f"({oa.A}) AND ({b})" for b in oa.B_PARTS_V06],
        "v0.7 v0.6 plus social/attention and human-likeness": [f"({oa.A}) AND ({b})" for b in oa.B_PARTS_V07],
    }
    lines = ["# Query versions: known-item recall and corpus size (OpenAlex, title and abstract)", "", f"Known-item file: `{a.items}`.", "",
             f"Known items verified: {len(dois)}; indexed in OpenAlex by DOI: {len(indexed_set)}.", "",
             "| Version | Corpus size (sum over sub-queries, before union) | Known items retrieved / indexed | Missed |",
             "|---|---|---|---|"]
    for name, qs in versions.items():
        size = sum(count(q, k, None) for q in qs)
        got: set[str] = set()
        for q in qs:
            got |= ids_retrieved(q, k, dfilt)
        missed = sorted(indexed_set - got)
        lines.append(f"| {name} | {size} | {len(got & indexed_set)} / {len(indexed_set)} | {', '.join(missed) or 'none'} |")
        print(lines[-1], flush=True)
    lines += ["", "Sub-query strings for v0.5b (B-narrow plus added phrases):", ""] + [
        f"- B{i}: `{b}`" for i, b in enumerate(B_NARROW_B, 1)]
    lines += ["", "Caveat: v0.5b phrases were added after seeing which known items v0.5 missed, so its "
              "known-item recall is an optimistic (in-sample) estimate; the human audit and citation "
              "chasing provide the out-of-sample check."]
    lines += ["", f"Not indexed in OpenAlex by DOI: {', '.join(sorted(set(dois) - indexed_set)) or 'none'}"]
    (ROOT / a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
