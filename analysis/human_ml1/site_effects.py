"""Human benchmark, step 1: site-level effects from the tidy ML1 files, plus the moment-estimator spread S^H.

Reads  data/processed/ml1/<P>.csv  (built by build_tidy.py)
Writes runs/human-ml1/site_effects.csv      one row per paradigm x metric x site: n1, n0, d, v, sd_pooled, mean1, mean0
       runs/human-ml1/moment_summary.json   dbar, S2hat, S^H and bootstrap CI per paradigm x metric
Metric ids: primary = 'primary', sensitivity = 'sens_*' (see METRICS).
Run: .venv/Scripts/python.exe -I analysis/human_ml1/site_effects.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "pilot"))
import estimators as E  # noqa: E402

TIDY = ROOT / "data/processed/ml1"
OUT = ROOT / "runs/human-ml1"
B = 2000
SEED = 20261015

# paradigm -> list of (metric id, kind, column)
METRICS = {
    "P1": [("primary", "binary", "y"), ("check_ml1_g_on_01", "cont", "y")],                     # log OR of choosing the sure program, gain vs loss
    "P2a": [("primary", "cont", "y"), ("sens_log", "cont", "y_log"), ("check_ml1_rank", "cont", "y_rank")],
    "P2b": [("primary", "cont", "y"), ("sens_log", "cont", "y_log"), ("check_ml1_rank", "cont", "y_rank")],
    "P2c": [("primary", "cont", "y"), ("sens_log", "cont", "y_log"), ("check_ml1_rank", "cont", "y_rank")],
    "P2d": [("primary", "cont", "y"), ("sens_log", "cont", "y_log"), ("check_ml1_rank", "cont", "y_rank")],
    "P3": [("primary", "cont", "y")],
    "P4check": [("check_ml1_released_group", "cont", "y")],  # ML1 released gambfalgroup/gambfalDV (reproduces published Q)
    "P4": [("primary", "cont", "y"), ("sens_raw", "cont", "y_raw"), ("check_ml1_sqrt", "cont", "y_sqrt")],  # primary = log(1+x), sensitivity = raw estimate
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows, summary = [], {}
    for p, mets in METRICS.items():
        df = pd.read_csv(TIDY / f"{p}.csv")
        sites = sorted(df.site.unique())
        for mid, kind, col in mets:
            dd, vv, ys = [], [], []
            for s in sites:
                g = df[df.site == s]
                y1 = g.loc[g.x == 1, col].to_numpy(float)
                y0 = g.loc[g.x == 0, col].to_numpy(float)
                d, v = E.effect(kind, y1, y0)
                n1, n0 = len(y1), len(y0)
                sp = float(np.sqrt(((n1 - 1) * y1.var(ddof=1) + (n0 - 1) * y0.var(ddof=1)) / (n1 + n0 - 2))) if kind == "cont" else np.nan
                rows.append(dict(paradigm=p, metric=mid, kind=kind, site=s, n1=n1, n0=n0, d=float(d), v=float(v),
                                 sd_pooled=sp, mean1=float(y1.mean()), mean0=float(y0.mean())))
                dd.append(d); vv.append(v)
                ys.append((y1, y0))
            dd, vv = np.array(dd), np.array(vv)
            # within-site response-level bootstrap of the moment estimator
            bd = np.empty((B, len(sites))); bv = np.empty((B, len(sites)))
            for j, (y1, y0) in enumerate(ys):
                bd[:, j], bv[:, j] = E.boot_effect(kind, y1, y0, rng, B)
            s2_b = E.spread_s2(bd, bv)
            S_b = np.sqrt(np.maximum(0, s2_b))
            s2 = float(E.spread_s2(dd, vv))
            s2_star = float(((dd - dd.mean()) ** 2).mean())
            q2 = lambda x, p_: float(np.quantile(x, p_))
            s2_basic = [s2 - (q2(s2_b, .975) - s2_star), s2 - (q2(s2_b, .025) - s2_star)]
            summary[f"{p}/{mid}"] = dict(
                paradigm=p, metric=mid, kind=kind, n_sites=len(sites), n_total=int(sum(len(a) + len(b) for a, b in ys)),
                dbar=float(dd.mean()), S2_untruncated=s2, S=float(np.sqrt(max(0, s2))),
                S_ci95=[float(np.sqrt(max(0, s2_basic[0]))), float(np.sqrt(max(0, s2_basic[1])))],   # basic bootstrap (working)
                S2_ci95_basic=s2_basic,
                S_ci95_percentile=[float(np.quantile(S_b, .025)), float(np.quantile(S_b, .975))],
                S2_ci95_percentile=[float(np.quantile(s2_b, .025)), float(np.quantile(s2_b, .975))],
                share_sites_positive_sign=float((dd > 0).mean()),
                boot_B=B, seed=SEED)
            print(p, mid, "k=%d dbar=%.3f S=%.3f CI=[%.3f, %.3f]" % (len(sites), dd.mean(), summary[f"{p}/{mid}"]["S"], *summary[f"{p}/{mid}"]["S_ci95"]))
    pd.DataFrame(rows).to_csv(OUT / "site_effects.csv", index=False)
    (OUT / "moment_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
