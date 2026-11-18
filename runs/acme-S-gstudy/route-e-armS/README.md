# Column (e), Arm S half: A1-S on the intersection roster

A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.
Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data (`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.

- roster file: `runs/acme-S-gstudy/route-e-armS/roster_intersection.csv` (intersection: ok in roster_strict.csv AND not in runs/acme-L/exclusions_per_type.csv (analysis/acme/route_e_inputs.py); partner: runs/acme-gstudy/A1-route-e-armL. P3 differs by construction: Arm S has no order facet (one forward scale), Arm L P3 has forward and reversed; prompt identity in the partner directory)
- switches: validity_cells=False, temps=[0.7, 1.0], logit=False, drop_W0=False
- wordings used: W0, W1, W2, W3; decomposability floor: >= 3 models on the roster
- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --approved-by-lead --no-bootstrap --roster runs/acme-S-gstudy/route-e-armS/roster_intersection.csv --out runs/acme-S-gstudy/route-e-armS --label 'Column (e), Arm S half: A1-S on the intersection roster' --roster-note 'intersection: ok in roster_strict.csv AND not in runs/acme-L/exclusions_per_type.csv (analysis/acme/route_e_inputs.py); partner: runs/acme-gstudy/A1-route-e-armL. P3 differs by construction: Arm S has no order facet (one forward scale), Arm L P3 has forward and reversed; prompt identity in the partner directory'`
- code commit at run time (HEAD): `272017853b7972584c804df9e360bf8f43e1ab42`; uncommitted changes under analysis/acme at run time: False

| item | models | array | facets | note |
|---|---|---|---|---|
| P1 | 8 | 8x4x2x2 | MWOT |  |
| AF | 11 | 11x4x2x2 | MWOT |  |
| NR | 12 | 12x4x2x2 | MWOT |  |
| P3 | 5 | 5x4x2 | MWT |  |
| QA | 5 | 5x4x2x2 | MWOT |  |
| P2c | 3 | 3x4x2 | MWT |  |

Not decomposed (fewer than the floor of models on this roster, or incomplete cells): P2a (0 models on this roster), P2b (0 models on this roster), P2d (0 models on this roster), P4 (0 models on this roster)

Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), `summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.
