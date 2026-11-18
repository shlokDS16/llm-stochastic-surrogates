"""PRISMA-S database search on OpenAlex for the review (protocol section 5).

    .venv/Scripts/python -I analysis/search/openalex_search.py --run-id S1 [--dry-run]

Reads OPENALEX_API_KEY from `.env` in the project root. Uses `search.title_and_abstract`
(stemmed, Boolean, quoted phrases; wildcards are not allowed in the stemmed form, so stems
replace the protocol's `*` terms). Cursor-pages every query, saves raw records to
`data/raw/search/openalex-<run>.jsonl`, and appends the exact query URLs and counts to
`research/protocol/search-log.md`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.openalex.org/works"
FROM_DATE = "2018-01-01"

A = ('"large language model" OR "language model" OR LLM OR GPT OR ChatGPT OR "GPT-4" OR LLaMA '
     'OR Llama OR Claude OR Gemini OR Mistral OR Qwen OR "foundation model"')
B_PARTS = [  # split so each request stays readable; results are unioned and deduplicated
    '"cognitive bias" OR heuristic OR "theory of mind" OR "false belief" OR anchoring OR framing',
    '"decision making" OR judgment OR judgement OR "conjunction fallacy" OR "base rate" OR "cognitive reflection"',
    'Wason OR syllogism OR syllogistic OR "working memory" OR psycholinguistic OR psycholinguistics OR "garden path" OR priming',
    '"moral judgment" OR "cognitive psychology" OR "cognitive science" OR "machine psychology" OR "developmental psychology"',
    '"analogical reasoning" OR "causal reasoning" OR "probabilistic reasoning"',
]
# Protocol v0.5 (amendment 2026-10-16): paradigm phrases replace the bare broad terms, chosen by
# known-item recall versus corpus size (research/protocol/query-recall.md).
B_PARTS_V05 = [
    '"cognitive bias" OR "cognitive biases" OR "heuristics and biases" OR "decision heuristics" OR '
    '"theory of mind" OR "false belief" OR "false-belief" OR "anchoring effect" OR "anchoring bias" OR '
    '"framing effect" OR "framing effects"',
    '"judgment and decision making" OR "judgement and decision making" OR "decision bias" OR '
    '"decision biases" OR "human judgment" OR "risky choice" OR "risk preference" OR '
    '"conjunction fallacy" OR "base rate" OR "base-rate" OR "cognitive reflection"',
    B_PARTS[2],
    B_PARTS[3],
    B_PARTS[4] + ' OR "moral dilemma" OR "moral dilemmas" OR "trolley problem" OR "sunk cost" OR '
    '"gambler\'s fallacy" OR "Many Labs" OR "replication of classic" OR "human-like reasoning" OR '
    '"moral machine" OR "psychology experiments" OR "psychological experiments" OR '
    '"experiments in psychology" OR "scenario-based experiments" OR "human subject studies" OR '
    '"behavioral experiments" OR "behavioural experiments" OR "script knowledge"',
]
# Protocol v0.6 (amendment 2026-10-16): the narrow v0.5 query overfit the first known-item set
# (held-out recall 11/19 versus 15/19 for the broad query), so the search returns to the broad
# block B and adds sub-queries for every paradigm family the protocol names, written from the
# protocol's family list (section 3, E2), not from individual missed items.
B_PARTS_V06 = B_PARTS + [
    B_PARTS_V05[4],  # moral dilemmas, sunk cost, gambler's fallacy, Many Labs, replication phrases
    '"prospect theory" OR "intertemporal choice" OR "probability weighting" OR "risk preferences" OR '
    '"risky decisions" OR "loss aversion" OR "expected utility" OR "economic games" OR "ultimatum game" OR '
    '"dictator game" OR "trust game" OR "public goods game" OR "prisoner\'s dilemma" OR "repeated games" OR '
    '"behavioral game theory" OR "behavioral economics" OR "behavioural economics"',
    '"human memory" OR "episodic memory" OR "false memory" OR "serial position" OR "primacy effect" OR '
    '"recency effect" OR "attention task" OR categorization OR categorisation OR "concept learning" OR '
    '"numerical cognition" OR "number sense" OR "Sally-Anne" OR ToM OR "developmental psychology" OR '
    '"child development" OR pragmatics OR implicature OR "metaphor comprehension" OR "humor comprehension"',
]
# Protocol v0.7 (amendment 2026-10-16): the untouched third validation set found 11/16 for v0.6;
# all five misses were social-psychology or attention paradigms that the protocol covers but
# block B never named. Two sub-queries are appended (B9, B10); B1 to B8 are unchanged.
B_PARTS_V07 = B_PARTS_V06 + [
    '"social psychology" OR conformity OR "social influence" OR "cognitive dissonance" OR '
    '"false consensus" OR "Stroop" OR "executive control" OR "executive function" OR "perspective-taking" OR '
    '"perspective taking" OR "mental rotation" OR "spatial reasoning" OR "consumer behavior" OR "consumer behaviour"',
    '"human-like" OR humanlike OR "like humans" OR "compared to humans" OR "compared with humans" OR '
    '"human participants" OR "human subjects" OR "how human"',
]
C = ('experiment OR paradigm OR participant OR "human-like" OR humanlike OR "human behavior" OR '
     '"human behaviour" OR "compared with humans" OR "compared to humans" OR "human baseline" OR '
     '"human data" OR replication OR replicate OR "psychological test"')
SELECT_LIGHT = "id,doi,title,publication_year,publication_date,type,language,primary_location"
SELECT = ("id,doi,title,publication_year,publication_date,type,language,primary_location,"
          "abstract_inverted_index,authorships,cited_by_count,referenced_works,ids,open_access")


def key() -> str:
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        if line.startswith("OPENALEX_API_KEY=") and line.split("=", 1)[1].strip():
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENALEX_API_KEY missing in .env")


def url_for(query: str, cursor: str, api_key: str | None, select: str = SELECT) -> str:
    params = {"search.title_and_abstract": query, "filter": f"from_publication_date:{FROM_DATE}",
              "per-page": "100" if select == SELECT_LIGHT else "50", "cursor": cursor, "select": select}
    if api_key:
        params["api_key"] = api_key
    return f"{API}?{urllib.parse.urlencode(params)}"


def _net_wait(attempt: int) -> bool:
    if attempt >= 37:
        return False
    time.sleep(60)
    return True


def get(url: str) -> dict:
    # 429 (rate) and 5xx (heavy Boolean searches time out at the gateway) are retried with backoff.
    for attempt in range(38):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < 7:
                time.sleep(min(60, 2 ** (attempt + 1)))
                continue
            raise
        except (urllib.error.URLError, http.client.IncompleteRead, ConnectionError, TimeoutError,
                json.JSONDecodeError):
            # Network outages (DNS failures, dropped Wi-Fi) can last minutes: keep waiting, up to
            # about 30 minutes in total, instead of the 8 attempts used for HTTP errors.
            if attempt < 7 or _net_wait(attempt):
                time.sleep(min(60, 2 ** (attempt + 1)))
                continue
            raise
    raise RuntimeError("unreachable")


def fetch_subquery(i: int, q: str, k: str, run: str, select: str, dry: bool) -> tuple[int, int]:
    """Cursor-page one sub-query into its own file; resumable through a state file."""
    out = ROOT / "data" / "raw" / "search" / f"openalex-{run}-B{i}.jsonl"
    state_f = out.with_suffix(".state.json")
    st = json.loads(state_f.read_text()) if state_f.exists() else {"cursor": "*", "n": 0, "total": None}
    if st["cursor"] is None:
        return st["total"], st["n"]
    with out.open("a", encoding="utf-8") as fh:
        while st["cursor"]:
            page = get(url_for(q, st["cursor"], k, select))
            st["total"] = page["meta"]["count"]
            for w in page["results"]:
                w["_query"] = f"B{i}"
                fh.write(json.dumps(w, ensure_ascii=False) + "\n")
            st["n"] += len(page["results"])
            st["cursor"] = None if dry else page["meta"].get("next_cursor")
            fh.flush()
            state_f.write_text(json.dumps(st))
            if st["n"] % 2000 < 50:
                print(f"B{i}: {st['n']}/{st['total']}", flush=True)
    return st["total"], st["n"]


def main() -> None:
    from concurrent.futures import ThreadPoolExecutor
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--version", choices=["v0.6", "v0.7"], default="v0.7")
    ap.add_argument("--light", action="store_true", help="light fields only (abstracts fetched later)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="first page only, print counts")
    a = ap.parse_args()
    k = key()
    parts = B_PARTS_V07 if a.version == "v0.7" else B_PARTS_V06
    queries = [(i, f"({A}) AND ({b})") for i, b in enumerate(parts, 1)]
    select = SELECT_LIGHT if a.light else SELECT
    (ROOT / "data" / "raw" / "search").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(lambda iq: fetch_subquery(iq[0], iq[1], k, a.run_id, select, a.dry_run), queries))
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    with (ROOT / "research" / "protocol" / "search-log.md").open("a", encoding="utf-8") as fh:
        fh.write(f"\n## OpenAlex run {a.run_id}, query {a.version} ({stamp}){' DRY RUN' if a.dry_run else ''}\n")
        fh.write(f"Endpoint `{API}`, parameter `search.title_and_abstract`, filter "
                 f"`from_publication_date:{FROM_DATE}`, cursor paging, per-page 50, fields "
                 f"{'light' if a.light else 'full'}.\n\n")
        fh.write("| Sub-query | OpenAlex count | Fetched | Query string |\n|---|---|---|---|\n")
        for (i, q), (total, n) in zip(queries, res):
            fh.write(f"| B{i} | {total} | {n} | `{q}` |\n")
        fh.write(f"\nRaw files: `data/raw/search/openalex-{a.run_id}-B<i>.jsonl` (union and deduplication in build_records.py).\n")
    for (i, _), (total, n) in zip(queries, res):
        print(f"B{i}: count={total} fetched={n}")


if __name__ == "__main__":
    main()
