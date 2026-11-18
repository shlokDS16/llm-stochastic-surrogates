# Errata and notes to the frozen PREREG-acme.md (append-only)

The frozen file (3fef16b, SHA-256 in PREREG-acme.sha256) is not edited. Corrections and notes are dated here. None changes a
decision rule, estimator, hypothesis or gate.

## E1 (2026-11-06, CRP-S08; from gate audit runs/gate-audits/P1-G0-G1-G2.md)
1. Section 0, bf16 ties: "2 to 22 of 64 prompts per model" should read "1 to 22" (Qwen2.5-14B has 1; smoke.json n_bf16_ties).
2. Sections 0 and 1 (A-L2), plain-digit grid mass: "0.001 to 0.004" holds only for some models. Across the 14 smoke.json
   files (grid_test.Z, one prompt, P2a W0 x = 1) it ranges from 1.2e-05 (Granite 3.3 2B) to 0.62 (Qwen2.5-14B): Qwen2.5-0.5B
   0.0010, Qwen2.5-1.5B 0.0041, Granite 8B 0.0017, OLMo-2 1B-13B 0.009-0.026, Qwen2.5-7B 0.60, Qwen2.5-14B 0.62. The reason for
   A-L2 stands (the grid captures little of the numeric mass for most models; the digit tree is exact for all), but the range as
   written overstated uniformity.
3. Section 1 (A-L2), calibration: the coverage thresholds of the high-coverage subset (0.95, 0.98, 0.99) were chosen after the
   errors were computed. All three results: >= 0.95, 40 effects, MAE 0.016 (max 0.092) vs y_lb 0.038; >= 0.98, 27 effects, 0.0008
   (max 0.0066) vs 0.011; >= 0.99, 21 effects, 0.0000 (max 0.0008) vs 0.0075 (`runs/acme-tree-calib/summary.json`). The decision
   itself used the rule fixed before the run (all 60 effects, MAE 0.029 <= 0.05 and below y_lb 0.114). The per-tree files
   `runs/acme-tree-calib/*.jsonl` (270 MB) are kept on disk but not in git.
4. Section 3, denominator check: the "24,000 random arrays, at least 0.93" figure had no saved artifact at freezing. The same
   generator is now saved as `analysis/acme/denominator_check.py`; its output `runs/acme-G1/denominator-check/result.json`
   (seed 1, 6 shapes x 4000 arrays) reproduces the pre-freeze minima: lowest ratio 0.938 (shape 13 x 9 x 2). The auditor's
   independent 4,500-array check gave a minimum of 0.946.
5. Gate G2 pass is a numerics and plumbing pass, not a readout-validity pass. Several models have P1 answer-path mass below 0.9
   on many prompts (OLMo-2 1B SFT 94%, Mistral 69%, OLMo-2 1B and DPO 25%); the valid-mass rule of section 7 will decide their
   inclusion per item, and gate G3 (at least 10 models and 8 items valid) is at risk. Pilot parity margins are one prompt for
   both Granite models (0.983).

## E2 (2026-11-06, CRP-S08; from gate audit runs/gate-audits/P1-G1b.md)
1. Gate G1b, H3 null: "residual 0.40" holds only for the two-order items. On the five one-order items MW is the residual, so the
   simulated null is M 0.40, W 0.30, MW 0.30 (the remaining 0.40 sits in the fixed M effect).
2. H2: 0 of 500 rejections shows that H2 does not over-reject; it is not evidence of nominal size. Item-level rejection 8/5000 =
   0.0016, the estimated median set-up SD is biased low (mean 0.1968 vs 0.2), and the at-least-5-of-10 rule is conservative. The H2
   p-value is not to be described as calibrated; H2 is a conservative test.
3. Provenance: `runs/acme-G1b/VERDICT.md` carries hand-written reading notes that the `aggregate` step does not generate. Two H3
   null replicates have p = 0.05 exactly; counting them as rejections gives 27/500 = 0.054, still below the 0.0695 limit.

## E3 (2026-11-06, CRP-S08): tree-expansion batch for OLMo-2 7B and 13B (engineering constant; no estimand, rule or threshold changed)
- Finding: `numtree.expand_trees` is called with its default forward batch of 32 (`run_armL.py`); with CHUNK = 16 prompts it sends up
  to 16 sequences per forward pass. Gate G2 set OLMo-2 7B and 13B to bs_f0 = 6 (13B: 12 ran out of memory), and G2 did not run a
  digit tree on any 7-14B model, so both jobs were at risk of failing out of memory twice and being skipped.
- Change: `run_armL.py` passes `batch=int(m.get("tree_bs", 32))`; `models.yaml` sets `tree_bs: 6` for olmo2-7b-instruct and
  olmo2-13b-instruct only. For every other model the call is identical to the frozen one (same default 32), so finished outputs are
  unchanged by construction. Expansion order is per tree (best-first, one node per tree per step), so batch size changes only which
  sequences share a forward pass, not which nodes are expanded. The two affected models had produced no output.
- New LF-normalised SHA-256: analysis/acme/run_armL.py 540b1b71191d8e4f8ed59aaf0ed5162bc462b4e95f1e5758f1b0f15391791e87; analysis/acme/models.yaml f12249638552675a633482b7f68ae962555b6ebab216d325fb81da26899f0398 (frozen values in PREREG section 9).

## E4 (2026-11-06, CRP-S08): schedule only
The GPU cut-off of 2026-11-07 18:00 IST is lifted (decision D0026) so that all 14 models and Arm S run; the readout, estimator,
hypotheses, gates and cut order are unchanged. Estimator amendment A-G1, frozen in this preregistration, is recorded as approved
by Shlok (decision D0027).

## E5 (2026-11-06, CRP-S08): scale of the between-site yardstick S^H in outcome P-c (ambiguity resolved before any model-human comparison)
- Gap: section 4 (P-c) compares the set-up SD (P-b, in ML1-SD units of Δ) with S^H "from runs/human-ml1/ and runs/human-ml1-acme/",
  but the primary rows of those runs are log odds ratios (P1, AF, NR) or Hedges g (the rest), which are not ML1-SD units of Δ
  (red team F3; Section 2 draft TODO). Section 3 defines Δ "on the item's raw scale ... also divided by the item's fixed ML1
  within-site SD on the same scale"; the yardstick must be on that scale.
- Rule: S^H for P-c = the between-site SD of site-level raw differences on Δ's scale (P1, AF, NR: risk difference of the 0/1 answer;
  P2a-d: difference of mean log x, column y_log; P4: difference of mean log(1 + x), column y_log; P3, QA: rating points, column y),
  estimated with the same estimator and interval as the human runs (`analysis/pilot/estimators.estimate2`, kind 'diff',
  var_method 'splithalf', K = 200, B = 2000, test-inversion bootstrap interval), divided by the item's sd_within
  (`runs/human-ml1-acme/arml_scales.csv`). Script `analysis/acme/human_SH_sdunits.py`, output `runs/human-ml1-acme/SH_sd_units.csv`.
  The log OR / Hedges g S^H rows are reported as the published-metric context only. Unchanged: ratio only where S^H > 0, boundary
  estimates never read as absence of between-site variation, single-site SE remains the primary yardstick (D0028).
- Computed on human data only; no model output is read.

## E6 (2026-11-07, CRP-S08; from the pre-results draft audit `research/relaunch/acme-draft-audit/REPORT.md`; before any outcome)
1. H2 decision rule in reporting. `gstudy.hypotheses` returns, besides the preregistered p-values, descriptive flags `holds` and
   `n_hold` that compare the two-sided 2.5 % bootstrap quantile with c_p (gstudy.py, H2 block). The H2 decision follows section 5
   only: item p_p = share of bootstrap s_p <= c_p, item passes when p_p < 0.05, H2 p = the ceil(k/2)-th smallest p_p (`iu_pvalue`),
   Holm over the three p-values (`p_raw`, `p_holm`). The flags are not used for any decision; if reported, they are labelled
   "two-sided 95 % lower bound above c_p (descriptive)".
2. Scale of the pooled human effect in outcome P-c (completes E5). The pooled human effect used as a yardstick is computed on Delta's
   scale for all ten items: random-effects (REML) mean of the site-level raw differences defined in E5, divided by the item's
   sd_within, with its 95 % interval (script `analysis/acme/human_SH_sdunits.py`, extended; human data only). The log OR / Hedges g
   REML estimates of the benchmark runs are reported as the metric of the benchmark's primary coding, and the published ML1
   statistics as a reproduction check (AF, QA, NR reproduced exactly; runs/human-ml1-acme/REPORT.md).
3. D-study target (secondary outcome). Section 4 names the D-study SE without a target. Curves are reported against two reference
   lines fixed now: 0.1 ML1-SD (gstudy.py `dstudy_min_design` default; compute-plan Fig C5) and the item's single-site SE c_p. Both
   are descriptive; no decision rests on them.
4. Clarification of E2.3: with the two H3 null replicates at p = 0.05 counted as rejections, the rejection rate is 27/500 = 0.054;
   its exact (Clopper-Pearson) upper 95 % bound exceeds 0.0695, so the G1b pass of H3 is a pass of the point rate at the
   preregistered limit, not a bound; the paper says so.

## Registration record (2026-11-07, CRP-S09; not an erratum, changes no rule)
The frozen plan is registered on OSF Registries: https://osf.io/t82jc (OSF Preregistration form; registered
2026-11-07 04:15:37 UTC, 10:00 NST, per the OSF API; embargoed, not public; decision D0032). Uploaded with it: PREREG-acme.md,
the frozen-file zip of commit 3fef16b, errata E1-E6 as they stood (identical to this file before this note), the exploratory
addendum (X1, X2), the README and both SHA-256 lists. At registration, Arm L outputs existed for 12 of the 14 models and had only
been hashed; no effect, variance component or human comparison had been computed from model output. Reviewer view-only link:
https://osf.io/t82jc/overview?view_only=946768b03d614878ad7df151d48e6a1d .

## E7 (2026-11-07 ~20:00 NST, CRP-S09; AFTER outcomes and gates, BEFORE any variance component or share is computed)
Post-outcome amendment. Status: G3 failed and G4 passed 5 of 14 models (D0034, audited 398b502). By the blueprint branch table the
benchmark is descriptive; PREREG section 6 routes G4-failing models to "Arm S only or excluded" without fixing an estimator. Arm S cell
effects were already seen inside G4 (`runs/acme-L/G4/cells.csv`), so everything below is post-outcome, exploratory and descriptive.
Basis: expert reports `research/relaunch/acme-gates/EXPERT-statistician.md`, `EXPERT-redteam.md`; Codex debate
`research/debates/2026-11-07-CRP-S09-acme-post-gate-analysis` (agreed).
1. Section 7 leads with the verification results: G3; G4 under its three readings (pre-outcome rule of 6cf3f5b; binary SE at sampled
   proportions; no valid-mass exclusion); valid mass lost to non-numeric first tokens; answer-path pass drift; Arm L vs Arm S agreement
   by response type; the multiplier bug of our own digit tree, with its effect on Arm L P2b per model.
2. Route table, fixed columns, equal billing, no column called primary; each column names its model population and the shares are not
   called a common estimand across columns:
   (a) Arm S "A1-S": frozen `gstudy.py` A1 imported unchanged, applied to the cell-mean array Delta-hat(m, w, o, T) = ybar1 - ybar0 in
       ML1-SD units, W0-W3 x order x T 0.7/1.0, 50 draws per condition; roster = pairs with >= 95% of cells at parse validity >= 0.9 and
       x1-x0 validity gap <= 0.1 in every cell (outcome-blind; rule of EXPERT-statistician.md section 1); residual split into draw noise
       mean(v_c), v_c = s1^2/n1 + s0^2/n0 (binary: at the sampled p, +0.5 continuity if p is 0 or 1), and the remainder (untruncated);
       shares E1 (without draw noise) and E2 (with draw noise as a component).
   (b) Arm L A1 on the per-type roster (`runs/acme-L/exclusions_per_type.csv`). (c) Arm L A1 on the 5 G4-passing models.
   (d) Arm L per-model roster (`exclusions_per_model.csv`): counts only, not decomposed.
   (e) Arm S A1-S and Arm L A1 on the intersection roster of (a) and (b), W0-W3 and T 0.7/1.0 cells in both: the only like-for-like
       comparison.
3. Uncertainty for (a) and (e)-Arm S: draw-level cell bootstrap (B = 2000, seed 20261106) labelled "draw uncertainty conditional on
   these four wordings", plus the four leave-one-wording-out (LOWO) estimates. Before any real component is computed, a synthetic check
   at the Arm S shape (14 models, 4 wordings, 2 orders, 2 temperatures, draw noise at n = 50 from the real v_c): pass = |bias| <= 0.02
   on every share and draw-bootstrap coverage 0.90-0.98. The check validates estimator behaviour under its simulated model only. If it
   fails, column (a) prints no intervals: point estimates and the LOWO range, the range labelled as fragility, not uncertainty.
   Arm L columns keep the frozen A1 inference, labelled underpowered.
4. Sensitivities, all reported, each tied to one question: loose roster 0.8/0.2 (does the validity rule drive (a)?); cells with
   validity >= 0.9 only (selection on valid answers); T = 1.0 only (temperature facet); logit scale for binary items (scale; S4 clip);
   drop W0 (original vs paraphrases); LOWO (four-wording fragility).
5. No p-values, no Holm family, no "supported" or "rejected" for H1-H3. Each is reported as an estimate with its interval (or LOWO
   range), roster, number of wordings and temperatures. "H1 analogue" (Arm S) = wording share minus the T 0.7-vs-1.0 share; it is
   not the preregistered H1, which needs four temperatures.
6. Human yardsticks (S^H, c_p, pooled human effect; ML1-SD units, canonical signs of `yardsticks.py`) are compared descriptively on
   (a) and (b), T = 1.0 cells; the Arm S set-up spread (4 wordings x 2 orders) is stated as a lower bound; not a validation claim.
7. No GPU re-run (no P2b multiplier-aware tree, no single-pass re-scoring): repairs would be selective. P2b is described from Arm S.
8. Adding E7 to the OSF record is an author step (Shlok); until then this file and its commit are the dated record.
Time correction to E7 (appended): the heading's "~20:00 NST" was an estimate; the dated record is the commit e8a543b,
2026-11-07 19:01:51 NST (see `git show -s e8a543b`). Ledger rows D0034 and D0035 carry estimated "ts" values; their commits (0aecb04,
e8a543b) give the true times.

## E7a (2026-11-07, CRP-S09; AFTER the A1-S synthetic check, BEFORE any real Arm S component or share is computed)
The synthetic check of E7 item 3 failed both criteria (`runs/acme-S-gstudy/synthetic/REPORT.md`, commit 514e242; gate-audit
`runs/gate-audits/A1S-SYNTH-AUDIT.md`). Applied as fixed, with three clarifications where E7 is silent. Codex debate
`research/debates/2026-11-07-CRP-S09-acme-synthetic-fail-handling` (agreed); decision D0036.
1. E7 item 3 verbatim: columns (a) and the Arm S half of (e) print point estimates and the four leave-one-wording-out (LOWO) estimates
   (min-max), labelled "fragility over the four wordings, not uncertainty". No interval of any kind (plain or corrected draw
   bootstrap) is computed or printed for real Arm S data. The corrected bootstrap's simulated coverage is reported as a property of
   the estimator under simulation.
2. Share set unchanged (E7 item 2): E1 and E2 both in the main table. Caveat from the check: E1 is heavy-tailed when draw noise is
   large and v_c uneven; each item's row carries its observed draw share.
3. Known bias: at four wordings A1 is biased by up to about 0.06 on a share (synthetic maximum 0.0565): remainder biased down, zero
   components up. In the four-wording arrays only (column (a), and both arms in column (e)), differences between shares or between
   columns smaller than 0.06 are not interpreted. Not carried over to the 10-wording Arm L columns (b), (c).
4. Section 7 reports the check's specification and results as a verification result.
5. Condition: column (e) requires W0-W3 prompt identity across arms (same manifest `analysis/acme/prompts/MANIFEST.json`); checked by
   the gate-auditor before (e) is reported.

## E7b (2026-11-07, CRP-S09; column (e) like-for-like fixes, after the first (e) run and before its values were interpreted)
Codex debate `research/debates/2026-11-07-CRP-S09-acme-synthetic-fail-handling` rounds 5-6; decision D0037. Disclosure: the lead had
seen one (e)-Arm L interval (AF M share) and the first rows of the (e)-Arm S component files when this was written.
1. (e)-Arm L P3 uses the forward order only, the prompts Arm S used (Arm S P3 has no order facet); reversed P3 stays in column (b).
   Prompt identity W0-W3 across arms: 40 item x wording groups, 0 mismatches (`runs/acme-gstudy/A1-route-e-armL/prompt_identity.csv`).
2. (e)-Arm L keeps the frozen A1 intervals as E7 fixes for Arm L columns, with the statement that the bootstrap-t was validated at 10
   wordings, not at 4, so they are not interpreted; it also carries the four LOWO values computed by the Arm S code path with draw
   noise 0 (`analysis/acme/route_e_armL_lowo.py`; reproduces frozen A1 shares to 1e-16), the same LOWO definition as (e)-Arm S.
   Codex did not accept suppressing these intervals without errata authority, so none is suppressed.
3. S-d reports the clip rate per item beside its shares (`runs/acme-S-gstudy/sens-S-d/summary.json`), no extra threshold.
