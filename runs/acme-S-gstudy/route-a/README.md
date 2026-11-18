# Column (a): Arm S A1-S, strict roster, all items

A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.
Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data (`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.

- roster file: `runs/acme-S-gstudy/roster_strict.csv` (strict: >= 95% of conditions at validity >= 0.9 and x1-x0 gap <= 0.1 (E7 item 2(a)))
- switches: validity_cells=False, temps=[0.7, 1.0], logit=False, drop_W0=False
- wordings used: W0, W1, W2, W3; decomposability floor: >= 3 models on the roster
- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --approved-by-lead --no-bootstrap --out runs/acme-S-gstudy/route-a --label 'Column (a): Arm S A1-S, strict roster, all items' --roster runs/acme-S-gstudy/roster_strict.csv --roster-note 'strict: >= 95% of conditions at validity >= 0.9 and x1-x0 gap <= 0.1 (E7 item 2(a))'`
- code commit at run time (HEAD): `01e3ade297c0d5f92db0279921149f352d95f389`; uncommitted changes under analysis/acme at run time: False

| item | models | array | facets | note |
|---|---|---|---|---|
| P1 | 9 | 9x4x2x2 | MWOT |  |
| AF | 12 | 12x4x2x2 | MWOT |  |
| NR | 13 | 13x4x2x2 | MWOT |  |
| P3 | 10 | 10x4x2 | MWT |  |
| QA | 9 | 9x4x2x2 | MWOT |  |
| P2a | 8 | 8x4x2 | MWT |  |
| P2b | 7 | 7x4x2 | MWT |  |
| P2c | 8 | 8x4x2 | MWT |  |
| P2d | 3 | 3x4x2 | MWT |  |
| P4 | 5 | 5x4x2 | MWT |  |

Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), `summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.
