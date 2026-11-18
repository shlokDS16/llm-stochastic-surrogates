"""E7 item 6, column (a): Arm S set-up SD per model for the descriptive human-yardstick comparison (post-outcome, exploratory).

Set-up SD = finite SD (ddof = 1) of the cell effect Delta-hat = (ybar1 - ybar0) / sd (ML1-SD units, runs/acme-S-gstudy/cells.csv) over
the (wording, order) cells at T = 1.0, the same definition as gstudy.setup_sd (frozen gstudy.py) applied to W0-W3 x orders.
Two rows per model, fixed before any value was read:
    setup_sd           raw SD of the noisy cell means (includes draw noise; n = 50 draws per condition)
    setup_sd_drawcorr  sqrt(max(SD^2 - mean(v_c), 0)), the expected-effect spread with mean draw-noise variance removed
No interval is computed (E7a item 1: no interval of any kind for real Arm S data), so lo and hi are empty and the frozen
yardsticks.py reports position only (its "separated" is then False by construction and is not read).
Roster: runs/acme-S-gstudy/roster_strict.csv (ok == True); items with fewer than 3 models are left out.
Four wordings x two orders is a lower bound on the set-up spread of the ten-wording design (E7 item 6).
    .venv/Scripts/python.exe -I analysis/acme/armS_setup_sd.py
    .venv/Scripts/python.exe -I analysis/acme/yardsticks.py compare --out runs/acme-S-gstudy/route-a-yardsticks/raw
    .venv/Scripts/python.exe -I analysis/acme/yardsticks.py compare --out runs/acme-S-gstudy/route-a-yardsticks/drawcorr
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/acme-S-gstudy/route-a-yardsticks"

def main():
    c = pd.read_csv(ROOT / "runs/acme-S-gstudy/cells.csv", dtype={"O": str, "W": str})
    r = pd.read_csv(ROOT / "runs/acme-S-gstudy/roster_strict.csv")
    ok = set(zip(r.loc[r["ok"], "model"], r.loc[r["ok"], "item"]))
    c = c[(c["T"] == 1.0).to_numpy() & np.array([(m, i) in ok for m, i in zip(c["model"], c["item"])], dtype=bool)]
    raw, cor = [], []
    for it, g in c.groupby("item"):
        ms = sorted(g["model"].unique())
        if len(ms) < 3:
            continue
        sds, sdc = [], []
        for m in ms:
            h = g[g["model"] == m]
            assert len(h) == h["W"].nunique() * max(1, h["O"].nunique()), (it, m)
            s2 = float(np.var(h["delta"].to_numpy(), ddof=1))
            vbar = float(h["v_c"].mean())
            sds.append(np.sqrt(s2)); sdc.append(np.sqrt(max(s2 - vbar, 0.0)))
            raw.append(dict(item=it, model=m, setup_sd=sds[-1], lo=np.nan, hi=np.nan, n_cells=len(h)))
            cor.append(dict(item=it, model=m, setup_sd=sdc[-1], lo=np.nan, hi=np.nan, n_cells=len(h)))
        raw.append(dict(item=it, model="__median__", setup_sd=float(np.median(sds)), lo=np.nan, hi=np.nan, n_cells=np.nan))
        cor.append(dict(item=it, model="__median__", setup_sd=float(np.median(sdc)), lo=np.nan, hi=np.nan, n_cells=np.nan))
    for name, rows in (("raw", raw), ("drawcorr", cor)):
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(d / "setup_sd.csv", index=False)
        print("wrote", d / "setup_sd.csv", len(rows))

if __name__ == "__main__":
    main()
