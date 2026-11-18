# Gate G1 verdict (recoverability of the ACME G-study estimator)

Run: 500 replicates per scenario, B = 2000 bootstrap draws per item, seed 20261106, scenarios a, b, c, d, e, f, g, h25, h50; runtime 157 s on 5 workers. The pass rule is PREREG-acme.md section 6, applied as written to the pooled (mean over 10 items) level.

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

## Variant `untruncated`: **FAIL**

diagnostic: shares = component / sum of untruncated components, percentile interval

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 1 of 63 scenario-components violate; worst b/W bias -0.034 | FAIL |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 16 of 63 (25.4%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 10 of 19 violate; worst a/M 1.000 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C1 violations (scenario, component, bias): b/W -0.034

C3 violations (scenario, component, rate): a/M 1.000; a/O 0.082; a/MO 0.998; b/M 1.000; b/MO 0.992; c/M 1.000; c/O 0.090; c/MO 0.998; d/M 0.998; d/MO 0.998

Informational, single-item levels (item2, item1; not gated): 4 of 119 abs(bias) > 0.02; coverage in range for 17 of 119 (14%); 12 of 58 zero components with false-positive rate > 0.05.

## Variant `untrunc_centered`: **FAIL**

diagnostic: untruncated shares, interval centred on the point estimate (est + quantile - bootstrap mean)

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 1 of 63 scenario-components violate; worst b/W bias -0.034 | FAIL |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 33 of 63 (52.4%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 3 of 19 violate; worst d/W 0.062 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C1 violations (scenario, component, bias): b/W -0.034

C3 violations (scenario, component, rate): a/W 0.052; d/W 0.062; d/MW 0.060

Informational, single-item levels (item2, item1; not gated): 4 of 119 abs(bias) > 0.02; coverage in range for 30 of 119 (25%); 4 of 58 zero components with false-positive rate > 0.05.

## Variant `A1`: **FAIL**

amendment A1 (gstudy estimator 'A1'): untruncated shares, delete-one-wording jackknife bias correction, centred percentile interval

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.003 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 35 of 63 (55.6%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 3 of 19 violate; worst d/W 0.060 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C3 violations (scenario, component, rate): a/W 0.052; d/W 0.060; d/MW 0.060

Informational, single-item levels (item2, item1; not gated): 0 of 119 abs(bias) > 0.02; coverage in range for 30 of 119 (25%); 4 of 58 zero components with false-positive rate > 0.05.
