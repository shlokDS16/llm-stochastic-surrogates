| paradigm | metric | k | N | mu_REML [95% CI] | tau_REML [Q-profile 95% CI] | I2 % | Q (p) | unweighted mean d | S^H moment (basic bootstrap 95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| AF allowed/forbidden (log OR, anti-speech; forbid vs allow) | primary | 36 | 6292 | -1.385 [-1.549, -1.220] | 0.000 [0.000, 0.360] | 0.0 | 29.0 (0.754) | -1.573 | 0.000 [0.000, 0.571] |
| AF allowed/forbidden (log OR, anti-speech; forbid vs allow) | sens_raw | 36 | 6292 | -0.182 [-0.210, -0.153] | 0.059 [0.030, 0.092] | 55.6 | 74.6 (0.000) | -0.193 | 0.053 [0.000, 0.084] |
| AF allowed/forbidden (log OR, anti-speech; forbid vs allow) | check_ml1_published_yes_coding | 36 | 6292 | -3.509 [-3.867, -3.152] | 0.901 [0.632, 1.242] | 75.6 | 180.4 (0.000) | -3.628 | 0.852 [0.609, 1.115] |
| QA quote attribution (g; Washington vs bin Laden) | primary | 36 | 6325 | 0.309 [0.229, 0.389] | 0.164 [0.090, 0.282] | 52.0 | 67.7 (0.001) | 0.303 | 0.180 [0.000, 0.257] |
| QA quote attribution (g; Washington vs bin Laden) | sens_raw | 36 | 6325 | 0.651 [0.480, 0.823] | 0.365 [0.213, 0.603] | 55.4 | 72.6 (0.000) | 0.639 | 0.390 [0.000, 0.549] |
| NR norm of reciprocity (log OR, Yes to US question; other first vs US first) | primary | 36 | 6276 | 0.659 [0.521, 0.797] | 0.165 [0.000, 0.345] | 17.2 | 38.9 (0.299) | 0.610 | 0.000 [0.000, 0.366] |
| NR norm of reciprocity (log OR, Yes to US question; other first vs US first) | sens_raw | 36 | 6276 | 0.123 [0.093, 0.153] | 0.051 [0.008, 0.090] | 36.9 | 54.5 (0.019) | 0.124 | 0.041 [0.000, 0.087] |

Metrics: `primary` = log odds ratio (AF, NR) or Hedges g (QA), x1 minus x0; `sens_raw` = raw-scale difference (risk difference, or rating points) with variance s1^2/n1 + s0^2/n0, so mu, tau and S^H are in raw units; `check_ml1_published_yes_coding` (AF only) = log OR of the raw Yes answer, the coding behind the published d = 1.96. Same estimators as `runs/human-ml1/benchmark_table.md` (metafor REML with Q-profile CI; moment estimator with within-site bootstrap, B = 2000, seed 20261106).

Test-inversion spread (code path of `spread_a1.py`, seed 20261107):

| paradigm | metric | S^H test inversion | 95% interval (S) | lower bound of S^2 interval above 0 |
|---|---|---|---|---|
| AF | primary | 0.000 | [0.000, 0.465] | False |
| AF | sens_raw | 0.052 | [0.000, 0.081] | False |
| AF | check_ml1_published_yes_coding | 0.844 | [0.589, 1.078] | True |
| QA | primary | 0.181 | [0.085, 0.262] | True |
| QA | sens_raw | 0.388 | [0.217, 0.554] | True |
| NR | primary | 0.000 | [0.000, 0.337] | False |
| NR | sens_raw | 0.039 | [0.000, 0.083] | False |
