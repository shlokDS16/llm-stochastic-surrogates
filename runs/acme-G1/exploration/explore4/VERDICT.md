# Gate G1 verdict (recoverability of the ACME G-study estimator)

Run: 500 replicates per scenario, B = 2000 bootstrap draws per item, seed 20261106, scenarios a, b, c, d, e, f, g, h25, h50; runtime 500 s on 5 workers. The pass rule is PREREG-acme.md section 6, applied as written to the pooled (mean over 10 items) level.

## Variant `as_written`: **FAIL**

PREREG as written: negative components set to 0, shares from truncated components, percentile interval (gstudy estimator 'prereg')

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 4 of 63 scenario-components violate; worst b/W bias -0.044 | FAIL |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 9 of 63 (14.3%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 19 of 19 violate; worst a/M 1.000 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C1 violations (scenario, component, bias): a/res -0.041; b/W -0.044; b/MW +0.022; c/MW -0.028

C3 violations (scenario, component, rate): a/M 1.000; a/O 0.614; a/MO 1.000; a/W 0.992; a/WO 0.498; b/M 1.000; b/O 0.636; b/MO 1.000; b/WO 0.472; c/M 1.000; c/O 0.654; c/MO 1.000; c/W 0.968; c/WO 0.492; d/M 1.000; d/MO 1.000; d/W 0.712; d/MW 0.678; d/WO 0.500

Informational, single-item levels (item2, item1; not gated): 9 of 119 abs(bias) > 0.02; coverage in range for 16 of 119 (13%); 12 of 58 zero components with false-positive rate > 0.05.

## Variant `A1`: **FAIL**

amendment A1 (gstudy estimator 'A1'): step 3 + bootstrap world with fixed effects shrunk to the unbiased estimates

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.003 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 49 of 63 (77.8%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/W 0.040 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 44 of 119 (37%); 1 of 58 zero components with false-positive rate > 0.05.

## Variant `P1_param_centered`: **FAIL**

diagnostic: parametric bootstrap from the fitted mixed model, jackknife-corrected shares, centred percentile interval

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.003 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 40 of 63 (63.5%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst a/M 0.026 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 38 of 119 (32%); 0 of 58 zero components with false-positive rate > 0.05.

## Variant `P2_param_pivotal`: **FAIL**

diagnostic: parametric bootstrap from the fitted mixed model, jackknife-corrected shares, pivotal (reflected) interval

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.003 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 37 of 63 (58.7%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/MW 0.024 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 25 of 119 (21%); 0 of 58 zero components with false-positive rate > 0.05.

## Variant `wald_jk`: **FAIL**

diagnostic alternative: jackknife-corrected shares with a normal interval from the delete-one-wording jackknife variance

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.003 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 51 of 63 (81.0%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/MW 0.020 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 52 of 119 (44%); 0 of 58 zero components with false-positive rate > 0.05.
