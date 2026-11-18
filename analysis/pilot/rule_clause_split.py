"""Split of the observed 'fragile' labels by rule clause, from the stored A1 results (runs/pilot-side-by-side/table_a1.csv).
No estimation: reads sign_stability (sigma), llm_mu (dbar), llm_S (S) and rule_outcome, applies the two clauses of
pilot-design section 6 literally (point estimates, as side_by_side.rule_outcome does) and checks that the recomputed label
equals the stored one for all 42 grids.

    .venv/Scripts/python.exe -I analysis/pilot/rule_clause_split.py [--out runs/pilot-rule-calibration]

Outputs: clause_split.csv (one row per grid), clause_split_summary.csv, sigma_ge_09.csv, clause_split.md, config_clause_split.json, log_clause_split.txt.
"""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from side_by_side import rule_outcome  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="runs/pilot-rule-calibration")
a = ap.parse_args()
out = ROOT / a.out
out.mkdir(parents=True, exist_ok=True)
src = ROOT / "runs/pilot-side-by-side/table_a1.csv"
t = pd.read_csv(src)
LOG = []


def log(*x):
    s = " ".join(str(i) for i in x)
    LOG.append(s)
    print(s)


t["sigma"] = t.sign_stability
t["sigma_clause"] = t.sigma < 0.6
t["range_clause"] = (t.llm_mu - 2 * t.llm_S < 0) & (0 < t.llm_mu + 2 * t.llm_S)
t["clause"] = np.select([t.sigma_clause & t.range_clause, t.sigma_clause, t.range_clause], ["both", "sigma only", "range only"], "none")
t["rule_recomputed"] = [rule_outcome(r.sigma, r.llm_mu, r.llm_S, r.dbar_minus_2S_lower) for r in t.itertuples()]
mism = int((t.rule_recomputed != t.rule_outcome).sum())
log(f"grids {len(t)}; recomputed label differs from stored rule_outcome in {mism}")
assert mism == 0
f = t[t.rule_outcome == "fragile"]
sumry = f.groupby("clause").size().reindex(["sigma only", "range only", "both"], fill_value=0)
log("fragile grids:", len(f), dict(sumry))
by_p = pd.crosstab(f.paradigm, f.clause).reindex(columns=["sigma only", "range only", "both"], fill_value=0)
by_p.to_csv(out / "clause_split_by_paradigm.csv")
sumry.rename("n").to_csv(out / "clause_split_summary.csv")
cols = ["model", "paradigm", "sigma", "llm_mu", "llm_S", "rule_outcome", "sigma_clause", "range_clause", "clause", "dbar_minus_2S_lower", "nd_flag_any"]
t[cols].to_csv(out / "clause_split.csv", index=False)
hi = t[t.sigma >= 0.9][cols + ["sign_agrees_with_human"]]
hi.to_csv(out / "sigma_ge_09.csv", index=False)
log(f"grids with sigma >= 0.9: {len(hi)}")
log(hi[["model", "paradigm", "sigma", "llm_mu", "llm_S", "rule_outcome", "clause", "dbar_minus_2S_lower", "nd_flag_any"]].to_string(index=False))


def to_md(df, index=True):
    d = df.reset_index() if index else df
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns)
    body = ["| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return head + "\n" + "\n".join(body)


md = ["# Clause split of the observed fragile labels (A1, 42 grids)\n",
      f"Source: `{src.relative_to(ROOT).as_posix()}`; script `analysis/pilot/rule_clause_split.py`; recomputed labels equal the stored labels in 42/42 grids. Evidence level E4.\n",
      f"Fragile grids: {len(f)} of {len(t)}. Sigma clause only (sign stability < 0.6, range clause not met): {sumry['sigma only']}; "
      f"range clause only (dbar-2S < 0 < dbar+2S, sigma >= 0.6): {sumry['range only']}; both: {sumry['both']}.\n",
      "By paradigm (fragile grids):\n", to_md(by_p), "",
      f"\nGrids with sigma >= 0.9 ({len(hi)}):\n",
      to_md(hi[["model", "paradigm", "sigma", "llm_mu", "llm_S", "rule_outcome", "clause", "dbar_minus_2S_lower"]], index=False), ""]
(out / "clause_split.md").write_text("\n".join(md), encoding="utf8")
(out / "config_clause_split.json").write_text(json.dumps(dict(script="analysis/pilot/rule_clause_split.py", script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                           input=src.relative_to(ROOT).as_posix(), input_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                                                           python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, seed=None,
                                                           note="deterministic table logic; no random numbers"), indent=1), encoding="utf8")
(out / "log_clause_split.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
