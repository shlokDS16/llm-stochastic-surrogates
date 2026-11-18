"""Outcome P-c (PREREG-acme section 4): the set-up SD of each model's effect against the three human yardsticks, in Many Labs 1 SD units.

Two steps, both CPU and reading human data plus gstudy.py output only:

  inputs  -> writes OUT/inputs/scale.csv (item, sd = sd_within) and OUT/inputs/se.csv (item, se = c_p in ML1-SD units) from
             runs/human-ml1-acme/arml_scales.csv, the two files gstudy.py reads with --scale and --single-site-se
             (the effect is divided by sd_within, so c_p must be in the same unit: column se_single_sd_units).
  compare -> reads OUT/setup_sd.csv (gstudy.py) and writes OUT/yardsticks.csv, one row per item x model (and the median-over-models
             row) x yardstick, with:
               setup_sd, its bootstrap interval;
               yardstick estimate and interval: S^H (SH_sd_units.csv, test-inversion interval), c_p (fixed, no interval),
               |pooled human effect| (pooled_sd_units.csv, REML, Wald interval; all ten intervals exclude zero, asserted);
               diff = setup_sd - yardstick;
               position of setup_sd relative to the human interval: below / inside / above (for c_p: below / above);
               separated = the model's interval lies wholly above or below the human interval (descriptive, not a test);
               ratio = setup_sd / yardstick, only where the yardstick estimate is > 0; for S^H, sh_lo_zero marks an interval
               that reaches 0 (the ratio is then flagged, never read as "humans agree").

    .venv/Scripts/python.exe -I analysis/acme/yardsticks.py inputs --out runs/acme-gstudy/A1
    .venv/Scripts/python.exe -I analysis/acme/yardsticks.py compare --out runs/acme-gstudy/A1
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / "runs" / "human-ml1-acme"


def make_inputs(out: Path) -> None:
    sc = pd.read_csv(H / "arml_scales.csv", dtype={"item": str})
    d = out / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    sc[["item"]].assign(sd=sc["sd_within"]).to_csv(d / "scale.csv", index=False)
    sc[["item"]].assign(se=sc["se_single_sd_units"]).to_csv(d / "se.csv", index=False)
    print(f"wrote {d / 'scale.csv'} and {d / 'se.csv'} ({len(sc)} items)")


def _position(x: float, lo: float, hi: float) -> str:
    return "below" if x < lo else ("above" if x > hi else "inside")


def compare(out: Path) -> None:
    s = pd.read_csv(out / "setup_sd.csv", dtype={"item": str, "model": str})
    sh = pd.read_csv(H / "SH_sd_units.csv", dtype={"item": str}).set_index("item")
    sc = pd.read_csv(H / "arml_scales.csv", dtype={"item": str}).set_index("item")
    hp = pd.read_csv(H / "pooled_sd_units.csv", dtype={"item": str}).set_index("item")
    assert (hp["mu_sd_lo"] * hp["mu_sd_hi"] > 0).all(), "a pooled-effect interval reaches zero; |mu| interval undefined"
    rows = []
    for r in s.itertuples(index=False):
        it = r.item
        mu, mlo, mhi = hp.at[it, "mu_sd"], hp.at[it, "mu_sd_lo"], hp.at[it, "mu_sd_hi"]
        amu_lo, amu_hi = sorted((abs(mlo), abs(mhi)))
        yard = {
            "S_H": (sh.at[it, "S_sd"], sh.at[it, "S_sd_lo"], sh.at[it, "S_sd_hi"]),
            "c_p": (sc.at[it, "se_single_sd_units"], None, None),
            "pooled_abs": (abs(mu), amu_lo, amu_hi),
        }
        for name, (est, lo, hi) in yard.items():
            x = float(r.setup_sd)
            if lo is None:
                pos = "above" if x > est else "below"
                sep = (r.lo > est) or (r.hi < est)
            else:
                pos = _position(x, lo, hi)
                sep = (r.lo > hi) or (r.hi < lo)
            rows.append(dict(item=it, model=r.model, setup_sd=x, setup_lo=r.lo, setup_hi=r.hi, yardstick=name,
                             y_est=est, y_lo=lo, y_hi=hi, diff=x - est, position=pos, separated=bool(sep),
                             ratio=(x / est) if est > 0 else None,
                             sh_lo_zero=bool(name == "S_H" and lo == 0)))
    pd.DataFrame(rows).to_csv(out / "yardsticks.csv", index=False)
    print(f"wrote {out / 'yardsticks.csv'} ({len(rows)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["inputs", "compare"])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out if a.out.is_absolute() else ROOT / a.out
    (make_inputs if a.step == "inputs" else compare)(out)


if __name__ == "__main__":
    main()
