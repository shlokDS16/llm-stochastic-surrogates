# Sensitivity: merged groups versus original strata (amendment v0.12.1 item 1)

Merged = the main analysis (strata with fewer than 2 respondents merged with the same family's adjacent period, later first; weights N_g / r_g and variance on the merged groups). Original = the 32 sampling strata as drawn. The original-strata columns are a LIMITED COMPARISON: a stratum with exactly 1 respondent carries its weight N_h / 1 in the point estimate but contributes no variance term (dropped from the variance only); a stratum with 0 respondents has no weight and is left out of the point estimate and of the frame denominator (so the original eligible share refers to the frame minus those strata). The original intervals therefore understate the variance and are not a validated alternative.


## Merged strata

| coder | merged | into | reason | a | r |
|---|---|---|---|---|---|
| claude | JDM/2024 | JDM/2025-2026 | adjacent period JDM/2025-2026 | 1 | 1 |
| claude | OTH/2024 | OTH/2025-2026 | adjacent period OTH/2025-2026 | 2 | 1 |
| claude | RE/2024 | RE/2025-2026 | adjacent period RE/2025-2026 | 2 | 1 |
| claude | MOR/2024 | MOR/2025-2026 | adjacent period MOR/2025-2026 | 3 | 1 |
| codex | JDM/2024 | JDM/2025-2026 | adjacent period JDM/2025-2026 | 1 | 1 |
| codex | OTH/2024 | OTH/2025-2026 | adjacent period OTH/2025-2026 | 2 | 1 |
| codex | RE/2024 | RE/2025-2026 | adjacent period RE/2025-2026 | 2 | 1 |
| codex | MOR/2024 | MOR/2025-2026 | adjacent period MOR/2025-2026 | 3 | 1 |


claude: 32 original strata, 28 merged groups; original strata with 1 respondent (no variance term): 4; with 0 respondents (outside the point estimate): 0; frame covered by the original point estimate 2022 of 2022; df merged 82, original 78.


codex: 32 original strata, 28 merged groups; original strata with 1 respondent (no variance term): 4; with 0 respondents (outside the point estimate): 0; frame covered by the original point estimate 2022 of 2022; df merged 82, original 78.


## Main estimates (percent); all RQ4 features are in sensitivity_merge.csv

| coder | estimand | feature | k | n_domain | merged_est_pct | merged_lo_pct | merged_hi_pct | limited_comparison_orig_est_pct | limited_comparison_orig_lo_pct | limited_comparison_orig_hi_pct | diff_est_pct_points | ci_width_ratio_merged_over_orig |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | eligible share of frame | ELIGIBLE_SHARE | 80 | 110 | 67.03 | 58.176 | 75.883 | 66.402 | 59.093 | 73.712 | 0.628 | 1.211 |
| claude | RQ2 any row by outcome kind | rq2/effect/ANY | 45 | 80 | 62.589 | 49.878 | 75.301 | 65.275 | 55.361 | 75.189 | -2.686 | 1.282 |
| claude | RQ2 any row by outcome kind | rq2/accuracy/ANY | 31 | 80 | 36.18 | 23.942 | 48.419 | 33.359 | 24.325 | 42.393 | 2.821 | 1.355 |
| claude | RQ2 any row by outcome kind | rq2/agreement/ANY | 14 | 80 | 9.802 | 3.621 | 15.983 | 9.969 | 3.655 | 16.284 | -0.167 | 0.979 |
| claude | RQ4 item prevalence among eligible | rq4/f1/yes | 15 | 80 | 25.023 | 13.724 | 36.321 | 24.019 | 13.923 | 34.115 | 1.004 | 1.119 |
| claude | RQ4 item prevalence among eligible | rq4/f2/yes | 31 | 80 | 42.193 | 30.338 | 54.048 | 41.644 | 30.58 | 52.709 | 0.549 | 1.071 |
| claude | RQ4 item prevalence among eligible | rq4/f3/yes | 38 | 80 | 52.353 | 38.787 | 65.919 | 50.952 | 37.266 | 64.638 | 1.401 | 0.991 |
| claude | RQ4 item prevalence among eligible | rq4/f4/yes | 56 | 80 | 68.62 | 56.212 | 81.028 | 67.838 | 54.953 | 80.722 | 0.782 | 0.963 |
| claude | RQ4 item prevalence among eligible | rq4/f5/yes | 27 | 80 | 24.376 | 14.41 | 34.341 | 25.023 | 15.605 | 34.44 | -0.647 | 1.058 |
| claude | RQ4 item prevalence among eligible | rq4/f6/yes | 14 | 80 | 13.275 | 4.552 | 21.998 | 13.303 | 4.673 | 21.932 | -0.028 | 1.011 |
| claude | RQ4 item prevalence among eligible | rq4/f7/yes | 12 | 80 | 17.253 | 8.359 | 26.147 | 17.832 | 9.514 | 26.151 | -0.579 | 1.069 |
| claude | RQ4 item prevalence among eligible | rq4/f8/yes | 27 | 80 | 33.635 | 21.68 | 45.59 | 32.522 | 22.971 | 42.073 | 1.114 | 1.252 |
| claude | RQ4 item prevalence among eligible | rq4/f9/yes | 26 | 80 | 20.683 | 11.405 | 29.961 | 20.83 | 11.64 | 30.02 | -0.147 | 1.01 |
| claude | RQ4 item prevalence among eligible | rq4/f10/yes | 58 | 80 | 75.91 | 65.059 | 86.761 | 76.799 | 67.251 | 86.348 | -0.89 | 1.136 |
| claude | RQ4 item prevalence among eligible | rq4/f11/yes | 5 | 80 | 5.294 | 0.0 | 12.408 | 5.927 | 0.0 | 14.198 | -0.633 | 0.874 |
| claude | RQ4 item prevalence among eligible | rq4/f12/yes | 41 | 80 | 46.44 | 32.865 | 60.015 | 46.098 | 32.447 | 59.749 | 0.341 | 0.994 |
| claude | RQ4 item prevalence among eligible | rq4/f6_applicable/yes | 14 | 40 | 29.464 | 12.39 | 46.538 | 29.262 | 12.329 | 46.196 | 0.201 | 1.008 |
| claude | RQ4 item prevalence among eligible | rq4/robustness_tested/yes | 48 | 80 | 54.078 | 41.228 | 66.928 | 51.917 | 41.359 | 62.475 | 2.161 | 1.217 |
| codex | eligible share of frame | ELIGIBLE_SHARE | 81 | 110 | 65.609 | 56.384 | 74.834 | 65.914 | 59.359 | 72.469 | -0.304 | 1.407 |
| codex | RQ2 any row by outcome kind | rq2/effect/ANY | 52 | 81 | 71.943 | 61.384 | 82.502 | 73.198 | 64.317 | 82.079 | -1.255 | 1.189 |
| codex | RQ2 any row by outcome kind | rq2/accuracy/ANY | 32 | 81 | 30.275 | 18.58 | 41.969 | 28.836 | 18.607 | 39.065 | 1.439 | 1.143 |
| codex | RQ2 any row by outcome kind | rq2/agreement/ANY | 18 | 81 | 20.537 | 10.127 | 30.948 | 20.544 | 10.456 | 30.631 | -0.006 | 1.032 |
| codex | RQ4 item prevalence among eligible | rq4/f1/yes | 4 | 81 | 8.092 | 0.0 | 16.88 | 8.593 | 0.0 | 18.325 | -0.501 | 0.921 |
| codex | RQ4 item prevalence among eligible | rq4/f2/yes | 38 | 81 | 49.995 | 37.111 | 62.879 | 48.46 | 36.869 | 60.051 | 1.535 | 1.112 |
| codex | RQ4 item prevalence among eligible | rq4/f3/yes | 41 | 81 | 55.28 | 41.762 | 68.799 | 54.355 | 41.079 | 67.632 | 0.925 | 1.018 |
| codex | RQ4 item prevalence among eligible | rq4/f4/yes | 63 | 81 | 74.265 | 62.378 | 86.153 | 72.914 | 60.974 | 84.853 | 1.352 | 0.996 |
| codex | RQ4 item prevalence among eligible | rq4/f5/yes | 14 | 81 | 10.719 | 4.274 | 17.165 | 10.745 | 4.334 | 17.156 | -0.026 | 1.005 |
| codex | RQ4 item prevalence among eligible | rq4/f6/yes | 17 | 81 | 12.119 | 4.3 | 19.937 | 12.039 | 4.419 | 19.659 | 0.079 | 1.026 |
| codex | RQ4 item prevalence among eligible | rq4/f7/yes | 14 | 81 | 21.64 | 11.714 | 31.567 | 21.66 | 12.806 | 30.514 | -0.019 | 1.121 |
| codex | RQ4 item prevalence among eligible | rq4/f8/yes | 30 | 81 | 37.723 | 25.488 | 49.958 | 37.57 | 26.349 | 48.791 | 0.153 | 1.09 |
| codex | RQ4 item prevalence among eligible | rq4/f9/yes | 35 | 81 | 29.234 | 17.592 | 40.876 | 28.7 | 17.913 | 39.488 | 0.534 | 1.079 |
| codex | RQ4 item prevalence among eligible | rq4/f10/yes | 70 | 81 | 88.057 | 79.423 | 96.691 | 88.037 | 79.461 | 96.614 | 0.02 | 1.007 |
| codex | RQ4 item prevalence among eligible | rq4/f11/yes | 7 | 81 | 6.316 | 0.0 | 13.907 | 6.874 | 0.0 | 15.585 | -0.559 | 0.892 |
| codex | RQ4 item prevalence among eligible | rq4/f12/yes | 53 | 81 | 62.571 | 48.481 | 76.661 | 61.76 | 47.484 | 76.037 | 0.811 | 0.987 |
| codex | RQ4 item prevalence among eligible | rq4/f6_applicable/yes | 17 | 45 | 21.045 | 7.484 | 34.605 | 21.418 | 7.771 | 35.064 | -0.373 | 0.994 |
| codex | RQ4 item prevalence among eligible | rq4/robustness_tested/yes | 47 | 81 | 48.962 | 36.561 | 61.363 | 48.832 | 37.728 | 59.937 | 0.13 | 1.117 |
