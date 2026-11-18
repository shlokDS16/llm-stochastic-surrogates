# Synthetic recoverability check of A1-S at the Arm S shape (E7 item 3): FAIL

Written by the lab-engineer agent (commit 514e242). The agent's Write tool refused a `.md` file, so the CRP-S09 lead saved this
report verbatim from its hand-back on 2026-11-07. Every number is in the files of this directory (`summary.json`, `bias_G.csv`,
`bias_coverage_C.csv`, `bias_by_scenario.csv`, `coverage_by_scenario.csv`, `nw_check.csv`). The per-part arrays in `parts/`
(85 MB) are not tracked.

## Verdict against E7 item 3 (pass = |bias| <= 0.02 on every share and draw-bootstrap coverage 0.90-0.98)
- Bias: worst E2 bias 0.0565 (P4, scenario e1, draw share; bias SE 0.004); 25 of 848 E2 cells exceed 0.02. E1 is unusable at high
  draw noise: max 2.5 (SE 1.7, heavy tails); 131 of 774 cells above 0.02.
- Coverage: corrected draw bootstrap 0.894 to 1.000, median 0.990; 31% of 1622 cells in 0.90-0.98 (1118 above 0.98, too wide).
  Plain recompute 0.002 to 1.000 (worst: QA, e1, E2 draw share).
- Both criteria fail. Consequence fixed in E7 item 3: column (a) prints no intervals, only point estimates and the four
  leave-one-wording-out (LOWO) range, the range labelled as fragility, not uncertainty.

## What was run (`analysis/acme/synth_armS.py`)
- Shape: 14 models, 4 wordings, 2 orders for AF/NR/P1/QA (facets M, W, O, T), none for P3/P2a-d/P4 (M, W, T), 2 temperatures,
  n = 50 draws per condition, all 10 items.
- Draw noise: each item's real per-cell v_c from `../cells.csv` over all 14 models, Gaussian draws. The binary +0.5 branch is not
  exercised here (covered by unit tests and exact agreement with `cells.csv`).
- True model: G1 convention. M, O, T and their interactions fixed; W and random interactions fresh per replicate; total variance =
  r x mean(v_c).
- Scenarios: a residual only; b W 0.7; c MxW 0.7; dT T 0.7; dO O 0.7 (two-order items only); e3, e1, e12 spread across terms with
  r = 3, 1, 12 (draw noise 25%, 50%, 7.7%); other scenarios r = 3.
- Design G: 2000 replicates with fresh wordings, judged against the generating shares; also run at infinite draws on the same
  wordings to split each bias into a wordings-only and a draw part.
- Design C: 500 replicates, B = 2000, seed 20261106, wordings fixed per item-scenario; target = the estimator at infinite draws on
  those wordings; coverage of the percentile interval.
- Estimator: gstudy A1 unchanged. With v = 0, E1 = E2 = gstudy's A1 shares bit for bit (selftest, all shapes). Draw + remainder =
  A1 residual share to 1e-12. Jackknife correction applied to E1 and E2.
- Harness validation (`nw_check.csv`): at 12 wordings max |bias| 0.010 (E1), 0.008 (E2); at 4 wordings 0.050 and 0.024.

## Findings
1. Plain recompute is wrong: the observed cell means carry their draw noise as signal in the bootstrap world, so each replicate's
   remainder is too large by mean(v_obs); replicates sit about 0.15 below the estimate (AF, dO, O share) and coverage drops to
   0.002-0.1 where draw noise is large. A corrected variant (`baked`) also removes mean(v_obs); its recentred intervals are
   conservative (median coverage 0.99, widths about 1.3 x estimator SD in the cases inspected). Only e12 (7.7% draw noise) is mostly
   in range (84% of E2 cells).
2. A1 itself is biased at 4 wordings: with infinite draws E2 bias up to 0.045, E1 up to 0.055. The remainder share is biased down by
   0.02-0.03 and the zero MOT component up by about 0.02, because W has 3 df. Independent of the draw split; the draw-attributable
   part of the E2 bias is at most 0.029 (5 cells above 0.02).
3. E1 is unstable when draw noise is large: at 25-50% draw noise with very uneven v_c (P4, P2d: top cell 38% and 21% of total v_c),
   E1 has heavy tails. E2 is stable (bias SE at most 0.015).
4. Coverage by term: draw share covers best (median 0.972, 73% of cells in range); remainder share most conservative (median 0.996).
5. Design C bias: against the same-wordings limit, E2 max 0.040 (5 cells above 0.02); E1 12.7 (heavy tails).

## Choices where E7 is silent (engineer's; lead to confirm)
- Bias judged against generating shares (design G) and the same-wordings infinite-draw limit (design C); both in `summary.json`.
- Coverage read two ways: every cell in range, and the G1 rule of at least 90% of cells in range; both fail.
- The corrected bootstrap is an addition to E7's "resample and recompute"; both variants reported.
- Gaussian draws, equal SD in the two conditions; real v_c pattern of 14 models including off-roster models with extreme cells.
  The check validates estimator behaviour under its simulated model only.
- The binary 0/1 path of `bootstrap_draws` is checked at unit level only.

## Corrections after the gate-audit (`runs/gate-audits/A1S-SYNTH-AUDIT.md`, 6fcb148), appended by the lead
Verdict FAIL confirmed; robust under E2-only, same-wordings target, generating-share target, the G1 90%-of-cells rule and excluding
scenario e1. Three loose sentences above (kept as written): (1) "widths about 1.3 x estimator SD" is 1.3 x the normal 95% width;
(2) the zero MOT component bias is 0.014 wordings-only (0.023 total); (3) design C E2 bias SE reaches 0.018, not 0.015.
`parts/` (85 MB) is untracked; its per-part arrays reproduce bit for bit on a tiny rerun (audit), no hash recorded.
