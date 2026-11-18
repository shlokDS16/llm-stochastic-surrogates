"""Table of the pilot results (primary metric) from runs/pilot/<model>/analysis_<paradigm>[tag].json.

    .venv/Scripts/python.exe -I analysis/pilot/summarise_pilot.py [--tag ""|.f0sens|.notopup] > runs/pilot-analysis/summary.md

One row per model x paradigm: validity, defined cells, Delta-bar with its 95 percent interval, S with its
95 percent test-inversion interval, whether the lower bound of S^2 exceeds 0, sign stability. No interpretation.
"""
import argparse
import glob
import json
import os

PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]


def fmt(x, d=3):
    return "NA" if x is None else f"{x:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/pilot")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    print(f"# Pilot results, primary metric (analysis tag '{a.tag or 'primary'}'; A1 + A1.10 rules)\n")
    print("| model | paradigm | metric | validity | cells | dbar [95% CI] | S [95% TI] | S2 lower > 0 | sign stability |")
    print("|---|---|---|---|---|---|---|---|---|")
    for d in sorted(glob.glob(os.path.join(a.runs, "*", ""))):
        model = os.path.basename(os.path.dirname(d))
        for p in PARADIGMS:
            f = os.path.join(d, f"analysis_{p}{a.tag}.json")
            if not os.path.exists(f):
                print(f"| {model} | {p} | not analysed | | | | | | |")
                continue
            o = json.load(open(f, encoding="utf8"))
            m = o["metrics"]["primary"]
            r = m.get("split_half")
            if r is None:
                print(f"| {model} | {p} | {m.get('label', '')} | {fmt(o['validity_overall'])} | {m.get('n_cells_defined')}/{m.get('n_cells')} "
                      f"| | S={fmt(m.get('S'))} ({m.get('note', '')}) | | |")
                continue
            dci = r.get("dbar_ci") or [None, None]
            lab = m.get("label", "") if m.get("scale") == "standardised" else ("risk difference" if p == "P1" else "raw difference on the metric scale") + f" ({m.get('scale')})"
            print(f"| {model} | {p} | {lab} | {fmt(o['validity_overall'])} | {m['n_cells_defined']}/{m['n_cells']} "
                  f"| {fmt(r['dbar'])} [{fmt(dci[0])}, {fmt(dci[1])}] | {fmt(r['S'])} [{fmt(r['S_ci'][0])}, {fmt(r['S_ci'][1])}] "
                  f"| {r['S2_ci'][0] > 0} | {fmt(r['sign_stability'], 2)} |")


if __name__ == "__main__":
    main()
