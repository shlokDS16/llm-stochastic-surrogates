# Like-for-like paired contrasts (DESCRIPTIVE; red-team F1, framework v2 unresolved list)

Difference = item A minus item B, in percentage points of eligible studies, over the SAME eligible studies (paired). Design-based: ratio estimator of stratified totals, Taylor linearised variance with collapsed merged groups and finite-population correction, t interval with the run's df (same machinery as every other estimate in this run). The interval states the precision of the paired difference; it is not a test and no hypothesis was prespecified. VARIED = the study varied that perturbation (F.perturbations_tested); REPORTED = the study states the information. Rows of kind `varied_supplementary` are item-based (f5, f7) and added as a cross-check of the perturbation-list contrasts.

`both_items_pass_v012_rule` = both underlying fields passed the v0.12 inter-coder rule; where False, read the two coders as a coder-sensitivity display. Nonresponse bounds are the extreme values of the difference if every unknown-status record were ineligible, or eligible with an extreme pair pattern (A yes and B no; A no and B yes): they are wide by construction.

| kind | contrast | coder | n_domain | n_both | n_a_only | n_b_only | a_est_pct | b_est_pct | diff_a_minus_b_pct_points | diff_lo_pct | diff_hi_pct | nr_bound_lo_pct | nr_bound_hi_pct | both_items_pass_v012_rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| varied | wording vs decoding | claude | 80 | 6 | 21 | 6 | 24.4 | 17.3 | 7.1 | -4.6 | 18.8 | -34.6 | 46.7 | True |
| varied | wording vs option order | claude | 80 | 7 | 20 | 6 | 24.4 | 12.6 | 11.7 | 0.6 | 22.9 | -30.9 | 50.4 | False |
| varied | wording vs seeds | claude | 80 | 3 | 24 | 2 | 24.4 | 6.9 | 17.5 | 4.6 | 30.4 | -26.0 | 55.3 | False |
| varied | wording vs model version | claude | 80 | 13 | 14 | 8 | 24.4 | 26.7 | -2.4 | -13.4 | 8.7 | -40.0 | 41.3 | False |
| reported | f2 decoding stated vs f4 prompts published | claude | 80 | 22 | 9 | 34 | 42.2 | 68.6 | -26.4 | -40.9 | -12.0 | -55.3 | 26.0 | False |
| reported | f1 model version stated vs f2 decoding stated | claude | 80 | 9 | 6 | 22 | 25.0 | 42.2 | -17.2 | -27.9 | -6.4 | -52.8 | 28.5 | True |
| varied_supplementary | f5 wordings compared vs f7 sampling settings compared | claude | 80 | 6 | 21 | 6 | 24.4 | 17.3 | 7.1 | -4.6 | 18.8 | -34.6 | 46.7 | False |
| varied | wording vs decoding | codex | 81 | 13 | 19 | 9 | 28.9 | 30.2 | -1.3 | -16.1 | 13.6 | -42.0 | 40.1 | True |
| varied | wording vs option order | codex | 81 | 10 | 22 | 8 | 28.9 | 16.1 | 12.8 | 0.2 | 25.4 | -32.4 | 49.7 | False |
| varied | wording vs seeds | codex | 81 | 5 | 27 | 9 | 28.9 | 23.6 | 5.3 | -10.8 | 21.5 | -34.7 | 47.4 | False |
| varied | wording vs model version | codex | 81 | 10 | 22 | 10 | 28.9 | 20.5 | 8.4 | -6.0 | 22.8 | -36.3 | 45.8 | False |
| reported | f2 decoding stated vs f4 prompts published | codex | 81 | 30 | 8 | 33 | 50.0 | 74.3 | -24.3 | -41.6 | -6.9 | -54.6 | 27.5 | False |
| reported | f1 model version stated vs f2 decoding stated | codex | 81 | 3 | 1 | 35 | 8.1 | 50.0 | -41.9 | -57.0 | -26.8 | -67.7 | 14.4 | True |
| varied_supplementary | f5 wordings compared vs f7 sampling settings compared | codex | 81 | 3 | 11 | 11 | 10.7 | 21.6 | -10.9 | -23.0 | 1.2 | -47.0 | 35.1 | False |
