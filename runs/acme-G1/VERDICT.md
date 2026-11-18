# Gate G1 verdict (recoverability of the ACME G-study estimator)

Run: 1000 replicates per scenario, B = 2000 bootstrap draws per item, seed 20261106, scenarios a, b, c, d, e, f, g, h25, h50; runtime 2892 s on 6 workers. The pass rule is PREREG-acme.md section 6, applied as written to the pooled (mean over 10 items) level.

## Summary

| variant | C1 bias | C2 coverage | C3 false positives | C4 ranking | overall |
|---|---|---|---|---|---|
| `as_written` | FAIL | FAIL (8/63) | FAIL | PASS | **FAIL** |
| `untruncated` | FAIL | FAIL (16/63) | FAIL | PASS | **FAIL** |
| `D1_centered` | PASS | FAIL (33/63) | FAIL | PASS | **FAIL** |
| `D2_shrunk_centered` | PASS | FAIL (49/63) | PASS | PASS | **FAIL** |
| `A1` | PASS | PASS (62/63) | PASS | PASS | **PASS** |

The preregistered estimator is `as_written`; its overall result is the G1 result under the rule as written. Other variants are diagnostic steps or the amendment (A1) and are not primary until approved.

## Variant `as_written`: **FAIL**

PREREG as written: negative components set to 0, shares from truncated components, percentile interval (gstudy estimator 'prereg')

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 4 of 63 scenario-components violate; worst b/W bias -0.044 | FAIL |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 8 of 63 (12.7%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 19 of 19 violate; worst a/M 1.000 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C1 violations (scenario, component, bias): a/res -0.041; b/W -0.044; b/MW +0.022; c/MW -0.028

C3 violations (scenario, component, rate): a/M 1.000; a/O 0.603; a/MO 1.000; a/W 0.986; a/WO 0.502; b/M 1.000; b/O 0.618; b/MO 1.000; b/WO 0.479; c/M 1.000; c/O 0.613; c/MO 1.000; c/W 0.968; c/WO 0.483; d/M 1.000; d/MO 1.000; d/W 0.691; d/MW 0.696; d/WO 0.510

Informational, single-item levels (item2, item1; not gated): 9 of 87 abs(bias) > 0.02; coverage in range for 16 of 87 (18%); 11 of 26 zero components with false-positive rate > 0.05.

## Variant `untruncated`: **FAIL**

diagnostic D0: shares = component / sum of untruncated components, percentile interval

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 1 of 63 scenario-components violate; worst b/W bias -0.034 | FAIL |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 16 of 63 (25.4%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 11 of 19 violate; worst a/M 1.000 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C1 violations (scenario, component, bias): b/W -0.034

C3 violations (scenario, component, rate): a/M 1.000; a/O 0.083; a/MO 0.998; b/M 1.000; b/O 0.052; b/MO 0.996; c/M 1.000; c/O 0.081; c/MO 0.999; d/M 0.997; d/MO 0.999

Informational, single-item levels (item2, item1; not gated): 4 of 87 abs(bias) > 0.02; coverage in range for 17 of 87 (20%); 11 of 26 zero components with false-positive rate > 0.05.

## Variant `D1_centered`: **FAIL**

diagnostic D1: D0 + delete-one-wording jackknife bias correction of the shares + interval centred on the corrected estimate (est + quantile - bootstrap mean)

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.004 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 33 of 63 (52.4%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 3 of 19 violate; worst d/W 0.058 | FAIL |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

C3 violations (scenario, component, rate): a/W 0.053; d/W 0.058; d/MW 0.057

Informational, single-item levels (item2, item1; not gated): 0 of 87 abs(bias) > 0.02; coverage in range for 28 of 87 (32%); 4 of 26 zero components with false-positive rate > 0.05.

## Variant `D2_shrunk_centered`: **FAIL**

diagnostic D2: D1 + bootstrap world with fixed effects shrunk to the unbiased estimates + deviations rescaled by sqrt(n_w/(n_w-1))

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.004 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 49 of 63 (77.8%) | FAIL |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/W 0.042 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 87 abs(bias) > 0.02; coverage in range for 45 of 87 (52%); 0 of 26 zero components with false-positive rate > 0.05.

## Variant `A1`: **PASS**

amendment A1 (gstudy estimator 'A1'): untruncated shares, delete-one-wording jackknife bias correction, studentized bootstrap-t interval (inner jackknife SE in every bootstrap sample) in a bootstrap world with fixed effects shrunk to the unbiased estimates

| criterion | rule | result | verdict |
|---|---|---|---|
| C1 bias | abs(bias) of every share <= 0.02 | 0 of 63 scenario-components violate; worst b/W bias +0.004 | PASS |
| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | 62 of 63 (98.4%) | PASS |
| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | 0 of 19 violate; worst d/W 0.034 | PASS |
| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | b: 1.000, c: 1.000, d: 1.000, e: 1.000, g: 1.000 | PASS |

Informational, single-item levels (item2, item1; not gated): 0 of 87 abs(bias) > 0.02; coverage in range for 82 of 87 (94%); 0 of 26 zero components with false-positive rate > 0.05.
