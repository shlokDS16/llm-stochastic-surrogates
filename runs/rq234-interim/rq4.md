# RQ4 (interim): reporting items and robustness checks

Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / unweighted eligible respondents. Interim run.

claude: 102 respondents, 72 eligible, 27 estimation groups, df 75; codex: 102 respondents, 74 eligible, 27 estimation groups, df 75

For fields that FAIL the full-sample rule the two coder columns are a coder-sensitivity display, explicitly not an uncertainty interval (amendment v0.12 item 4). `f6_applicable` = f6 yes among studies with f6 not na; `robustness_outcome_among_tested` has only studies with robustness_outcome not na as denominator; `robustness_tested` = robustness_outcome not na (derived here as the headline of the six-type robustness judgement).


| feature | Claude % (95% CI) | Claude k/n | Codex % (95% CI) | Codex k/n | kappa | agree % | n pairs | rule |
|---|---|---|---|---|---|---|---|---|
| f1/yes | 29.9 (17.1 to 42.6) | 15/72 | 6.3 (0.0 to 14.6) | 3/74 | 0.064 | 80.0 | 65 | pass |
| f1/no | 70.2 (57.4 to 82.9) | 57/72 | 93.7 (85.4 to 100.0) | 71/74 | 0.064 | 80.0 | 65 | pass |
| f1/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.064 | 80.0 | 65 | pass |
| f2/yes | 45.5 (34.3 to 56.7) | 29/72 | 49.9 (36.6 to 63.2) | 36/74 | 0.794 | 89.2 | 65 | pass |
| f2/no | 48.8 (37.7 to 60.0) | 38/72 | 49.8 (36.5 to 63.1) | 36/74 | 0.794 | 89.2 | 65 | pass |
| f2/na | 5.7 (1.7 to 9.6) | 5/72 | 0.3 (0.0 to 0.7) | 2/74 | 0.794 | 89.2 | 65 | pass |
| f3/yes | 46.8 (27.8 to 65.8) | 32/72 | 51.9 (33.6 to 70.2) | 36/74 | 0.636 | 81.5 | 65 | pass |
| f3/no | 53.1 (34.0 to 72.1) | 39/72 | 48.1 (29.8 to 66.4) | 38/74 | 0.636 | 81.5 | 65 | pass |
| f3/na | 0.1 (0.0 to 0.4) | 1/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.636 | 81.5 | 65 | pass |
| f4/yes | 68.7 (50.8 to 86.7) | 53/72 | 68.5 (57.4 to 79.6) | 58/74 | 0.503 | 81.5 | 65 | FAIL |
| f4/no | 31.3 (13.3 to 49.2) | 19/72 | 31.5 (20.4 to 42.6) | 16/74 | 0.503 | 81.5 | 65 | FAIL |
| f4/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.503 | 81.5 | 65 | FAIL |
| f5/yes | 24.2 (14.1 to 34.3) | 26/72 | 10.6 (4.3 to 17.0) | 14/74 | 0.532 | 80.0 | 65 | FAIL |
| f5/no | 75.8 (65.7 to 85.9) | 46/72 | 89.4 (83.0 to 95.7) | 60/74 | 0.532 | 80.0 | 65 | FAIL |
| f5/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.532 | 80.0 | 65 | FAIL |
| f6/yes | 11.7 (3.5 to 19.8) | 12/72 | 12.1 (4.4 to 19.7) | 16/74 | 0.282 | 55.4 | 65 | FAIL |
| f6/no | 35.9 (26.1 to 45.6) | 25/72 | 41.2 (28.0 to 54.5) | 25/74 | 0.282 | 55.4 | 65 | FAIL |
| f6/na | 52.5 (41.4 to 63.6) | 35/72 | 46.7 (34.5 to 58.9) | 33/74 | 0.282 | 55.4 | 65 | FAIL |
| f7/yes | 15.4 (6.1 to 24.8) | 11/72 | 19.2 (9.3 to 29.1) | 13/74 | 0.892 | 96.9 | 65 | pass |
| f7/no | 84.4 (75.0 to 93.8) | 60/72 | 80.8 (70.9 to 90.7) | 61/74 | 0.892 | 96.9 | 65 | pass |
| f7/na | 0.1 (0.0 to 0.4) | 1/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.892 | 96.9 | 65 | pass |
| f8/yes | 28.4 (18.1 to 38.8) | 24/72 | 34.4 (22.5 to 46.3) | 28/74 | 0.453 | 73.8 | 65 | FAIL |
| f8/no | 71.6 (61.2 to 81.9) | 48/72 | 65.6 (53.7 to 77.5) | 46/74 | 0.453 | 73.8 | 65 | FAIL |
| f8/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.453 | 73.8 | 65 | FAIL |
| f9/yes | 20.5 (9.6 to 31.4) | 23/72 | 31.7 (19.2 to 44.3) | 33/74 | 0.616 | 81.5 | 65 | pass |
| f9/no | 79.5 (68.6 to 90.5) | 49/72 | 68.3 (55.7 to 80.8) | 41/74 | 0.616 | 81.5 | 65 | pass |
| f9/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.616 | 81.5 | 65 | pass |
| f10/yes | 77.9 (66.0 to 89.8) | 53/72 | 91.8 (84.9 to 98.7) | 65/74 | 0.574 | 87.7 | 65 | FAIL |
| f10/no | 22.1 (10.2 to 34.0) | 19/72 | 8.2 (1.3 to 15.1) | 9/74 | 0.574 | 87.7 | 65 | FAIL |
| f10/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.574 | 87.7 | 65 | FAIL |
| f11/yes | 8.6 (0.0 to 22.3) | 4/72 | 11.2 (0.0 to 26.2) | 6/74 | 0.735 | 96.9 | 65 | pass |
| f11/no | 91.4 (77.7 to 100.0) | 68/72 | 88.8 (73.8 to 100.0) | 68/74 | 0.735 | 96.9 | 65 | pass |
| f11/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.735 | 96.9 | 65 | pass |
| f12/yes | 52.5 (34.0 to 71.0) | 38/72 | 61.6 (42.9 to 80.3) | 48/74 | 0.726 | 86.2 | 65 | pass |
| f12/no | 47.5 (29.1 to 66.0) | 34/72 | 36.3 (17.9 to 54.8) | 25/74 | 0.726 | 86.2 | 65 | pass |
| f12/na | 0.0 (0.0 to 0.0) * | 0/72 | 0.0 (0.0 to 0.0) * | 0/74 | 0.726 | 86.2 | 65 | pass |
| f6_applicable/yes | 24.5 (9.5 to 39.5) | 12/37 | 22.6 (8.2 to 37.1) | 16/41 | 0.282 | 55.4 | 65 | FAIL |
| perturbation/wording | 24.2 (14.1 to 34.3) | 26/72 | 29.4 (13.1 to 45.6) | 30/74 | 0.71 | 86.2 | 65 | pass |
| perturbation/option_order | 10.8 (2.8 to 18.9) | 11/72 | 14.0 (5.5 to 22.5) | 16/74 | 0.49 | 84.6 | 65 | FAIL |
| perturbation/response_format | 5.7 (1.4 to 10.1) | 7/72 | 11.3 (3.3 to 19.2) | 10/74 | 0.259 | 83.1 | 65 | FAIL |
| perturbation/decoding | 15.4 (6.1 to 24.8) | 11/72 | 27.7 (16.7 to 38.7) | 21/74 | 0.611 | 86.2 | 65 | pass |
| perturbation/seeds | 6.3 (0.0 to 13.9) | 4/72 | 26.5 (9.5 to 43.5) | 14/74 | 0.34 | 86.2 | 65 | pass |
| perturbation/model_version | 21.1 (11.6 to 30.7) | 18/72 | 19.5 (9.2 to 29.8) | 19/74 | 0.257 | 70.8 | 65 | FAIL |
| perturbation/contamination | 8.1 (1.5 to 14.8) | 8/72 | 24.9 (13.0 to 36.8) | 20/74 | 0.479 | 83.1 | 65 | FAIL |
| perturbation/persona | 11.4 (0.0 to 25.9) | 5/72 | 19.1 (3.3 to 34.9) | 11/74 | 0.683 | 93.8 | 65 | pass |
| perturbation/language | 4.4 (0.0 to 11.6) | 2/72 | 8.1 (0.0 to 17.1) | 3/74 | 0.377 | 95.4 | 65 | pass |
| perturbation/other | 50.5 (31.3 to 69.6) | 34/72 | 19.4 (7.7 to 31.0) | 17/74 | 0.401 | 70.8 | 65 | FAIL |
| perturbation/none_listed | 23.0 (6.9 to 39.2) | 14/72 | 5.3 (0.0 to 11.3) | 4/74 | 0.352 | 86.2 | 65 | pass |
| robustness_outcome/survived | 12.5 (5.3 to 19.8) | 14/72 | 10.9 (3.2 to 18.6) | 10/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome/weakened | 9.7 (1.6 to 17.8) | 6/72 | 24.8 (14.7 to 34.8) | 25/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome/reversed | 1.0 (0.0 to 2.3) | 2/72 | 0.5 (0.0 to 1.2) | 2/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome/mixed | 18.9 (9.2 to 28.7) | 16/72 | 4.7 (0.0 to 10.7) | 3/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome/not_reported | 5.1 (0.0 to 12.2) | 5/72 | 1.1 (0.0 to 2.6) | 2/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome/na | 52.8 (41.7 to 63.9) | 29/72 | 58.1 (47.0 to 69.2) | 32/74 | 0.3 | 46.2 | 65 | FAIL |
| robustness_tested/yes | 47.2 (36.1 to 58.3) | 43/72 | 41.9 (30.8 to 53.0) | 42/74 | 0.619 | 81.5 | 65 | pass |
| robustness_outcome_among_tested/survived | 26.5 (11.4 to 41.6) | 14/43 | 26.0 (9.3 to 42.6) | 10/42 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome_among_tested/weakened | 20.5 (4.4 to 36.6) | 6/43 | 59.1 (39.4 to 78.9) | 25/42 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome_among_tested/reversed | 2.1 (0.0 to 5.0) | 2/43 | 1.2 (0.0 to 2.9) | 2/42 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome_among_tested/mixed | 40.0 (21.4 to 58.7) | 16/43 | 11.1 (0.0 to 24.7) | 3/42 | 0.3 | 46.2 | 65 | FAIL |
| robustness_outcome_among_tested/not_reported | 10.8 (0.0 to 25.1) | 5/43 | 2.5 (0.0 to 6.3) | 2/42 | 0.3 | 46.2 | 65 | FAIL |
| f12/not_reported | 0.0 (0.0 to 0.0) * | 0/72 | 2.1 (0.0 to 6.1) | 1/74 | 0.726 | 86.2 | 65 | pass |


## Year trends: design-weighted logistic regression of the item on publication year (odds ratio per year), per coder. SENSITIVITY ANALYSIS: neither the presence nor the absence of a trend is claimed. Needs at least 10 events and 10 non-events in the domain; sandwich variance on merged strata; t interval.

| coder | feature | n | events | OR per year (95% CI) | note | field rule |
|---|---|---|---|---|---|---|
| claude | f1/yes | 72 | 15 | 0.96 (0.65 to 1.43) |  | pass |
| claude | f2/yes | 72 | 29 | 1.17 (0.87 to 1.58) |  | pass |
| claude | f3/yes | 72 | 32 | 1.34 (0.83 to 2.15) |  | pass |
| claude | f4/yes | 72 | 53 | 0.69 (0.36 to 1.29) |  | FAIL |
| claude | f5/yes | 72 | 26 | 0.81 (0.59 to 1.09) |  | FAIL |
| claude | f6/yes | 72 | 12 | 0.79 (0.56 to 1.10) |  | FAIL |
| claude | f7/yes | 72 | 11 | 0.88 (0.60 to 1.28) |  | pass |
| claude | f8/yes | 72 | 24 | 0.87 (0.63 to 1.19) |  | FAIL |
| claude | f9/yes | 72 | 23 | 0.75 (0.47 to 1.20) |  | pass |
| claude | f10/yes | 72 | 53 | 1.41 (0.87 to 2.28) |  | FAIL |
| claude | f11/yes | 72 | 4 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | f12/yes | 72 | 38 | 0.95 (0.59 to 1.51) |  | pass |
| claude | f6_applicable/yes | 37 | 12 | 0.61 (0.30 to 1.22) |  | FAIL |
| claude | perturbation/wording | 72 | 26 | 0.81 (0.59 to 1.09) |  | pass |
| claude | perturbation/option_order | 72 | 11 | 0.81 (0.58 to 1.14) |  | FAIL |
| claude | perturbation/response_format | 72 | 7 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | perturbation/decoding | 72 | 11 | 0.88 (0.60 to 1.28) |  | pass |
| claude | perturbation/seeds | 72 | 4 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | perturbation/model_version | 72 | 18 | 0.86 (0.64 to 1.17) |  | FAIL |
| claude | perturbation/contamination | 72 | 8 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | perturbation/persona | 72 | 5 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | perturbation/language | 72 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| claude | perturbation/other | 72 | 34 | 1.15 (0.68 to 1.95) |  | FAIL |
| claude | robustness_tested/yes | 72 | 43 | 0.73 (0.49 to 1.08) |  | pass |
| claude | robustness_outcome_among_tested/survived | 43 | 14 | 0.84 (0.43 to 1.67) |  | FAIL |
| claude | robustness_outcome_among_tested/weakened | 43 | 6 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | robustness_outcome_among_tested/reversed | 43 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| claude | robustness_outcome_among_tested/mixed | 43 | 16 | 1.37 (0.70 to 2.67) |  | FAIL |
| codex | f1/yes | 74 | 3 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | f2/yes | 74 | 36 | 0.93 (0.59 to 1.47) |  | pass |
| codex | f3/yes | 74 | 36 | 1.07 (0.60 to 1.90) |  | pass |
| codex | f4/yes | 74 | 58 | 0.70 (0.40 to 1.22) |  | FAIL |
| codex | f5/yes | 74 | 14 | 0.65 (0.37 to 1.16) |  | FAIL |
| codex | f6/yes | 74 | 16 | 0.61 (0.33 to 1.13) |  | FAIL |
| codex | f7/yes | 74 | 13 | 0.72 (0.41 to 1.25) |  | pass |
| codex | f8/yes | 74 | 28 | 0.81 (0.51 to 1.30) |  | FAIL |
| codex | f9/yes | 74 | 33 | 0.73 (0.45 to 1.17) |  | pass |
| codex | f10/yes | 74 | 65 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| codex | f11/yes | 74 | 6 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | f12/yes | 74 | 48 | 1.15 (0.61 to 2.17) |  | pass |
| codex | f6_applicable/yes | 41 | 16 | 0.58 (0.27 to 1.23) |  | FAIL |
| codex | perturbation/wording | 74 | 30 | 0.66 (0.33 to 1.31) |  | pass |
| codex | perturbation/option_order | 74 | 16 | 0.43 (0.25 to 0.76) |  | FAIL |
| codex | perturbation/response_format | 74 | 10 | 0.97 (0.53 to 1.77) |  | FAIL |
| codex | perturbation/decoding | 74 | 21 | 0.87 (0.52 to 1.44) |  | pass |
| codex | perturbation/seeds | 74 | 14 | 1.07 (0.50 to 2.29) |  | pass |
| codex | perturbation/model_version | 74 | 19 | 0.99 (0.62 to 1.58) |  | FAIL |
| codex | perturbation/contamination | 74 | 20 | 1.03 (0.60 to 1.78) |  | FAIL |
| codex | perturbation/persona | 74 | 11 | 1.18 (0.54 to 2.56) |  | pass |
| codex | perturbation/language | 74 | 3 | NA | not estimated (fewer than 10 events or 10 non-events) | pass |
| codex | perturbation/other | 74 | 17 | 1.32 (0.68 to 2.55) |  | FAIL |
| codex | robustness_tested/yes | 74 | 42 | 0.56 (0.36 to 0.89) |  | pass |
| codex | robustness_outcome_among_tested/survived | 42 | 10 | 1.20 (0.66 to 2.16) |  | FAIL |
| codex | robustness_outcome_among_tested/weakened | 42 | 25 | 0.79 (0.40 to 1.53) |  | FAIL |
| codex | robustness_outcome_among_tested/reversed | 42 | 2 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
| codex | robustness_outcome_among_tested/mixed | 42 | 3 | NA | not estimated (fewer than 10 events or 10 non-events) | FAIL |
