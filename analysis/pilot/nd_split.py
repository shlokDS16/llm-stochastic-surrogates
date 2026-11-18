"""Split of the pilot variance shares by near-deterministic (ND) status (red-team F2, 2026-10-17). DESCRIPTIVE OVER CELLS ONLY.

    .venv/Scripts/python.exe -I analysis/pilot/nd_split.py [--out runs/pilot-nd-split]

Reads, never edits, `runs/pilot-side-by-side/fig_inputs/{fig11_forest,fig12_variance_terms}.csv` (the ND flag `nd_flag_any` comes from
`analysis/pilot/diagnose_near_deterministic.py` via side_by_side.py; the share of term W is the corrected sum of squares of the
wording main effect over the corrected total, preregistration section 6). No model run, no new estimator.

Question answered: of the grids whose factor shares are reportable (S^2 lower bound > 0, A1.5), how many carry a near-deterministic
flag, and how many of the grids in which wording has a share >= 0.5 fall in each group? Counts are reported for the preregistered scale
(A1, primary) and the post-results raw scale (A2, not preregistered), per scale.

What this is NOT: the shares are shares of a corrected sum of squares over fixed, purposive cells (4 wordings, 2 temperatures, one item
per paradigm), not variance components (prereg section 6, summary.md section 8). Counts of grids are descriptive over these 42 model x
paradigm grids; no interval, no test, no statement about the population of prompts or models. The reportable grids are selected on the
S^2 lower bound > 0, which is itself related to the ND flag, so the split is a description of the selection, not an estimate.
Threshold 0.5 is the red-team's ("half or more"); a sensitivity at 0.4 and 0.6 is written to the csv only.
The red-team counts (24 of 29 reportable grids ND-flagged; 11 of the 14 wording-dominated) were known to the author before this
script was written; the script reproduces them and adds the other cells of the table.
"""
import argparse
import csv
import hashlib
import json
import logging
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "runs/pilot-side-by-side/fig_inputs"
SCALES = [("A1_preregistered", "preregistered (A1)", "A1"), ("A2_post_results", "post-results (A2, not preregistered)", "A2")]
THRESHOLDS = [0.4, 0.5, 0.6]
log = logging.getLogger("nd_split")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rd(p: Path):
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def b(v) -> bool:
    return str(v).strip() == "True"


def write_csv(p: Path, rows):
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/pilot-nd-split")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.FileHandler(out / "log.txt", mode="w", encoding="utf-8"), logging.StreamHandler()])
    f11, f12 = SRC / "fig11_forest.csv", SRC / "fig12_variance_terms.csv"
    forest, terms = rd(f11), rd(f12)
    grid_rows, summary = [], []
    for scale, status, tag in SCALES:
        g = {(r["model"], r["paradigm"]): r for r in forest if r["scale_status"] == status}
        w = {(r["model"], r["paradigm"]): r for r in terms if r["scale"] == scale and r["term"] == "W"}
        assert len(g) == 42 and set(g) == set(w), f"{scale}: grid sets differ ({len(g)}, {len(w)})"
        rows = []
        for k in sorted(g):
            rep = b(w[k]["shares_reportable"])
            assert rep == b(g[k]["llm_S2_lower_gt0"]), f"{scale} {k}: reportable flags disagree between fig11 and fig12"
            share = float(w[k]["share"]) if rep and w[k]["share"] != "" else None
            rows.append(dict(scale=tag, model=k[0], paradigm=k[1], reportable=rep, nd_flag_any=b(g[k]["nd_flag_any"]),
                             nd_n_flagged=int(float(g[k]["nd_n_flagged"])), n_cells=int(float(g[k]["nd_C"])),
                             wording_share=share, wording_ge_0_5=(share is not None and share >= 0.5)))
        grid_rows += rows
        rep = [r for r in rows if r["reportable"]]
        assert all(r["wording_share"] is not None for r in rep), "reportable grid without a wording share"
        c = Counter((r["nd_flag_any"], r["wording_ge_0_5"]) for r in rep)
        s = dict(scale=tag, scale_status=status, grids=len(rows), grids_nd_flagged=sum(r["nd_flag_any"] for r in rows),
                 reportable=len(rep), reportable_nd=sum(r["nd_flag_any"] for r in rep),
                 reportable_not_nd=sum(not r["nd_flag_any"] for r in rep),
                 wording_dominated=sum(r["wording_ge_0_5"] for r in rep),
                 wording_dominated_nd=c[(True, True)], wording_dominated_not_nd=c[(False, True)],
                 not_wording_dominated_nd=c[(True, False)], not_wording_dominated_not_nd=c[(False, False)],
                 median_wording_share_nd=round(statistics.median([r["wording_share"] for r in rep if r["nd_flag_any"]]), 4),
                 median_wording_share_not_nd=round(statistics.median([r["wording_share"] for r in rep if not r["nd_flag_any"]]), 4))
        for t in THRESHOLDS:
            s[f"wording_ge_{t}_nd"] = sum(r["wording_share"] >= t for r in rep if r["nd_flag_any"])
            s[f"wording_ge_{t}_not_nd"] = sum(r["wording_share"] >= t for r in rep if not r["nd_flag_any"])
        assert s["wording_dominated"] == s["wording_dominated_nd"] + s["wording_dominated_not_nd"]
        assert s["reportable"] == s["wording_dominated"] + s["not_wording_dominated_nd"] + s["not_wording_dominated_not_nd"]
        summary.append(s)
        log.info("%s: %s", tag, s)
    write_csv(out / "grids.csv", grid_rows)
    write_csv(out / "summary.csv", summary)
    cfg = dict(script="analysis/pilot/nd_split.py", script_sha256=sha(Path(__file__)), python=sys.version.split()[0],
               inputs_sha256={str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (f11, f12)},
               nd_definition="nd_flag_any from analysis/pilot/diagnose_near_deterministic.py (any flagged cell in the grid), as stored in fig11_forest.csv",
               wording_dominated="share of term W (corrected SS of the wording main effect over total corrected SS) >= 0.5, among grids with shares_reportable",
               thresholds_sensitivity=THRESHOLDS, label="descriptive over cells; shares are not variance components (prereg section 6)",
               outputs=["grids.csv", "summary.csv", "summary.md", "config.json", "log.txt"])
    (out / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    md = ["# Pilot variance shares split by near-deterministic status (DESCRIPTIVE over cells)\n",
          "Source: `runs/pilot-side-by-side/fig_inputs/` (sha256 in config.json). Grids are model x paradigm (6 x 7 = 42). 'Reportable' = S^2 lower "
          "bound above 0 (A1.5). ND = near-deterministic flag on any cell of the grid (`diagnose_near_deterministic.py`). Wording-dominated = wording "
          "share of the corrected sum of squares >= 0.5. Shares are shares of a corrected sum of squares over fixed purposive cells, not variance "
          "components (prereg section 6); counts are over these 42 grids, with no interval and no test, and the reportable set is itself selected on "
          "the S^2 lower bound.\n",
          "| scale | grids | ND-flagged grids | reportable | reportable and ND | reportable and not ND | wording >= 0.5 (all) | of which ND | of which not ND | median W share, ND | median W share, not ND |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summary:
        md.append(f"| {s['scale']} | {s['grids']} | {s['grids_nd_flagged']} | {s['reportable']} | {s['reportable_nd']} | {s['reportable_not_nd']} | "
                  f"{s['wording_dominated']} | {s['wording_dominated_nd']} | {s['wording_dominated_not_nd']} | {s['median_wording_share_nd']} | "
                  f"{s['median_wording_share_not_nd']} |")
    md.append("\nThreshold sensitivity (grids with wording share >= t among reportable grids; ND / not ND) is in `summary.csv`.\n")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    log.info("done")


if __name__ == "__main__":
    main()
