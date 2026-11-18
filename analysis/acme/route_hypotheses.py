"""E7 item 5: H1-H3 reported as estimates, never as tests (post-outcome, exploratory, descriptive). No p-value is read or written.

Definitions are those of PREREG-acme section 5 / frozen gstudy.py: pooled = mean over the decomposed items of a column;
H1 estimate = pooled wording share (W + MW) minus pooled temperature share (every term whose label contains T);
H3 estimate = pooled MW share minus pooled W share; H2 = per item, median over models of the set-up SD against c_p.
Arm L columns (b), (c), (e)-Arm L: the frozen estimate and its frozen A1 interval are copied from <dir>/hypotheses.json (p-values dropped).
Arm S columns (a), (e)-Arm S (E2 and E1 bases): computed here from components_<item>.csv; uncertainty = range of the four
leave-one-wording-out values of the pooled difference (fragility, not uncertainty; E7a item 1). For Arm S the temperature facet has two
levels (0.7, 1.0), so H1 here is the "H1 analogue" of E7 item 5, not the preregistered H1. Arm S H2: count of items whose median set-up
SD (raw, and draw-corrected) exceeds c_p, from route-a-yardsticks; no interval.
Item sets, both reported: all decomposed items of the column; choice/rating items only (AF, NR, P1, P3, QA).
    .venv/Scripts/python.exe -I analysis/acme/route_hypotheses.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/acme-gstudy/route-table/hypotheses_estimates.csv"
CR = ["AF", "NR", "P1", "P3", "QA"]
ARM_L = {"(b)": "runs/acme-gstudy/A1-route-b-pertype", "(c)": "runs/acme-gstudy/A1-route-c-permodel",
         "(e)-ArmL": "runs/acme-gstudy/A1-route-e-armL"}
ARM_S = {"(a)": "runs/acme-S-gstudy/route-a", "(e)-ArmS": "runs/acme-S-gstudy/route-e-armS"}
ARM_L_CR = {"(b)": "runs/acme-gstudy/A1-route-b-pertype-cr", "(e)-ArmL": "runs/acme-gstudy/A1-route-e-armL-cr"}


def is_T(t):
    return "T" in t and t not in ("draw",)


def armS(col, d):
    rows = []
    comps = {p.stem.split("_", 1)[1]: pd.read_csv(p) for p in sorted((ROOT / d).glob("components_*.csv"))}
    for basis in ("E2", "E1"):
        for setname, items in (("all", sorted(comps)), ("choice_rating", [i for i in sorted(comps) if i in CR])):
            if not items:
                continue
            nw = len([c for c in comps[items[0]].columns if c.startswith(f"{basis}_lowo_drop_W")])
            def pooled(colname):
                h1, h3 = [], []
                for it in items:
                    c = comps[it].set_index("term")
                    if colname not in c.columns:
                        return None, None
                    s = c[colname].dropna()
                    wrd = s.get("W", 0.0) + s.get("MW", 0.0)
                    tmp = sum(v for t, v in s.items() if is_T(t))
                    h1.append(wrd - tmp)
                    h3.append(s.get("MW", 0.0) - s.get("W", 0.0))
                return float(np.mean(h1)), float(np.mean(h3))
            e1, e3 = pooled(f"{basis}_share")
            lo1, lo3 = zip(*[pooled(f"{basis}_lowo_drop_W{w}") for w in range(nw)])
            for h, est, lw in (("H1_analogue", e1, lo1), ("H3", e3, lo3)):
                rows.append(dict(column=col, arm="S", hypothesis=h, basis=basis, item_set=setname, k_items=len(items), estimate=est,
                                 lowo_min=min(lw), lowo_max=max(lw), lo=None, hi=None,
                                 note="Arm S: LOWO range = fragility over the four wordings, not uncertainty; T has 2 levels; differences under 0.06 not interpreted (E7a)"))
    return rows


def armL(col, d):
    h = json.loads((ROOT / d / "hypotheses.json").read_text(encoding="utf8"))
    rows = []
    for k in ("H1", "H3"):
        rows.append(dict(column=col, arm="L", hypothesis=k, basis="A1", item_set="all", k_items=h[k]["k_items"], estimate=h[k]["estimate"],
                         lo=h[k]["lo"], hi=h[k]["hi"], note="frozen A1 estimate and interval; p-values not reported (E7 item 5); underpowered"
                         + ("; 4-wording interval not interpreted" if col == "(e)-ArmL" else "")))
    it = h["H2"]["items"]
    rows.append(dict(column=col, arm="L", hypothesis="H2", basis="A1", item_set="all", k_items=len(it),
                     estimate=sum(bool(x["median_setup_sd"] > x["single_site_se"]) for x in it),
                     note="count of items whose median set-up SD exceeds c_p (point estimates)"))
    rows.append(dict(column=col, arm="L", hypothesis="H2", basis="A1_lb95_onesided", item_set="all", k_items=len(it),
                     estimate=sum(bool(x["lb95_onesided"] > x["single_site_se"]) for x in it),
                     note="count of items whose frozen one-sided 95% lower bound of the median set-up SD exceeds c_p (descriptive, no test)"))
    return rows


def armS_H2():
    rows = []
    sc = pd.read_csv(ROOT / "runs/human-ml1-acme/arml_scales.csv").set_index("item")["se_single_sd_units"]
    for k in ("raw", "drawcorr"):
        s = pd.read_csv(ROOT / f"runs/acme-S-gstudy/route-a-yardsticks/{k}/setup_sd.csv")
        m = s[s["model"] == "__median__"].set_index("item")["setup_sd"]
        for setname, items in (("all", list(m.index)), ("choice_rating", [i for i in m.index if i in CR])):
            rows.append(dict(column="(a)", arm="S", hypothesis="H2", basis=f"setup_sd_{k}", item_set=setname, k_items=len(items),
                             estimate=int(sum(m[i] > sc[i] for i in items)),
                             note="count of items whose median set-up SD exceeds c_p; no interval (E7a); 4 wordings x 2 orders, T = 1.0"))
    return rows


def main():
    rows = []
    for c, d in ARM_S.items():
        rows += armS(c, d)
    rows += armS_H2()
    for c, d in ARM_L.items():
        rows += armL(c, d)
    # choice and rating items only (P2c, the one numeric item these columns decompose, left out; red-team REDTEAM-final MAJOR 1):
    # the frozen gstudy.py run on the column's inputs restricted to AF, NR, P1, P3, QA (runs/acme-gstudy/*-cr/README.md)
    for c, d in ARM_L_CR.items():
        h = json.loads((ROOT / d / "hypotheses.json").read_text(encoding="utf8"))
        for k in ("H1", "H3"):
            rows.append(dict(column=c, arm="L", hypothesis=k, basis="A1", item_set="choice_rating", k_items=h[k]["k_items"],
                             estimate=h[k]["estimate"], lo=h[k]["lo"], hi=h[k]["hi"],
                             note="frozen A1 on the choice and rating items only; p-values not reported (E7 item 5); underpowered"
                             + ("; 4-wording interval not interpreted" if c == "(e)-ArmL" else "")))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(df.drop(columns="note").to_string(index=False))


if __name__ == "__main__":
    main()
