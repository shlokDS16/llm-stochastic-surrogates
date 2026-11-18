# Column (b): Arm L, frozen gstudy.py A1

Frozen `analysis/acme/gstudy.py --estimator A1` (B = 2000, seed 20261106) on the Arm L effects table restricted by `analysis/acme/route_inputs.py` to items with at least 3 models on the roster (decomposability floor). All ten wordings, four temperatures. Shares carry the frozen A1 inference, labelled underpowered. `hypotheses.json` is a by-product of the frozen script and is not reported as a test (E7 item 5: no p-values, no Holm family, no 'supported' or 'rejected').

- roster: per-type: runs/acme-L/exclusions_per_type.csv
- command: `route_inputs.py (inputs), then .venv/Scripts/python.exe -I analysis/acme/gstudy.py --effects runs/acme-gstudy/A1-route-b-pertype/inputs/effects.csv --scale runs/acme-gstudy/A1/inputs/scale.csv --single-site-se runs/acme-gstudy/A1/inputs/se.csv --out runs/acme-gstudy/A1-route-b-pertype --estimator A1 --exclude runs/acme-gstudy/A1-route-b-pertype/inputs/exclude.csv`
- code commit at the time this README was written (HEAD): `4f3920b1e5294c110f0313b42121e8fed377cbd0`; uncommitted changes under analysis/acme: False
- last commit that touched this directory before this README: c82a17a CRP-S09: E7b (D0037): column (e) P3 forward only, Arm L LOWO by the Arm S code path (reproduces frozen A1 to 1e-16); route table rebuilt

Engineer's reading: the gstudy.py command line of the original run (commit d88e613) was not recorded; the line above (same inputs, scale.csv and se.csv as the A1 run, `exclude.csv` from route_inputs.py) was re-run into a scratch directory and reproduces `components_by_item.csv` exactly (cell-for-cell identical, CSV comparison).
