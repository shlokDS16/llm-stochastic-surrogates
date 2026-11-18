# Rule calibration: zero-spread human-replica model, n = 50 per arm per cell

Replicates per paradigm and variant: 10 (smoke=True); seed 20261017; Monte-Carlo SE in brackets. Source: `analysis/pilot/rule_calibration.py`; rule = `side_by_side.rule_outcome`. Evidence level E4.

| paradigm | variant | cells | P(fragile) | P(stable) | P(neither) | mean sigma | P(sigma<0.6) | P(range clause) |
|---|---|---|---|---|---|---|---|---|
| P1 | normal | 32 | 0.000 (0.000) | 0.200 (0.126) | 0.800 (0.126) | 0.875 (0.016) | 0.000 | 0.000 |
| P2a | normal | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2a | empirical | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2b | normal | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2b | empirical | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2c | normal | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2c | empirical | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2d | normal | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P2d | empirical | 16 | 0.000 (0.000) | 1.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) | 0.000 | 0.000 |
| P3 | normal | 16 | 1.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.269 (0.040) | 1.000 | 0.100 |
| P3 | empirical | 16 | 1.000 (0.000) | 0.000 (0.000) | 0.000 (0.000) | 0.256 (0.035) | 1.000 | 0.000 |
| P4 | normal | 16 | 0.700 (0.145) | 0.000 (0.000) | 0.300 (0.145) | 0.531 (0.056) | 0.700 | 0.000 |
| P4 | empirical | 16 | 0.800 (0.126) | 0.000 (0.000) | 0.200 (0.126) | 0.519 (0.023) | 0.800 | 0.000 |

## Human ML1 sites as cells (36 sites; A1 metric rows of site_effects.csv)

| paradigm | sigma (sites with CI above 0) | dbar | S (moment, site_effects) | S^H (table_a1) | range clause | label (moment S) | label (S^H, interval for stable) |
|---|---|---|---|---|---|---|---|
| P1 | 0.861 (31/36) | 1.234 | 0.160 | 0.121 | False | neither | neither |
| P2a | 1.000 (36/36) | 1.236 | 0.171 | 0.128 | False | stable | stable |
| P2b | 1.000 (36/36) | 2.067 | 0.470 | 0.376 | False | stable | stable |
| P2c | 1.000 (36/36) | 2.261 | 0.771 | 0.684 | False | stable | stable |
| P2d | 1.000 (36/36) | 2.640 | 0.423 | 0.288 | False | stable | stable |
| P3 | 0.417 (15/36) | 0.303 | 0.000 | 0.000 | False | fragile | fragile |
| P4 | 0.556 (20/36) | 0.377 | 0.151 | 0.154 | False | fragile | fragile |
