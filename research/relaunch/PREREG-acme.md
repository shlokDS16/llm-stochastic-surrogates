# Preregistration: ACME benchmark (Option A, D0021), Arm L and Arm S

Status: FROZEN (CRP-S08, 2026-11-06). Becomes binding when the line "FROZEN" below carries a timestamp, the SHA-256 of this file
is in `research/relaunch/PREREG-acme.sha256` and both are committed (gate G0). No Arm L or Arm S data on the new design exist
before that commit. Design source: `research/relaunch/compute-plan.md` (sections 2-5, 7.2, amendment 12), contract
`research/relaunch/P1-CONTRACT.md`. Everything not restated here is as in the plan.

FROZEN: 2026-11-06 17:04 IST (11:34 UTC) (CRP-S08; Codex debate 2026-11-06-CRP-S08-acme-prereg, verdict agreed)

## 0. What was seen before freezing (transparency)
The G2 smoke test (`runs/acme-smoke/`, `analysis/acme/smoke.py`) read, for all 14 models, the first-token distribution and the
answer-path mass on the **pilot's** W0-W3 F0 prompts (frozen 2026-10-15), and compared it with the pilot's greedy answers. It
looked at readout validity and numerics only; it did not compute any effect, any variance component or any human comparison, and
it read none of the new wordings W4-W9, the new items AF, QA, NR or the decoys. Findings that shaped the amendments below:
bf16 ties in the output logits (2 to 22 of 64 prompts per model); first-token letter mass well below 0.9 on P1 for several models
because they begin with "Program" (answer-path mass 0.71 to 1.00); plain-digit grid mass 0.001 to 0.004 for numeric items;
verbal openings ("With", "I", "Def...") in the OLMo-2 1B SFT and DPO models; Phi-4-mini answering A/B to prompts whose options
are C/D; Mistral-7B emits a space token before digits and opens P1 answers with words ("Given", "This"). A plumbing test of
`run_armL.py` (Qwen2.5-0.5B, pilot items P1, P2a, P4, wordings W0-W1, pilot common file; `runs/acme-L-plumbing/`) checked that the
readouts run and measured digit-tree coverage; no effect was computed. The 0.9 valid-mass threshold of the plan is kept unchanged.
The digit-tree truncation calibration (`runs/acme-tree-calib/`; three small models, PILOT numeric prompts P2a-d and P4, W0-W3, F0)
computed pilot-prompt numeric effects internally; only their truncation errors (truncated minus reference) and coverage were
read, not the effects. Gate G1 (`runs/acme-G1/`) and the denominator check used synthetic arrays only. No new-wording, new-item or
decoy output of any model exists at freezing.

## 1. Amendments to the plan's Arm L readout (dated 2026-11-06, before freezing)
- **A-L1 fp32 output layer.** Logits are recomputed in float32 from the model's own bf16 final hidden state (forward hook on the
  output layer, `analysis/acme/scoring.py:fp32_head`). Reason: bf16 rounding of the logits (one step is 0.125 at |logit| 16-32)
  creates ties and caps the resolution of the exact probabilities. Model numerics are otherwise unchanged (bf16 / NF4).
- **A-L2 numeric items by digit tree.** P2a-d and P4 are read by best-first expansion of the model's number-token tree
  (`analysis/acme/numtree.py`): tokens that start a number open the tree, digit/','/'.' tokens extend it, any other token ends it,
  '3,000 miles' reads as 3000. Stopping: unresolved mass at most 1 percent of the numeric-start mass, or 1024 expansions, or best
  open node below 1e-5; children stored if within 12 nats of the node's best token and above 1e-7 absolute (the extension mass
  itself is exact, so what is not stored counts as unresolved). These thresholds are fixed engineering constants; unresolved mass
  is reported for every prompt. Outcome E[log x] (P2) and E[log(1 + x)] (P4) over the resolved numbers, renormalised. Valid mass =
  mass on a numeric answer (the 0.9 rule of section 7); coverage = resolved share of that mass, flagged below 0.5 (the plan's
  grid-mass flag carried over); sensitivity S5 drops cells with coverage below 0.9; y_lb values the unresolved open prefixes at
  their digits (a lower-bound imputation) and is reported beside the primary value. The plumbing test (Qwen2.5-0.5B, pilot W0-W1)
  resolved 0.58-0.68 of P2a and 0.99 of P4 at 256 expansions; hence the cap of 1024.
  **Estimand and calibration (2026-11-06, Codex debate rounds 2-4).** The numeric primary is the mean of log x (P4: log(1 + x))
  over the resolved numeric mass at the frozen cap, i.e. conditional on resolution; it is not claimed to equal the full-tree
  mean. Calibration on the PILOT numeric prompts only (`analysis/acme/tree_truncation.py`; P2a-d, P4; W0-W3; F0; Qwen2.5-0.5B,
  OLMo-2 1B instruct, Granite 3.3 2B; reference = the same tree at 4096 expansions; `runs/acme-tree-calib/summary.json`; rule
  fixed in the script before the run): mean absolute truncation error of the effect at 1024 = 0.029 log units for resolved-only
  and 0.114 for y_lb (n = 60; max 0.265, OLMo-1B P2b); by the rule resolved-only stays primary. On the 27 effects whose reference
  resolves at least 0.98 of the numeric mass, the error at 1024 is 0.0008 (max 0.0066) against 0.011 for y_lb. The reference is
  itself truncated (minimum reference coverage 0.83), so these are lower bounds on the error against the full tree; S5 and y_lb are
  reported as labelled sensitivities and coverage is reported per cell. Replaces the 15-value grid (smoke grid mass 0.001-0.004). `analysis/acme/grids.yaml` is kept only for
  figure axes.
- **A-L3 answer paths for options.** Choice and yes/no items are read as prefix probabilities of answer paths: the bare label
  with and without a leading space (case variants for words) and, for P1, '<noun> <label>' with the noun the prompt puts before
  the label ('Program A'). Exact rule (`scoring.choice_variants`): the inventory is generated from the option labels shown in
  that prompt (P1 letters, Yes/No); each candidate text is tokenised as a continuation of the rendered prompt; identical token
  sequences are kept once; a path whose token sequence extends another kept path is dropped, because the shorter path's prefix
  probability already contains it. Kept paths are therefore disjoint events and each option's probability is the sum of its
  paths' prefix probabilities. Paths of different options never share a full token sequence (they differ at the label token). Ratings: answer
  paths '1' to '9' with and without a leading space (for SentencePiece models the digit follows a space token); the first-token
  digit logits are stored as well (diagnostic).
- **A-L4 Mistral system turn.** Mistral-7B-Instruct-v0.3's own chat template has no system role; it writes the system text
  before the last user message inside `[INST] ... [/INST]`. That template is used unchanged (`runs/acme-smoke/templates.md`).
- **A-L6 memory for the 13-14B models.** Qwen2.5-14B and OLMo-2 13B keep their bf16 input-embedding table on CPU (an exact
  row lookup; `scoring.load`, `embed_cpu`) and run at batch sizes 16/4 and 6/2 (F0/F1); the plan's sizes ran out of memory in G2.
- **A-L5 generation settings for Arm S and the smoke test.** `repetition_penalty = 1.0`, `num_beams = 1`, overriding the
  1.05-1.1 in the Qwen2.5 generation configs, as in the pilot.

## 2. Fixed design
- Items (10): P1, P2a, P2b, P2c, P2d, P3, P4, AF, QA, NR; inclusion rule: every ML1 effect administrable as text without changing the
  manipulation (plan section 2). Canonical signs: `runs/human-ml1-acme/canonical_signs.csv` (hash in section 9).
  AF is coded as the anti-speech answer (Yes to forbid, No to allow), the allow/forbid asymmetry; ML1's published AF statistics
  compare raw Yes across the two questions (d 1.96) and are reproduced as a check only (`runs/human-ml1-acme/REPORT.md`).
  The human pooled AF effect on this coding is negative (canonical sign -1, verified in `canonical_signs.csv`: log OR -1.38).
  This is a new recoding, labelled as such. Mapping: forbid question (x1): Yes -> 1, No -> 0; allow question (x0): No -> 1,
  Yes -> 0 (the same mapping for humans, Arm L and Arm S).
- Models (14): `analysis/acme/models.yaml`, revisions in `runs/models/MODELS.jsonl`. Substitute order if a model fails G2 twice:
  Qwen3-8B, then Phi-4 (14B). (Mistral-7B, the plan's first substitute, is already row 14 by D0025.)
- Wordings W0-W9 per item, decoys D1, D2 at W0, P2 no-anchor baselines per wording: manifest `analysis/acme/prompts/MANIFEST.json`
  (hash in section 9) plus the pilot manifest `analysis/pilot/prompts/MANIFEST.json`.
- Orders: P1 sure/risky first; P3, QA scale forward/reversed; AF, NR Yes/No listing order; P2a-d, P4 one level.
- Temperatures (analytic, Arm L): 0.3, 0.7, 1.0, 1.5. Format F0 in Arm L.
- Arm S: plan section 4.4 (S1, S3, S2) with the pilot sampler (`run_pilot.py` GumbelSampler, recorded seeds).

## 3. Estimand and estimator (amendment 12 applied)
Arm L measures the model's choice preference under a stated prompt and scoring rule; it is neither the published human effect nor
the distribution of sampled answers. Model is a **fixed** facet (the 14-model set); wording is the random facet (the universe is the
output of the generator specification); order is a fixed design facet; temperature is a deterministic transform of the logits and
is reported as a sensitivity facet, never as decoding variance. Seed variance comes only from Arm S.

For item p, Δ[m, w, o] is the exact effect at T = 1 on the item's raw scale (risk difference; E[rating] difference; E[log]
difference), also divided by the item's fixed ML1 within-site SD on the same scale (ML1-SD units): median over the 36 sites of
the pooled within-site SD of y (log x for P2a-d, log(1 + x) for P4, the 1-9 rating for P3 and QA, the 0/1 answer for P1, AF,
NR); the single-site SE on that scale is the median over sites of sqrt(s1²/n1 + s0²/n0). Both are computed from
`data/processed/ml1/` by `analysis/acme/human_scales.py` (output `runs/human-ml1-acme/arml_scales.csv`) before any model-human comparison is opened. Models whose pair
(m, p) fails the valid-mass rule are excluded from the primary analysis of p, so each item's array is complete.

**Decomposition (`analysis/acme/gstudy.py`).** Two-way or three-way crossed ANOVA on the complete array with one value per cell
(no replication: in Arm L the highest interaction is the residual). Mixed-model expected mean squares, unrestricted, with W random
and M, O fixed (n_m models, n_w = 10, n_o orders):
- E[MS_res] = σ²_res; E[MS_MW] = σ²_res + n_o σ²_MW; E[MS_WO] = σ²_res + n_m σ²_WO; E[MS_W] = σ²_res + n_o σ²_MW + n_m σ²_WO + n_m n_o σ²_W;
- fixed-facet quadratic forms θ²_M = (MS_M − MS_MW)/(n_w n_o), θ²_O = (MS_O − MS_WO)/(n_m n_w), θ²_MO = (MS_MO − MS_res)/n_w.
For one-order items the O terms are dropped and the residual is the M×W interaction.
~~Negative estimates are set to 0 for shares (untruncated values reported). Share of a component = component / sum of truncated
components. Intervals: percentile bootstrap over wordings (resample the 10 wordings with replacement, B = 2000, seed 20261106),
models and orders held fixed.~~ (text before amendment A-G1; this estimator failed gate G1, `runs/acme-G1/REPORT.md`)

**Amendment A-G1 (dated 2026-11-06, before freezing; the G1 failure path of section 6; `gstudy.py --estimator A1`).** Component
estimates and EMS formulas above unchanged. (1) Share of a component = untruncated component / sum of untruncated components.
(2) Each item's shares are bias-corrected by the delete-one-wording jackknife: n_w·share − (n_w − 1)·mean of the n_w
leave-one-wording-out shares. (3) Intervals and p-values: studentized bootstrap-t over wordings (B = 2000, seed 20261106, models and
orders fixed). The bootstrap world keeps the estimated random-facet structure and rescales the fixed effects (M, O, M×O and the T
terms) to their unbiased quadratic-form estimates, truncated at 0; every bootstrap sample gets an inner delete-one-wording jackknife
SE; t* = (θ* − mean θ*)/SE*; interval = (est − SE₀·t*₀.₉₇₅, est − SE₀·t*₀.₀₂₅). Shares may be negative; a negative share is reported
as it is and read as "indistinguishable from 0". Denominator rule: the sum of untruncated components is a positive combination of
mean squares and equals 0 only for a constant array (in 24,000 random 2-4 facet arrays of the real shapes it was at least 0.93 of
the array variance); an item whose effect array has variance below 1e-8 (ML1-SD² units) has undefined shares, is left out of the
per-item and pooled shares and of H1/H3, and is listed (its set-up SD still enters H2); a leave-one-out or bootstrap array that is
constant gets shares 0 (`gstudy.py`, CONST_VAR). G1 under A-G1: C1-C4 all pass (1000 replicates per scenario, B = 2000;
`runs/acme-G1/VERDICT.md`). The estimator as first written is reported as a sensitivity (labelled).
Exploratory variant (labelled, bounded to the 14-model set): also resample models.
Pooling over items: (i) median over items of each share; (ii) mean over items, with the joint bootstrap (wordings resampled
independently within item).
Temperature sensitivity: the same decomposition on Δ[m, w, o, τ] with τ as a fourth, fixed facet (4 levels); the T share = θ²_T plus
all interactions with T.

## 4. Outcomes
Primary: (P-a) pooled shares (section 3); (P-b) per item and model, the set-up SD of Δ over (w, o) at T = 1 (finite SD, n−1), with
bootstrap interval; (P-c) (P-b) against three human yardsticks: S^H (between-site SD, `runs/human-ml1/` and `runs/human-ml1-acme/`),
the single-site SE at the median site size (`runs/human-ml1-acme/single_site_se.csv`), and the pooled human effect; reported as
difference and position relative to the human interval, ratio only where S^H > 0.
Secondary: item-level shares; D-study SE of a model's effect against number of wordings and orders; ladder contrasts (Qwen2.5
0.5-14B, OLMo 2 1-13B, OLMo 2 1B SFT/DPO/instruct; descriptive); L-S agreement; F1 vs F0 in Arm S; share of near-deterministic cells
(max option probability > 0.99) by model; decoy shift relative to the paraphrase spread; P2 no-anchor baseline position.

## 5. Confirmatory hypotheses (Holm over 3, α = 0.05; over fewer if a hypothesis fails gate G1b)
- **H1 (wording over temperature).** In the four-facet decomposition, pooled (mean over items) wording share (W + M×W) minus T share
  > 0; one-sided p from the studentized bootstrap pivot of that difference (amendment A-G1).
- **H2 (set-up spread above single-site noise).** For item p, s_p = median over the valid models of (P-b) in ML1-SD units; the
  bootstrap target is s_p itself (wordings resampled, s_p recomputed in every replicate); c_p = single-site SE in ML1-SD units
  (`arml_scales.csv`, fixed). Item test: p_p = share of bootstrap s_p <= c_p; item passes when p_p < 0.05, which is the same as the
  95 percent one-sided lower bound of s_p exceeding c_p. H2 holds if at least ⌈k/2⌉ of the k analysed items pass; its p-value is
  the ⌈k/2⌉-th smallest p_p (intersection-union test of exactly that rule).
- **H3 (not transferable).** Pooled M×W share minus W share ≠ 0; two-sided p from the studentized bootstrap pivot (A-G1).
  Pooled = mean over items (the median over items is reported, not tested). H2 is unchanged by A-G1 (percentile bootstrap of s_p).
Not hypotheses: scaling trends, ladders, families, single items.

## 6. Gates
- **G1 recoverability** (`analysis/acme/simulate_G1.py`, before any real data): synthetic arrays with the real shape (14 models; 5
  two-order and 5 one-order items; one model missing in one scenario) from known components: (a) residual only, (b) W dominant,
  (c) M×W dominant, (d) O dominant (two-order items), (e) all components 8-12 percent, (f) near-saturated binary items through a
  logistic link with model-specific offsets, (g) missing model, (h) Arm S layer (binomial noise n = 25 and 50). Pass, fixed now:
  |bias| of each share ≤ 0.02; coverage of the 95 percent interval between 0.90 and 0.98 in at least 90 percent of
  scenario-components; false-positive rate of "lower bound > 0" ≤ 0.05 for components that are zero; the largest component ranked
  first in at least 90 percent of replicates where it is at least twice the next. Failure: amend the estimator (dated), rerun.
  **Result (2026-11-06):** the estimator as first written failed C1-C3 (C4 passed); amendment A-G1 (section 3) passes C1-C4
  (C1 max |bias| 0.004; C2 62/63 in range, 0.926-0.989; C3 max 0.034; C4 1.000). Criteria applied at the pooled level (mean over
  items); 1000 replicates per scenario, B = 2000; `runs/acme-G1/REPORT.md`. Not simulated in G1: type-I error and power of H1-H3.
- **G1b hypothesis error rates** (fixed at freezing; run on synthetic data only, before any real Arm L outcome or effect is
  computed; extension of `simulate_G1.py`; estimator A-G1; real array shapes: 14 models, 10 wordings, 5 two-order and 5 one-order
  items, 4 temperatures for H1). Boundary nulls: H1, pooled wording share (W + M×W) = T share = 0.25 in every item; H3, M×W share
  = W share = 0.30, residual 0.40; H2, every item's true median set-up SD equal to its c_p (0.2 ML1-SD), the rest of the design as
  scenario (e). 500 replicates per null, B = 1000 (reduced from 2000 for cost; stated). Pass for a hypothesis: rejection rate at
  α = 0.05 ≤ 0.05 + 2·sqrt(0.05·0.95/500) = 0.0695. Power, information only (300 replicates): H1 wording 0.40 vs T 0.10; H3 M×W
  0.45 vs W 0.15; H2 true s_p = 2c_p. **Consequence fixed now:** a hypothesis that fails G1b is reported as exploratory and leaves
  the confirmatory family; Holm runs over the hypotheses that pass. G1b does not change the estimator.
- **G2 smoke**: plan 7.2, with (ii) evaluated on prompts that are not bf16 ties (top-2 gap above one bf16 step), all ties listed.
- **G3**: Arm L complete for at least 10 models and 8 of 10 items with valid readouts.
- **G4 L-S agreement** (amendment 12.4 and plan G4) is a diagnostic gate: it decides how a model is analysed, never enters
  H1-H3. On the Arm S prompts (W0-W3, F0, T 0.7 and 1.0): per (model, item, W, O, T) the
  Arm L effect against the Arm S sampled effect (parsed answers, canonical scale), pooled over models and items by response type:
  Arm L is exact, so its error variance is zero and the slope is the OLS slope of the Arm S effect on the Arm L effect (errors in
  the response only); criteria per response type (binary, rating, numeric) and per model: slope in [0.9, 1.1] and SD of the
  z-scores (difference / binomial or sample SE of the Arm S effect) at most 1.3; the pooled slope is reported but decides nothing. A model failing is analysed from Arm S only or excluded, with the reason stated.
- **G5** gate-auditor reconciliation before drafting is final.

## 7. Exclusion, sensitivity and stopping
- Valid-mass rule (primary): a model-item pair is excluded when valid mass < 0.9 on more than 5 percent of its prompts (T = 1).
  Sensitivity S1: threshold 0.5. S2: drop the lowest decile of bge similarity per item (limited: bge similarity does not separate
  the meaning-changing decoys from the paraphrases, `runs/acme-wordings/REPORT.md`; S2 therefore removes the most reworded
  paraphrases, not the least equivalent). S3 (model flag) is not run: it needs a model outside the roster and none is on disk.
  S4: logit scale for binary items (clip ±12, clip rate reported). S5: numeric cells with digit-tree coverage below 0.9 dropped;
  and y_lb in place of the primary numeric value.
- No data-dependent stopping. Compute stop: no new GPU job after 2026-11-07 18:00 IST. Cut order: plan 7.3.
- The estimator freeze (this file) precedes any comparison with human values.

## 8. Arm S
Plan 4.4 unchanged except: S3 includes P3/QA scale order only where Arm L has it; NR in Arm S is a two-turn conversation (the first
answer sampled, then the second question); parsers for Yes/No extend `analysis/pilot/parsers.py` without changing its existing rules.

## 9. Hashes (SHA-256 at freezing, of each file with line endings normalised to LF, i.e. the content git stores)
- `analysis/acme/prompts/MANIFEST.json`: 72b4045b3eb734a076050b196a22698d98eeb34f041174f798e5e6d9438791a2
- `runs/human-ml1-acme/canonical_signs.csv`: 4b645af41ee32475e723476482347ee63c63b001b29731dc5e1929d509312c80
- `runs/human-ml1-acme/arml_scales.csv`: 4e4c991082b41e16bd70f73be7daa2a25ae2087c0f7966f7ce99af9806aba4a9
- `analysis/acme/models.yaml`: 43bc44beba6e88fbb688e0077da0163bdc3ea425415558b1ddaf39621ef542b2
- `analysis/acme/scoring.py`: 8e6168d0f3616485d069faec235490d79440b1e7213a4df5dc4ac9e911804698
- `analysis/acme/numtree.py`: 88eefedf53640a3f196c416f8bc035073c6f6e6c361dabcda574fca4395feb6a
- `analysis/acme/armL_outcomes.py`: 9d3779d08c280703e9c5b65f8347588a034d02ac9c54e6d7947de25e41c3d721
- `analysis/acme/gstudy.py`: 25eb9ac0d1178ed9e04d9cc0656d9907681fb0465dffdca6aea0b99ef327146c
- `analysis/acme/simulate_G1.py`: 393842cb4fe3a2382455ef51b9f82bbb41ac9fa0e5b986251704431767666749
- `analysis/acme/prompts_acme.py`: e472dc93faf41b719f56e840bbfb6c95ba01936d9bf6f35b0b0bbf6b435f93fd
- `analysis/acme/run_armL.py`: ef2c285dace48e511ce2f09ede065a8fb1b4aff7486fd442c8614ab38de91903
- `analysis/acme/run_armS.py`: 80019d0246ea66c43793835dd060890874c1d9e49c8f38f5e81b94b9df6f54ee
- `analysis/acme/parsers_acme.py`: cc812e2355d108f67c36941a4e99db808c88a7da3f304e384e88a7b06e5453fe
- `analysis/acme/tree_truncation.py`: 3a8c0db7cb8770bd5b1673b3e3691ddf3a89c66736799e3258466b99dea3f4ae
- `analysis/acme/jobs_P1.txt`: df38e5ebcaf4ea6abb8e61e3ea40b61825c3e611c40fb4ac4d4daefd37d4cbb7
- G1b simulation code is written after freezing to the specification of section 6 and published with its gate report (`runs/acme-G1b/`), before any real outcome is computed.
