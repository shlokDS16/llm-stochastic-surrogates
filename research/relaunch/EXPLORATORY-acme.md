# Exploratory analyses for ACME (addendum to the frozen PREREG-acme.md; not confirmatory)

Written 2026-11-06 21:44 IST, after gate G1b passed (af3500d) and BEFORE any real Arm L outcome was computed: `armL_outcomes.py` and
`gstudy.py` have not been run on real data (only row counts and hashes of the run files were read; data/manifest.jsonl).
These analyses are labelled exploratory in the manuscript, carry no Holm adjustment and cannot change H1-H3 decisions.

1. H1 recomputed excluding near-deterministic cells (same estimator A1; same B and seed), to show whether saturation drives
   the temperature share.
2. Leave-one-item-out pooled shares (wording, temperature, model x wording), each with the A1 interval.
3. Per item and model: Wasserstein-1 distance between the model's exact answer distribution and the human response
   distribution of Many Labs 1, and the dispersion ratio (model SD / human SD) on the item's response scale.
4. Per item: rate of model-ranking reversals across wordings and Kendall tau between wording-specific model rankings.
5. Descriptive ladders: OLMo-2 1B SFT -> DPO -> instruct, and the Qwen2.5 size ladder (set-up SD and mean effect); no test.
6. Contamination check: per item, association between the effect and the lexical overlap (token-level Jaccard) of each
   wording with the original Many Labs 1 materials; descriptive.
Source of the list: research/relaunch/ACME-BLUEPRINT.md section 6 (domain survey section 5 referee demands).

## Amendment X1 (2026-11-06, after Codex round 2 of debate 2026-11-06-CRP-S08-acme-blueprint; still before any outcome is opened)
- Item 3 fixed in advance: the response categories are those of each item's frozen readout (the answer paths of A-L3; numeric
  items on the resolved digit-tree support binned to the integer grid used by the human data); human distribution = pooled Many
  Labs 1 responses on the same categories; human sampling uncertainty by a site-cluster bootstrap (B = 1000, seed 1) giving an
  interval for the human-vs-human reference distance (split by sites). Model-vs-human distances are reported descriptively beside
  that reference interval, without a test.
- Item 6 renamed "descriptive contamination proxy": token-level Jaccard overlap between each wording and the original Many Labs 1
  item text (lower-cased, whitespace tokens); reported as an association plot and Spearman rho without causal language.

## Amendment X2 (2026-11-06, after the red-team pass `research/relaunch/REDTEAM-blueprint.md`; still before any outcome is opened)
All items below are computed on the same Arm L arrays with estimator A1 and are labelled sensitivities, not tests; H1-H3 and their
Holm decisions stay as frozen. Reporting rule fixed now: if a sensitivity below disagrees with the frozen decision of H1 or H3 in
direction or in the side of zero its 95 % interval lies on, the paper reports the frozen decision and states in the same sentence
that it depends on the stated component definition or scale.
7. Symmetric component definitions for H1 and H3 (F2). Frozen H1 counts W + M×W as wording and every T-containing term as
   temperature (PREREG section 3). Two symmetric versions: (a) "pure" shares: wording = terms containing W and not T; temperature =
   terms containing T and not W; terms containing both are reported as a third block; (b) "inclusive" shares: wording = every term
   containing W, temperature = every term containing T (shared terms counted in both). Residual excluded throughout. One-order and
   two-order items are reported separately as well as pooled.
8. Scale (M3): H1 and H3 differences also on the logit scale for binary items (PREREG sensitivity S4) and with near-deterministic
   cells (max option probability > 0.99) excluded, for both H1 and H3 (extends item 1). Shown beside the frozen values in Table 8.
9. Unit of generalisation (M4): leave-one-effect-out pooled shares (the four anchoring items P2a-d removed together), in addition to
   leave-one-item-out (item 2).
10. Numeric readout (M2): for every numeric (model, item), resolved tree mass in the anchored and unanchored conditions side by side,
    and the frozen sensitivities S5 and y_lb shown in the main text for those items.
11. Wording set (M1): shares and set-up SD also for W1-W9 without W0 (the verbatim public ML1 text), and without paraphrases flagged
    as not meaning-equivalent by the equivalence check run before outcomes are opened (two independent judges outside the 14-model
    roster; protocol and flags written to `runs/acme-equivalence/` before `armL_outcomes.py` runs on real data).
12. Replication-style outcome (M11): per item and model, sign agreement of Δ with the pooled human effect, and the share of set-ups
    whose Δ lies inside the human 95 % interval.

## Provenance correction (2026-11-06, red-team m3)
The preamble says only row counts and hashes of the run files had been read. Exactly what was read from `runs/acme-L/` before
this addendum and its amendments: row counts, duplicate-key counts and SHA-256 of every finished file (data/manifest.jsonl);
`tree.n_exp` and `n_prompt_tokens` of the P2a and P2b rows of qwen2.5-0.5b-instruct and olmo2-1b-sft, for the run-time estimate
(research/relaunch/P1-ETA.md); and file sizes. No answer probability, path mass, tree value distribution, effect or summary_T1
field was read or computed.
