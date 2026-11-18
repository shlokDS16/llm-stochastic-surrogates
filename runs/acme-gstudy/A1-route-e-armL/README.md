# Column (e), Arm L half: frozen A1 on the intersection roster

Frozen `gstudy.py --estimator A1` on Arm L effects restricted to the intersection roster (pairs ok in `roster_strict.csv` AND not in `runs/acme-L/exclusions_per_type.csv`), W0-W3 and T in {0.7, 1.0}, variant main, items with at least 3 intersection models; same scale.csv and se.csv as the A1 run. Comparison partner: `runs/acme-S-gstudy/route-e-armS` (A1-S on the same roster). `components_by_item.csv` has the '4facet' analysis (M, W, O, T; the like-for-like partner of Arm S) and 'T1' (T = 1.0 only). `hypotheses.json` is a by-product of the frozen script and is not reported as a test (E7 item 5).

- roster: intersection roster `runs/acme-S-gstudy/route-e-armS/roster_intersection.csv`; per-item model lists in `inputs/roster.json`
- command: `.venv/Scripts/python.exe -I analysis/acme/route_e_inputs.py; .venv/Scripts/python.exe -I analysis/acme/gstudy.py --effects runs/acme-gstudy/A1-route-e-armL/inputs/effects.csv --scale runs/acme-gstudy/A1/inputs/scale.csv --single-site-se runs/acme-gstudy/A1/inputs/se.csv --out runs/acme-gstudy/A1-route-e-armL --estimator A1`
- code commit at the time this README was written (HEAD): `4f3920b1e5294c110f0313b42121e8fed377cbd0`; uncommitted changes under analysis/acme: False
- last commit that touched this directory before this README: c82a17a CRP-S09: E7b (D0037): column (e) P3 forward only, Arm L LOWO by the Arm S code path (reproduces frozen A1 to 1e-16); route table rebuilt

Prompt identity (E7a item 5): `prompt_identity.csv` (per item and W0-W3), `prompt_identity_detail.csv` (per order and x), `prompt_identity.json` (manifest verification). Result of this run: 40 (item, W) groups compared, 0 mismatch(es). Both manifests verify (see prompt_identity.json).

P3 (E7b item 1): Arm S has no order facet for P3 (one forward scale), so (e)-Arm L P3 uses Arm L's 'forward' prompts only (array M x W x T); Arm L's 'reversed' P3 prompts stay in column (b). LOWO values: `lowo.csv` (route_e_armL_lowo.py, E7b item 2). Arm L P2c has 3 models in the intersection. `hypotheses.json` is a by-product of the frozen script; its p-values are not reported (E7 item 5).
