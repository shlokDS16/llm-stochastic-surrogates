"""Models per item after the exclusions of D0034 (descriptive benchmark; G3 failed).

Readings: validmass_only (PREREG section 7 rule); per_model (valid-mass + every model failing G4 under the 6cf3f5b rule, primary)
; per_type (valid-mass + model x response type failing G4, sensitivity). Arm L P2b is invalid for every model (D0034) in the two G4
readings. Writes runs/acme-L/rosters.csv (counts) and runs/acme-L/exclusions_{per_model,per_type}.csv (model,item; gstudy --exclude).

    .venv/Scripts/python.exe -I analysis/acme/rosters.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
L = ROOT / "runs" / "acme-L"
TYPE = {"P1": "binary", "AF": "binary", "NR": "binary", "P3": "rating", "QA": "rating",
        **{k: "numeric" for k in ("P2a", "P2b", "P2c", "P2d", "P4")}}


def main() -> None:
    vm = pd.read_csv(L / "outcomes" / "valid_mass.csv")
    b = pd.read_csv(L / "G4" / "by_model_type.csv")
    fail_m = set(b.loc[~b.passes, "model"])
    fail_mt = set(zip(b.loc[~b.passes, "model"], b.loc[~b.passes, "type"]))
    counts, excl = [], {"per_model": [], "per_type": []}
    for r in vm.itertuples(index=False):
        base = bool(r.excluded)
        for name, bad in (("per_model", r.model in fail_m), ("per_type", (r.model, TYPE[r.item]) in fail_mt)):
            if base or bad or r.item == "P2b":
                excl[name].append(dict(model=r.model, item=r.item))
    for it in sorted(vm.item.unique()):
        keep = vm[(vm.item == it) & (~vm.excluded)].model
        row = dict(item=it, validmass_only=len(keep))
        for name in excl:
            ex = {(e["model"], e["item"]) for e in excl[name]}
            row[name] = sum((m, it) not in ex for m in vm.model.unique())
        counts.append(row)
    pd.DataFrame(counts).to_csv(L / "rosters.csv", index=False)
    for name, rows in excl.items():
        pd.DataFrame(rows).to_csv(L / f"exclusions_{name}.csv", index=False)
    print(pd.DataFrame(counts).set_index("item").T.to_string())


if __name__ == "__main__":
    main()
