# Stage 2 (title and abstract), classifier A (Claude Sonnet): summary (CRP-S02, 2026-10-16)

Scope so far: the 3,786 title-stage survivors of batches 01-18 (final title decisions, merged by CRP-S01).
The survivors of batches 19-55 get their own abstract batches (from 20) after the new title merge.

- Input: `data/processed/screen/stage2-input.jsonl`; abstracts added by
  `analysis/screening/fetch_abstracts.py` (OpenAlex, by ID; cache `data/processed/abstracts.jsonl`):
  3,299 of 3,786 records (87.1 percent) have an abstract; the rest are judged on the title.
- Batches: 19 x 200 (last 186), `abstract-batch-NN.tsv` (title || first 1,500 characters of abstract).
- Classifier: one Claude Sonnet agent per batch, frozen brief `claude-abstract-brief.md` + `criteria.md`,
  at most 6 at once, 50-line Read chunks, one output line per record with a reason code, no code run.
- Integrity: all 19 outputs present; every record labelled exactly once, in file order; labels and
  codes valid.
- Labels: INCLUDE 752, MAYBE 998, EXCLUDE 2,036.
  Codes: ok 1,402; no-abstract 348 (INCLUDE/MAYBE judged on title); EXCLUDE codes: other 945,
  benchmark-only 430, tool-use 301, no-new-data 259, not-llm 38, neural-only 32, questionnaire-only 31.
  "other" is used for 46 percent of excludes, so the code is a weak reason field; PRISMA exclusion
  reasons will come from the full-text stage, not from these codes.
- Known items among the 3,786: tuning 26 (Claude excluded 2: Kiciman et al. 2023, Feng et al. 2025,
  both coded benchmark-only), held-out 20 (excluded 1: Chen et al. 2025, benchmark-only), third set
  12 (excluded 0). Under the stage-2 rule a record is removed only if the local model also excludes
  it; whether these three survive is reported after the local abstract run.
- Cost: 19 Sonnet agent runs, about 3.7M tokens in total (agent usage reports, 186k to 208k each).

## Second wave (CRP-S02, 2026-10-16 afternoon): survivors of the full title merge
- Full title merge (all 79,009 records, local OLMo-2-7B labels for the 54,404 new ones): 6,209 to stage 2.
  Of the first 3,786, 3,483 are still in the record set; 303 were superseded by deduplication of the full
  download (their IDs no longer exist in `records.jsonl`; their Claude labels are ignored by the merge).
  2,726 new survivors went to batches 20-33 (14 x 200, last 126). Abstracts: 5,498 of 6,209 (88.5 percent).
- Labels for batches 20-33: INCLUDE 371, MAYBE 516, EXCLUDE 1,839 (2,726).
- Integrity: 13 of 14 batches clean. Batch 31: one abstract contained a carriage return, which made one
  line look like two; all 200 real records were labelled (the fragment is not a record); `batches.py` now
  strips carriage returns. Batch 32: one ID mistyped by the agent (W4389520959 for W4389520459, one digit);
  corrected after checking the position in the file (commit bf96157).
- Cost: 14 Sonnet agent runs at 3 at a time, about 2.8M tokens (agent usage reports, 159k to 217k each).

## Merged stage 2 (Claude Sonnet + local OLMo-2-1124-7B-Instruct 4-bit, argmax label, batch 8; CRP-S02 15:20)
- Local abstract run: 6,209 records, 42 minutes, peak VRAM 6.3 GiB; labels EXCLUDE 5,529, MAYBE 315, INCLUDE 365.
- Claude over the same 6,209: EXCLUDE 3,705, MAYBE 1,446, INCLUDE 1,058.
- Rule (amendment v0.4): excluded only if both exclude; both INCLUDE -> full text; everything else -> full text
  (disagreement). Result: excluded 3,418; full text 2,791 (both include 120; disagreement or maybe 2,671).
- Agreement: kappa 0.075 (3-class), 0.09 (exclude vs not). The two classifiers disagree far more at stage 2
  than at the title stage (0.153), mostly Claude INCLUDE/MAYBE against local EXCLUDE.
- Known items through both stages (records present): tuning 24/28 reach full text, held-out 19/21, third set
  18/18; overall 67 present, 61 retained (91 percent). Lost at the title stage: Yax et al. 2024, Park et al.
  2024, Barua et al. 2024; lost at stage 2 (both classifiers, Claude code benchmark-only): Kiciman et al. 2023,
  Feng et al. 2025, Chen et al. 2025. Recovery route: citation chasing; the loss is reported.
- Consequence: 2,791 full-text candidates is far above the AIR blueprint (~50 included studies) and above what
  paper-reader can read by Tuesday. The full-text plan needs a decision (see progress.md RESUME).
