# Nonresponse (protocol v0.9.1): respondents vs nonrespondents

Respondent = full text obtained (open copy now; eGateway copies will be added on rerun). Nonrespondent = no full text. Interim run. Response rates are unweighted counts with Wilson 95% intervals; the permutation p-value (5,000 permutations, seed 20261016) is a secondary descriptive column, not a result.


## By flag (RQ1 abstract coder)

| flag (RQ1 abstract coder) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| no | 23 | 14 | 9 | 60.9 | 40.8 to 77.8 |
| unclear | 46 | 28 | 18 | 60.9 | 46.5 to 73.6 |
| yes | 81 | 60 | 21 | 74.1 | 63.6 to 82.4 |

Permutation p (secondary): 0.245


## By paradigm family (stratum)

| paradigm family (stratum) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| DEV | 5 | 5 | 0 | 100.0 | 56.6 to 100.0 |
| HB | 15 | 8 | 7 | 53.3 | 30.1 to 75.2 |
| JDM | 16 | 12 | 4 | 75.0 | 50.5 to 89.8 |
| LANG | 20 | 14 | 6 | 70.0 | 48.1 to 85.5 |
| LEARN | 8 | 6 | 2 | 75.0 | 40.9 to 92.9 |
| MEM | 11 | 10 | 1 | 90.9 | 62.3 to 98.4 |
| MOR | 14 | 9 | 5 | 64.3 | 38.8 to 83.7 |
| NUM | 4 | 3 | 1 | 75.0 | 30.1 to 95.4 |
| OTH | 15 | 4 | 11 | 26.7 | 10.9 to 52.0 |
| RE | 9 | 7 | 2 | 77.8 | 45.3 to 93.7 |
| TOM | 17 | 14 | 3 | 82.4 | 59.0 to 93.8 |
| none | 16 | 10 | 6 | 62.5 | 38.6 to 81.5 |

Permutation p (secondary): 0.027


## By year

| year | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| 2024 | 32 | 23 | 9 | 71.9 | 54.6 to 84.4 |
| 2025 | 27 | 13 | 14 | 48.1 | 30.7 to 66.0 |
| 2026 | 56 | 37 | 19 | 66.1 | 53.0 to 77.1 |
| <=2023 | 35 | 29 | 6 | 82.9 | 67.3 to 91.9 |

Permutation p (secondary): 0.035


## By venue type (OpenAlex type)

| venue type (OpenAlex type) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| article | 35 | 19 | 16 | 54.3 | 38.2 to 69.5 |
| book-chapter | 2 | 1 | 1 | 50.0 | 9.5 to 90.5 |
| conference-paper | 39 | 30 | 9 | 76.9 | 61.7 to 87.4 |
| dataset | 3 | 0 | 3 | 0.0 | 0.0 to 56.1 |
| dissertation | 1 | 0 | 1 | 0.0 | 0.0 to 79.3 |
| preprint | 69 | 52 | 17 | 75.4 | 64.0 to 84.0 |
| software | 1 | 0 | 1 | 0.0 | 0.0 to 79.3 |

Permutation p (secondary): 0.003


## Pending and unresolved records (interim)

| coder | coded_ineligible | coded_eligible | no_full_text |
|---|---|---|---|
| claude | 30 | 72 | 48 |
| codex | 28 | 74 | 48 |

In this interim run records with a full text but no usable extraction (pending_extraction) and records with an unresolved eligibility decision (coded_unclear) are treated like nonrespondents (their weight is redistributed within stratum; they enter the bounds as unknown).


## Eligible share of the frame (2,022 liberal-eligible records)

| coder | n_analysed | n_respondents | n_eligible_respondents | n_unknown_status | est_share_of_frame_pct | lo_pct | hi_pct | N_hat_eligible | frame_N | bound_all_unknown_ineligible_pct | bound_all_unknown_eligible_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | 150 | 102 | 72 | 48 | 66.34 | 57.3 | 75.38 | 1341.4 | 2022 | 41.92 | 78.61 |
| codex | 150 | 102 | 74 | 48 | 67.2 | 58.9 | 75.5 | 1358.8 | 2022 | 41.71 | 78.4 |


Point estimate: design-weighted with within-stratum response-propensity weights (N_g / r_g). Bounds: unadjusted sampling weights N_h / n_analysed_h; lower = every unknown-status analysed record ineligible, upper = every one eligible.


## Bounds on prevalences among eligible studies (every RQ3 and RQ4 row: items, perturbation types, comparison types, robustness outcomes)

Scenario A: all unknown-status records ineligible (prevalence among observed eligible, sampling weights only). Scenario B: all unknown-status records eligible, with none / all of them having the outcome. Overall bounds are the minimum and maximum of the three.

| coder | feature | n_domain | k | est_pct | all_unknown_ineligible_pct | all_unknown_eligible_none_have_outcome_pct | all_unknown_eligible_all_have_outcome_pct | overall_bounds_pct |
|---|---|---|---|---|---|---|---|---|
| claude | rq3/types_any/none | 72 | 14 | 19.4 | 19.6 | 10.5 | 57.1 | 10.5 to 57.1 |
| claude | rq3/types_any/own_sample | 72 | 21 | 35.7 | 31.8 | 16.9 | 63.6 | 16.9 to 63.6 |
| claude | rq3/types_any/published_norms | 72 | 40 | 47.6 | 51.7 | 27.6 | 74.3 | 27.6 to 74.3 |
| claude | rq3/types_any/replication_dataset | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq3/types_any/crowd_norms | 72 | 3 | 3.5 | 4.4 | 2.3 | 49.0 | 2.3 to 49.0 |
| claude | rq3/primary_type/none | 72 | 14 | 19.4 | 19.6 | 10.5 | 57.1 | 10.5 to 57.1 |
| claude | rq3/primary_type/own_sample | 72 | 20 | 33.4 | 29.2 | 15.6 | 62.2 | 15.6 to 62.2 |
| claude | rq3/primary_type/published_norms | 72 | 35 | 43.7 | 46.8 | 25.0 | 71.6 | 25.0 to 71.6 |
| claude | rq3/primary_type/replication_dataset | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq3/primary_type/crowd_norms | 72 | 3 | 3.5 | 4.4 | 2.3 | 49.0 | 2.3 to 49.0 |
| claude | rq3/human_n/reported | 72 | 28 | 40.4 | 37.8 | 20.2 | 66.8 | 20.2 to 66.8 |
| claude | rq3/outcome_types/accuracy | 72 | 35 | 38.6 | 42.4 | 22.6 | 69.3 | 22.6 to 69.3 |
| claude | rq3/outcome_types/bias_magnitude | 72 | 17 | 32.2 | 28.2 | 15.1 | 61.7 | 15.1 to 61.7 |
| claude | rq3/outcome_types/effect_size | 72 | 25 | 46.6 | 42.0 | 22.4 | 69.1 | 22.4 to 69.1 |
| claude | rq3/outcome_types/choice_distribution | 72 | 21 | 30.4 | 33.6 | 17.9 | 64.6 | 17.9 to 64.6 |
| claude | rq3/outcome_types/human_correlation | 72 | 15 | 14.9 | 18.4 | 9.8 | 56.5 | 9.8 to 56.5 |
| claude | rq3/outcome_types/other | 72 | 18 | 25.3 | 23.9 | 12.7 | 59.4 | 12.7 to 59.4 |
| claude | rq4/f1/yes | 72 | 15 | 29.9 | 26.7 | 14.2 | 60.9 | 14.2 to 60.9 |
| claude | rq4/f1/no | 72 | 57 | 70.1 | 73.3 | 39.1 | 85.8 | 39.1 to 85.8 |
| claude | rq4/f1/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f2/yes | 72 | 29 | 45.5 | 46.0 | 24.5 | 71.2 | 24.5 to 71.2 |
| claude | rq4/f2/no | 72 | 38 | 48.8 | 47.7 | 25.4 | 72.1 | 25.4 to 72.1 |
| claude | rq4/f2/na | 72 | 5 | 5.6 | 6.3 | 3.4 | 50.0 | 3.4 to 50.0 |
| claude | rq4/f3/yes | 72 | 32 | 46.8 | 45.4 | 24.2 | 70.9 | 24.2 to 70.9 |
| claude | rq4/f3/no | 72 | 39 | 53.1 | 54.4 | 29.0 | 75.7 | 29.0 to 75.7 |
| claude | rq4/f3/na | 72 | 1 | 0.1 | 0.2 | 0.1 | 46.8 | 0.1 to 46.8 |
| claude | rq4/f4/yes | 72 | 53 | 68.7 | 73.6 | 39.2 | 85.9 | 39.2 to 85.9 |
| claude | rq4/f4/no | 72 | 19 | 31.3 | 26.4 | 14.1 | 60.8 | 14.1 to 60.8 |
| claude | rq4/f4/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f5/yes | 72 | 26 | 24.2 | 32.6 | 17.4 | 64.0 | 17.4 to 64.0 |
| claude | rq4/f5/no | 72 | 46 | 75.8 | 67.4 | 36.0 | 82.6 | 36.0 to 82.6 |
| claude | rq4/f5/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f6/yes | 72 | 12 | 11.7 | 14.5 | 7.7 | 54.4 | 7.7 to 54.4 |
| claude | rq4/f6/no | 72 | 25 | 35.8 | 35.8 | 19.1 | 65.8 | 19.1 to 65.8 |
| claude | rq4/f6/na | 72 | 35 | 52.5 | 49.7 | 26.5 | 73.2 | 26.5 to 73.2 |
| claude | rq4/f7/yes | 72 | 11 | 15.4 | 20.4 | 10.9 | 57.5 | 10.9 to 57.5 |
| claude | rq4/f7/no | 72 | 60 | 84.4 | 79.4 | 42.3 | 89.0 | 42.3 to 89.0 |
| claude | rq4/f7/na | 72 | 1 | 0.1 | 0.2 | 0.1 | 46.8 | 0.1 to 46.8 |
| claude | rq4/f8/yes | 72 | 24 | 28.4 | 37.1 | 19.8 | 66.5 | 19.8 to 66.5 |
| claude | rq4/f8/no | 72 | 48 | 71.6 | 62.9 | 33.5 | 80.2 | 33.5 to 80.2 |
| claude | rq4/f8/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f9/yes | 72 | 23 | 20.5 | 23.3 | 12.4 | 59.1 | 12.4 to 59.1 |
| claude | rq4/f9/no | 72 | 49 | 79.5 | 76.7 | 40.9 | 87.6 | 40.9 to 87.6 |
| claude | rq4/f9/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f10/yes | 72 | 53 | 77.9 | 77.3 | 41.2 | 87.9 | 41.2 to 87.9 |
| claude | rq4/f10/no | 72 | 19 | 22.1 | 22.7 | 12.1 | 58.8 | 12.1 to 58.8 |
| claude | rq4/f10/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f11/yes | 72 | 4 | 8.6 | 4.1 | 2.2 | 48.9 | 2.2 to 48.9 |
| claude | rq4/f11/no | 72 | 68 | 91.4 | 95.9 | 51.1 | 97.8 | 51.1 to 97.8 |
| claude | rq4/f11/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f12/yes | 72 | 38 | 52.5 | 49.5 | 26.4 | 73.1 | 26.4 to 73.1 |
| claude | rq4/f12/no | 72 | 34 | 47.5 | 50.5 | 26.9 | 73.6 | 26.9 to 73.6 |
| claude | rq4/f12/na | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f6_applicable/yes | 37 | 12 | 24.5 | 28.8 | 10.5 | 74.0 | 10.5 to 74.0 |
| claude | rq4/perturbation/wording | 72 | 26 | 24.2 | 32.6 | 17.4 | 64.0 | 17.4 to 64.0 |
| claude | rq4/perturbation/option_order | 72 | 11 | 10.9 | 13.5 | 7.2 | 53.9 | 7.2 to 53.9 |
| claude | rq4/perturbation/response_format | 72 | 7 | 5.7 | 8.0 | 4.2 | 50.9 | 4.2 to 50.9 |
| claude | rq4/perturbation/decoding | 72 | 11 | 15.4 | 20.4 | 10.9 | 57.5 | 10.9 to 57.5 |
| claude | rq4/perturbation/seeds | 72 | 4 | 6.3 | 5.2 | 2.8 | 49.4 | 2.8 to 49.4 |
| claude | rq4/perturbation/model_version | 72 | 18 | 21.1 | 28.3 | 15.1 | 61.8 | 15.1 to 61.8 |
| claude | rq4/perturbation/contamination | 72 | 8 | 8.1 | 9.9 | 5.3 | 52.0 | 5.3 to 52.0 |
| claude | rq4/perturbation/persona | 72 | 5 | 11.4 | 7.3 | 3.9 | 50.6 | 3.9 to 50.6 |
| claude | rq4/perturbation/language | 72 | 2 | 4.4 | 2.7 | 1.4 | 48.1 | 1.4 to 48.1 |
| claude | rq4/perturbation/other | 72 | 34 | 50.5 | 51.8 | 27.6 | 74.3 | 27.6 to 74.3 |
| claude | rq4/perturbation/none_listed | 72 | 14 | 23.0 | 20.2 | 10.8 | 57.4 | 10.8 to 57.4 |
| claude | rq4/robustness_outcome/survived | 72 | 14 | 12.5 | 15.9 | 8.5 | 55.2 | 8.5 to 55.2 |
| claude | rq4/robustness_outcome/weakened | 72 | 6 | 9.7 | 11.4 | 6.1 | 52.8 | 6.1 to 52.8 |
| claude | rq4/robustness_outcome/reversed | 72 | 2 | 1.0 | 1.6 | 0.8 | 47.5 | 0.8 to 47.5 |
| claude | rq4/robustness_outcome/mixed | 72 | 16 | 18.9 | 25.1 | 13.4 | 60.1 | 13.4 to 60.1 |
| claude | rq4/robustness_outcome/not_reported | 72 | 5 | 5.1 | 3.8 | 2.1 | 48.7 | 2.1 to 48.7 |
| claude | rq4/robustness_outcome/na | 72 | 29 | 52.8 | 42.2 | 22.5 | 69.2 | 22.5 to 69.2 |
| claude | rq4/robustness_tested/yes | 72 | 43 | 47.2 | 57.8 | 30.8 | 77.5 | 30.8 to 77.5 |
| claude | rq4/robustness_outcome_among_tested/survived | 43 | 14 | 26.5 | 27.5 | 10.9 | 71.2 | 10.9 to 71.2 |
| claude | rq4/robustness_outcome_among_tested/weakened | 43 | 6 | 20.5 | 19.7 | 7.8 | 68.1 | 7.8 to 68.1 |
| claude | rq4/robustness_outcome_among_tested/reversed | 43 | 2 | 2.1 | 2.7 | 1.1 | 61.3 | 1.1 to 61.3 |
| claude | rq4/robustness_outcome_among_tested/mixed | 43 | 16 | 40.1 | 43.4 | 17.3 | 77.5 | 17.3 to 77.5 |
| claude | rq4/robustness_outcome_among_tested/not_reported | 43 | 5 | 10.9 | 6.7 | 2.6 | 62.9 | 2.6 to 62.9 |
| claude | rq3/outcome_types/agreement | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq3/outcome_types/effect | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| claude | rq4/f12/not_reported | 72 | 0 | 0.0 | 0.0 | 0.0 | 46.7 | 0.0 to 46.7 |
| codex | rq3/types_any/none | 74 | 10 | 20.2 | 15.8 | 8.4 | 55.2 | 8.4 to 55.2 |
| codex | rq3/types_any/own_sample | 74 | 23 | 38.6 | 35.5 | 18.9 | 65.7 | 18.9 to 65.7 |
| codex | rq3/types_any/published_norms | 74 | 49 | 50.2 | 60.1 | 32.0 | 78.8 | 32.0 to 78.8 |
| codex | rq3/types_any/replication_dataset | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq3/types_any/crowd_norms | 74 | 4 | 4.6 | 5.5 | 2.9 | 49.8 | 2.9 to 49.8 |
| codex | rq3/primary_type/none | 74 | 9 | 19.5 | 14.6 | 7.8 | 54.6 | 7.8 to 54.6 |
| codex | rq3/primary_type/own_sample | 74 | 21 | 34.3 | 30.4 | 16.2 | 63.0 | 16.2 to 63.0 |
| codex | rq3/primary_type/published_norms | 74 | 42 | 43.9 | 52.2 | 27.8 | 74.6 | 27.8 to 74.6 |
| codex | rq3/primary_type/replication_dataset | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq3/primary_type/crowd_norms | 74 | 2 | 2.4 | 2.8 | 1.5 | 48.3 | 1.5 to 48.3 |
| codex | rq3/human_n/reported | 74 | 31 | 44.2 | 41.2 | 21.9 | 68.7 | 21.9 to 68.7 |
| codex | rq3/outcome_types/accuracy | 74 | 30 | 27.7 | 30.2 | 16.1 | 62.9 | 16.1 to 62.9 |
| codex | rq3/outcome_types/bias_magnitude | 74 | 49 | 74.9 | 72.5 | 38.6 | 85.4 | 38.6 to 85.4 |
| codex | rq3/outcome_types/effect_size | 74 | 24 | 38.1 | 34.7 | 18.4 | 65.2 | 18.4 to 65.2 |
| codex | rq3/outcome_types/choice_distribution | 74 | 30 | 49.9 | 51.4 | 27.3 | 74.1 | 27.3 to 74.1 |
| codex | rq3/outcome_types/human_correlation | 74 | 15 | 14.6 | 17.8 | 9.4 | 56.3 | 9.4 to 56.3 |
| codex | rq3/outcome_types/other | 74 | 23 | 33.0 | 31.7 | 16.9 | 63.7 | 16.9 to 63.7 |
| codex | rq4/f1/yes | 74 | 3 | 6.3 | 5.2 | 2.8 | 49.6 | 2.8 to 49.6 |
| codex | rq4/f1/no | 74 | 71 | 93.7 | 94.8 | 50.4 | 97.2 | 50.4 to 97.2 |
| codex | rq4/f1/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f2/yes | 74 | 36 | 49.9 | 53.3 | 28.4 | 75.2 | 28.4 to 75.2 |
| codex | rq4/f2/no | 74 | 36 | 49.8 | 46.3 | 24.6 | 71.4 | 24.6 to 71.4 |
| codex | rq4/f2/na | 74 | 2 | 0.3 | 0.4 | 0.2 | 47.0 | 0.2 to 47.0 |
| codex | rq4/f3/yes | 74 | 36 | 51.9 | 51.2 | 27.2 | 74.0 | 27.2 to 74.0 |
| codex | rq4/f3/no | 74 | 38 | 48.1 | 48.8 | 26.0 | 72.8 | 26.0 to 72.8 |
| codex | rq4/f3/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f4/yes | 74 | 58 | 68.5 | 74.7 | 39.8 | 86.6 | 39.8 to 86.6 |
| codex | rq4/f4/no | 74 | 16 | 31.5 | 25.3 | 13.4 | 60.2 | 13.4 to 60.2 |
| codex | rq4/f4/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f5/yes | 74 | 14 | 10.6 | 14.3 | 7.6 | 54.4 | 7.6 to 54.4 |
| codex | rq4/f5/no | 74 | 60 | 89.4 | 85.7 | 45.6 | 92.4 | 45.6 to 92.4 |
| codex | rq4/f5/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f6/yes | 74 | 16 | 12.1 | 15.4 | 8.2 | 55.0 | 8.2 to 55.0 |
| codex | rq4/f6/no | 74 | 25 | 41.2 | 40.6 | 21.6 | 68.4 | 21.6 to 68.4 |
| codex | rq4/f6/na | 74 | 33 | 46.7 | 44.0 | 23.4 | 70.2 | 23.4 to 70.2 |
| codex | rq4/f7/yes | 74 | 13 | 19.2 | 23.5 | 12.5 | 59.3 | 12.5 to 59.3 |
| codex | rq4/f7/no | 74 | 61 | 80.8 | 76.5 | 40.7 | 87.5 | 40.7 to 87.5 |
| codex | rq4/f7/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f8/yes | 74 | 28 | 34.4 | 42.8 | 22.8 | 69.6 | 22.8 to 69.6 |
| codex | rq4/f8/no | 74 | 46 | 65.6 | 57.2 | 30.4 | 77.2 | 30.4 to 77.2 |
| codex | rq4/f8/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f9/yes | 74 | 33 | 31.7 | 34.3 | 18.3 | 65.1 | 18.3 to 65.1 |
| codex | rq4/f9/no | 74 | 41 | 68.3 | 65.7 | 34.9 | 81.7 | 34.9 to 81.7 |
| codex | rq4/f9/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f10/yes | 74 | 65 | 91.8 | 89.5 | 47.6 | 94.4 | 47.6 to 94.4 |
| codex | rq4/f10/no | 74 | 9 | 8.2 | 10.5 | 5.6 | 52.4 | 5.6 to 52.4 |
| codex | rq4/f10/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f11/yes | 74 | 6 | 11.2 | 5.1 | 2.7 | 49.5 | 2.7 to 49.5 |
| codex | rq4/f11/no | 74 | 68 | 88.8 | 94.9 | 50.5 | 97.3 | 50.5 to 97.3 |
| codex | rq4/f11/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f12/yes | 74 | 48 | 61.6 | 60.3 | 32.1 | 78.9 | 32.1 to 78.9 |
| codex | rq4/f12/no | 74 | 25 | 36.3 | 37.2 | 19.8 | 66.6 | 19.8 to 66.6 |
| codex | rq4/f12/na | 74 | 0 | 0.0 | 0.0 | 0.0 | 46.8 | 0.0 to 46.8 |
| codex | rq4/f6_applicable/yes | 41 | 16 | 22.6 | 27.4 | 10.7 | 71.8 | 10.7 to 71.8 |
| codex | rq4/perturbation/wording | 74 | 30 | 29.4 | 31.6 | 16.8 | 63.6 | 16.8 to 63.6 |
| codex | rq4/perturbation/option_order | 74 | 16 | 14.0 | 16.3 | 8.7 | 55.5 | 8.7 to 55.5 |
| codex | rq4/perturbation/response_format | 74 | 10 | 11.3 | 14.4 | 7.7 | 54.5 | 7.7 to 54.5 |
| codex | rq4/perturbation/decoding | 74 | 21 | 27.7 | 34.4 | 18.3 | 65.1 | 18.3 to 65.1 |
| codex | rq4/perturbation/seeds | 74 | 14 | 26.5 | 22.5 | 12.0 | 58.8 | 12.0 to 58.8 |
| codex | rq4/perturbation/model_version | 74 | 19 | 19.5 | 24.5 | 13.0 | 59.8 | 13.0 to 59.8 |
| codex | rq4/perturbation/contamination | 74 | 20 | 24.9 | 24.8 | 13.2 | 60.0 | 13.2 to 60.0 |
| codex | rq4/perturbation/persona | 74 | 11 | 19.1 | 17.0 | 9.1 | 55.9 | 9.1 to 55.9 |
| codex | rq4/perturbation/language | 74 | 3 | 8.1 | 6.9 | 3.7 | 50.5 | 3.7 to 50.5 |
| codex | rq4/perturbation/other | 74 | 17 | 19.4 | 22.0 | 11.7 | 58.5 | 11.7 to 58.5 |
| codex | rq4/perturbation/none_listed | 74 | 4 | 5.3 | 5.3 | 2.8 | 49.6 | 2.8 to 49.6 |
| codex | rq4/robustness_outcome/survived | 74 | 10 | 10.9 | 13.9 | 7.4 | 54.2 | 7.4 to 54.2 |
| codex | rq4/robustness_outcome/weakened | 74 | 25 | 24.8 | 31.2 | 16.6 | 63.4 | 16.6 to 63.4 |
| codex | rq4/robustness_outcome/reversed | 74 | 2 | 0.5 | 0.8 | 0.4 | 47.2 | 0.4 to 47.2 |
| codex | rq4/robustness_outcome/mixed | 74 | 3 | 4.7 | 5.5 | 2.9 | 49.7 | 2.9 to 49.7 |
| codex | rq4/robustness_outcome/not_reported | 74 | 2 | 1.1 | 1.1 | 0.6 | 47.4 | 0.6 to 47.4 |
| codex | rq4/robustness_outcome/na | 74 | 32 | 58.1 | 47.4 | 25.2 | 72.0 | 25.2 to 72.0 |
| codex | rq4/robustness_tested/yes | 74 | 42 | 41.9 | 52.6 | 28.0 | 74.8 | 28.0 to 74.8 |
| codex | rq4/robustness_outcome_among_tested/survived | 42 | 10 | 26.0 | 26.4 | 9.9 | 72.4 | 9.9 to 72.4 |
| codex | rq4/robustness_outcome_among_tested/weakened | 42 | 25 | 59.1 | 59.4 | 22.2 | 84.8 | 22.2 to 84.8 |
| codex | rq4/robustness_outcome_among_tested/reversed | 42 | 2 | 1.2 | 1.6 | 0.6 | 63.2 | 0.6 to 63.2 |
| codex | rq4/robustness_outcome_among_tested/mixed | 42 | 3 | 11.1 | 10.5 | 3.9 | 66.5 | 3.9 to 66.5 |
| codex | rq4/robustness_outcome_among_tested/not_reported | 42 | 2 | 2.5 | 2.2 | 0.8 | 63.4 | 0.8 to 63.4 |
| codex | rq3/outcome_types/agreement | 74 | 1 | 0.1 | 0.2 | 0.1 | 46.9 | 0.1 to 46.9 |
| codex | rq3/outcome_types/effect | 74 | 1 | 0.1 | 0.2 | 0.1 | 46.9 | 0.1 to 46.9 |
| codex | rq4/f12/not_reported | 74 | 1 | 2.1 | 2.5 | 1.3 | 48.1 | 1.3 to 48.1 |
