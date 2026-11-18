# Placement sensitivity (A1 estimator, existing responses)

Models: 1; smoke=True. Placement = LLM S interval wholly above (larger), overlapping, or wholly below (smaller) the human S^H interval of `runs/pilot-side-by-side/table_a1.csv`. The full-grid re-analysis reproduces the stored S, dbar and S upper bound of every grid to 1e-9 (assert in the script). Evidence level E4.

| analysis | grids | larger | overlap | smaller |
|---|---|---|---|---|
| original (all grids, F kept) | 7 | 4 | 3 | 0 |
| (a) grids without near-deterministic cells, F kept | 1 | 1 | 0 | 0 |
| (a') grids with near-deterministic cells, F kept | 6 | 3 | 3 | 0 |
| (b) F0 cells only (F removed), all grids | 7 | 3 | 4 | 0 |
| (b) F0 cells only, grids without near-deterministic cells | 1 | 1 | 0 | 0 |
| (b') F1 cells only (F removed), all grids | 7 | 2 | 5 | 0 |
| (b') F1 cells only, grids without near-deterministic cells | 1 | 0 | 1 | 0 |

Per paradigm (original larger count; F0-only larger / overlap / smaller):

| paradigm | original larger | F0 larger | F0 overlap | F0 smaller |
|---|---|---|---|---|
| P1 | 1 | 0 | 1 | 0 |
| P2a | 1 | 1 | 0 | 0 |
| P2b | 0 | 0 | 1 | 0 |
| P2c | 0 | 0 | 1 | 0 |
| P2d | 1 | 1 | 0 | 0 |
| P3 | 0 | 0 | 1 | 0 |
| P4 | 1 | 1 | 0 | 0 |
