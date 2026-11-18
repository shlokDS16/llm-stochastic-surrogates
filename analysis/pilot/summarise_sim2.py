"""Markdown tables from simulate_recovery2 results (statistician, 2026-10-16).

    .venv/Scripts/python.exe -I analysis/pilot/summarise_sim2.py runs/pilot-sim2/results.json [more.json] > runs/pilot-sim2/tables.md
"""
import json
import sys

import numpy as np

res = []
for p in sys.argv[1:]:
    res += json.loads(open(p, encoding="utf8").read())
order = ["binary", "normal", "emp_P3", "emp_P2c_log", "emp_P2d_log", "emp_P2b_log", "emp_P4_log1p", "skew", "emp_P2b_raw", "emp_P2d_raw", "emp_P4_raw"]
SO = ["S0", "S0.1W", "S0.1split", "S0.15split", "S0.2split", "S0.25split", "S0.3W", "S0.3split", "S0.5split"]
res.sort(key=lambda r: (order.index(r["family"]) if r["family"] in order else 99, SO.index(r["scenario"])))
for r in res:                       # S = 0: coverage is 1 - P(lower bound > 0) (the stored comparison hits a -1e-17 rounding artefact)
    if r["S"] == 0:
        for vv in r["variants"].values():
            if "lower_gt0" in vv:
                vv["coverage_vs_nominal"] = 1 - vv["lower_gt0"]
full = not res[0].get("lean", False)
print("### A. Point estimate: bias of the untruncated S2-hat (true S2 = nominal) and of the truncated S-hat, default estimator")
print("| family | scenario | true S2 | S2 of E[d_c] | bias S2 (default) | bias S-hat | " + ("bias S2 formula | bias S2 bootstrap | bias S2 oracle | " if full else "") + "SD of S2-hat |")
print("|---|---|---|---|---|---|" + ("---|---|---|" if full else "") + "---|")
for r in res:
    v = r["variants"]
    d = v["splithalf+ti_boot"]
    print(f"| {r['family']}{' ('+r.get('var_method_main','splithalf')+')' if r['family']=='binary' else ''} | {r['scenario']} | {r['S2_true']['nominal']:.4f} | {r['S2_true']['E']:.4f} | {d['bias_S2_vs_nominal']:+.4f} | {d['bias_S_truncated_vs_nominal']:+.3f} | "
          + (f"{v['formula+basic']['bias_S2_vs_nominal']:+.4f} | {v['bootstrap+basic']['bias_S2_vs_nominal']:+.4f} | {v['oracle']['bias_S2_vs_nominal']:+.4f} | " if full else "") + f"{d['sd_S2']:.4f} |")
print("\n### B. Interval for S (95 percent): coverage of the nominal S and of the S implied by E[d_c]; share of replicates whose lower bound exceeds 0 (power)")
print("| family | scenario | " + ("formula + basic | " if full else "") + "A1 variance + basic | A1 + ti_gauss | A1 + ti_boot (default) | ti_boot cov vs E-truth | lower>0 (basic) | lower>0 (ti_boot) | mean S interval (ti_boot) |")
print("|---|---|" + ("---|" if full else "") + "---|---|---|---|---|---|---|")
for r in res:
    v = r["variants"]
    print(f"| {r['family']} | {r['scenario']} | " + (f"{v['formula+basic']['coverage_vs_nominal']:.3f} | " if full else "") + f"{v['splithalf+basic']['coverage_vs_nominal']:.3f} | {v['splithalf+ti_gauss']['coverage_vs_nominal']:.3f} | "
          f"{v['splithalf+ti_boot']['coverage_vs_nominal']:.3f} | {v['splithalf+ti_boot']['coverage_vs_E']:.3f} | {v['splithalf+basic']['lower_gt0']:.2f} | {v['splithalf+ti_boot']['lower_gt0']:.2f} | "
          f"[{v['splithalf+ti_boot']['mean_S_interval'][0]:.2f}, {v['splithalf+ti_boot']['mean_S_interval'][1]:.2f}] |")
print("\n### C. Corrected term sums of squares (default estimator, ti_boot): bias, coverage, false-positive rate; factor shares")
print("| family | scenario | term | true SS | bias | coverage | lower>0 |")
print("|---|---|---|---|---|---|---|")
for r in res:
    if r["S"] < 0.3:
        continue
    for nm, t in r["terms"].items():
        if nm in ("W", "F", "T") or r["structure"] == "split" and nm in ("W:F",):
            print(f"| {r['family']} | {r['scenario']} | {nm} | {t['true_SS_nominal']:.3f} | {t['bias_vs_nominal']:+.3f} | {t['coverage_vs_nominal']:.3f} | {t['lower_gt0']:.2f} |")
print("\n| family | scenario | shares reportable (S2 lower>0) | max |ratio-of-means share bias| | mean MAE of shares when reported | max MAE when reported |")
print("|---|---|---|---|---|---|")
for r in res:
    if r["S"] < 0.1:
        continue
    sh = r["shares"]
    print(f"| {r['family']} | {r['scenario']} | {sh['reported_fraction']:.2f} | {sh.get('max_abs_ratio_of_means_bias', float('nan')):.3f} | {sh.get('mean_mae_when_reported', float('nan')):.3f} | {sh.get('max_mae_when_reported', float('nan')):.3f} |")
