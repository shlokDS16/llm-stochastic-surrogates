# Sensitivity S-c: T = 1.0 only

A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.
Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data (`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.

- roster file: `runs/acme-S-gstudy/roster_strict.csv` (outcome-blind validity rule of EXPERT-statistician.md section 1)
- switches: validity_cells=False, temps=[1.0], logit=False, drop_W0=False
- wordings used: W0, W1, W2, W3; decomposability floor: >= 3 models on the roster
- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --approved-by-lead --no-bootstrap --out runs/acme-S-gstudy/sens-S-c --label 'Sensitivity S-c: T = 1.0 only' --roster runs/acme-S-gstudy/roster_strict.csv --temps 1.0`
- code commit at run time (HEAD): `01e3ade297c0d5f92db0279921149f352d95f389`; uncommitted changes under analysis/acme at run time: False

| item | models | array | facets | note |
|---|---|---|---|---|
| P1 | 9 | 9x4x2 | MWO |  |
| AF | 12 | 12x4x2 | MWO |  |
| NR | 13 | 13x4x2 | MWO |  |
| P3 | 10 | 10x4 | MW |  |
| QA | 9 | 9x4x2 | MWO |  |
| P2a | 8 | 8x4 | MW |  |
| P2b | 7 | 7x4 | MW |  |
| P2c | 8 | 8x4 | MW |  |
| P2d | 3 | 3x4 | MW |  |
| P4 | 5 | 5x4 | MW |  |

Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), `summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.

T = 1.0 only (S-c): no T facet (facets M, W, O or M, W); LOWO as before over the four wordings.
