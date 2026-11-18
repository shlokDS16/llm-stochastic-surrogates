### A. Point estimate: bias of the untruncated S2-hat (true S2 = nominal) and of the truncated S-hat, default estimator
| family | scenario | true S2 | S2 of E[d_c] | bias S2 (default) | bias S-hat | SD of S2-hat |
|---|---|---|---|---|---|---|
| binary (formula) | S0.15split | 0.0225 | 0.0229 | -0.0010 | -0.023 | 0.0458 |
| binary (formula) | S0.2split | 0.0400 | 0.0425 | +0.0042 | -0.014 | 0.0520 |
| binary (formula) | S0.25split | 0.0625 | 0.0675 | +0.0071 | -0.012 | 0.0609 |
| binary (formula) | S0.5split | 0.2500 | 0.2622 | +0.0176 | +0.008 | 0.0991 |
| normal | S0.15split | 0.0225 | 0.0231 | +0.0018 | -0.009 | 0.0211 |
| normal | S0.2split | 0.0400 | 0.0396 | -0.0015 | -0.016 | 0.0244 |
| normal | S0.25split | 0.0625 | 0.0635 | +0.0023 | -0.002 | 0.0290 |
| normal | S0.5split | 0.2500 | 0.2499 | +0.0036 | +0.001 | 0.0520 |
| emp_P2c_log | S0.15split | 0.0225 | 0.0244 | +0.0040 | -0.005 | 0.0276 |
| emp_P2c_log | S0.2split | 0.0400 | 0.0431 | +0.0017 | -0.012 | 0.0330 |
| emp_P2c_log | S0.25split | 0.0625 | 0.0685 | +0.0041 | -0.001 | 0.0331 |
| emp_P2c_log | S0.5split | 0.2500 | 0.2688 | +0.0123 | +0.007 | 0.0741 |

### B. Interval for S (95 percent): coverage of the nominal S and of the S implied by E[d_c]; share of replicates whose lower bound exceeds 0 (power)
| family | scenario | A1 variance + basic | A1 + ti_gauss | A1 + ti_boot (default) | ti_boot cov vs E-truth | lower>0 (basic) | lower>0 (ti_boot) | mean S interval (ti_boot) |
|---|---|---|---|---|---|---|---|---|
| binary | S0.15split | 0.997 | 0.957 | 0.963 | 0.963 | 0.00 | 0.07 | [0.01, 0.37] |
| binary | S0.2split | 0.990 | 0.947 | 0.960 | 0.957 | 0.00 | 0.15 | [0.02, 0.41] |
| binary | S0.25split | 0.990 | 0.940 | 0.960 | 0.960 | 0.00 | 0.26 | [0.04, 0.46] |
| binary | S0.5split | 0.990 | 0.937 | 0.943 | 0.950 | 0.45 | 0.97 | [0.31, 0.69] |
| normal | S0.15split | 0.973 | 0.930 | 0.950 | 0.950 | 0.00 | 0.32 | [0.03, 0.28] |
| normal | S0.2split | 0.957 | 0.950 | 0.953 | 0.957 | 0.03 | 0.54 | [0.06, 0.31] |
| normal | S0.25split | 0.980 | 0.960 | 0.963 | 0.963 | 0.19 | 0.84 | [0.12, 0.37] |
| normal | S0.5split | 0.967 | 0.960 | 0.967 | 0.967 | 1.00 | 1.00 | [0.39, 0.61] |
| emp_P2c_log | S0.15split | 0.983 | 0.940 | 0.953 | 0.953 | 0.01 | 0.17 | [0.02, 0.29] |
| emp_P2c_log | S0.2split | 0.963 | 0.933 | 0.943 | 0.943 | 0.02 | 0.35 | [0.04, 0.33] |
| emp_P2c_log | S0.25split | 0.983 | 0.957 | 0.987 | 0.977 | 0.05 | 0.61 | [0.07, 0.38] |
| emp_P2c_log | S0.5split | 0.963 | 0.923 | 0.957 | 0.943 | 0.68 | 0.99 | [0.33, 0.64] |

### C. Corrected term sums of squares (default estimator, ti_boot): bias, coverage, false-positive rate; factor shares
| family | scenario | term | true SS | bias | coverage | lower>0 |
|---|---|---|---|---|---|---|
| binary | S0.5split | W | 4.000 | +0.363 | 0.947 | 0.99 |
| binary | S0.5split | F | 4.000 | +0.059 | 0.950 | 1.00 |
| binary | S0.5split | T | 0.000 | +0.010 | 0.967 | 0.03 |
| binary | S0.5split | W:F | 0.000 | -0.015 | 0.947 | 0.02 |
| normal | S0.5split | W | 2.000 | +0.012 | 0.957 | 1.00 |
| normal | S0.5split | F | 2.000 | +0.022 | 0.953 | 1.00 |
| normal | S0.5split | T | 0.000 | -0.001 | 0.960 | 0.04 |
| normal | S0.5split | W:F | 0.000 | +0.016 | 0.950 | 0.03 |
| emp_P2c_log | S0.5split | W | 2.000 | +0.049 | 0.953 | 1.00 |
| emp_P2c_log | S0.5split | F | 2.000 | +0.133 | 0.957 | 1.00 |
| emp_P2c_log | S0.5split | T | 0.000 | -0.003 | 0.977 | 0.02 |
| emp_P2c_log | S0.5split | W:F | 0.000 | -0.006 | 0.963 | 0.01 |

| family | scenario | shares reportable (S2 lower>0) | max |ratio-of-means share bias| | mean MAE of shares when reported | max MAE when reported |
|---|---|---|---|---|---|
| binary | S0.15split | 0.07 | 0.100 | 0.122 | 0.339 |
| binary | S0.2split | 0.15 | 0.035 | 0.103 | 0.289 |
| binary | S0.25split | 0.26 | 0.044 | 0.089 | 0.248 |
| binary | S0.5split | 0.97 | 0.026 | 0.047 | 0.135 |
| normal | S0.15split | 0.32 | 0.041 | 0.149 | 0.267 |
| normal | S0.2split | 0.54 | 0.021 | 0.110 | 0.206 |
| normal | S0.25split | 0.84 | 0.007 | 0.095 | 0.185 |
| normal | S0.5split | 1.00 | 0.004 | 0.038 | 0.092 |
| emp_P2c_log | S0.15split | 0.17 | 0.057 | 0.142 | 0.237 |
| emp_P2c_log | S0.2split | 0.35 | 0.017 | 0.117 | 0.224 |
| emp_P2c_log | S0.25split | 0.61 | 0.009 | 0.096 | 0.181 |
| emp_P2c_log | S0.5split | 0.99 | 0.012 | 0.042 | 0.095 |
