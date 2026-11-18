# Pooled human effect on Delta's scale (erratum E6 item 2)

Script `analysis/acme/human_SH_sdunits.py` (function `pooled()`), human data only, no random numbers. Outputs: `pooled_sd_units.csv`/`.json` (pooled effects), `pooled_site_inputs.csv` (the 36 site-level yi, vi per item, as fed to the REML fit and to metafor), `pooled_check.txt` (metafor comparison). `SH_sd_units.csv` and `.json` were left untouched: re-running the extended script reproduces both byte-for-byte (diffed against copies made before the edit).

## Method
- Site effect: mean of the x1 cell minus mean of the x0 cell (same cells and columns as E5: P1, AF, NR 0/1 answer; P2a-d and P4 column `y_log`; P3, QA column `y`). 36 sites per item, every site has both arms.
- Sampling variance: s1^2/n1 + s0^2/n0 (sample variance, ddof 1) for the continuous items; p1(1-p1)/n1 + p0(1-p0)/n0 for P1, AF, NR. No site has vi = 0.
- Pooling: REML random-effects mean (tau^2 truncated at 0), own implementation (root of the REML score), interval Wald mu +- 1.96 se with se = 1/sqrt(sum 1/(vi + tau^2)); no Hartung-Knapp adjustment, so the intervals do not widen for the uncertainty in tau^2 (36 sites, small effect on the interval). Estimate, interval and tau-hat are divided by the item's `sd_within` (`arml_scales.csv`).
- Check against metafor 5.2.1 (R 4.5.2) `rma(yi, vi, method="REML")`: mu, se, tau^2 and both Wald limits agree to at most 6.2e-12 on all ten items when metafor's Fisher-scoring threshold is tightened to 1e-12 (default control: at most 4.4e-5, P1, whose tau^2 sits on the zero boundary; 1.5e-6 or less elsewhere, so the default metafor stopping rule (threshold 1e-5), not the estimate, is what exceeds 1e-6). See `pooled_check.txt`.

## Orientation (same as Delta = outcome(x1) - outcome(x0), canonical outcome of `armL_outcomes.py`)
The processed columns are already in canonical direction, so no recoding is applied in this script; `check_orientation` asserts that the sign of each pooled effect equals `canonical_signs.csv`, and, for AF, that column `y` equals `y_yes` at x1 and `1 - y_yes` at x0 (anti-speech answer). All ten checks passed.

| Item | Convention |
|---|---|
| P1 | risk difference of P(sure option), gain frame (x1) minus loss frame (x0); canonical sign +1 |
| P2a | difference of mean log x, high anchor (x1) minus low anchor (x0); +1 |
| P2b | difference of mean log x, high anchor minus low anchor; +1 |
| P2c | difference of mean log x, high anchor minus low anchor; +1 |
| P2d | difference of mean log x, high anchor minus low anchor; +1 |
| P3 | rating points, 9 = definitely go (not reversed), paid ticket (x1) minus free ticket (x0); +1 |
| P4 | difference of mean log(1 + x), three 6s (x1) minus one 3 and two 6s (x0); +1 |
| AF | risk difference of the anti-speech answer (Yes to forbid at x1, No to allow at x0; column y, not the raw-Yes column y_yes), forbid minus allow; canonical sign -1 (negative = forbid wording lowers the anti-speech share) |
| QA | rating points, 9 = strongly agree (y = 10 - raw ML1 value; raw 1 = strongly agree), Washington (x1) minus bin Laden (x0); +1 |
| NR | risk difference of Yes to the US question, other-country question first (x1) minus US question first (x0); +1 |

## Pooled effect (ML1-SD units of Delta)

| Item | pooled mu (95 % Wald) | tau-hat | pooled mu, raw scale | tau-hat raw | sd_within |
|---|---|---|---|---|---|
| P1 | 0.611 [0.562, 0.661] | 0.000 | 0.293 [0.269, 0.316] | 0.000 | 0.478 |
| P2a | 1.219 [1.126, 1.313] | 0.200 | 0.366 [0.338, 0.394] | 0.060 | 0.300 |
| P2b | 2.023 [1.886, 2.160] | 0.367 | 1.423 [1.327, 1.520] | 0.258 | 0.703 |
| P2c | 2.182 [1.962, 2.403] | 0.645 | 1.462 [1.314, 1.610] | 0.432 | 0.670 |
| P2d | 2.640 [2.543, 2.736] | 0.218 | 3.257 [3.138, 3.376] | 0.269 | 1.234 |
| P3 | 0.310 [0.256, 0.365] | 0.025 | 0.583 [0.481, 0.685] | 0.046 | 1.879 |
| P4 | 0.384 [0.305, 0.463] | 0.154 | 0.435 [0.346, 0.524] | 0.175 | 1.133 |
| AF | -0.498 [-0.576, -0.420] | 0.163 | -0.182 [-0.211, -0.153] | 0.059 | 0.365 |
| QA | 0.314 [0.231, 0.396] | 0.176 | 0.651 [0.480, 0.823] | 0.365 | 2.075 |
| NR | 0.263 [0.198, 0.327] | 0.110 | 0.123 [0.093, 0.153] | 0.052 | 0.468 |

Notes. AF is negative by construction (forbid wording lowers the anti-speech share; canonical sign -1). Tau-hat here is the REML between-site SD of the raw difference, a different estimator from the E5 split-half S^H in `SH_sd_units.csv` (which is the preregistered yardstick); the two are not interchangeable and are not compared here. These are the pooled yardstick values for P-c; the log OR and Hedges g REML estimates in `canonical_signs.csv` remain the benchmark's primary-coding metric.

NUM keys `hp.<item>.mu|lo|hi` (2 decimals, ML1-SD units) are defined by `_human_pooled_numbers()` in `analysis/acme/make_autonumbers.py`.
