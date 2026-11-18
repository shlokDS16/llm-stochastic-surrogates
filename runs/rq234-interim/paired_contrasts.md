# Like-for-like paired contrasts (DESCRIPTIVE; red-team F1, framework v2 unresolved list)

Difference = item A minus item B, in percentage points of eligible studies, over the SAME eligible studies (paired). Design-based: ratio estimator of stratified totals, Taylor linearised variance with collapsed merged groups and finite-population correction, t interval with the run's df (same machinery as every other estimate in this run). The interval states the precision of the paired difference; it is not a test and no hypothesis was prespecified. VARIED = the study varied that perturbation (F.perturbations_tested); REPORTED = the study states the information. Rows of kind `varied_supplementary` are item-based (f5, f7) and added as a cross-check of the perturbation-list contrasts.

`both_items_pass_v012_rule` = both underlying fields passed the v0.12 inter-coder rule; where False, read the two coders as a coder-sensitivity display. Nonresponse bounds are the extreme values of the difference if every unknown-status record were ineligible, or eligible with an extreme pair pattern (A yes and B no; A no and B yes): they are wide by construction.

| kind | contrast | coder | n_domain | n_both | n_a_only | n_b_only | a_est_pct | b_est_pct | diff_a_minus_b_pct_points | diff_lo_pct | diff_hi_pct | nr_bound_lo_pct | nr_bound_hi_pct | both_items_pass_v012_rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| varied | wording vs decoding | claude | 72 | 6 | 20 | 5 | 24.2 | 15.4 | 8.7 | -3.4 | 20.9 | -40.2 | 53.2 | True |
| varied | wording vs option order | claude | 72 | 7 | 19 | 4 | 24.2 | 10.9 | 13.3 | 2.6 | 24.1 | -36.5 | 56.9 | False |
| varied | wording vs seeds | claude | 72 | 2 | 24 | 2 | 24.2 | 6.3 | 17.9 | 4.7 | 31.0 | -32.1 | 61.3 | True |
| varied | wording vs model version | claude | 72 | 12 | 14 | 6 | 24.2 | 21.1 | 3.0 | -6.4 | 12.5 | -44.4 | 49.0 | False |
| reported | f2 decoding stated vs f4 prompts published | claude | 72 | 22 | 7 | 31 | 45.5 | 68.7 | -23.2 | -42.4 | -4.0 | -61.4 | 32.0 | False |
| reported | f1 model version stated vs f2 decoding stated | claude | 72 | 9 | 6 | 20 | 29.9 | 45.5 | -15.7 | -28.2 | -3.2 | -57.0 | 36.4 | True |
| varied_supplementary | f5 wordings compared vs f7 sampling settings compared | claude | 72 | 6 | 20 | 5 | 24.2 | 15.4 | 8.7 | -3.4 | 20.9 | -40.2 | 53.2 | False |
| varied | wording vs decoding | codex | 74 | 13 | 17 | 8 | 29.4 | 27.7 | 1.7 | -16.7 | 20.1 | -48.3 | 45.3 | True |
| varied | wording vs option order | codex | 74 | 10 | 20 | 6 | 29.4 | 14.0 | 15.4 | -0.8 | 31.5 | -38.6 | 55.0 | False |
| varied | wording vs seeds | codex | 74 | 5 | 25 | 9 | 29.4 | 26.5 | 2.8 | -12.5 | 18.2 | -41.9 | 51.7 | True |
| varied | wording vs model version | codex | 74 | 9 | 21 | 10 | 29.4 | 19.5 | 9.8 | -8.1 | 27.8 | -43.0 | 50.6 | False |
| reported | f2 decoding stated vs f4 prompts published | codex | 74 | 28 | 8 | 30 | 49.9 | 68.5 | -18.6 | -34.1 | -3.1 | -58.2 | 35.4 | False |
| reported | f1 model version stated vs f2 decoding stated | codex | 74 | 3 | 0 | 33 | 6.3 | 49.9 | -43.6 | -57.3 | -29.9 | -72.4 | 21.2 | True |
| varied_supplementary | f5 wordings compared vs f7 sampling settings compared | codex | 74 | 3 | 11 | 10 | 10.6 | 19.2 | -8.5 | -20.6 | 3.6 | -51.7 | 41.9 | False |
