# Sensitivity: merged groups versus original strata (amendment v0.12.1 item 1)

Merged = the main analysis (strata with fewer than 2 respondents merged with the same family's adjacent period, later first; weights N_g / r_g and variance on the merged groups). Original = the 32 sampling strata as drawn. The original-strata columns are a LIMITED COMPARISON: a stratum with exactly 1 respondent carries its weight N_h / 1 in the point estimate but contributes no variance term (dropped from the variance only); a stratum with 0 respondents has no weight and is left out of the point estimate and of the frame denominator (so the original eligible share refers to the frame minus those strata). The original intervals therefore understate the variance and are not a validated alternative.


## Merged strata

| coder | merged | into | reason | a | r |
|---|---|---|---|---|---|
| claude | OTH/2024 | OTH/2025-2026 | adjacent period OTH/2025-2026 | 2 | 0 |
| claude | JDM/2024 | JDM/2025-2026 | adjacent period JDM/2025-2026 | 1 | 1 |
| claude | RE/2024 | RE/2025-2026 | adjacent period RE/2025-2026 | 2 | 1 |
| claude | LEARN/2025-2026 | LEARN/2024 | adjacent period LEARN/2024 | 3 | 1 |
| claude | MOR/2024 | MOR/2025-2026 | adjacent period MOR/2025-2026 | 3 | 1 |
| codex | OTH/2024 | OTH/2025-2026 | adjacent period OTH/2025-2026 | 2 | 0 |
| codex | JDM/2024 | JDM/2025-2026 | adjacent period JDM/2025-2026 | 1 | 1 |
| codex | RE/2024 | RE/2025-2026 | adjacent period RE/2025-2026 | 2 | 1 |
| codex | LEARN/2025-2026 | LEARN/2024 | adjacent period LEARN/2024 | 3 | 1 |
| codex | MOR/2024 | MOR/2025-2026 | adjacent period MOR/2025-2026 | 3 | 1 |


claude: 32 original strata, 27 merged groups; original strata with 1 respondent (no variance term): 4; with 0 respondents (outside the point estimate): 1; frame covered by the original point estimate 2000 of 2022; df merged 75, original 71.


codex: 32 original strata, 27 merged groups; original strata with 1 respondent (no variance term): 4; with 0 respondents (outside the point estimate): 1; frame covered by the original point estimate 2000 of 2022; df merged 75, original 71.


## Main estimates (percent); all RQ4 features are in sensitivity_merge.csv

| coder | estimand | feature | k | n_domain | merged_est_pct | merged_lo_pct | merged_hi_pct | limited_comparison_orig_est_pct | limited_comparison_orig_lo_pct | limited_comparison_orig_hi_pct | diff_est_pct_points | ci_width_ratio_merged_over_orig |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | eligible share of frame | ELIGIBLE_SHARE | 72 | 102 | 66.341 | 57.299 | 75.384 | 66.003 | 58.601 | 73.406 | 0.338 | 1.222 |
| claude | RQ2 any row by outcome kind | rq2/effect/ANY | 39 | 72 | 64.077 | 51.68 | 76.474 | 62.787 | 51.388 | 74.186 | 1.29 | 1.087 |
| claude | RQ2 any row by outcome kind | rq2/accuracy/ANY | 29 | 72 | 34.632 | 22.445 | 46.82 | 33.756 | 22.592 | 44.919 | 0.877 | 1.092 |
| claude | RQ2 any row by outcome kind | rq2/agreement/ANY | 14 | 72 | 9.951 | 3.952 | 15.95 | 12.208 | 6.655 | 17.76 | -2.257 | 1.08 |
| claude | RQ4 item prevalence among eligible | rq4/f1/yes | 15 | 72 | 29.855 | 17.121 | 42.588 | 28.066 | 16.404 | 39.728 | 1.789 | 1.092 |
| claude | RQ4 item prevalence among eligible | rq4/f2/yes | 29 | 72 | 45.536 | 34.336 | 56.735 | 46.319 | 35.929 | 56.708 | -0.783 | 1.078 |
| claude | RQ4 item prevalence among eligible | rq4/f3/yes | 32 | 72 | 46.788 | 27.754 | 65.823 | 47.397 | 29.927 | 64.867 | -0.609 | 1.09 |
| claude | RQ4 item prevalence among eligible | rq4/f4/yes | 53 | 72 | 68.727 | 50.794 | 86.659 | 69.154 | 52.391 | 85.916 | -0.427 | 1.07 |
| claude | RQ4 item prevalence among eligible | rq4/f5/yes | 26 | 72 | 24.191 | 14.079 | 34.304 | 25.006 | 15.403 | 34.609 | -0.815 | 1.053 |
| claude | RQ4 item prevalence among eligible | rq4/f6/yes | 12 | 72 | 11.653 | 3.494 | 19.812 | 11.742 | 3.636 | 19.848 | -0.089 | 1.007 |
| claude | RQ4 item prevalence among eligible | rq4/f7/yes | 11 | 72 | 15.444 | 6.085 | 24.803 | 18.137 | 9.663 | 26.612 | -2.693 | 1.104 |
| claude | RQ4 item prevalence among eligible | rq4/f8/yes | 24 | 72 | 28.444 | 18.113 | 38.776 | 31.249 | 21.481 | 41.016 | -2.804 | 1.058 |
| claude | RQ4 item prevalence among eligible | rq4/f9/yes | 23 | 72 | 20.49 | 9.554 | 31.426 | 20.772 | 9.82 | 31.724 | -0.282 | 0.999 |
| claude | RQ4 item prevalence among eligible | rq4/f10/yes | 53 | 72 | 77.855 | 65.957 | 89.753 | 78.633 | 67.937 | 89.33 | -0.778 | 1.112 |
| claude | RQ4 item prevalence among eligible | rq4/f11/yes | 4 | 72 | 8.61 | 0.0 | 22.339 | 7.916 | 0.0 | 20.234 | 0.694 | 1.104 |
| claude | RQ4 item prevalence among eligible | rq4/f12/yes | 38 | 72 | 52.459 | 33.971 | 70.948 | 52.098 | 34.985 | 69.21 | 0.362 | 1.08 |
| claude | RQ4 item prevalence among eligible | rq4/f6_applicable/yes | 12 | 37 | 24.532 | 9.522 | 39.543 | 24.337 | 9.473 | 39.201 | 0.195 | 1.01 |
| claude | RQ4 item prevalence among eligible | rq4/robustness_tested/yes | 43 | 72 | 47.223 | 36.149 | 58.297 | 49.069 | 38.871 | 59.268 | -1.846 | 1.086 |
| codex | eligible share of frame | ELIGIBLE_SHARE | 74 | 102 | 67.2 | 58.904 | 75.497 | 66.639 | 60.001 | 73.276 | 0.561 | 1.25 |
| codex | RQ2 any row by outcome kind | rq2/effect/ANY | 46 | 74 | 70.087 | 58.636 | 81.537 | 69.628 | 59.335 | 79.921 | 0.459 | 1.112 |
| codex | RQ2 any row by outcome kind | rq2/accuracy/ANY | 31 | 74 | 32.233 | 19.259 | 45.207 | 30.563 | 18.574 | 42.552 | 1.67 | 1.082 |
| codex | RQ2 any row by outcome kind | rq2/agreement/ANY | 18 | 74 | 20.098 | 10.193 | 30.003 | 22.592 | 13.033 | 32.151 | -2.494 | 1.036 |
| codex | RQ4 item prevalence among eligible | rq4/f1/yes | 3 | 74 | 6.318 | 0.0 | 14.609 | 6.392 | 0.0 | 14.787 | -0.074 | 0.988 |
| codex | RQ4 item prevalence among eligible | rq4/f2/yes | 36 | 74 | 49.913 | 36.585 | 63.241 | 50.584 | 37.785 | 63.382 | -0.671 | 1.041 |
| codex | RQ4 item prevalence among eligible | rq4/f3/yes | 36 | 74 | 51.92 | 33.633 | 70.206 | 50.263 | 33.645 | 66.88 | 1.657 | 1.1 |
| codex | RQ4 item prevalence among eligible | rq4/f4/yes | 58 | 74 | 68.494 | 57.374 | 79.614 | 69.235 | 58.58 | 79.889 | -0.741 | 1.044 |
| codex | RQ4 item prevalence among eligible | rq4/f5/yes | 14 | 74 | 10.624 | 4.288 | 16.959 | 10.906 | 4.419 | 17.394 | -0.282 | 0.977 |
| codex | RQ4 item prevalence among eligible | rq4/f6/yes | 16 | 74 | 12.062 | 4.394 | 19.731 | 12.274 | 4.579 | 19.97 | -0.212 | 0.996 |
| codex | RQ4 item prevalence among eligible | rq4/f7/yes | 13 | 74 | 19.166 | 9.26 | 29.071 | 21.66 | 12.792 | 30.527 | -2.494 | 1.117 |
| codex | RQ4 item prevalence among eligible | rq4/f8/yes | 28 | 74 | 34.393 | 22.46 | 46.325 | 37.086 | 25.837 | 48.334 | -2.693 | 1.061 |
| codex | RQ4 item prevalence among eligible | rq4/f9/yes | 33 | 74 | 31.715 | 19.156 | 44.274 | 31.936 | 19.749 | 44.122 | -0.22 | 1.031 |
| codex | RQ4 item prevalence among eligible | rq4/f10/yes | 65 | 74 | 91.799 | 84.894 | 98.703 | 91.564 | 84.473 | 98.655 | 0.235 | 0.974 |
| codex | RQ4 item prevalence among eligible | rq4/f11/yes | 6 | 74 | 11.152 | 0.0 | 26.224 | 10.544 | 0.0 | 24.467 | 0.608 | 1.072 |
| codex | RQ4 item prevalence among eligible | rq4/f12/yes | 48 | 74 | 61.6 | 42.944 | 80.256 | 61.28 | 43.85 | 78.71 | 0.32 | 1.07 |
| codex | RQ4 item prevalence among eligible | rq4/f6_applicable/yes | 16 | 41 | 22.629 | 8.18 | 37.078 | 23.313 | 8.718 | 37.908 | -0.684 | 0.99 |
| codex | RQ4 item prevalence among eligible | rq4/robustness_tested/yes | 42 | 74 | 41.906 | 30.842 | 52.97 | 44.82 | 34.548 | 55.093 | -2.915 | 1.077 |
