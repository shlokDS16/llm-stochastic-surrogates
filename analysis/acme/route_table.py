"""E7 route table: merges the route columns into one long table (post-outcome, exploratory, descriptive; equal billing, no primary column).

Columns merged (every value is read from a file written by the analysis scripts; nothing is typed in):
  (a)       runs/acme-S-gstudy/route-a                  Arm S A1-S, strict roster                (gstudy_armS.py)
  (b)       runs/acme-gstudy/A1-route-b-pertype         Arm L frozen A1, per-type roster         (gstudy.py)
  (c)       runs/acme-gstudy/A1-route-c-permodel        Arm L frozen A1, the 5 G4-passing models (gstudy.py)
  (d)       runs/acme-L/rosters.csv                     Arm L per-model roster: counts only, not decomposed
  (e)-Arm S runs/acme-S-gstudy/route-e-armS             A1-S on the intersection roster          (gstudy_armS.py)
  (e)-Arm L runs/acme-gstudy/A1-route-e-armL            frozen A1 on the intersection roster, W0-W3, T 0.7/1.0 (gstudy.py)
Sensitivities S-a to S-e (Arm S only): runs/acme-S-gstudy/sens-S-a ... sens-S-e -> sens_table.csv.

Long format, one row per (column, item, analysis, component, basis):
  column, arm, item, n_models, n_wordings, temps, facets, analysis, component, basis, share, lowo_min, lowo_max, share_lo, share_hi,
  draw_share, note
  Arm S: basis E1 (expected-effect shares, no draw component) and E2 (variance of one 50-draw estimate, draw noise a component); share = point
  estimate; lowo_min/lowo_max = range of the leave-one-wording-out values (fragility over the wordings, NOT uncertainty); share_lo/share_hi empty
  (no interval of any kind is computed for real Arm S data, E7a item 1). draw_share = E2 share of the draw component of the item (E7a item 2).
  Arm L: basis A1 (frozen A1 share), share_lo/share_hi = the frozen A1 interval (labelled underpowered); analysis = '4facet' (M, W, O, T over all
  temperatures in the inputs) or 'T1' (T = 1.0 only, three facets); lowo empty.
  An item that was not decomposed (fewer than 3 models on the roster) has one row with an empty component and the reason in note.

    .venv/Scripts/python.exe -I analysis/acme/route_table.py            (writes route-table/ and the README files of the Arm L route directories)
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S = ROOT / "runs/acme-S-gstudy"
L = ROOT / "runs/acme-gstudy"
OUT = L / "route-table"
ITEMS = ["P1", "AF", "NR", "P3", "QA", "P2a", "P2b", "P2c", "P2d", "P4"]
COLS = ["column", "arm", "item", "n_models", "n_wordings", "temps", "facets", "analysis", "component", "basis", "share", "lowo_min", "lowo_max",
        "share_lo", "share_hi", "draw_share", "note"]
ARM_S = {"(a)": S / "route-a", "(e)-ArmS": S / "route-e-armS"}
ARM_L = {"(b)": L / "A1-route-b-pertype", "(c)": L / "A1-route-c-permodel", "(e)-ArmL": L / "A1-route-e-armL"}
NOTE_L = {"(e)-ArmL": "frozen A1 interval, underpowered; the studentized bootstrap-t was validated at 10 wordings and is not valid at 4 (EXPERT-statistician.md section 2): intervals at 4 wordings are not interpreted; LOWO from route_e_armL_lowo.py (E7b item 2); P3 uses the forward order only (E7b item 1)"}
SENS = {"S-a": "loose roster 0.8/0.2", "S-b": "cells with validity >= 0.9 (every cell, both conditions)", "S-c": "T = 1.0 only (no T facet)",
        "S-d": "logit scale, binary items (clip +-12)", "S-e": "drop W0 (W1-W3 only)"}


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def nn(x):
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else x


def armS_rows(label, d, note_prefix=""):
    summ = json.loads((d / "summary.json").read_text(encoding="utf8"))
    rows = []
    for it in ITEMS:
        if it in summ["not_decomposed"]:
            rows.append(dict(column=label, arm="S", item=it, component="", note=note_prefix + "not decomposed: " + summ["not_decomposed"][it]))
            continue
        if it not in summ["items"]:
            continue
        s = summ["items"][it]
        c = pd.read_csv(d / f"components_{it}.csv")
        draw = float(c[c["term"] == "draw"]["E2_share"].iloc[0])
        base = dict(column=label, arm="S", item=it, n_models=s["n_models"], n_wordings=len(s["wordings"]), temps=",".join(str(t) for t in s["temps"]),
                    facets="".join(s["facets"]), analysis="A1-S", draw_share=draw, note=note_prefix.strip())
        if "clip_rate" in s:
            base["note"] = (base["note"] + " " if base["note"] else "") + f"clip rate {s['clip_rate']:.4f}"
        for r in c.itertuples(index=False):
            rows.append(dict(base, component=r.term, basis="E2", share=r.E2_share, lowo_min=r.E2_lowo_min, lowo_max=r.E2_lowo_max))
            if not pd.isna(r.E1_share):
                rows.append(dict(base, component=r.term, basis="E1", share=r.E1_share, lowo_min=r.E1_lowo_min, lowo_max=r.E1_lowo_max))
    return rows


def armL_rows(label, d):
    roster = json.loads((d / "inputs" / "roster.json").read_text(encoding="utf8"))
    eff = pd.read_csv(d / "inputs" / "effects.csv", dtype={"W": str, "O": str, "item": str, "variant": str})
    eff = eff[eff["variant"] == "main"]
    comp = pd.read_csv(d / "components_by_item.csv")
    # E7b item 2: (e)-Arm L also carries LOWO values (route_e_armL_lowo.py, same code path as Arm S), beside its frozen A1 interval
    lowo = {}
    if (d / "lowo.csv").exists():
        lw = pd.read_csv(d / "lowo.csv")
        lowo = {(r.item, r.term): (r.lowo_min, r.lowo_max) for r in lw.itertuples(index=False)}
    rows = []
    for it in ITEMS:
        if it in roster["not_decomposed"]:
            rows.append(dict(column=label, arm="L", item=it, n_models=roster["not_decomposed"][it], component="",
                             note=f"not decomposed: {roster['not_decomposed'][it]} models on this roster (floor {roster['min_models']})"))
            continue
        if it not in roster["decomposed"]:
            continue
        e = eff[eff["item"] == it]
        for an in ("4facet", "T1"):
            c = comp[(comp["item"] == it) & (comp["analysis"] == an)]
            if c.empty:
                continue
            letters = "".join(f for f in "MWOT" if any(f in str(n) for n in c["component"]))
            temps = ",".join(str(t) for t in sorted(e["T"].unique())) if an == "4facet" else "1.0"
            for r in c.itertuples(index=False):
                rows.append(dict(column=label, arm="L", item=it, n_models=int(r.n_models), n_wordings=int(e["W"].nunique()), temps=temps, facets=letters,
                                 analysis=an, component=r.component, basis="A1", share=r.share, share_lo=r.share_lo, share_hi=r.share_hi,
                                 lowo_min=lowo.get((it, r.component), (None, None))[0] if an == "4facet" else None,
                                 lowo_max=lowo.get((it, r.component), (None, None))[1] if an == "4facet" else None,
                                 note=NOTE_L.get(label, "frozen A1 interval, underpowered")))
    return rows


def count_rows():
    r = pd.read_csv(L.parent / "acme-L" / "rosters.csv")
    rows = []
    for it in ITEMS:
        x = r[r["item"] == it].iloc[0]
        rows.append(dict(column="(d)", arm="L", item=it, n_models=int(x["per_model"]), component="",
                         note=f"count only, not decomposed (runs/acme-L/rosters.csv: per_model {int(x['per_model'])}; also valid-mass only {int(x['validmass_only'])}, "
                              f"per type {int(x['per_type'])})"))
    return rows


def readme(d: Path, title, what, roster, command, extra=""):
    head = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--", "analysis/acme"))
    last = git("log", "-1", "--format=%h %s", "--", str(d.relative_to(ROOT)).replace("\\", "/"))
    lines = [f"# {title}", "", what, "", f"- roster: {roster}", f"- command: `{command}`",
             f"- code commit at the time this README was written (HEAD): `{head}`; uncommitted changes under analysis/acme: {dirty}"]
    if last:
        lines.append(f"- last commit that touched this directory before this README: {last}")
    if extra:
        lines += ["", extra]
    (d / "README.md").write_text("\n".join(lines) + "\n", encoding="utf8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for lab, d in ARM_S.items():
        rows += armS_rows(lab, d, "")
    for lab, d in ARM_L.items():
        rows += armL_rows(lab, d)
    rows += count_rows()
    order = {"(a)": 0, "(b)": 1, "(c)": 2, "(d)": 3, "(e)-ArmS": 4, "(e)-ArmL": 5}
    df = pd.DataFrame(rows).reindex(columns=COLS)
    df["_o"] = df["column"].map(order)
    df["_i"] = df["item"].map({k: i for i, k in enumerate(ITEMS)})
    df = df.sort_values(["_o", "_i"], kind="stable").drop(columns=["_o", "_i"])
    df.to_csv(OUT / "route_table.csv", index=False)
    srows = []
    for tag, desc in SENS.items():
        d = S / f"sens-{tag}"
        for r in armS_rows(f"sens-{tag}", d, f"{tag}: {desc}."):
            srows.append(dict(r))
    sdf = pd.DataFrame(srows).reindex(columns=COLS)
    sdf.insert(0, "sens", sdf["column"].str.replace("sens-", "", regex=False))
    sdf.to_csv(OUT / "sens_table.csv", index=False)
    print("route_table rows", len(df), "| sens_table rows", len(sdf))

    # READMEs
    py = ".venv/Scripts/python.exe -I"
    readme(OUT, "Route table (E7 item 2) and sensitivity table (E7 item 4)",
           "`route_table.csv`: columns (a), (b), (c), (d), (e)-Arm S, (e)-Arm L in one long table; `sens_table.csv`: sensitivities S-a to S-e (Arm S only). "
           "Post-outcome, exploratory, descriptive; equal billing, no primary column; each column names its model population and the shares are not "
           "called a common estimand across columns. Column semantics are in the docstring of `analysis/acme/route_table.py`. Arm S rows carry point "
           "estimates and the leave-one-wording-out (LOWO) range only (fragility over the wordings, not uncertainty; no interval of any kind, E7a item 1); "
           "Arm L rows carry the frozen A1 interval (underpowered). In the four-wording arrays (column (a) and Arm S and Arm L in column (e)) differences "
           "smaller than 0.06 on a share are not interpreted (E7a item 3).",
           "see the per-column READMEs: runs/acme-S-gstudy/route-a, runs/acme-gstudy/A1-route-b-pertype, A1-route-c-permodel, "
           "runs/acme-S-gstudy/route-e-armS, runs/acme-gstudy/A1-route-e-armL", f"{py} analysis/acme/route_table.py")
    gcmd = ("{py} analysis/acme/gstudy.py --effects {d}/inputs/effects.csv --scale runs/acme-gstudy/A1/inputs/scale.csv "
            "--single-site-se runs/acme-gstudy/A1/inputs/se.csv --out {d} --estimator A1")
    for lab, d, ros in (("(b)", ARM_L["(b)"], "per-type: runs/acme-L/exclusions_per_type.csv"),
                        ("(c)", ARM_L["(c)"], "per-model: runs/acme-L/exclusions_per_model.csv (the 5 G4-passing models)")):
        rel = str(d.relative_to(ROOT)).replace("\\", "/")
        readme(d, f"Column {lab}: Arm L, frozen gstudy.py A1", "Frozen `analysis/acme/gstudy.py --estimator A1` (B = 2000, seed 20261106) on the Arm L effects table "
               "restricted by `analysis/acme/route_inputs.py` to items with at least 3 models on the roster (decomposability floor). All ten wordings, four "
               "temperatures. Shares carry the frozen A1 inference, labelled underpowered. `hypotheses.json` is a by-product of the frozen script and is not "
               "reported as a test (E7 item 5: no p-values, no Holm family, no 'supported' or 'rejected').", ros,
               "route_inputs.py (inputs), then " + gcmd.format(py=py, d=rel) + " --exclude " + rel + "/inputs/exclude.csv",
               "Engineer's reading: the gstudy.py command line of the original run (commit d88e613) was not recorded; the line above (same inputs, "
               "scale.csv and se.csv as the A1 run, `exclude.csv` from route_inputs.py) was re-run into a scratch directory and reproduces "
               "`components_by_item.csv` exactly (cell-for-cell identical, CSV comparison).")
    rel = str(ARM_L["(e)-ArmL"].relative_to(ROOT)).replace("\\", "/")
    pi = pd.read_csv(ARM_L["(e)-ArmL"] / "prompt_identity.csv", dtype=str, keep_default_na=False)
    mism = pi[pi["match"] != "True"]
    readme(ARM_L["(e)-ArmL"], "Column (e), Arm L half: frozen A1 on the intersection roster",
           "Frozen `gstudy.py --estimator A1` on Arm L effects restricted to the intersection roster (pairs ok in `roster_strict.csv` AND not in "
           "`runs/acme-L/exclusions_per_type.csv`), W0-W3 and T in {0.7, 1.0}, variant main, items with at least 3 intersection models; same scale.csv and "
           "se.csv as the A1 run. Comparison partner: `runs/acme-S-gstudy/route-e-armS` (A1-S on the same roster). `components_by_item.csv` has the "
           "'4facet' analysis (M, W, O, T; the like-for-like partner of Arm S) and 'T1' (T = 1.0 only). `hypotheses.json` is a by-product of the frozen "
           "script and is not reported as a test (E7 item 5).",
           "intersection roster `runs/acme-S-gstudy/route-e-armS/roster_intersection.csv`; per-item model lists in `inputs/roster.json`",
           f"{py} analysis/acme/route_e_inputs.py; " + gcmd.format(py=py, d=rel),
           "Prompt identity (E7a item 5): `prompt_identity.csv` (per item and W0-W3), `prompt_identity_detail.csv` (per order and x), "
           "`prompt_identity.json` (manifest verification). Result of this run: "
           + (f"{len(pi)} (item, W) groups compared, {len(mism)} mismatch(es)" + ("" if mism.empty else ": " + "; ".join(f"{r.item} {r.W}" for r in mism.itertuples()))
              if len(pi) else "no groups") + ". Both manifests verify (see prompt_identity.json).\n\n"
           "P3 (E7b item 1): Arm S has no order facet for P3 (one forward scale), so (e)-Arm L P3 uses Arm L's 'forward' prompts only "
           "(array M x W x T); Arm L's 'reversed' P3 prompts stay in column (b). LOWO values: `lowo.csv` (route_e_armL_lowo.py, E7b item 2). "
           "Arm L P2c has 3 models in the intersection. `hypotheses.json` is a by-product of the frozen script; its p-values are not reported (E7 item 5).")


if __name__ == "__main__":
    main()
