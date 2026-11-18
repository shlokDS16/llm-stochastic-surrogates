# Gate G1b verdict (type-I error and power of H1-H3, synthetic data)

Estimator A-G1 (`A1`), B = 1000, alpha = 0.05, pass for a hypothesis: rejection rate under its boundary null <= 0.0695 (= 0.05 + 2 sqrt(0.05 x 0.95 / 500)). Rejection = raw p < 0.05 (H1 one-sided, H3 two-sided, H2 intersection-union as in `gstudy.hypotheses`). Monte Carlo SE = sqrt(r (1 - r) / R). Synthetic data only.

## Type-I error under the boundary nulls

| hypothesis | replicates | rejections | rejection rate | MC SE | limit | verdict |
|---|---|---|---|---|---|---|
| H1 | 500 | 21 | 0.0420 | 0.0090 | 0.0695 | **PASS** |
| H2 | 500 | 0 | 0.0000 | 0.0000 | 0.0695 | **PASS** |
| H3 | 500 | 25 | 0.0500 | 0.0097 | 0.0695 | **PASS** |

## Power (information only)

| hypothesis | alternative | replicates | rejection rate | MC SE |
|---|---|---|---|---|
| H1 | wording (W + MW) 0.40 vs T 0.10 | 300 | 1.000 | 0.000 |
| H2 | true median set-up SD = 2 c_p = 0.4 ML1-SD (c_p = 0.2) | 300 | 1.000 | 0.000 |
| H3 | MW 0.45 vs W 0.15 | 300 | 1.000 | 0.000 |

## Diagnostics (means over replicates)

- `H1_null`: mean estimate (wording - T) -0.0006, mean wording share 0.2501, mean T share 0.2507; median p 0.512.
- `H2_null`: mean over replicates and items of the estimated median set-up SD 0.1968 (true 0.2); mean number of items passing (item-level p < 0.05) 0.02 of 10 (item-level rejection rate 0.0016); median p 0.827.
- `H3_null`: mean estimate (MW - W) -0.0035, mean MW 0.2982, mean W 0.3017; median p 0.451.
- `H1_alt`: mean estimate (wording - T) +0.2991, mean wording share 0.3992, mean T share 0.1002; median p 0.000.
- `H2_alt`: mean over replicates and items of the estimated median set-up SD 0.3908 (true 0.4); mean number of items passing (item-level p < 0.05) 10.00 of 10 (item-level rejection rate 1.0000); median p 0.000.
- `H3_alt`: mean estimate (MW - W) +0.2951, mean MW 0.4474, mean W 0.1523; median p 0.000.

## Run

- CPU seconds summed over replicates: 4985 s (1.38 h) on 2 workers (below-normal priority); wall seconds per session: [3613.9].
- git HEAD at run time: `1431596c8cbe95cd9c2f8a758bc4f68bd232a08c`.
- SHA-256 (LF) of the code used: `analysis/acme/gstudy.py` 25eb9ac0d117; `analysis/acme/simulate_G1.py` 393842cb4fe3; `analysis/acme/simulate_G1b.py` d5627d1cbd70.
- Commands:
  - `.venv/Scripts/python.exe -I analysis/acme/simulate_G1b.py run --workers 2 --out runs/acme-G1b`

## Definitions and choices (fixed by the brief and the prereg; stated for the record)

- H1 null per item: two-order items (M, W, O, T): W .10, MW .15, T .10, MT .05, WT .05, MWT .05, M .10, O .05, MO .05, WO .05, residual .25. One-order items (M, W, T): W .10, MW .15, T .10, MT .05, WT .10, M .10, residual .40. Alternative: wording .40 (W .15, MW .25), T .10 (T .05, MT .02, WT .02, MWT .01 or T .04, MT .03, WT .03), remaining mass as in the null.
- H3 null: two-order items W .30, MW .30, residual .40; one-order items W .30, MW .30 and the remaining .40 in the fixed M effect (the residual cannot be separated from MW in one-order items). Alternative: MW .45, W .15, remainder as in the null.
- H2: design as scenario (e) of `simulate_G1.py` (shares from `shares_two/shares_one('e')`, rescaled by one factor per item). True set-up SD of model m = population SD of Delta[m, w, o] over the wording universe and the order set (sigma2_W + sigma2_MW + sigma2_WO + sigma2_res + mean_o (omega_o + gamma_mo)^2; one-order items sigma2_W + sigma2_MW); the item's true median over the 14 models is set to 0.2 (null) or 0.4 (alternative). The estimator uses the finite-sample SD (ddof 1) over 10 x n_o cells, so its small-sample bias belongs to what the gate measures.
- H1 replicates call `hypotheses()` with one stub H3 item (T = 1 slice of item 0) to avoid building the full H3 pool; its H3 output is discarded. H3 replicates call `hypotheses()` with items3 only. H2 replicates use `setup_sd` and `iu_pvalue` with the same seeds as `hypotheses()` (equality checked in `tests/test_simulate_G1b.py`).
- Fixed effects are sum-to-zero patterns with sum(x^2)/prod(n_f - 1) equal to the target component (the quadratic-form convention of the prereg); shares are component / sum of components.
- Consequence (prereg section 6): a hypothesis that fails leaves the confirmatory family and is reported as exploratory; G1b does not change the estimator.

## Reading notes

- H2 under its boundary null is very conservative (rejection 0 of 500 replicates; item-level rejection rate about 0.002): the estimator is the finite-sample SD (ddof 1) over 10 x n_o cells, whose downward small-sample bias (mean estimated median set-up SD 0.197 against the true 0.2) and the intersection-union rule (at least 5 of 10 items) both push the rate below 0.05. The pass is a pass on the type-I criterion; it is not evidence that H2 has nominal size.
- Power is 1.000 for all three alternatives at the stated effect sizes with 10 items and 14 models; the alternatives are therefore not informative about smaller effects.
- Rejection rates from 500 replicates carry a Monte Carlo SE of about 0.01 (H1 0.042, H3 0.050).
- Code edit after the run: only the H2 diagnostic text of the aggregate report (see run.json note). Generators, tests and results unchanged.
