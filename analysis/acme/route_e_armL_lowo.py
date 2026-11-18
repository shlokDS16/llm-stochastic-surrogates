"""E7b item 2: leave-one-wording-out (LOWO) shares for column (e) Arm L, by the same code path as Arm S (post-outcome, descriptive).

The (e)-Arm L effect arrays (M, W, O, T) or (M, W, T) in ML1-SD units (W0-W3, T 0.7/1.0, intersection roster, P3 forward only) are
passed to gstudy_armS.estimate with draw noise v = 0. With v = 0, A1-S reduces to the frozen A1 estimator (E1 = E2 = A1 jackknife-corrected
shares; gstudy_armS selftest), and its delete-one-wording shares are A1's own jackknife inputs, i.e. the same LOWO definition as the Arm S
half of (e). The script checks its point shares against the frozen gstudy.py output (components_by_item.csv, analysis '4facet').
Frozen A1 intervals stay in components_by_item.csv (E7: Arm L columns keep the frozen inference); they come from a bootstrap-t
validated at 10 wordings only, not at 4 (stated beside them).
    .venv/Scripts/python.exe -I analysis/acme/route_e_armL_lowo.py
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gstudy as G          # frozen, imported only
import gstudy_armS as S

ROOT = HERE.parents[1]
D = ROOT / "runs/acme-gstudy/A1-route-e-armL"

def main():
    eff = pd.read_csv(D / "inputs/effects.csv", dtype={"W": str, "O": str, "model": str, "item": str, "variant": str})
    eff["O"] = eff["O"].fillna("0")
    sc = pd.read_csv(ROOT / "runs/acme-gstudy/A1/inputs/scale.csv")
    sd = dict(zip(sc["item"], sc["sd"]))
    ref = pd.read_csv(D / "components_by_item.csv")
    ref = ref[ref["analysis"] == "4facet"]
    rows, worst = [], 0.0
    for it, sub in eff.groupby("item"):
        sub = sub.assign(delta=sub["delta"] / sd[it])
        arr, ms, ws, os_, ts = G.build_arrays(sub, temps=sorted(sub["T"].unique()))
        assert np.isfinite(arr).all(), it
        if arr.shape[2] == 1:
            arr = arr[:, :, 0, :]
        fac = G.FACETS4 if arr.ndim == 4 else G.FACETS3T
        est = S.estimate(arr, np.zeros_like(arr), fac)
        names = list(est["names"])
        r = ref[ref["item"] == it].set_index("component")
        for k, nm in enumerate(names):
            share = float(est["e2"][k])
            lo = est["loo_e2"][:, k]
            if nm in r.index:
                worst = max(worst, abs(share - float(r.at[nm, "share"])))
            rows.append(dict(item=it, n_models=arr.shape[0], term=nm, share=share, lowo_min=float(lo.min()), lowo_max=float(lo.max()),
                             **{f"lowo_drop_{ws[w]}": float(lo[w]) for w in range(lo.shape[0])}))
    out = pd.DataFrame(rows)
    out.to_csv(D / "lowo.csv", index=False)
    print("wrote", D / "lowo.csv", len(out), "rows; max |share - frozen A1 share| =", worst)
    assert worst < 1e-9, "LOWO code path does not reproduce frozen A1 shares"

if __name__ == "__main__":
    main()
