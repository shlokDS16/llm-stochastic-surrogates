"""Valid-mass exclusions (PREREG-acme section 7) and gate G3 (section 6) from runs/acme-L/outcomes/outcomes.csv. CPU, no outcome values read.

Rule (frozen): a model-item pair is excluded from the primary analysis of the item when valid mass < 0.9 on more than 5 percent of its
prompts at T = 1. "Its prompts" is read as the prompts that enter the primary analysis (variant 'main', both conditions, every wording
and order); the same rule over all variants (decoys and no-anchor baselines included) is written beside it for comparison.
G3 (frozen): Arm L complete for at least 10 models and 8 of 10 items with valid readouts. Two readings are reported, and G3 passes
only if both hold: (a) at least 10 models are valid on at least 8 of the 10 items; (b) at least 8 items have at least 10 valid models.
Only the `valid` column (mass of valid answers) is read; the outcome `y` is not.

    .venv/Scripts/python.exe -I analysis/acme/gate_g3.py [--outcomes runs/acme-L/outcomes/outcomes.csv] [--out runs/acme-L/outcomes]
Writes exclusions.csv (model,item, the input of gstudy.py --exclude), valid_mass.csv (every pair) and G3.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

THRESH, MAX_SHARE, T_REF = 0.9, 0.05, 1.0
N_MODELS, N_ITEMS_MIN, N_MODELS_MIN = 14, 8, 10


def pair_table(o: pd.DataFrame) -> pd.DataFrame:
    o = o[o["T"].astype(float) == T_REF]
    g = o.groupby(["model", "item"])["valid"]
    t = pd.DataFrame({"n_prompts": g.size(), "n_low": g.apply(lambda v: int((v < THRESH).sum())), "min_valid": g.min(),
                      "median_valid": g.median()}).reset_index()
    t["share_low"] = t["n_low"] / t["n_prompts"]
    t["excluded"] = t["share_low"] > MAX_SHARE
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outcomes", default="runs/acme-L/outcomes/outcomes.csv")
    ap.add_argument("--out", default="runs/acme-L/outcomes")
    a = ap.parse_args()
    o = pd.read_csv(a.outcomes, usecols=["model", "item", "W", "O", "x", "variant", "T", "valid"], dtype={"W": str, "O": str})
    main_t = pair_table(o[o["variant"] == "main"])
    all_t = pair_table(o).rename(columns={c: c + "_allvariants" for c in ["n_prompts", "n_low", "min_valid", "median_valid", "share_low", "excluded"]})
    t = main_t.merge(all_t, on=["model", "item"], how="left")
    out = Path(a.out)
    t.to_csv(out / "valid_mass.csv", index=False)
    t.loc[t["excluded"], ["model", "item"]].to_csv(out / "exclusions.csv", index=False)
    models = sorted(t["model"].unique())
    items = sorted(t["item"].unique())
    ok = t[~t["excluded"]]
    per_model = ok.groupby("model")["item"].nunique().reindex(models, fill_value=0)
    per_item = ok.groupby("item")["model"].nunique().reindex(items, fill_value=0)
    ra = int((per_model >= N_ITEMS_MIN).sum())
    rb = int((per_item >= N_MODELS_MIN).sum())
    res = dict(
        rule=dict(threshold=THRESH, max_share=MAX_SHARE, T=T_REF, prompts="variant main, both conditions"),
        n_models_complete=len(models), n_items=len(items), n_pairs=len(t), n_excluded=int(t["excluded"].sum()),
        n_excluded_allvariants=int(t["excluded_allvariants"].sum()),
        excluded=[f"{m}|{i}" for m, i in t.loc[t["excluded"], ["model", "item"]].itertuples(index=False)],
        valid_items_per_model=per_model.to_dict(), valid_models_per_item=per_item.to_dict(),
        G3_reading_a=dict(models_valid_on_8plus_items=ra, required=N_MODELS_MIN, holds=ra >= N_MODELS_MIN),
        G3_reading_b=dict(items_with_10plus_valid_models=rb, required=N_ITEMS_MIN, holds=rb >= N_ITEMS_MIN),
    )
    res["G3_pass"] = bool(len(models) == N_MODELS and res["G3_reading_a"]["holds"] and res["G3_reading_b"]["holds"])
    (out / "G3.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ["n_models_complete", "n_excluded", "n_excluded_allvariants", "G3_reading_a", "G3_reading_b", "G3_pass"]}))


if __name__ == "__main__":
    main()
