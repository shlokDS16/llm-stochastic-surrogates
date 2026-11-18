"""Unblind and score the meaning-equivalence check. Inputs: judge_A.jsonl, judge_B.jsonl, key.json. Outputs: scores.json, flags.csv."""
import csv, json
from collections import defaultdict
from pathlib import Path
H = Path(__file__).resolve().parent
def load(p): return {r["id"]: r for r in map(json.loads, (H / p).read_text(encoding="utf8").splitlines()) if r}
A, B, key = load("judge_A.jsonl"), load("judge_B.jsonl"), json.loads((H / "key.json").read_text(encoding="utf8"))
assert set(A) == set(B) == set(key), (len(A), len(B), len(key))
ITEMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR"]
ne = lambda J, i: J[i]["label"] == "NOT-EQUIVALENT"
def kappa(x, y):
    n = len(x); po = sum(a == b for a, b in zip(x, y)) / n
    pa, pb = sum(x) / n, sum(y) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe), po
par = [i for i in key if key[i]["kind"] == "paraphrase"]
dec = [i for i in key if key[i]["kind"] == "decoy"]
S = {"n_pairs": len(key), "n_paraphrase": len(par), "n_decoy": len(dec)}
for name, J in (("A", A), ("B", B)):
    S[f"judge{name}"] = {
        "decoy_detected": sum(ne(J, i) for i in dec),
        "paraphrase_equivalent": sum(not ne(J, i) for i in par),
        "paraphrase_not_equivalent": sum(ne(J, i) for i in par),
        "per_item": {it: {"decoy_detected": sum(ne(J, i) for i in dec if key[i]["item"] == it),
                          "paraphrase_equivalent": sum(not ne(J, i) for i in par if key[i]["item"] == it)} for it in ITEMS},
        "mean_confidence": round(sum(J[i]["confidence"] for i in J) / len(J), 2),
    }
# decoys missed
S["decoys_missed"] = {n: [f'{i}:{key[i]["item"]}_{key[i]["wording"]}' for i in dec if not ne(J, i)] for n, J in (("A", A), ("B", B))}
# agreement
xa, xb = [ne(A, i) for i in par], [ne(B, i) for i in par]
k, po = kappa(xa, xb)
S["kappa_paraphrase"] = {"kappa": k, "percent_agreement": po, "n": len(par), "both_ne": sum(a and b for a, b in zip(xa, xb)),
                          "A_only_ne": sum(a and not b for a, b in zip(xa, xb)), "B_only_ne": sum(b and not a for a, b in zip(xa, xb))}
allids = list(key)
k2, po2 = kappa([ne(A, i) for i in allids], [ne(B, i) for i in allids])
S["kappa_all110"] = {"kappa": k2, "percent_agreement": po2, "n": len(allids)}
# decoy-element agreement where both detect
S["decoy_element_match_when_both_detect"] = {"n_both_detect": sum(ne(A, i) and ne(B, i) for i in dec),
                                              "same_element": sum(ne(A, i) and ne(B, i) and A[i]["element"] == B[i]["element"] for i in dec)}
# flags
rows, flagged = [], defaultdict(int)
for it in ITEMS:
    for k_ in range(1, 10):
        w = f"W{k_}"
        i = next(i for i in par if key[i]["item"] == it and key[i]["wording"] == w)
        fa, fb = ne(A, i), ne(B, i)
        flag = fa or fb
        el = ";".join(f"{n}:{J[i]['element']}" for n, J in (("A", A), ("B", B)) if ne(J, i))
        rows.append([it, w, i, A[i]["label"], B[i]["label"], "FLAGGED" if flag else "ok", el,
                     A[i]["reason"] if fa else "", B[i]["reason"] if fb else ""])
        flagged[it] += flag
with open(H / "flags.csv", "w", newline="", encoding="utf8") as f:
    w_ = csv.writer(f); w_.writerow(["item", "wording", "pair_id", "judge_A", "judge_B", "flag", "element", "reason_A", "reason_B"]); w_.writerows(rows)
S["flagged_per_item"] = {it: flagged[it] for it in ITEMS}
S["flagged_total"] = sum(flagged.values())
S["flagged_by_wording"] = {f"W{k_}": sum(r[5] == "FLAGGED" for r in rows if r[1] == f"W{k_}") for k_ in range(1, 10)}
S["flagged_wordings_items"] = [f"{r[0]}_{r[1]}" for r in rows if r[5] == "FLAGGED"]
(H / "scores.json").write_text(json.dumps(S, indent=1), encoding="utf8")
print(json.dumps(S, indent=1))

# supplementary: low-confidence paraphrase labels and decoy element disagreements (appended after the main outputs)
S = json.loads((H / "scores.json").read_text(encoding="utf8"))
S["low_confidence_paraphrases"] = {n: sorted(f'{key[i]["item"]}_{key[i]["wording"]}:{J[i]["confidence"]}' for i in par if J[i]["confidence"] < 5)
                                   for n, J in (("A", A), ("B", B))}
S["decoy_element_disagreements"] = [f'{key[i]["item"]}_{key[i]["wording"]}: A={A[i]["element"]}, B={B[i]["element"]}' for i in dec if A[i]["element"] != B[i]["element"]]
S["elements_used_decoys"] = {n: dict(sorted(__import__("collections").Counter(J[i]["element"] for i in dec).items())) for n, J in (("A", A), ("B", B))}
S["judgeB_model_logged"] = next((l.split(":", 1)[1].strip() for l in (H / "codex/batch1.raw.log").read_text(encoding="utf8").splitlines() if l.startswith("model:")), None)
(H / "scores.json").write_text(json.dumps(S, indent=1), encoding="utf8")
