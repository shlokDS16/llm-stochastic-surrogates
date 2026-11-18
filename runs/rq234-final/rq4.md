# RQ4 (interim): reporting items and robustness checks

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 110 respondents, 80 eligible, 28 estimation groups, df 82; codex: 110 respondents, 81 eligible, 28 estimation groups, df 82

For fields that FAIL the full-sample rule the two coder columns are a coder-sensitivity display, explicitly not an uncertainty interval (amendment v0.12 item 4). `f6_applicable` = f6 yes among studies with f6 not na; `robustness_outcome_among_tested` has only studies with robustness_outcome not na as denominator; `robustness_tested` = robustness_outcome not na (derived here as the headline of the six-type robustness judgement).


| feature | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n | kappa | agree % | n pairs | rule |
|---|---|---|---|---|---|---|---|---|
| f1/yes | 25.0 (13.7 to 36.3) | 15/80 | 8.1 (0.0 to 16.9) | 4/81 | 0.045 | 80.6 | 72 | pass |
| f1/no | 75.0 (63.7 to 86.3) | 65/80 | 91.9 (83.1 to 100.0) | 77/81 | 0.045 | 80.6 | 72 | pass |
| f1/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.045 | 80.6 | 72 | pass |
| f2/yes | 42.2 (30.3 to 54.0) | 31/80 | 50.0 (37.1 to 62.9) | 38/81 | 0.813 | 90.3 | 72 | pass |
| f2/no | 52.2 (40.4 to 64.0) | 44/80 | 49.7 (36.8 to 62.6) | 41/81 | 0.813 | 90.3 | 72 | pass |
| f2/na | 5.6 (1.7 to 9.5) | 5/80 | 0.3 (0.0 to 0.6) | 2/81 | 0.813 | 90.3 | 72 | pass |
| f3/yes | 52.4 (38.8 to 65.9) | 38/80 | 55.3 (41.8 to 68.8) | 41/81 | 0.671 | 83.3 | 72 | pass |
| f3/no | 47.5 (33.9 to 61.1) | 41/80 | 44.7 (31.2 to 58.2) | 40/81 | 0.671 | 83.3 | 72 | pass |
| f3/na | 0.1 (0.0 to 0.4) | 1/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.671 | 83.3 | 72 | pass |
| f4/yes | 68.6 (56.2 to 81.0) | 56/80 | 74.3 (62.4 to 86.2) | 63/81 | 0.476 | 79.2 | 72 | FAIL |
| f4/no | 31.4 (19.0 to 43.8) | 24/80 | 25.7 (13.8 to 37.6) | 18/81 | 0.476 | 79.2 | 72 | FAIL |
| f4/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.476 | 79.2 | 72 | FAIL |
| f5/yes | 24.4 (14.4 to 34.3) | 27/80 | 10.7 (4.3 to 17.2) | 14/81 | 0.523 | 80.6 | 72 | FAIL |
| f5/no | 75.6 (65.7 to 85.6) | 53/80 | 89.3 (82.8 to 95.7) | 67/81 | 0.523 | 80.6 | 72 | FAIL |
| f5/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.523 | 80.6 | 72 | FAIL |
| f6/yes | 13.3 (4.5 to 22.0) | 14/80 | 12.1 (4.3 to 19.9) | 17/81 | 0.309 | 56.9 | 72 | FAIL |
| f6/no | 31.8 (21.3 to 42.3) | 26/80 | 45.5 (31.7 to 59.2) | 28/81 | 0.309 | 56.9 | 72 | FAIL |
| f6/na | 55.0 (43.5 to 66.3) | 40/80 | 42.4 (29.7 to 55.1) | 36/81 | 0.309 | 56.9 | 72 | FAIL |
| f7/yes | 17.2 (8.4 to 26.1) | 12/80 | 21.6 (11.7 to 31.6) | 14/81 | 0.901 | 97.2 | 72 | pass |
| f7/no | 82.6 (73.7 to 91.5) | 67/80 | 78.4 (68.4 to 88.3) | 67/81 | 0.901 | 97.2 | 72 | pass |
| f7/na | 0.1 (0.0 to 0.4) | 1/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.901 | 97.2 | 72 | pass |
| f8/yes | 33.6 (21.7 to 45.6) | 27/80 | 37.7 (25.5 to 50.0) | 30/81 | 0.501 | 76.4 | 72 | FAIL |
| f8/no | 66.4 (54.4 to 78.3) | 53/80 | 62.3 (50.0 to 74.5) | 51/81 | 0.501 | 76.4 | 72 | FAIL |
| f8/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.501 | 76.4 | 72 | FAIL |
| f9/yes | 20.7 (11.4 to 30.0) | 26/80 | 29.2 (17.6 to 40.9) | 35/81 | 0.621 | 81.9 | 72 | pass |
| f9/no | 79.3 (70.0 to 88.6) | 54/80 | 70.8 (59.1 to 82.4) | 46/81 | 0.621 | 81.9 | 72 | pass |
| f9/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.621 | 81.9 | 72 | pass |
| f10/yes | 75.9 (65.1 to 86.8) | 58/80 | 88.1 (79.4 to 96.7) | 70/81 | 0.6 | 87.5 | 72 | pass |
| f10/no | 24.1 (13.2 to 34.9) | 22/80 | 11.9 (3.3 to 20.6) | 11/81 | 0.6 | 87.5 | 72 | pass |
| f10/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.6 | 87.5 | 72 | pass |
| f11/yes | 5.3 (0.0 to 12.4) | 5/80 | 6.3 (0.0 to 13.9) | 7/81 | 0.786 | 97.2 | 72 | pass |
| f11/no | 94.7 (87.6 to 100.0) | 75/80 | 93.7 (86.1 to 100.0) | 74/81 | 0.786 | 97.2 | 72 | pass |
| f11/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.786 | 97.2 | 72 | pass |
| f12/yes | 46.4 (32.9 to 60.0) | 41/80 | 62.6 (48.5 to 76.7) | 53/81 | 0.676 | 83.3 | 72 | pass |
| f12/no | 53.6 (40.0 to 67.1) | 39/80 | 33.6 (20.3 to 46.9) | 26/81 | 0.676 | 83.3 | 72 | pass |
| f12/na | 0.0 (0.0 to 0.0) * | 0/80 | 0.0 (0.0 to 0.0) * | 0/81 | 0.676 | 83.3 | 72 | pass |
| f6_applicable/yes | 29.5 (12.4 to 46.5) | 14/40 | 21.0 (7.5 to 34.6) | 17/45 | 0.309 | 56.9 | 72 | FAIL |
| perturbation/wording | 24.4 (14.4 to 34.3) | 27/80 | 28.9 (16.9 to 40.9) | 32/81 | 0.704 | 86.1 | 72 | pass |
| perturbation/option_order | 12.6 (4.0 to 21.3) | 13/80 | 16.1 (6.7 to 25.5) | 18/81 | 0.557 | 86.1 | 72 | FAIL |
| perturbation/response_format | 5.8 (1.5 to 10.1) | 8/80 | 11.8 (3.4 to 20.1) | 11/81 | 0.336 | 84.7 | 72 | FAIL |
| perturbation/decoding | 17.2 (8.4 to 26.1) | 12/80 | 30.2 (19.1 to 41.3) | 22/81 | 0.638 | 87.5 | 72 | pass |
| perturbation/seeds | 6.9 (0.0 to 14.5) | 5/80 | 23.6 (10.9 to 36.2) | 14/81 | 0.309 | 86.1 | 72 | FAIL |
| perturbation/model_version | 26.7 (15.4 to 38.1) | 21/80 | 20.5 (9.9 to 31.1) | 20/81 | 0.286 | 72.2 | 72 | FAIL |
| perturbation/contamination | 8.7 (2.1 to 15.3) | 9/80 | 22.5 (11.6 to 33.4) | 22/81 | 0.491 | 83.3 | 72 | FAIL |
| perturbation/persona | 8.2 (0.0 to 16.9) | 5/80 | 18.0 (7.5 to 28.4) | 12/81 | 0.633 | 93.1 | 72 | pass |
| perturbation/language | 2.4 (0.0 to 6.1) | 2/80 | 6.5 (0.0 to 13.4) | 3/81 | 0.379 | 95.8 | 72 | pass |
| perturbation/other | 43.6 (29.5 to 57.7) | 35/80 | 18.0 (7.8 to 28.2) | 17/81 | 0.408 | 72.2 | 72 | FAIL |
| perturbation/none_listed | 25.1 (13.0 to 37.3) | 17/80 | 9.7 (0.4 to 18.9) | 6/81 | 0.442 | 86.1 | 72 | FAIL |
| robustness_outcome/survived | 17.5 (7.1 to 27.9) | 17/80 | 14.8 (5.5 to 24.1) | 13/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome/weakened | 11.3 (2.6 to 19.9) | 7/80 | 27.8 (16.5 to 39.0) | 27/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome/reversed | 1.0 (0.0 to 2.3) | 2/80 | 0.5 (0.0 to 1.2) | 2/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome/mixed | 19.4 (9.6 to 29.3) | 17/80 | 4.8 (0.0 to 10.9) | 3/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome/not_reported | 4.9 (0.0 to 11.8) | 5/80 | 1.1 (0.0 to 2.7) | 2/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome/na | 45.9 (33.1 to 58.8) | 32/80 | 51.0 (38.6 to 63.4) | 34/81 | 0.311 | 47.2 | 72 | FAIL |
| robustness_tested/yes | 54.1 (41.2 to 66.9) | 48/80 | 49.0 (36.6 to 61.4) | 47/81 | 0.624 | 81.9 | 72 | pass |
| robustness_outcome_among_tested/survived | 32.3 (16.1 to 48.6) | 17/48 | 30.3 (13.2 to 47.4) | 13/47 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome_among_tested/weakened | 20.8 (5.5 to 36.2) | 7/48 | 56.7 (37.5 to 75.9) | 27/47 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome_among_tested/reversed | 1.8 (0.0 to 4.3) | 2/48 | 1.1 (0.0 to 2.5) | 2/47 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome_among_tested/mixed | 35.9 (18.4 to 53.5) | 17/48 | 9.7 (0.0 to 21.8) | 3/47 | 0.311 | 47.2 | 72 | FAIL |
| robustness_outcome_among_tested/not_reported | 9.1 (0.0 to 21.5) | 5/48 | 2.2 (0.0 to 5.5) | 2/47 | 0.311 | 47.2 | 72 | FAIL |
| f12/not_reported | 0.0 (0.0 to 0.0) * | 0/80 | 3.8 (0.0 to 9.2) | 2/81 | 0.676 | 83.3 | 72 | pass |


## Year trends: design-weighted logistic regression of the item on publication year (odds ratio per year), per coder. SENSITIVITY ANALYSIS: neither the presence nor the absence of a trend is claimed. Needs at least 10 events and 10 non-events in the domain; sandwich variance on merged strata; t interval.

| coder | feature | n | events | OR per year (95% CI) | note | field rule |
|---|---|---|---|---|---|---|
| claude | f1/yes | 80 | 15 | 0.96 (0.61 to 1.51) |  | pass |
| claude | f2/yes | 80 | 31 | 1.26 (0.87 to 1.83) |  | pass |
| claude | f3/yes | 80 | 38 | 1.35 (0.93 to 1.94) |  | pass |
| claude | f4/yes | 80 | 56 | 0.77 (0.48 to 1.21) |  | FAIL |
| claude | f5/yes | 80 | 27 | 0.85 (0.61 to 1.17) |  | FAIL |
| claude | f6/yes | 80 | 14 | 0.84 (0.60 to 1.17) |  | FAIL |
| claude | f7/yes | 80 | 12 | 1.02 (0.68 to 1.53) |  | pass |
| claude | f8/yes | 80 | 27 | 0.90 (0.66 to 1.22) |  | FAIL |
| claude | f9/yes | 80 | 26 | 0.74 (0.48 to 1.14) |  | pass |
| claude | f10/yes | 80 | 58 | 1.34 (0.86 to 2.09) |  | pass |
| claude | f11/yes | 80 | 5 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | f12/yes | 80 | 41 | 0.92 (0.62 to 1.35) |  | pass |
| claude | f6_applicable/yes | 40 | 14 | 0.65 (0.33 to 1.29) |  | FAIL |
| claude | perturbation/wording | 80 | 27 | 0.85 (0.61 to 1.17) |  | pass |
| claude | perturbation/option_order | 80 | 13 | 0.86 (0.61 to 1.21) |  | FAIL |
| claude | perturbation/response_format | 80 | 8 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | perturbation/decoding | 80 | 12 | 1.02 (0.68 to 1.53) |  | pass |
| claude | perturbation/seeds | 80 | 5 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | perturbation/model_version | 80 | 21 | 0.88 (0.66 to 1.18) |  | FAIL |
| claude | perturbation/contamination | 80 | 9 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | perturbation/persona | 80 | 5 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | perturbation/language | 80 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | perturbation/other | 80 | 35 | 1.08 (0.69 to 1.72) |  | FAIL |
| claude | robustness_tested/yes | 80 | 48 | 0.78 (0.53 to 1.15) |  | pass |
| claude | robustness_outcome_among_tested/survived | 48 | 17 | 0.72 (0.38 to 1.37) |  | FAIL |
| claude | robustness_outcome_among_tested/weakened | 48 | 7 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | robustness_outcome_among_tested/reversed | 48 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | robustness_outcome_among_tested/mixed | 48 | 17 | 1.36 (0.68 to 2.73) |  | FAIL |
| codex | f1/yes | 81 | 4 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | f2/yes | 81 | 38 | 1.04 (0.66 to 1.61) |  | pass |
| codex | f3/yes | 81 | 41 | 1.16 (0.75 to 1.81) |  | pass |
| codex | f4/yes | 81 | 63 | 0.93 (0.53 to 1.66) |  | FAIL |
| codex | f5/yes | 81 | 14 | 0.68 (0.37 to 1.26) |  | FAIL |
| codex | f6/yes | 81 | 17 | 0.64 (0.33 to 1.23) |  | FAIL |
| codex | f7/yes | 81 | 14 | 0.84 (0.48 to 1.46) |  | pass |
| codex | f8/yes | 81 | 30 | 0.92 (0.56 to 1.50) |  | FAIL |
| codex | f9/yes | 81 | 35 | 0.65 (0.41 to 1.03) |  | pass |
| codex | f10/yes | 81 | 70 | 1.12 (0.61 to 2.06) |  | pass |
| codex | f11/yes | 81 | 7 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | f12/yes | 81 | 53 | 1.21 (0.73 to 2.00) |  | pass |
| codex | f6_applicable/yes | 45 | 17 | 0.58 (0.27 to 1.28) |  | FAIL |
| codex | perturbation/wording | 81 | 32 | 0.58 (0.34 to 0.99) |  | pass |
| codex | perturbation/option_order | 81 | 18 | 0.46 (0.27 to 0.78) |  | FAIL |
| codex | perturbation/response_format | 81 | 11 | 1.06 (0.54 to 2.07) |  | FAIL |
| codex | perturbation/decoding | 81 | 22 | 1.02 (0.60 to 1.74) |  | pass |
| codex | perturbation/seeds | 81 | 14 | 1.01 (0.51 to 1.99) |  | FAIL |
| codex | perturbation/model_version | 81 | 20 | 1.02 (0.62 to 1.67) |  | FAIL |
| codex | perturbation/contamination | 81 | 22 | 0.90 (0.53 to 1.54) |  | FAIL |
| codex | perturbation/persona | 81 | 12 | 1.21 (0.67 to 2.18) |  | pass |
| codex | perturbation/language | 81 | 3 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | perturbation/other | 81 | 17 | 1.32 (0.68 to 2.58) |  | FAIL |
| codex | robustness_tested/yes | 81 | 47 | 0.62 (0.38 to 0.99) |  | pass |
| codex | robustness_outcome_among_tested/survived | 47 | 13 | 1.32 (0.71 to 2.44) |  | FAIL |
| codex | robustness_outcome_among_tested/weakened | 47 | 27 | 0.74 (0.38 to 1.45) |  | FAIL |
| codex | robustness_outcome_among_tested/reversed | 47 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| codex | robustness_outcome_among_tested/mixed | 47 | 3 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
