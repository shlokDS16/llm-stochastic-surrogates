"""Write REPORT.md. Every number is read from scores.json (made by score.py)."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
S = json.loads((H / "scores.json").read_text(encoding="utf8"))
key = json.loads((H / "key.json").read_text(encoding="utf8"))
A = {r["id"]: r for r in map(json.loads, (H / "judge_A.jsonl").read_text(encoding="utf8").splitlines())}
ITEMS = list(S["judgeA"]["per_item"])
a, b, kp = S["judgeA"], S["judgeB"], S["kappa_paraphrase"]
npar, ndec = S["n_paraphrase"], S["n_decoy"]
low = []
for i, k in key.items():
    if k["kind"] == "paraphrase" and A[i]["confidence"] < 5:
        low.append(f'- {k["item"]} {k["wording"]} (Judge A, confidence {A[i]["confidence"]}): {A[i]["reason"]}')
low.sort()
rows = "\n".join(f'| {it} | {a["per_item"][it]["paraphrase_equivalent"]} / 9 | {b["per_item"][it]["paraphrase_equivalent"]} / 9 | '
                 f'{a["per_item"][it]["decoy_detected"]} / 2 | {b["per_item"][it]["decoy_detected"]} / 2 | {S["flagged_per_item"][it]} |' for it in ITEMS)
kap = "undefined (no variance: neither judge labelled any paraphrase NOT-EQUIVALENT)" if kp["kappa"] is None else f'{kp["kappa"]:.3f}'
nlowA, nlowB = len(S["low_confidence_paraphrases"]["A"]), len(S["low_confidence_paraphrases"]["B"])
dis = "; ".join(S["decoy_element_disagreements"])
per_item_flags = ", ".join(f"{k} {v}" for k, v in S["flagged_per_item"].items())
per_w_flags = ", ".join(f"{k} {v}" for k, v in S["flagged_by_wording"].items())
md = f"""# Meaning-equivalence check of the frozen ACME wordings: report

Protocol: `PROTOCOL.md` (written before judging). Item 11 of amendment X2 (`research/relaunch/EXPLORATORY-acme.md`); answers red-team
finding M1. All numbers below are read from `scores.json`, which `score.py` computes from `judge_A.jsonl`, `judge_B.jsonl` and
`key.json`. Run before any Arm L outcome was opened. The frozen wording files were not touched (manifest verify result in
`manifest_verify.txt`).

## Design

- {S["n_pairs"]} pairs: {npar} paraphrase pairs (W0 against W1 to W9, 10 items) and {ndec} decoy pairs (W0 against D1 and D2, positive controls).
- Blinded: neutral ids, shuffled, side of W0 randomised, no decoy notes shown. Judge A: Claude (claude-sonnet-5-5; the same model
  family that wrote the wordings). Judge B: Codex CLI, read-only sandbox, empty working directory, model logged as `{S["judgeB_model_logged"]}`
  (6 batches of at most 19 pairs; prompts and raw outputs in `codex/`).

## Results

| | Judge A | Judge B |
|---|---|---|
| Decoys labelled NOT-EQUIVALENT | {a["decoy_detected"]} / {ndec} | {b["decoy_detected"]} / {ndec} |
| Paraphrases labelled EQUIVALENT | {a["paraphrase_equivalent"]} / {npar} | {b["paraphrase_equivalent"]} / {npar} |
| Paraphrases labelled NOT-EQUIVALENT | {a["paraphrase_not_equivalent"]} | {b["paraphrase_not_equivalent"]} |
| Mean confidence (all {S["n_pairs"]} pairs) | {a["mean_confidence"]} | {b["mean_confidence"]} |

Per item (paraphrases EQUIVALENT of 9; decoys detected of 2; paraphrases flagged by either judge):

| Item | A para. equiv. | B para. equiv. | A decoys | B decoys | Flagged |
|---|---|---|---|---|---|
{rows}

- Agreement on the {kp["n"]} paraphrase pairs: {kp["percent_agreement"]*100:.1f} per cent; Cohen's kappa {kap}. Pairs where both said NOT-EQUIVALENT:
  {kp["both_ne"]}; only A: {kp["A_only_ne"]}; only B: {kp["B_only_ne"]}.
- Over all {S["kappa_all110"]["n"]} pairs (paraphrases and decoys together): agreement {S["kappa_all110"]["percent_agreement"]*100:.1f} per cent, kappa {S["kappa_all110"]["kappa"]:.3f}. This figure is driven by the
  decoy/paraphrase split and says nothing about borderline paraphrases.
- Decoys missed: Judge A {len(S["decoys_missed"]["A"])}, Judge B {len(S["decoys_missed"]["B"])}. The element named for a decoy agreed between the judges in
  {S["decoy_element_match_when_both_detect"]["same_element"]} of {S["decoy_element_match_when_both_detect"]["n_both_detect"]} decoys; the differences were: {dis}
  (manipulation versus scenario_fact is a labelling choice, not a disagreement about meaning).
- **Flags (FLAGGED if either judge says NOT-EQUIVALENT): {S["flagged_total"]} of {npar} paraphrases.** Per item: {per_item_flags}.
  Per wording W1 to W9: {per_w_flags}. Full table: `flags.csv`.

## What this does and does not show

- Both judges separated every decoy from the paraphrases, so neither simply approved everything; the check can detect a changed
  anchor, flipped direction, changed frame number, changed agent or country, changed question or an altered quote.
- No paraphrase was flagged by either judge. The conservative rule therefore removes no wording, and the wording-set sensitivity
  analysis of X2 item 11 (W1 to W9 without the verbatim W0, and without flagged paraphrases) coincides with the W1-W9 analysis on
  these flags. Kappa on paraphrases is undefined because the paraphrase column has no variance; the {kp["n"]} / {kp["n"]} agreement is a
  ceiling result, not a measured reliability.
- Decoys are blatant by construction (changed numerals, polarity, source or agent), so the detection rate shows sensitivity to
  gross meaning changes only. A shift in nuance that leaves task, options, anchor and facts intact (for example the connotation
  of 'recorded as', 'known to be', 'measured as', or an added actor) is outside what this protocol calls a difference. Judge A recorded
  such cases as lower-confidence EQUIVALENT labels ({nlowA} of {npar} paraphrases below confidence 5; Judge B: {nlowB}):

{chr(10).join(low)}

- Judge A shares a model family with the wordings' author, a stated limitation; Judge B (Codex) is independent of it. Both are
  language models; no human rating of equivalence was collected, and the manuscript must not claim one (GENERATOR-SPEC, Claim attached).
- Scope: the pairs show the condition texts, the reversed-scale and no-anchor versions, and the answer-format line. The order facets
  (sure-first or risky-first, Yes-first or No-first) and the system line are shared by all wordings and were not part of the wording
  comparison.

## Integrity

- Nothing under `runs/acme-L/`, `runs/acme-P1-queue/` or `runs/gpu.lock` was read; `armL_outcomes.py` and `gstudy.py` were not run; no GPU use.
- No file outside `runs/acme-equivalence/` was modified. `python analysis/acme/prompt_manifest.py` verify output after the check: see `manifest_verify.txt`.
- Reproduce: `build_pairs.py` (pairs, key), `run_codex.py` (Judge B), `score.py` (scores.json, flags.csv), `gen_report.py` (this file).
"""
(H / "REPORT.md").write_text(md, encoding="utf8")
print("REPORT.md written")
