"""Score the blind A1.10 check: reviewer verdicts vs the parser's value (key file). Writes blind_check.md and blind_check.json."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parent
j = {r["sid"]: r for r in map(json.loads, open(D / "unfinished_judgments.jsonl", encoding="utf8"))}
k = {r["sid"]: r for r in map(json.loads, open(D / "unfinished_sample_key.jsonl", encoding="utf8"))}
def same(a, b):
    try:
        return math.isclose(float(str(a).replace(",", "")), float(str(b).replace(",", "")), rel_tol=1e-9)
    except (TypeError, ValueError):
        return str(a).strip().upper() == str(b).strip().upper()
def wilson(x, n, z=1.959964):
    p = x / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)
n = len(j); comp = [s for s in j if j[s]["verdict"] == "COMPLETE"]
match = [s for s in comp if same(j[s]["answer"], k[s]["parsed"])]
lo, hi = wilson(len(comp), n); lo2, hi2 = wilson(len(match), len(comp))
res = dict(n=n, complete=len(comp), incomplete=sum(j[s]["verdict"] == "INCOMPLETE" for s in j), ambiguous=sum(j[s]["verdict"] == "AMBIGUOUS" for s in j),
           complete_share=len(comp) / n, complete_wilson=[lo, hi], parser_matches_complete=len(match), match_share=len(match) / len(comp), match_wilson=[lo2, hi2],
           mismatches=[dict(sid=s, reviewer=j[s]["answer"], parser=k[s]["parsed"], raw=k[s]["raw"][:80]) for s in comp if s not in match])
json.dump(res, open(D / "blind_check.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
open(D / "blind_check.md", "w", encoding="utf8").write(
    f"# A1.10 blind check (Claude Sonnet reviewer, condition-blind; sample of {n} parsed-but-unfinished F0 answers)\n\n"
    f"COMPLETE {res['complete']} ({100*res['complete_share']:.1f}%, Wilson {100*lo:.1f} to {100*hi:.1f}), INCOMPLETE {res['incomplete']}, AMBIGUOUS {res['ambiguous']}.\n"
    f"Parser value equals the reviewer's answer in {len(match)} of {len(comp)} COMPLETE answers ({100*res['match_share']:.1f}%, Wilson {100*lo2:.1f} to {100*hi2:.1f}).\n\n"
    + "\n".join(f"- {m['sid']}: reviewer {m['reviewer']} / parser {m['parser']} / {m['raw']!r}" for m in res["mismatches"]) + "\n")
print(open(D / "blind_check.md", encoding="utf8").read())
