# Sensitivity S-a: loose roster (0.8 and 0.2)

A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.
Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data (`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.

- roster file: `runs/acme-S-gstudy/roster_loose.csv` (loose: >= 95% of conditions at validity >= 0.8 and gap <= 0.2)
- switches: validity_cells=False, temps=[0.7, 1.0], logit=False, drop_W0=False
- wordings used: W0, W1, W2, W3; decomposability floor: >= 3 models on the roster
- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --approved-by-lead --no-bootstrap --out runs/acme-S-gstudy/sens-S-a --label 'Sensitivity S-a: loose roster (0.8 and 0.2)' --roster runs/acme-S-gstudy/roster_loose.csv --roster-note 'loose: >= 95% of conditions at validity >= 0.8 and gap <= 0.2'`
- code commit at run time (HEAD): `01e3ade297c0d5f92db0279921149f352d95f389`; uncommitted changes under analysis/acme at run time: False

| item | models | array | facets | note |
|---|---|---|---|---|
| P1 | 13 | 13x4x2x2 | MWOT |  |
| AF | 14 | 14x4x2x2 | MWOT |  |
| NR | 14 | 14x4x2x2 | MWOT |  |
| P3 | 11 | 11x4x2 | MWT |  |
| QA | 12 | 12x4x2x2 | MWOT |  |
| P2a | 9 | 9x4x2 | MWT |  |
| P2b | 8 | 8x4x2 | MWT |  |
| P2c | 9 | 9x4x2 | MWT |  |
| P2d | 8 | 8x4x2 | MWT |  |
| P4 | 7 | 7x4x2 | MWT |  |

Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), `summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.
