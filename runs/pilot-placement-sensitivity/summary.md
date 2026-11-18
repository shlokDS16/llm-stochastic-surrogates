# Placement sensitivity (A1 estimator, existing responses)

Models: 6; smoke=False. Placement = LLM S interval wholly above (larger), overlapping, or wholly below (smaller) the human S^H interval of `runs/pilot-side-by-side/table_a1.csv`. The full-grid re-analysis reproduces the stored S, dbar and S upper bound of every grid to 1e-9 (assert in the script). Evidence level E4.

| analysis | grids | larger | overlap | smaller |
|---|---|---|---|---|
| original (all grids, F kept) | 42 | 24 | 17 | 1 |
| (a) grids without near-deterministic cells, F kept | 10 | 4 | 6 | 0 |
| (a') grids with near-deterministic cells, F kept | 32 | 20 | 11 | 1 |
| (b) F0 cells only (F removed), all grids | 42 | 21 | 20 | 1 |
| (b) F0 cells only, grids without near-deterministic cells | 10 | 4 | 6 | 0 |
| (b') F1 cells only (F removed), all grids | 42 | 8 | 31 | 3 |
| (b') F1 cells only, grids without near-deterministic cells | 10 | 1 | 9 | 0 |

Per paradigm (original larger count; F0-only larger / overlap / smaller):

| paradigm | original larger | F0 larger | F0 overlap | F0 smaller |
|---|---|---|---|---|
| P1 | 5 | 3 | 3 | 0 |
| P2a | 5 | 5 | 1 | 0 |
| P2b | 3 | 3 | 3 | 0 |
| P2c | 1 | 1 | 4 | 1 |
| P2d | 4 | 4 | 2 | 0 |
| P3 | 2 | 1 | 5 | 0 |
| P4 | 4 | 4 | 2 | 0 |
