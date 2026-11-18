# Gate G1 verdict (recoverability of the ACME G-study estimator)

Run: 300 replicates per scenario, B = 1000 bootstrap draws per item, seed 20261106, scenarios a, b, c, d, e, f, g, h25, h50; runtime 448 s on 5 workers. The pass rule is PREREG-acme.md section 6, applied as written to the pooled (mean over 10 items) level.

## Variant `A1`: **FAIL**

amendment A1 (gstudy estimator 'A1'): step 3 + bootstrap world with fixed effects shrunk to the unbiased estimates

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst f/M bias +0.004 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 50 of 63 (79.4%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/MW 0.043 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 43 of 119 (36%); 2 of 58 zero components with false-positive rate > 0.05.

## Variant `S1_student`: **PASS**

diagnostic: jackknife-corrected shares, studentized (bootstrap-t) interval with an inner delete-one-wording jackknife SE, shrunk-fixed-effects bootstrap world

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst f/M bias +0.004 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 61 of 63 (96.8%) | PASS |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst a/M 0.050 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 81 of 119 (68%); 0 of 58 zero components with false-positive rate > 0.05.
