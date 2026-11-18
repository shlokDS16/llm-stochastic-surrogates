# Sensitivity S-d: logit scale, binary items

A1-S (errata E7 item 2(a), E7a): the frozen `gstudy.py` A1 estimator applied to the Arm S cell-mean array Delta-hat(m, w, o, T), residual split into draw noise mean(v_c) and remainder, shares E1 and E2, with the leave-one-wording-out (LOWO) values.
Post-outcome, exploratory, descriptive. Under E7 item 3 / E7a item 1 NO interval of any kind is computed for real Arm S data (`--no-bootstrap`): point estimates and the LOWO range, the range being fragility over the wordings, not uncertainty.

- roster file: `runs/acme-S-gstudy/roster_strict.csv` (outcome-blind validity rule of EXPERT-statistician.md section 1)
- switches: validity_cells=False, temps=[0.7, 1.0], logit=True, drop_W0=False
- wordings used: W0, W1, W2, W3; decomposability floor: >= 3 models on the roster
- command: `.venv/Scripts/python.exe -I analysis/acme/gstudy_armS.py run --approved-by-lead --no-bootstrap --out runs/acme-S-gstudy/sens-S-d --label 'Sensitivity S-d: logit scale, binary items' --roster runs/acme-S-gstudy/roster_strict.csv --logit`
- code commit at run time (HEAD): `01e3ade297c0d5f92db0279921149f352d95f389`; uncommitted changes under analysis/acme at run time: False

| item | models | array | facets | note |
|---|---|---|---|---|
| P1 | 9 | 9x4x2x2 | MWOT | logit scale, clip rate 0.3194 (92 of 288 conditions) |
| AF | 12 | 12x4x2x2 | MWOT | logit scale, clip rate 0.6042 (232 of 384 conditions) |
| NR | 13 | 13x4x2x2 | MWOT | logit scale, clip rate 0.2620 (109 of 416 conditions) |

Files: `components_<item>.csv` (one row per term: component, E1/E2 shares, LOWO min/max, the LOWO value with each wording dropped), `summary.json` (models, shapes, A1 consistency check, draw share, clip rate on the logit scale), this README.

Logit scale (S-d): cell delta = logit(p1) - logit(p0), each logit clipped to +-12 (PREREG S4); v_c = delta method 1/(n p (1-p)) per condition, p replaced by (k + 0.5)/(n + 1) when the sampled p is 0 or 1. Shares are invariant to a common rescaling of an item's array, so no ML1-SD rescale is applied. Engineer's reading: the continuity rule is for the variance only; the point value of an edge proportion is the clipped logit (+-12). Clip rate per item is in summary.json.
