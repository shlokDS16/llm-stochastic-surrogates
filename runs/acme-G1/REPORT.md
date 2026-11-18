# Gate G1: recoverability of the ACME G-study estimator (2026-11-06)

Written by the G1/gstudy subagent (a64a310fdffb795ef, Sonnet). Saved here by the CRP-S08 P1 lead
because the subagent's Write was refused. Numbers come from runs/acme-G1/results*.csv and VERDICT.md.

## Short answer
1. The estimator exactly as preregistered FAILS G1: C1 (bias), C2 (coverage) and C3 (false
   positives) fail; C4 (ranking) passes. The pass rule was not changed.
2. Cause: truncation at 0 makes pooled shares of true-zero components positive, and the percentile
   bootstrap of the fixed-effect components (M, O, MO) is shifted up and too wide.
3. Amendment A1 (`gstudy.py --estimator A1`) passes all four criteria at 1000 replicates per
   scenario and B = 2000: untruncated shares, delete-one-wording jackknife bias correction,
   studentized bootstrap-t intervals.
4. A1 is not primary until approved. The subagent did not edit PREREG-acme.md.
5. Not simulated: type-I error and power of H1-H3. 20 unit tests pass.

## Files
- analysis/acme/gstudy.py: decompose, bootstrap, setup_sd, dstudy, dstudy_min_design, pool_items,
  hypotheses, iu_pvalue, holm_adjust, CLI.
- analysis/acme/tests/test_gstudy.py: 20 tests
  (`.venv/Scripts/python.exe -I -m pytest analysis/acme/tests/test_gstudy.py`).
- analysis/acme/simulate_G1.py: the G1 simulation (`--regen` rebuilds VERDICT.md from the CSVs).
- runs/acme-G1/: results.csv (preregistered estimator), results_<variant>.csv, VERDICT.md, run.json,
  run.log, exploration/ (earlier 300-500 replicate runs).

## What was run
- 9 scenarios x 1000 replicates, B = 2000 bootstrap draws per item (the preregistered B), seed
  20261106. Each replicate is a full set of 10 items (5 two-order, 5 one-order), 14 models x 10
  wordings. 2892 s on 6 CPU workers, no GPU.
- Scenarios: (a) residual only; (b) W 0.7, residual 0.3; (c) M x W 0.7, residual 0.3; (d) O 0.7,
  residual 0.3, two-order items only; (e) M, O, MO, W, MW, WO each drawn from 8-12 percent per item,
  residual the rest; (f) saturated binary items (latent logit effects with (e)'s shares, variance 2,
  mean 1, model offsets -6 to 6, Delta = exact probability difference, truth from 60,000 wordings);
  (g) = (e) with 13 models; (h25), (h50) = (f) with binomial draws at n = 25 or 50 per arm before
  differencing (truth = (f) plus mean binomial variance added to the residual).
- Pass rule, applied at the pooled level (mean over the 10 items, the quantity H1-H3 test), over 63
  scenario-components:
  - C1: |bias| <= 0.02 for every share.
  - C2: 95% interval coverage in [0.90, 0.98] for at least 90% of scenario-components, true-zero
    ones included.
  - C3: rate of "lower bound > 0" <= 0.05 for the 19 true-zero components.
  - C4: largest share ranked first in at least 90% of replicates where it is at least twice the
    next (scenarios b, c, d, e, g).
- Single-item levels are in the CSV and VERDICT.md as information only, not gated.

## Verdict (1000 replicates, B = 2000)
| variant | C1 bias | C2 coverage in range | C3 false positives | C4 ranking | overall |
|---|---|---|---|---|---|
| as_written (PREREG) | FAIL (4 cells; worst b/W -0.044) | FAIL (8/63) | FAIL (19/19 zero cells; M and MO rate 1.00) | PASS | FAIL |
| D0 untruncated | FAIL (b/W -0.034) | FAIL (16/63) | FAIL (11/19) | PASS | FAIL |
| D1 centred + jackknife | PASS | FAIL (33/63) | FAIL (max 0.058) | PASS | FAIL |
| D2 shrunk world, centred, rescaled | PASS | FAIL (49/63) | PASS (max 0.042) | PASS | FAIL |
| A1 | PASS (max abs bias 0.004) | PASS (62/63; range 0.926-0.989) | PASS (max 0.034) | PASS (1.000 in all five) | PASS |

## Diagnosis of the preregistered estimator
1. Truncation breaks pooled shares. An item's truncated zero component is positive about half the
   time, so the mean over 10 items is positive almost surely; for true-zero M and MO, "lower bound
   > 0" fires in 100% of replicates and coverage is 0. Truncated shares are biased: a/res -0.041,
   b/W -0.044, b/MW +0.022, c/MW -0.028.
2. Ratio bias: even untruncated, a dominant noisy component biases its own share (b/W -0.034). A
   delete-one-wording jackknife removes it (max abs bias 0.004).
3. The percentile bootstrap of a fixed-effect quadratic form is shifted and too wide: it plugs the
   noisy effect estimate in as truth (null item: M share shifts +0.047 against a true SD of 0.019);
   with 9 independent wording vectors against 28 effect dimensions, the wording-bootstrap SD of M
   is about 1.7 times the true SD (0.032 vs 0.019). True-zero fixed effects are over-covered
   (0.99-1.00) and random components slightly under-covered. Centring, shrinking and rescaling
   (D1, D2) fix the shift but not the over-dispersion.
4. Rejected alternatives (500 replicates, exploration/explore3, explore4): jackknife-SE Wald
   interval (C2 51/63); parametric bootstrap from the fitted mixed model (C2 40/63; coverage
   0.75-0.85 for M, MO, MW, res in the saturated scenarios f and h, because it assumes iid models).

## Amendment A1 (needs approval before it becomes primary)
Components, EMS formulas and component estimates unchanged. Three changes:
1. Shares = component / sum of untruncated components (the untruncated values were already reported).
2. Delete-one-wording jackknife bias correction of each item's shares:
   n*share - (n-1)*mean(leave-one-out shares). Pooled = mean over items.
3. Studentized bootstrap-t intervals and p-values: wordings are resampled in a world whose fixed
   effects (M, O, MO, T terms) are rescaled to the unbiased estimates, truncated at 0; every
   bootstrap sample gets an inner delete-one-wording jackknife SE;
   t* = (theta* - mean theta*)/SE*; interval = est - SE0*t*(0.975) to est - SE0*t*(0.025).
   H1 (one-sided) and H3 (two-sided) use the same pivot for their contrast. H2 unchanged.
- Single-item level (information only): coverage in range in 82 of 87 cells; the failures are all
  the O component of the second two-order item (0.99-1.00 when true O is zero in a, b, c; 0.82 and
  0.89 in f and h25).
- Cost: about 28 s for a full analysis on realistic-size synthetic data (14 models, 10 items, 4
  temperatures, B = 2000), against 5 s for the preregistered estimator.
- CLI check on the same synthetic data: prereg and A1 gave nearly identical hypothesis estimates;
  all raw p-values near 0.

## Interpretation choices to check
- Fixed terms use the prereg's n-1 convention (theta2 = sum of squared effects / df). The
  simulation draws fixed effects once per item and random effects afresh each replicate.
- For one-order items the highest interaction is M x W, labelled `MW` (no `res`); the pooled MW
  share mixes M x W from two-order items with M x W + residual from one-order items. Absent terms
  count as 0 in pooled means.
- H1: T share = every term containing T except the residual; wording share = W + MW only.
- H2: "95 percent lower bound" = 2.5% end of the 95% percentile interval; the one-sided 5% bound is
  also reported.
- Scenario (d) uses only the five two-order items.

## Caveats
- Type-I error and power of H1-H3 were not simulated.
- Data-generating process is normal with iid random effects, except (f) and (h).
- exploration/*/VERDICT.md and CSVs come from earlier code revisions with different variant names:
  `A1` in explore2-4 is today's D2; `A1a_centered` = D1; `S1_student` in explore5 = A1 at 300
  replicates and B = 1000 (passed, a/M false-positive rate exactly 0.050). Those older variants are
  not in the final code.
- Reproducibility: replicate r of scenario s uses default_rng([20261106, 7000+s, r]); a rerun
  reproduces results*.csv exactly (checked on a 20-replicate smoke run).

## Prereg text to change if A1 is approved
- Section 3: "Negative estimates are set to 0 for shares" -> untruncated shares plus jackknife bias
  correction; "percentile bootstrap" -> studentized bootstrap-t as above.
- Section 5: H1 and H3 p-values from the studentized pivot; H2 unchanged.
- Section 6: record G1 as passed under A1 with this report.
- Section 9: add hashes of gstudy.py and simulate_G1.py.

## CLI
`.venv/Scripts/python.exe -I analysis/acme/gstudy.py --effects effects.csv --scale scale.csv
--single-site-se se.csv [--exclude exclude.csv] --out OUTDIR [--estimator prereg|A1]
[--exploratory-models]` (default `prereg`). effects.csv columns model,item,W,O,variant,T,delta;
primary arrays use variant == "main" and T == 1.0; four-facet arrays use every T present.
scale.csv: item,sd. se.csv: item,se. Models with an incomplete array for an item are dropped and
logged in summary.json.
