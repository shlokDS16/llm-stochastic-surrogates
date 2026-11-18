# Pilot variance shares split by near-deterministic status (DESCRIPTIVE over cells)

Source: `runs/pilot-side-by-side/fig_inputs/` (sha256 in config.json). Grids are model x paradigm (6 x 7 = 42). 'Reportable' = S^2 lower bound above 0 (A1.5). ND = near-deterministic flag on any cell of the grid (`diagnose_near_deterministic.py`). Wording-dominated = wording share of the corrected sum of squares >= 0.5. Shares are shares of a corrected sum of squares over fixed purposive cells, not variance components (prereg section 6); counts are over these 42 grids, with no interval and no test, and the reportable set is itself selected on the S^2 lower bound.

| scale | grids | ND-flagged grids | reportable | reportable and ND | reportable and not ND | wording >= 0.5 (all) | of which ND | of which not ND | median W share, ND | median W share, not ND |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 42 | 32 | 29 | 24 | 5 | 14 | 11 | 3 | 0.4411 | 0.5188 |
| A2 | 42 | 32 | 33 | 25 | 8 | 14 | 10 | 4 | 0.3826 | 0.4316 |

Threshold sensitivity (grids with wording share >= t among reportable grids; ND / not ND) is in `summary.csv`.

