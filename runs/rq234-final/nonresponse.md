# Nonresponse (protocol v0.9.1): respondents vs nonrespondents

Respondent = full text obtained (open copy now; eGateway copies will be added on rerun). Nonrespondent = no full text. Interim run. Response rates are unweighted counts with Wilson 95% intervals; the permutation p-value (5,000 permutations, seed 20261016) is a secondary descriptive column, not a result.


## By flag (RQ1 abstract coder)

| flag (RQ1 abstract coder) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| no | 23 | 14 | 9 | 60.9 | 40.8 to 77.8 |
| unclear | 46 | 29 | 17 | 63.0 | 48.6 to 75.5 |
| yes | 81 | 67 | 14 | 82.7 | 73.1 to 89.4 |

Permutation p (secondary): 0.018


## By paradigm family (stratum)

| paradigm family (stratum) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| DEV | 5 | 5 | 0 | 100.0 | 56.6 to 100.0 |
| HB | 15 | 11 | 4 | 73.3 | 48.0 to 89.1 |
| JDM | 16 | 12 | 4 | 75.0 | 50.5 to 89.8 |
| LANG | 20 | 14 | 6 | 70.0 | 48.1 to 85.5 |
| LEARN | 8 | 7 | 1 | 87.5 | 52.9 to 97.8 |
| MEM | 11 | 11 | 0 | 100.0 | 74.1 to 100.0 |
| MOR | 14 | 9 | 5 | 64.3 | 38.8 to 83.7 |
| NUM | 4 | 3 | 1 | 75.0 | 30.1 to 95.4 |
| OTH | 15 | 6 | 9 | 40.0 | 19.8 to 64.3 |
| RE | 9 | 7 | 2 | 77.8 | 45.3 to 93.7 |
| TOM | 17 | 15 | 2 | 88.2 | 65.7 to 96.7 |
| none | 16 | 10 | 6 | 62.5 | 38.6 to 81.5 |

Permutation p (secondary): 0.059


## By year

| year | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| 2024 | 32 | 26 | 6 | 81.2 | 64.7 to 91.1 |
| 2025 | 27 | 16 | 11 | 59.3 | 40.7 to 75.5 |
| 2026 | 56 | 39 | 17 | 69.6 | 56.7 to 80.1 |
| <=2023 | 35 | 29 | 6 | 82.9 | 67.3 to 91.9 |

Permutation p (secondary): 0.119


## By venue type (OpenAlex type)

| venue type (OpenAlex type) | analysed | respondents (full text) | nonrespondents | response % | Wilson 95% (%) |
|---|---|---|---|---|---|
| article | 35 | 24 | 11 | 68.6 | 52.0 to 81.4 |
| book-chapter | 2 | 1 | 1 | 50.0 | 9.5 to 90.5 |
| conference-paper | 39 | 33 | 6 | 84.6 | 70.3 to 92.8 |
| dataset | 3 | 0 | 3 | 0.0 | 0.0 to 56.1 |
| dissertation | 1 | 0 | 1 | 0.0 | 0.0 to 79.3 |
| preprint | 69 | 52 | 17 | 75.4 | 64.0 to 84.0 |
| software | 1 | 0 | 1 | 0.0 | 0.0 to 79.3 |

Permutation p (secondary): 0.004


## Pending and unresolved records (interim)

| coder | coded_ineligible | coded_eligible | no_full_text |
|---|---|---|---|
| claude | 30 | 80 | 40 |
| codex | 29 | 81 | 40 |

In this interim run records with a full text but no usable extraction (pending_extraction) and records with an unresolved eligibility decision (coded_unclear) are treated like nonrespondents (their weight is redistributed within stratum; they enter the bounds as unknown).


## Eligible share of the frame (2,022 liberal-eligible records)

| coder | n_analysed | n_respondents | n_eligible_respondents | n_unknown_status | est_share_of_frame_pct | lo_pct | hi_pct | N_hat_eligible | frame_N | bound_all_unknown_ineligible_pct | bound_all_unknown_eligible_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | 150 | 110 | 80 | 40 | 67.03 | 58.18 | 75.88 | 1355.3 | 2022 | 46.66 | 78.61 |
| codex | 150 | 110 | 81 | 40 | 65.61 | 56.38 | 74.83 | 1326.6 | 2022 | 45.91 | 77.86 |


Point estimate: design-weighted with within-stratum response-propensity weights (N_g / r_g). Bounds: unadjusted sampling weights N_h / n_analysed_h; lower = every unknown-status analysed record ineligible, upper = every one eligible.


## Bounds on prevalences among eligible studies (every RQ3 and RQ4 row: items, perturbation types, comparison types, robustness outcomes)

Scenario A: all unknown-status records ineligible (prevalence among observed eligible, sampling weights only). Scenario B: all unknown-status records eligible, with none / all of them having the outcome. Overall bounds are the minimum and maximum of the three.

| coder | feature | n_domain | k | est_pct | all_unknown_ineligible_pct | all_unknown_eligible_none_have_outcome_pct | all_unknown_eligible_all_have_outcome_pct | overall_bounds_pct |
|---|---|---|---|---|---|---|---|---|
| claude | rq3/types_any/none | 80 | 17 | 21.7 | 22.3 | 13.2 | 53.9 | 13.2 to 53.9 |
| claude | rq3/types_any/own_sample | 80 | 24 | 35.0 | 31.6 | 18.7 | 59.4 | 18.7 to 59.4 |
| claude | rq3/types_any/published_norms | 80 | 42 | 46.0 | 48.9 | 29.0 | 69.7 | 29.0 to 69.7 |
| claude | rq3/types_any/replication_dataset | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq3/types_any/crowd_norms | 80 | 3 | 3.3 | 3.9 | 2.3 | 43.0 | 2.3 to 43.0 |
| claude | rq3/primary_type/none | 80 | 17 | 21.7 | 22.3 | 13.2 | 53.9 | 13.2 to 53.9 |
| claude | rq3/primary_type/own_sample | 80 | 23 | 32.7 | 29.3 | 17.4 | 58.0 | 17.4 to 58.0 |
| claude | rq3/primary_type/published_norms | 80 | 37 | 42.3 | 44.5 | 26.4 | 67.1 | 26.4 to 67.1 |
| claude | rq3/primary_type/replication_dataset | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq3/primary_type/crowd_norms | 80 | 3 | 3.3 | 3.9 | 2.3 | 43.0 | 2.3 to 43.0 |
| claude | rq3/human_n/reported | 80 | 32 | 40.4 | 37.9 | 22.5 | 63.2 | 22.5 to 63.2 |
| claude | rq3/outcome_types/accuracy | 80 | 36 | 35.6 | 39.0 | 23.1 | 63.8 | 23.1 to 63.8 |
| claude | rq3/outcome_types/bias_magnitude | 80 | 19 | 25.8 | 27.1 | 16.1 | 56.7 | 16.1 to 56.7 |
| claude | rq3/outcome_types/effect_size | 80 | 28 | 44.5 | 42.5 | 25.2 | 65.9 | 25.2 to 65.9 |
| claude | rq3/outcome_types/choice_distribution | 80 | 25 | 35.4 | 35.1 | 20.8 | 61.5 | 20.8 to 61.5 |
| claude | rq3/outcome_types/human_correlation | 80 | 15 | 14.7 | 16.5 | 9.8 | 50.4 | 9.8 to 50.4 |
| claude | rq3/outcome_types/other | 80 | 20 | 28.2 | 24.3 | 14.4 | 55.1 | 14.4 to 55.1 |
| claude | rq4/f1/yes | 80 | 15 | 25.0 | 23.9 | 14.2 | 54.9 | 14.2 to 54.9 |
| claude | rq4/f1/no | 80 | 65 | 75.0 | 76.1 | 45.1 | 85.8 | 45.1 to 85.8 |
| claude | rq4/f1/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f2/yes | 80 | 31 | 42.2 | 44.5 | 26.4 | 67.0 | 26.4 to 67.0 |
| claude | rq4/f2/no | 80 | 44 | 52.2 | 49.8 | 29.6 | 70.2 | 29.6 to 70.2 |
| claude | rq4/f2/na | 80 | 5 | 5.6 | 5.7 | 3.4 | 44.0 | 3.4 to 44.0 |
| claude | rq4/f3/yes | 80 | 38 | 52.4 | 47.9 | 28.4 | 69.1 | 28.4 to 69.1 |
| claude | rq4/f3/no | 80 | 41 | 47.5 | 51.9 | 30.8 | 71.4 | 30.8 to 71.4 |
| claude | rq4/f3/na | 80 | 1 | 0.1 | 0.2 | 0.1 | 40.8 | 0.1 to 40.8 |
| claude | rq4/f4/yes | 80 | 56 | 68.6 | 69.1 | 41.0 | 81.7 | 41.0 to 81.7 |
| claude | rq4/f4/no | 80 | 24 | 31.4 | 30.9 | 18.3 | 59.0 | 18.3 to 59.0 |
| claude | rq4/f4/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f5/yes | 80 | 27 | 24.4 | 30.2 | 17.9 | 58.6 | 17.9 to 58.6 |
| claude | rq4/f5/no | 80 | 53 | 75.6 | 69.8 | 41.4 | 82.1 | 41.4 to 82.1 |
| claude | rq4/f5/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f6/yes | 80 | 14 | 13.3 | 14.7 | 8.7 | 49.4 | 8.7 to 49.4 |
| claude | rq4/f6/no | 80 | 26 | 31.8 | 33.7 | 20.0 | 60.6 | 20.0 to 60.6 |
| claude | rq4/f6/na | 80 | 40 | 54.9 | 51.6 | 30.6 | 71.3 | 30.6 to 71.3 |
| claude | rq4/f7/yes | 80 | 12 | 17.3 | 19.9 | 11.8 | 52.5 | 11.8 to 52.5 |
| claude | rq4/f7/no | 80 | 67 | 82.6 | 79.9 | 47.4 | 88.1 | 47.4 to 88.1 |
| claude | rq4/f7/na | 80 | 1 | 0.1 | 0.2 | 0.1 | 40.8 | 0.1 to 40.8 |
| claude | rq4/f8/yes | 80 | 27 | 33.6 | 37.1 | 22.0 | 62.6 | 22.0 to 62.6 |
| claude | rq4/f8/no | 80 | 53 | 66.4 | 62.9 | 37.4 | 78.0 | 37.4 to 78.0 |
| claude | rq4/f8/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f9/yes | 80 | 26 | 20.7 | 23.6 | 14.0 | 54.6 | 14.0 to 54.6 |
| claude | rq4/f9/no | 80 | 54 | 79.3 | 76.4 | 45.4 | 86.0 | 45.4 to 86.0 |
| claude | rq4/f9/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f10/yes | 80 | 58 | 75.9 | 75.6 | 44.9 | 85.5 | 44.9 to 85.5 |
| claude | rq4/f10/no | 80 | 22 | 24.1 | 24.4 | 14.5 | 55.1 | 14.5 to 55.1 |
| claude | rq4/f10/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f11/yes | 80 | 5 | 5.3 | 3.9 | 2.3 | 42.9 | 2.3 to 42.9 |
| claude | rq4/f11/no | 80 | 75 | 94.7 | 96.1 | 57.1 | 97.7 | 57.1 to 97.7 |
| claude | rq4/f11/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f12/yes | 80 | 41 | 46.4 | 47.1 | 28.0 | 68.6 | 28.0 to 68.6 |
| claude | rq4/f12/no | 80 | 39 | 53.6 | 52.9 | 31.4 | 72.0 | 31.4 to 72.0 |
| claude | rq4/f12/na | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f6_applicable/yes | 40 | 14 | 29.5 | 30.4 | 12.6 | 71.2 | 12.6 to 71.2 |
| claude | rq4/perturbation/wording | 80 | 27 | 24.4 | 30.2 | 17.9 | 58.6 | 17.9 to 58.6 |
| claude | rq4/perturbation/option_order | 80 | 13 | 12.6 | 13.8 | 8.2 | 48.8 | 8.2 to 48.8 |
| claude | rq4/perturbation/response_format | 80 | 8 | 5.8 | 7.3 | 4.4 | 45.0 | 4.4 to 45.0 |
| claude | rq4/perturbation/decoding | 80 | 12 | 17.3 | 19.9 | 11.8 | 52.5 | 11.8 to 52.5 |
| claude | rq4/perturbation/seeds | 80 | 5 | 6.9 | 5.5 | 3.3 | 43.9 | 3.3 to 43.9 |
| claude | rq4/perturbation/model_version | 80 | 21 | 26.7 | 29.1 | 17.3 | 57.9 | 17.3 to 57.9 |
| claude | rq4/perturbation/contamination | 80 | 9 | 8.7 | 9.8 | 5.8 | 46.5 | 5.8 to 46.5 |
| claude | rq4/perturbation/persona | 80 | 5 | 8.2 | 6.6 | 3.9 | 44.6 | 3.9 to 44.6 |
| claude | rq4/perturbation/language | 80 | 2 | 2.4 | 2.4 | 1.4 | 42.1 | 1.4 to 42.1 |
| claude | rq4/perturbation/other | 80 | 35 | 43.6 | 47.4 | 28.2 | 68.8 | 28.2 to 68.8 |
| claude | rq4/perturbation/none_listed | 80 | 17 | 25.2 | 22.9 | 13.6 | 54.2 | 13.6 to 54.2 |
| claude | rq4/robustness_outcome/survived | 80 | 17 | 17.5 | 17.2 | 10.2 | 50.8 | 10.2 to 50.8 |
| claude | rq4/robustness_outcome/weakened | 80 | 7 | 11.3 | 11.9 | 7.0 | 47.7 | 7.0 to 47.7 |
| claude | rq4/robustness_outcome/reversed | 80 | 2 | 1.0 | 1.4 | 0.8 | 41.5 | 0.8 to 41.5 |
| claude | rq4/robustness_outcome/mixed | 80 | 17 | 19.4 | 23.4 | 13.9 | 54.6 | 13.9 to 54.6 |
| claude | rq4/robustness_outcome/not_reported | 80 | 5 | 4.9 | 3.5 | 2.1 | 42.7 | 2.1 to 42.7 |
| claude | rq4/robustness_outcome/na | 80 | 32 | 45.9 | 42.7 | 25.3 | 66.0 | 25.3 to 66.0 |
| claude | rq4/robustness_tested/yes | 80 | 48 | 54.1 | 57.3 | 34.0 | 74.7 | 34.0 to 74.7 |
| claude | rq4/robustness_outcome_among_tested/survived | 48 | 17 | 32.3 | 29.9 | 13.6 | 68.1 | 13.6 to 68.1 |
| claude | rq4/robustness_outcome_among_tested/weakened | 48 | 7 | 20.8 | 20.7 | 9.4 | 63.9 | 9.4 to 63.9 |
| claude | rq4/robustness_outcome_among_tested/reversed | 48 | 2 | 1.8 | 2.5 | 1.1 | 55.6 | 1.1 to 55.6 |
| claude | rq4/robustness_outcome_among_tested/mixed | 48 | 17 | 35.9 | 40.9 | 18.6 | 73.1 | 18.6 to 73.1 |
| claude | rq4/robustness_outcome_among_tested/not_reported | 48 | 5 | 9.1 | 6.0 | 2.7 | 57.2 | 2.7 to 57.2 |
| claude | rq3/outcome_types/agreement | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq3/outcome_types/effect | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| claude | rq4/f12/not_reported | 80 | 0 | 0.0 | 0.0 | 0.0 | 40.6 | 0.0 to 40.6 |
| codex | rq3/types_any/none | 81 | 13 | 20.8 | 19.1 | 11.3 | 52.3 | 11.3 to 52.3 |
| codex | rq3/types_any/own_sample | 81 | 25 | 35.7 | 34.1 | 20.1 | 61.2 | 20.1 to 61.2 |
| codex | rq3/types_any/published_norms | 81 | 51 | 52.7 | 57.1 | 33.7 | 74.7 | 33.7 to 74.7 |
| codex | rq3/types_any/replication_dataset | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq3/types_any/crowd_norms | 81 | 4 | 4.5 | 5.0 | 3.0 | 44.0 | 3.0 to 44.0 |
| codex | rq3/primary_type/none | 81 | 12 | 20.0 | 18.0 | 10.6 | 51.7 | 10.6 to 51.7 |
| codex | rq3/primary_type/own_sample | 81 | 23 | 31.2 | 29.6 | 17.4 | 58.5 | 17.4 to 58.5 |
| codex | rq3/primary_type/published_norms | 81 | 44 | 46.3 | 49.9 | 29.4 | 70.5 | 29.4 to 70.5 |
| codex | rq3/primary_type/replication_dataset | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq3/primary_type/crowd_norms | 81 | 2 | 2.4 | 2.5 | 1.5 | 42.5 | 1.5 to 42.5 |
| codex | rq3/human_n/reported | 81 | 34 | 42.3 | 40.2 | 23.7 | 64.8 | 23.7 to 64.8 |
| codex | rq3/outcome_types/accuracy | 81 | 31 | 25.6 | 28.4 | 16.7 | 57.8 | 16.7 to 57.8 |
| codex | rq3/outcome_types/bias_magnitude | 81 | 55 | 73.6 | 73.3 | 43.2 | 84.3 | 43.2 to 84.3 |
| codex | rq3/outcome_types/effect_size | 81 | 25 | 35.4 | 33.2 | 19.6 | 60.6 | 19.6 to 60.6 |
| codex | rq3/outcome_types/choice_distribution | 81 | 35 | 54.7 | 53.3 | 31.5 | 72.5 | 31.5 to 72.5 |
| codex | rq3/outcome_types/human_correlation | 81 | 15 | 14.9 | 16.1 | 9.5 | 50.6 | 9.5 to 50.6 |
| codex | rq3/outcome_types/other | 81 | 24 | 32.0 | 30.5 | 18.0 | 59.0 | 18.0 to 59.0 |
| codex | rq4/f1/yes | 81 | 4 | 8.1 | 6.5 | 3.8 | 44.9 | 3.8 to 44.9 |
| codex | rq4/f1/no | 81 | 77 | 91.9 | 93.5 | 55.1 | 96.2 | 55.1 to 96.2 |
| codex | rq4/f1/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f2/yes | 81 | 38 | 50.0 | 51.6 | 30.4 | 71.5 | 30.4 to 71.5 |
| codex | rq4/f2/no | 81 | 41 | 49.7 | 48.0 | 28.3 | 69.3 | 28.3 to 69.3 |
| codex | rq4/f2/na | 81 | 2 | 0.3 | 0.4 | 0.2 | 41.3 | 0.2 to 41.3 |
| codex | rq4/f3/yes | 81 | 41 | 55.3 | 52.6 | 31.0 | 72.0 | 31.0 to 72.0 |
| codex | rq4/f3/no | 81 | 40 | 44.7 | 47.4 | 28.0 | 69.0 | 28.0 to 69.0 |
| codex | rq4/f3/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f4/yes | 81 | 63 | 74.3 | 74.6 | 44.0 | 85.0 | 44.0 to 85.0 |
| codex | rq4/f4/no | 81 | 18 | 25.7 | 25.4 | 15.0 | 56.0 | 15.0 to 56.0 |
| codex | rq4/f4/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f5/yes | 81 | 14 | 10.7 | 13.0 | 7.7 | 48.7 | 7.7 to 48.7 |
| codex | rq4/f5/no | 81 | 67 | 89.3 | 87.0 | 51.3 | 92.3 | 51.3 to 92.3 |
| codex | rq4/f5/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f6/yes | 81 | 17 | 12.1 | 14.1 | 8.3 | 49.4 | 8.3 to 49.4 |
| codex | rq4/f6/no | 81 | 28 | 45.5 | 41.7 | 24.6 | 65.7 | 24.6 to 65.7 |
| codex | rq4/f6/na | 81 | 36 | 42.4 | 44.1 | 26.0 | 67.0 | 26.0 to 67.0 |
| codex | rq4/f7/yes | 81 | 14 | 21.6 | 23.0 | 13.6 | 54.6 | 13.6 to 54.6 |
| codex | rq4/f7/no | 81 | 67 | 78.4 | 77.0 | 45.4 | 86.4 | 45.4 to 86.4 |
| codex | rq4/f7/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f8/yes | 81 | 30 | 37.7 | 41.5 | 24.5 | 65.5 | 24.5 to 65.5 |
| codex | rq4/f8/no | 81 | 51 | 62.3 | 58.5 | 34.5 | 75.5 | 34.5 to 75.5 |
| codex | rq4/f8/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f9/yes | 81 | 35 | 29.2 | 32.3 | 19.0 | 60.1 | 19.0 to 60.1 |
| codex | rq4/f9/no | 81 | 46 | 70.8 | 67.7 | 39.9 | 81.0 | 39.9 to 81.0 |
| codex | rq4/f9/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f10/yes | 81 | 70 | 88.1 | 87.3 | 51.4 | 92.5 | 51.4 to 92.5 |
| codex | rq4/f10/no | 81 | 11 | 11.9 | 12.7 | 7.5 | 48.6 | 7.5 to 48.6 |
| codex | rq4/f10/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f11/yes | 81 | 7 | 6.3 | 4.8 | 2.8 | 43.9 | 2.8 to 43.9 |
| codex | rq4/f11/no | 81 | 74 | 93.7 | 95.2 | 56.1 | 97.2 | 56.1 to 97.2 |
| codex | rq4/f11/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f12/yes | 81 | 53 | 62.6 | 60.7 | 35.8 | 76.8 | 35.8 to 76.8 |
| codex | rq4/f12/no | 81 | 26 | 33.6 | 35.4 | 20.9 | 61.9 | 20.9 to 61.9 |
| codex | rq4/f12/na | 81 | 0 | 0.0 | 0.0 | 0.0 | 41.0 | 0.0 to 41.0 |
| codex | rq4/f6_applicable/yes | 45 | 17 | 21.0 | 25.3 | 11.3 | 66.7 | 11.3 to 66.7 |
| codex | rq4/perturbation/wording | 81 | 32 | 28.9 | 31.2 | 18.4 | 59.4 | 18.4 to 59.4 |
| codex | rq4/perturbation/option_order | 81 | 18 | 16.1 | 16.5 | 9.7 | 50.8 | 9.7 to 50.8 |
| codex | rq4/perturbation/response_format | 81 | 11 | 11.8 | 13.3 | 7.8 | 48.9 | 7.8 to 48.9 |
| codex | rq4/perturbation/decoding | 81 | 22 | 30.2 | 32.9 | 19.4 | 60.4 | 19.4 to 60.4 |
| codex | rq4/perturbation/seeds | 81 | 14 | 23.6 | 20.4 | 12.0 | 53.1 | 12.0 to 53.1 |
| codex | rq4/perturbation/model_version | 81 | 20 | 20.5 | 23.2 | 13.7 | 54.7 | 13.7 to 54.7 |
| codex | rq4/perturbation/contamination | 81 | 22 | 22.5 | 23.6 | 13.9 | 55.0 | 13.9 to 55.0 |
| codex | rq4/perturbation/persona | 81 | 12 | 18.0 | 17.1 | 10.1 | 51.1 | 10.1 to 51.1 |
| codex | rq4/perturbation/language | 81 | 3 | 6.5 | 6.3 | 3.7 | 44.7 | 3.7 to 44.7 |
| codex | rq4/perturbation/other | 81 | 17 | 18.0 | 19.9 | 11.8 | 52.8 | 11.8 to 52.8 |
| codex | rq4/perturbation/none_listed | 81 | 6 | 9.7 | 8.1 | 4.8 | 45.8 | 4.8 to 45.8 |
| codex | rq4/robustness_outcome/survived | 81 | 13 | 14.8 | 16.0 | 9.4 | 50.5 | 9.4 to 50.5 |
| codex | rq4/robustness_outcome/weakened | 81 | 27 | 27.7 | 30.9 | 18.2 | 59.2 | 18.2 to 59.2 |
| codex | rq4/robustness_outcome/reversed | 81 | 2 | 0.5 | 0.8 | 0.4 | 41.5 | 0.4 to 41.5 |
| codex | rq4/robustness_outcome/mixed | 81 | 3 | 4.8 | 5.0 | 3.0 | 44.0 | 3.0 to 44.0 |
| codex | rq4/robustness_outcome/not_reported | 81 | 2 | 1.1 | 1.0 | 0.6 | 41.7 | 0.6 to 41.7 |
| codex | rq4/robustness_outcome/na | 81 | 34 | 51.0 | 46.3 | 27.3 | 68.3 | 27.3 to 68.3 |
| codex | rq4/robustness_tested/yes | 81 | 47 | 49.0 | 53.7 | 31.7 | 72.7 | 31.7 to 72.7 |
| codex | rq4/robustness_outcome_among_tested/survived | 47 | 13 | 30.3 | 29.8 | 13.0 | 69.4 | 13.0 to 69.4 |
| codex | rq4/robustness_outcome_among_tested/weakened | 47 | 27 | 56.7 | 57.5 | 25.0 | 81.5 | 25.0 to 81.5 |
| codex | rq4/robustness_outcome_among_tested/reversed | 47 | 2 | 1.1 | 1.4 | 0.6 | 57.1 | 0.6 to 57.1 |
| codex | rq4/robustness_outcome_among_tested/mixed | 47 | 3 | 9.7 | 9.4 | 4.1 | 60.5 | 4.1 to 60.5 |
| codex | rq4/robustness_outcome_among_tested/not_reported | 47 | 2 | 2.2 | 1.9 | 0.8 | 57.3 | 0.8 to 57.3 |
| codex | rq3/outcome_types/agreement | 81 | 1 | 0.2 | 0.2 | 0.1 | 41.2 | 0.1 to 41.2 |
| codex | rq3/outcome_types/effect | 81 | 1 | 0.2 | 0.2 | 0.1 | 41.2 | 0.1 to 41.2 |
| codex | rq4/f12/not_reported | 81 | 2 | 3.8 | 3.9 | 2.3 | 43.3 | 2.3 to 43.3 |
