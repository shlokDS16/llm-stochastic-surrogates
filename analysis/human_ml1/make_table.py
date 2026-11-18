"""Merge moment_summary.json (Python) and metafor_results.json (R) into runs/human-ml1/benchmark_table.md and .csv."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "runs/human-ml1"
mom = json.loads((D / "moment_summary.json").read_text(encoding="utf8"))
rma = json.loads((D / "metafor_results.json").read_text(encoding="utf8"))
NAMES = {"P1": "P1 framing (log OR, sure option)", "P2a": "P2a anchoring SF-NYC distance", "P2b": "P2b anchoring Chicago",
         "P2c": "P2c anchoring Everest", "P2d": "P2d anchoring babies/day", "P3": "P3 sunk cost", "P4": "P4 gambler (log(1+x))",
         "P4check": "P4 released ML1 coding (check)"}
rows = ["paradigm|metric|k|N|mu_REML [95% CI]|tau_REML [Q-profile 95% CI]|I2 %|Q (p)|unweighted mean d|S^H moment (basic bootstrap 95% CI)"]
csv = ["paradigm,metric,k,N,mu,mu_lo,mu_hi,tau,tau_lo,tau_hi,I2,Q,Q_p,dbar,S_H,S_H_lo,S_H_hi"]
for key, r in rma.items():
    m = mom[key]
    rows.append("%s|%s|%d|%d|%.3f [%.3f, %.3f]|%.3f [%.3f, %.3f]|%.1f|%.1f (%.3f)|%.3f|%.3f [%.3f, %.3f]" % (
        NAMES.get(r["paradigm"], r["paradigm"]), r["metric"], r["k"], m["n_total"], r["mu"], r["mu_ci"][0], r["mu_ci"][1], r["tau"],
        r["tau_ci_qprofile"][0], r["tau_ci_qprofile"][1], r["I2"], r["Q"], r["Q_p"], m["dbar"], m["S"], m["S_ci95"][0], m["S_ci95"][1]))
    csv.append(",".join(map(str, [r["paradigm"], r["metric"], r["k"], m["n_total"], r["mu"], *r["mu_ci"], r["tau"], *r["tau_ci_qprofile"], r["I2"],
                                  r["Q"], r["Q_p"], m["dbar"], m["S"], *m["S_ci95"]])))
(D / "benchmark_table.md").write_text("| " + " | ".join(rows[0].split("|")) + " |\n|" + "---|" * 10 + "\n" +
                                      "\n".join("| " + " | ".join(x.split("|")) + " |" for x in rows[1:]) + "\n", encoding="utf8")
(D / "benchmark_table.csv").write_text("\n".join(csv), encoding="utf8")
print((D / "benchmark_table.md").read_text(encoding="utf8"))
