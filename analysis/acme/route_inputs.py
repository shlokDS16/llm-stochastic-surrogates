"""E7 route table, Arm L columns (b) and (c): derived gstudy inputs (post-outcome, exploratory, descriptive).

Writes, for each column, an effects table restricted to items with at least 3 models left on that column's roster (the
decomposability floor of the agreed debate research/debates/2026-11-07-CRP-S09-acme-post-gate-analysis, round 3, column d), and
copies the column's exclusion list. The frozen analysis/acme/gstudy.py is then run unchanged on these inputs.
    (b) per-type roster:  runs/acme-L/exclusions_per_type.csv
    (c) per-model roster: runs/acme-L/exclusions_per_model.csv (the 5 G4-passing models, valid-mass and P2b exclusions applied)
Usage: .venv/Scripts/python.exe -I analysis/acme/route_inputs.py
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EFF = ROOT / "runs/acme-L/outcomes/effects.csv"
COLS = {"A1-route-b-pertype": "runs/acme-L/exclusions_per_type.csv",
        "A1-route-c-permodel": "runs/acme-L/exclusions_per_model.csv"}
MIN_MODELS = 3

def main():
    eff = pd.read_csv(EFF, dtype={"W": str, "O": str, "model": str, "item": str, "variant": str})
    models = sorted(eff["model"].unique())
    for col, exf in COLS.items():
        ex = pd.read_csv(ROOT / exf, dtype=str)
        excl = set(zip(ex["model"], ex["item"]))
        n_left = {it: sum((m, it) not in excl for m in models) for it in sorted(eff["item"].unique())}
        keep = [it for it, n in n_left.items() if n >= MIN_MODELS]
        out = ROOT / "runs/acme-gstudy" / col / "inputs"
        out.mkdir(parents=True, exist_ok=True)
        eff[eff["item"].isin(keep)].to_csv(out / "effects.csv", index=False)
        ex.to_csv(out / "exclude.csv", index=False)
        (out / "roster.json").write_text(json.dumps(dict(source_exclusions=exf, models_left=n_left, decomposed=keep,
                                                         not_decomposed={k: v for k, v in n_left.items() if k not in keep},
                                                         min_models=MIN_MODELS), indent=1))
        print(col, "decomposed:", keep, "| left:", n_left)

if __name__ == "__main__":
    main()
