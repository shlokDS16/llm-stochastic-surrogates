"""Choose max_new_tokens for the F1 format from observed answer lengths (statistician, 2026-10-16).

    .venv/Scripts/python.exe -I analysis/pilot/truncation_tail.py

For OLMo-2 1B (the model with the longest F1 answers) the F1 lengths observed with a cap of 128 tokens are right-censored
(unfinished answers have unknown length). A lognormal is fitted by censored maximum likelihood per paradigm and used to
predict the share of answers longer than 192, 256, 320, 384 and 512 tokens. Only probe and stage-test runs are read (runs/pilot is not opened). Lengths = n_new_tokens.
"""
import glob
import json
from pathlib import Path

import numpy as np
from scipy import optimize, stats

ROOT = Path(__file__).resolve().parents[2]


def rows(pattern):
    out = []
    for p in glob.glob(str(ROOT / pattern)):
        if "batches" in p:
            continue
        out += [json.loads(l) for l in open(p, encoding="utf8") if l.strip()]
    return [r for r in out if r["F"] == "F1" and not r["greedy"]]


def fit(rs, cap):
    n = np.array([r["n_new_tokens"] for r in rs], float)
    fin = np.array([r["finished"] for r in rs])
    x, c = np.log(n[fin]), int((~fin).sum())

    def nll(th):
        mu, ls = th
        s = np.exp(ls)
        return -(stats.norm.logpdf(x, mu, s).sum() + c * stats.norm.logsf(np.log(cap), mu, s))

    r = optimize.minimize(nll, [np.log(80), np.log(0.4)], method="Nelder-Mead")
    return r.x[0], np.exp(r.x[1]), len(rs), c


def tail(mu, s, t):
    return float(stats.norm.sf(np.log(t), mu, s))


groups = {
    "P1 (cap 128 probe+stage)": rows("runs/pilot-probe/olmo2-1b-instruct/P1.jsonl") + rows("runs/pilot-stage-test/olmo2-1b-instruct/P1.jsonl"),
    "P2a-d (cap 128)": sum([rows(f"runs/pilot-probe/olmo2-1b-instruct/P2{x}.jsonl") for x in "abcd"], []),
    "P3 (cap 128 probe+stage)": rows("runs/pilot-probe/olmo2-1b-instruct/P3.jsonl") + rows("runs/pilot-stage-test/olmo2-1b-instruct/P3.jsonl"),
    "P4 (cap 128)": rows("runs/pilot-probe/olmo2-1b-instruct/P4.jsonl"),
}
print("OLMo-2 1B, F1, censored-lognormal fit of answer length (tokens)")
print(f"{'paradigm':28s} {'n':>5s} {'cens@128':>9s} {'median':>7s} " + " ".join(f"P(>{t})" .rjust(8) for t in (192, 256, 320, 384, 512)))
for k, rs in groups.items():
    mu, s, n, c = fit(rs, 128)
    print(f"{k:28s} {n:5d} {c / n:9.3f} {np.exp(mu):7.0f} " + " ".join(f"{tail(mu, s, t):8.4f}" for t in (192, 256, 320, 384, 512)))
