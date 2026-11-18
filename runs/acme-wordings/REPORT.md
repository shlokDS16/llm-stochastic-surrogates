# ACME wording universe: report (P1 prep, CPU only)

Written by Claude Sonnet (claude-sonnet-5-5) blind to model output: no file under `runs/pilot*` or `runs/acme-*` model output was read. Frozen with SHA-256 in `analysis/acme/prompts/MANIFEST.json` (114 files), `python analysis/acme/prompt_manifest.py verify` returns OK.

## Files written

- `analysis/acme/prompts/GENERATOR-SPEC.md`, `common.yaml` (pilot content verbatim plus `yesno` and `yesno_no_first` under F0 and F1; the rating line is reused for reversed scales), `MANIFEST.json`
- `W4`-`W9` x 7 pilot items (42 files); `W0`-`W9` x AF, QA, NR (30 files); `overlay/W0..W3/` (P2a-d `baseline`, P3 `scale_reversed`: 20 files); `decoys/<item>_D1|D2.yaml` (20 files)
- `analysis/acme/check_wordings.py`, `analysis/acme/tests/test_check_wordings.py` (14 tests pass), `analysis/acme/wording_similarity.py`, `analysis/acme/prompt_manifest.py`
- `runs/acme-wordings/invariants.json`, `similarity.csv` (517 rows: item, wording, field, cosine), `similarity_summary.json`, this report
- Nothing committed. The builder script that emitted the YAML files is in the session scratchpad, not in the repo; the YAML files are the source of truth.

## Invariants (gate)

1616 rule evaluations, 0 failures; paraphrase files passing 69/69 (42 pilot-item W4-W9 plus 27 new-item W1-W9); overlay fields W0-W3 and the 20 decoys pass their checks. Three first drafts failed the number-word rule on the pronoun 'one' (P1 W9, QA W4, QA W6) and were rewritten (sentence regenerated, not patched) before freezing.

| item | files | rule evaluations | failures | paraphrases passing |
|---|---|---|---|---|
| P1 | 13 | 219 | 0 | 6/6 |
| P2a | 13 | 193 | 0 | 6/6 |
| P2b | 13 | 149 | 0 | 6/6 |
| P2c | 13 | 171 | 0 | 6/6 |
| P2d | 13 | 171 | 0 | 6/6 |
| P3 | 13 | 139 | 0 | 6/6 |
| P4 | 13 | 73 | 0 | 6/6 |
| AF | 13 | 145 | 0 | 9/9 |
| QA | 13 | 223 | 0 | 9/9 |
| NR | 13 | 133 | 0 | 9/9 |

Informational only (pilot's frozen W1, cannot be changed): P2a W1 x1 and x0 contain the number word 'two' ('the two cities') that W0 lacks. 2 flags, no gate effect.

## Similarity to W0 (bge-small-en-v1.5, CPU, pooled text of all fields)

| item | paraphrases W1-W9: min | median | max | decoys D1, D2: min | median | max |
|---|---|---|---|---|---|---|
| P1 | 0.946 | 0.974 | 0.990 | 0.988 | 0.994 | 0.999 |
| P2a | 0.921 | 0.953 | 0.986 | 0.989 | 0.993 | 0.998 |
| P2b | 0.915 | 0.948 | 0.985 | 0.993 | 0.995 | 0.996 |
| P2c | 0.929 | 0.968 | 0.992 | 0.986 | 0.991 | 0.996 |
| P2d | 0.946 | 0.973 | 0.991 | 0.989 | 0.994 | 0.999 |
| P3 | 0.930 | 0.968 | 0.989 | 0.972 | 0.986 | 1.000 |
| P4 | 0.933 | 0.962 | 0.989 | 0.981 | 0.988 | 0.996 |
| AF | 0.874 | 0.915 | 0.991 | 0.865 | 0.920 | 0.975 |
| QA | 0.944 | 0.960 | 0.978 | 0.851 | 0.896 | 0.942 |
| NR | 0.956 | 0.988 | 0.993 | 0.959 | 0.964 | 0.968 |

Reading: all paraphrases sit at 0.87-0.99. The decoys sit in the same range or higher (cosine 0.85-1.00) for most items: bge-small does not separate a changed numeral or a flipped direction from a paraphrase. The similarity decile rule (drop the lowest decile per item) therefore removes the most reworded wordings, not the least equivalent ones; this is a limit of the planned check, to be stated, not hidden. AF has the lowest paraphrase similarity (min 0.874, W5) because the sentence is short.

## Not done / caveats

- The model flag (bidirectional same-decision-problem scoring) of compute-plan 4.3 step 3 is not part of this task and was not run (needs a model, GPU in use).
- Pilot W1-W3 are frozen and unaudited by the new gate except the overlay fields; their similarity rows are included in `similarity.csv`.
- NR (response type yesno2) uses the same `yesno` / `yesno_no_first` format keys as AF; how the two questions are presented to the model in one prompt or two is for the runner to decide (x1 = `q_other` first, then `q_us`).
- QA keeps the ML1 orientation as forward (1 = strongly agree, 9 = strongly disagree) and lists point 5 ('neither agree nor disagree') as ML1 does; `condition_names` is not in the QA schema and was not added.
- Baselines name the unit (miles, feet) so baseline answers share the anchored answers' scale; this is a choice of this prep, flag it in the preregistration if it matters.
- Decoy D1/D2 for P1 changes the sure option to 300 saved / 300 die (a consistent frame pair) rather than only the gain line, so the decoy does not also break gain-loss equivalence.
