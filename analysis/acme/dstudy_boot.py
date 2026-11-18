"""Bootstrap intervals over wordings for the D-study curves (blueprint M9; Fig 11).  Companion of gstudy.py, which writes the D-study
standard errors (dstudy.csv) but no interval.  This script imports gstudy.py unchanged (frozen file, not edited), rebuilds the per-item
arrays exactly as gstudy.run_cli does, repeats the wording bootstrap with the SAME seeds, estimator and B (so the bootstrap draws are the
draws behind components_by_item.csv), and writes, per item, n_w, n_o:  se (point), lo, hi (95 percent percentile interval of the
D-study SE over the bootstrap components, negative components counted as 0 as in gstudy.dstudy).

It then ASSERTS (i) that its point SE equals dstudy.csv and (ii) that its point components equal components_by_item.csv, so a mismatch
of --scale, --exclude or --effects against the run is caught.  It reads the effects table of the run: run it only after the lead session
has produced the real G-study, with the same --scale and --exclude arguments.

    .venv/Scripts/python.exe -I analysis/acme/dstudy_boot.py --gstudy runs/acme-gstudy/A1 --scale runs/acme-gstudy/A1/inputs/scale.csv \
        [--exclude exclude.csv] [--effects effects.csv] [--out <gstudy>/dstudy_boot.csv]
Writes OUT (default beside the gstudy output) and OUT.source.json (inputs hashed).  Never writes under paper/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402
import gstudy  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gstudy", default=str(rc.DEFAULT_GSTUDY))
    ap.add_argument("--effects", default=None, help="default: summary.json config.effects")
    ap.add_argument("--scale", default=None, help="scale.csv given to gstudy.py (default: <gstudy>/inputs/scale.csv when summary says scaled)")
    ap.add_argument("--exclude", default=None, help="exclude.csv given to gstudy.py, if any")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    gs = rc.resolve_arg(a.gstudy)
    tr = rc.Tracker()
    summ = tr.json(gs / "summary.json")
    cfg = summ["config"]
    eff_path = rc.resolve_arg(a.effects or cfg["effects"])
    if not eff_path.exists():
        eff_path = rc.ROOT / cfg["effects"]
    out = rc.resolve_arg(a.out, gs / "dstudy_boot.csv")
    rc.guard([out], True, gs, forbid_paper=True, allow_runs=True)

    import pandas as pd
    df = tr.csv(eff_path, dtype={"W": str, "O": str, "model": str, "item": str, "variant": str})
    df["O"] = df["O"].fillna("0")
    df["T"] = df["T"].astype(float)
    df = df[df["variant"] == "main"].copy()
    sd = None
    if cfg.get("scaled"):
        sp = rc.resolve_arg(a.scale) if a.scale else gs / "inputs" / "scale.csv"
        sc = tr.csv(sp, dtype={"item": str})
        sd = dict(zip(sc["item"], sc["sd"].astype(float)))
    excl = set()
    if a.exclude:
        ex = tr.csv(rc.resolve_arg(a.exclude), dtype=str)
        excl = set(zip(ex["model"], ex["item"]))
    comp = tr.csv(gs / "components_by_item.csv", dtype={"item": str, "component": str})
    comp = comp[comp["analysis"] == "T1"]
    ds = tr.csv(gs / "dstudy.csv", dtype={"item": str})
    est = gstudy.get_estimator(cfg["estimator"])
    boot_fn = gstudy.student_bootstrap if est["interval"] == "student" else gstudy.bootstrap
    B, seed = int(cfg["B"]), int(cfg["seed"])

    items = sorted(df["item"].unique())
    logd, arrs = [], []
    for it in items:
        sub = df[df["item"] == it]
        if sd is not None:
            sub = sub.assign(delta=sub["delta"] / sd[it])
        sub = sub[[(m, it) not in excl for m in sub["model"]]]
        arr, ms, ws, os_, _ = gstudy.build_arrays(sub)
        arr, ms = gstudy._complete_models(arr, ms, logd, it)
        a3 = arr[..., 0]
        if a3.shape[2] == 1:
            a3 = a3[:, :, 0]
        if float(np.var(a3)) >= gstudy.CONST_VAR:          # constant arrays are left out of the shares and the D-study, as in run_cli
            arrs.append((it, a3, len(os_)))
    rows = []
    for j, (it, a3, n_o_item) in enumerate(arrs):
        fac = gstudy.FACETS3 if a3.ndim == 3 else gstudy.FACETS2
        b = boot_fn(a3, fac, B, [seed, j, 1], shrink_fixed=est["shrink_fixed"])
        names = b["names"]
        # (i) the point components of this item must be the ones behind components_by_item.csv
        ci = comp[comp["item"] == it].set_index("component")["estimate_untruncated"]
        for n in names:
            assert abs(b["point"]["components"][n] - float(ci[n])) < 1e-9, f"components differ for {it}/{n}: check --scale/--exclude/--effects"
        n_w_grid = sorted(ds[ds["item"] == it]["n_w"].unique())
        n_o_grid = sorted(ds[ds["item"] == it]["n_o"].unique())
        c = np.maximum(b["comps"], 0.0)
        col = {n: k for k, n in enumerate(names)}
        vw = sum(c[:, col[n]] for n in ("W", "MW") if n in col)
        vr = sum(c[:, col[n]] for n in ("WO", "res") if n in col)
        pc = {n: max(float(v), 0.0) for n, v in b["point"]["components"].items()}
        pw = pc.get("W", 0.0) + pc.get("MW", 0.0)
        pr = pc.get("WO", 0.0) + pc.get("res", 0.0)
        for nw in n_w_grid:
            for no in n_o_grid:
                se_b = np.sqrt(vw / nw + vr / (nw * no))
                lo, hi = np.quantile(se_b, [0.025, 0.975])
                se0 = float(np.sqrt(pw / nw + pr / (nw * no)))
                got = float(ds[(ds["item"] == it) & (ds["n_w"] == nw) & (ds["n_o"] == no)]["se"].iloc[0])
                assert abs(se0 - got) < 1e-9, f"D-study SE differs from dstudy.csv for {it} {nw} {no}"
                rows.append(dict(item=it, n_w=int(nw), n_o=int(no), se=se0, lo=float(lo), hi=float(hi)))
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    rc.write_source([out], "analysis/acme/dstudy_boot.py", gs, tr, extra=dict(B=B, seed=seed, estimator=cfg["estimator"]))


if __name__ == "__main__":
    main()
