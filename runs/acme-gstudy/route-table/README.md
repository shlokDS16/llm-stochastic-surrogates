# Route table (E7 item 2) and sensitivity table (E7 item 4)

`route_table.csv`: columns (a), (b), (c), (d), (e)-Arm S, (e)-Arm L in one long table; `sens_table.csv`: sensitivities S-a to S-e (Arm S only). Post-outcome, exploratory, descriptive; equal billing, no primary column; each column names its model population and the shares are not called a common estimand across columns. Column semantics are in the docstring of `analysis/acme/route_table.py`. Arm S rows carry point estimates and the leave-one-wording-out (LOWO) range only (fragility over the wordings, not uncertainty; no interval of any kind, E7a item 1); Arm L rows carry the frozen A1 interval (underpowered). In the four-wording arrays (column (a) and Arm S and Arm L in column (e)) differences smaller than 0.06 on a share are not interpreted (E7a item 3).

- roster: see the per-column READMEs: runs/acme-S-gstudy/route-a, runs/acme-gstudy/A1-route-b-pertype, A1-route-c-permodel, runs/acme-S-gstudy/route-e-armS, runs/acme-gstudy/A1-route-e-armL
- command: `.venv/Scripts/python.exe -I analysis/acme/route_table.py`
- code commit at the time this README was written (HEAD): `4f3920b1e5294c110f0313b42121e8fed377cbd0`; uncommitted changes under analysis/acme: False
- last commit that touched this directory before this README: c82a17a CRP-S09: E7b (D0037): column (e) P3 forward only, Arm L LOWO by the Arm S code path (reproduces frozen A1 to 1e-16); route table rebuilt
