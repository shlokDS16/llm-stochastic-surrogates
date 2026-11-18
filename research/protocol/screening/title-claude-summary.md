# Title stage, classifier A (Claude Haiku): summary (2026-10-16)

- Records (partial S2 download, deduplicated): 26,047 in 18 batches (17 x 1,500 + 548).
- Kept (not excluded): 3,592 (13.8 percent): INCLUDE 539, MAYBE 3,053. Excluded by omission: 22,455.
- Integrity: every batch has an output file; all kept IDs exist in their batch; every 300-line block
  of every batch has at least one kept record (no sign of skipped reading).
- Known-item retention among records present: tuning set 25/27; held-out set 17/17; third set 10/10.
  Lost by Claude: Yax et al. 2024 ("Studying and improving reasoning in humans and machines") and
  Park et al. 2024 ("Diminished diversity-of-thought in a standard large language model"); both
  titles lack paradigm vocabulary. They stay in the review only if classifier B (local model) keeps
  them, which is what the double-exclude gate is for; this is reported either way.
- Cost: 18 Haiku agent runs, about 4.5M Haiku tokens in total (agent usage reports).

## Merged title stage (Claude Haiku + local OLMo-2-1124-7B-Instruct, 4-bit, argmax label as frozen)
- Local labels: EXCLUDE 25,322, MAYBE 722, INCLUDE 3 (97.8 minutes on the RTX 5070 Ti).
- Gate (removed only if both exclude): 3,786 to stage 2; 22,261 excluded at title stage.
  Kept by both 531; Claude only 3,061; local only 194.
- Agreement: kappa 0.179 (3-class), 0.209 (exclude vs not): the local model is much stricter.
- Known items passing the gate: 52/54. Both classifiers excluded Yax et al. 2024 and Park et al. 2024
  (titles without paradigm vocabulary); citation chasing is the planned recovery route, and the
  loss is reported.
- The lab engineer suggested thresholding p_include + p_maybe instead of argmax; not adopted,
  because the decision rule was frozen before the run.

## Batches 19 to 55 (CRP-S02, 2026-10-16; records added by the completed S2 download and arXiv)
- Records: 54,404 in 37 batches (36 x 1,500 + 404). Same frozen brief and criteria, one Claude Haiku
  agent per batch, at most 6 at once.
- Kept (not excluded): 2,555 (4.7 percent): INCLUDE 200, MAYBE 2,355. Excluded by omission: 51,849.
  Keep rate by batch 0.5 to 19.1 percent (later batches hold fewer language-model titles).
- Integrity: every batch has an output file; all kept IDs exist in their batch; labels valid; no
  duplicates. Seven 300-line blocks had no kept record (batch 28 block 601; batch 30 blocks 1, 301,
  901; batch 52 blocks 601, 901, 1201; batch 53 block 1). Each was spot-checked by grepping its
  titles for language-model terms: the hits were only tool-use or non-cognitive papers (chatbots in
  health, education, commerce; transformer architectures; scGPT), so no re-screening was needed. At
  keep rates near 1 percent an empty 300-line block is expected by chance, so this check is weak in
  the late batches and the spot-check is the real test.
- Known-item retention among records in the new batches: tuning set 1/1, held-out 0/0, third set 6/6.
- Cost: 37 Haiku agent runs, about 8.1M Haiku tokens in total (agent usage reports, 139k to 284k each).
- Agents' replies often said "1,501 records"; the files have 1,500 lines (the Read tool shows the
  empty line after the final newline). Two agents reported duplicate IDs that are not in the files.
