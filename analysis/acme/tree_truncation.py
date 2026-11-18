"""Digit-tree truncation calibration (Codex debate 2026-11-06-CRP-S08-acme-prereg, round 2), on the PILOT numeric prompts only
(P2a-d, P4; W0-W3; F0; already used by the smoke test), before any new-wording data.

    GPU: .venv/Scripts/python.exe -I analysis/acme/tree_truncation.py run --model M [--cap 4096]
    CPU: .venv/Scripts/python.exe -I analysis/acme/tree_truncation.py analyse

Each prompt's tree is expanded to `cap` expansions; estimates recomputed from the first 256 / 512 / 1024 expansions are compared
with the cap-limited reference (resolved-only E[log] and the lower-bound imputation y_lb), per prompt and for the effect x1 - x0.
Decision rule fixed before running: resolved-only stays primary if its mean absolute truncation error on the effect at 1024 is
<= 0.05 log units and below that of y_lb; otherwise y_lb becomes primary.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis/pilot"))
OUT = ROOT / "runs/acme-tree-calib"


def est(tree, item, max_exp=None):
    import numtree
    d = numtree.distribution(tree, 1.0, max_exp=max_exp)
    g = math.log1p if item == "P4" else math.log
    ok = (lambda x: x >= 0) if item == "P4" else (lambda x: x > 0)
    v = {x: m for x, m in d["values"].items() if ok(x)}
    t = sum(v.values())
    y = sum(g(x) * m for x, m in v.items()) / t if t else None
    a = dict(v)
    for x, m in d["open_prefixes"].items():
        if ok(x):
            a[x] = a.get(x, 0.0) + m
    ta = sum(a.values())
    ylb = sum(g(x) * m for x, m in a.items()) / ta if ta else None
    return y, ylb, (d["resolved"] / d["numeric_mass"] if d["numeric_mass"] else 0.0)


def run(model, cap):
    import yaml
    import numtree
    import prompt_manifest
    import run_pilot
    import scoring
    assert not prompt_manifest.verify()
    m = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf8"))["models"][model]
    common, words = run_pilot.load_prompts()
    mdl, tok = scoring.load(m)
    voc = numtree.Vocab(tok, mdl.get_output_embeddings().weight.shape[0])
    prs = []
    for it in ["P2a", "P2b", "P2c", "P2d", "P4"]:
        for W in ["W0", "W1", "W2", "W3"]:
            for x in (1, 0):
                pr = run_pilot.build_prompt(common, words, it, W, "F0", x)
                prs.append(dict(item=it, W=W, x=x, rendered=scoring.render(tok, pr["system"], pr["user"])))
    trees = numtree.expand_trees(mdl, tok, [p["rendered"] for p in prs], voc, max_exp=cap)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / f"{model}.jsonl").open("w", encoding="utf8") as f:
        for p, t in zip(prs, trees):
            f.write(json.dumps(dict(model=model, item=p["item"], W=p["W"], x=p["x"], cap=cap, tree=t)) + "\n")
    print(model, "done")


def analyse():
    rows = []
    for fp in sorted(OUT.glob("*.jsonl")):
        recs = [json.loads(l) for l in fp.open(encoding="utf8")]
        by = {(r["item"], r["W"], r["x"]): r for r in recs}
        for (it, W, x), r in by.items():
            if x != 1:
                continue
            r0 = by[(it, W, 0)]
            ref1, reflb1, cov1 = est(r["tree"], it)
            ref0, reflb0, cov0 = est(r0["tree"], it)
            for N in (256, 512, 1024):
                a1, l1, c1 = est(r["tree"], it, N)
                a0, l0, c0 = est(r0["tree"], it, N)
                rows.append(dict(model=r["model"], item=it, W=W, N=N, cov_ref=min(cov1, cov0), cov_N=min(c1, c0),
                                 err_resolved=(a1 - a0) - (ref1 - ref0), err_lb=(l1 - l0) - (ref1 - ref0),
                                 err_lb_vs_lbref=(l1 - l0) - (reflb1 - reflb0)))
    import statistics as st
    summ = {}
    for N in (256, 512, 1024):
        rr = [r for r in rows if r["N"] == N]
        summ[N] = dict(n=len(rr), mae_resolved=st.mean(abs(r["err_resolved"]) for r in rr), mae_lb=st.mean(abs(r["err_lb"]) for r in rr),
                       max_resolved=max(abs(r["err_resolved"]) for r in rr), min_cov_ref=min(r["cov_ref"] for r in rr),
                       median_cov_N=st.median(r["cov_N"] for r in rr))
    d = summ[1024]
    verdict = "resolved-only stays primary" if d["mae_resolved"] <= 0.05 and d["mae_resolved"] < d["mae_lb"] else "y_lb becomes primary"
    (OUT / "summary.json").write_text(json.dumps(dict(summary=summ, verdict=verdict, rows=rows), indent=1), encoding="utf8")
    print(json.dumps(summ, indent=1), verdict)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        a = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        run(a["--model"], int(a.get("--cap", 4096)))
    else:
        analyse()
