"""Diagnostic (not preregistered; reported as such): agreement between the two forward passes that score a rating prompt in Arm L.

Arm L rating records (P3, QA) hold (i) a single pass at the answer position: candidate logits `cand_logits` for `cand_ids` and the
full-vocabulary LSE `lse[T]`, and (ii) the answer paths `paths[label]` (primary readout, amendment A-L3), each scored in its own
teacher-forced pass with its own `tgt_logits` and `lse`. For a single-token path the two passes score the same token at the same
position, so their log-probabilities should agree up to bf16 numerics. This script measures that gap and its effect on the two
quantities read downstream: valid mass (gate G3) and the renormalised outcome y.

Per record and T: d_logp = path log p - single-pass log p for each single-token path whose id is a candidate; valid_path (what
armL_outcomes.py uses) and valid_single (sum of single-pass probabilities over the same labels' single-token ids); y_path and
y_single (renormalised canonical rating, single-token paths only on both sides so the comparison is like for like).
CPU only; reads runs/acme-L/<model>/{P3,QA}.jsonl; writes runs/acme-L/diagnostics/pass_consistency_{records.csv,summary.json}.

    .venv/Scripts/python.exe -I analysis/acme/pass_consistency.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "acme-L"
OUT = RUNS / "diagnostics"
TEMPS = ("0.3", "0.7", "1.0", "1.5")
FWD = {"P3": lambda r: r, "QA": lambda r: 10 - r}
REV = {"P3": lambda r: 10 - r, "QA": lambda r: r}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, gaps = [], []
    models = sorted(p.name for p in RUNS.iterdir() if p.is_dir() and (p / "QA.jsonl").exists())
    for m in models:
        for it in ("P3", "QA"):
            with open(RUNS / m / f"{it}.jsonl", encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if "paths" not in r or "cand_ids" not in r:
                        continue
                    pos = {t: k for k, t in enumerate(r["cand_ids"])}
                    f_c = (REV if r["O"] == "reversed" else FWD)[it]
                    for T in TEMPS:
                        t = float(T)
                        mp, ms = {}, {}
                        for L, ps in r["paths"].items():
                            for p in ps:
                                if len(p["ids"]) != 1 or p["ids"][0] not in pos:
                                    continue
                                lp_path = p["tgt_logits"][0] / t - p["lse"][T][0]
                                lp_one = r["cand_logits"][pos[p["ids"][0]]] / t - r["lse"][T]
                                gaps.append(dict(model=m, item=it, T=t, d_logp=lp_path - lp_one, p_one=math.exp(lp_one)))
                                mp[int(L)] = mp.get(int(L), 0.0) + math.exp(lp_path)
                                ms[int(L)] = ms.get(int(L), 0.0) + math.exp(lp_one)
                        vp, vs = sum(mp.values()), sum(ms.values())
                        rows.append(dict(model=m, item=it, W=r["W"], O=r["O"], x=r["x"], variant=r["variant"], T=t,
                                         valid_path=vp, valid_single=vs,
                                         y_path=sum(f_c(k) * v for k, v in mp.items()) / vp if vp > 0 else None,
                                         y_single=sum(f_c(k) * v for k, v in ms.items()) / vs if vs > 0 else None))
    rec = pd.DataFrame(rows)
    rec["dy"] = rec["y_path"] - rec["y_single"]
    rec.to_csv(OUT / "pass_consistency_records.csv", index=False)
    g = pd.DataFrame(gaps)
    g_top = g[g["p_one"] > 0.01]
    summ = dict(
        n_records=int(len(rec) / len(TEMPS)), n_gaps=len(g), n_gaps_p_gt_001=len(g_top),
        logit_gap_T1=dict(  # at T = 1 d_logp is the raw logit gap minus the LSE gap
            median_abs=float(g_top[g_top["T"] == 1.0]["d_logp"].abs().median()),
            p95_abs=float(g_top[g_top["T"] == 1.0]["d_logp"].abs().quantile(0.95)),
            max_abs=float(g_top[g_top["T"] == 1.0]["d_logp"].abs().max())),
        by_T={T: dict(valid_path_gt_1001=int((rec[rec["T"] == float(T)]["valid_path"] > 1.001).sum()),
                      valid_path_max=float(rec[rec["T"] == float(T)]["valid_path"].max()),
                      valid_single_max=float(rec[rec["T"] == float(T)]["valid_single"].max()),
                      dy_median_abs=float(rec[rec["T"] == float(T)]["dy"].abs().median()),
                      dy_p95_abs=float(rec[rec["T"] == float(T)]["dy"].abs().quantile(0.95)),
                      dy_max_abs=float(rec[rec["T"] == float(T)]["dy"].abs().max())) for T in TEMPS},
        by_model_T1=rec[rec["T"] == 1.0].groupby("model").agg(dy_median_abs=("dy", lambda s: float(s.abs().median())),
                                                              valid_path_max=("valid_path", "max")).to_dict("index"),
        note="P1, AF and NR paths are multi-token or have no single-pass candidate table, so they are not covered here.",
    )
    (OUT / "pass_consistency_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps({k: summ[k] for k in ["n_records", "n_gaps_p_gt_001", "logit_gap_T1", "by_T"]}, indent=1))


if __name__ == "__main__":
    main()
