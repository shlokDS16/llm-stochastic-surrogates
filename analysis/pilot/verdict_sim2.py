"""Pass/fail of the preregistered recoverability criteria (design v0.4 section 5) for the Amendment A1 estimator.

    .venv/Scripts/python.exe -I analysis/pilot/verdict_sim2.py runs/pilot-sim2/final/results.json > runs/pilot-sim2/verdict.md

Criteria (each scenario with S >= 0.1): (1) |mean S-hat - S| < 0.02 (S-hat truncated at 0, as preregistered);
(2) coverage of the 95 % interval for S in [0.90, 0.98] (strict preregistered) and >= 0.90 (amended: over-coverage is conservative);
(3) factor shares recovered within 0.10 of truth on average: the mean absolute error of the share of each term over the
replicates in which shares would be reported (lower bound of S^2 > 0), averaged over terms; plus the share of replicates
in which that happens. A criterion on bias of the untruncated S^2-hat is added: |bias| < 0.04 S (equivalent to 0.02 on S to first order).
"""
import json
import sys

res = json.loads(open(sys.argv[1], encoding="utf8").read())
primary = ["binary", "normal", "emp_P3", "emp_P2c_log", "emp_P2d_log", "emp_P2b_log", "emp_P4_log1p"]
print("| family | scenario | bias S-hat | pass (<0.02) | bias S2 | pass (<0.04 S) | coverage | pass strict [0.90,0.98] | pass amended (>=0.90) | shares reportable | mean MAE shares | pass (<0.10) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
allp = {"strict": True, "amended": True}
for fam in primary + ["skew"]:
    for r in res:
        if r["family"] != fam or r["S"] < 0.1:
            continue
        v = r["variants"]["splithalf+ti_boot"]
        b, b2, cov = v["bias_S_truncated_vs_nominal"], v["bias_S2_vs_nominal"], v["coverage_vs_nominal"]
        pb, pb2 = abs(b) < 0.02, abs(b2) < 0.04 * r["S"]
        pcs, pca = 0.90 <= cov <= 0.98, cov >= 0.90
        sh = r["shares"]
        mae = sh.get("mean_mae_when_reported", float("nan"))
        psh = (mae < 0.10) if mae == mae else None
        if fam in primary:
            allp["strict"] &= pb and pcs and (psh is not False)
            allp["amended"] &= pb and pca and (psh is not False)
        print(f"| {fam} | {r['scenario']} | {b:+.3f} | {pb} | {b2:+.4f} | {pb2} | {cov:.3f} | {pcs} | {pca} | {sh['reported_fraction']:.2f} | {mae:.3f} | {psh} |")
print("\nAll primary-metric scenarios pass (bias S-hat, coverage, shares-when-reported):", allp)
