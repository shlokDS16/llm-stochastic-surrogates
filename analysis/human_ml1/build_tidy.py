"""Build tidy response-level ML1 files (one per pilot paradigm) from the released cleaned dataset.

Input : data/raw/ml1/extracted/Data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.values.dat
Output: data/processed/ml1/<P>.csv with columns site, x, y, y_log, y_raw (see below).

x is coded 1 for the condition expected to give the HIGHER outcome under the canonical effect, so a
canonical effect has a positive sign everywhere:
  P1  framing    x=1 gain frame ("saved"), y=1 if sure program chosen (A in gain, C in loss frame)
  P2* anchoring  x=1 high anchor, y = estimate in US units (miles, people, feet, babies)
  P3  sunk cost  x=1 paid ticket, y = 1..9 rating (9 = definitely go to the game)
  P4  gambler    x=1 three 6s, y = log(1 + estimate of earlier rolls); y_raw = estimate itself
y_log: log(y) for anchoring (sensitivity metric), log(1+y) for P4; empty for P1, P3.
Deviation from the ML1 SPSS syntax (documented in data/cards/ml1.md): the P4 condition is taken from
which gambler variable is non-missing, because the released syntax (gambfalgroup: 'if gamblerfallacya GE 1')
puts 297 three-6s respondents who answered 0 into the two-6s group.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/raw/ml1/extracted/Data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.values.dat"
OUT = ROOT / "data/processed/ml1"


def num(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    d = pd.read_csv(SRC, sep="\t", low_memory=False, encoding="latin-1")
    d["site"] = d["referrer"].astype(str)
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}

    # P1 framing
    y = num(d["gainlossDV"])
    p = pd.DataFrame({"site": d.site, "x": d["gainlossgroup"], "y": (y == 1).astype(float).where(y.notna())})
    out["P1"] = p.dropna(subset=["y"])

    # P2 anchoring: items 1..4 = distance SF-NYC, Chicago population, Everest height, babies per day
    names = {1: "P2a", 2: "P2b", 3: "P2c", 4: "P2d"}
    for k, nm in names.items():
        y = num(d[f"anchoring{k}"])
        rk = num(d[{1: "Ranchori", 2: "RAN001", 3: "RAN002", 4: "RAN003"}[k]])   # ML1's released rank transform
        p = pd.DataFrame({"site": d.site, "x": d[f"anch{k}group"], "y": y, "y_rank": rk})
        p = p.dropna(subset=["y"])
        p = p[p.y > 0]
        p["y_log"] = np.log(p.y)
        out[nm] = p

    # P3 sunk cost: sunkgroup 0 = paid, 1 = free in the released file; recode so paid = 1
    y = num(d["sunkDV"])
    p = pd.DataFrame({"site": d.site, "x": 1 - d["sunkgroup"], "y": y}).dropna(subset=["y"])
    out["P3"] = p

    # P4 gambler's fallacy. Released values are sqrt-transformed; back-transform to the estimate.
    a, b = num(d["gamblerfallacya"]), num(d["gamblerfallacyb"])
    sq = a.where(a.notna(), b)
    x = pd.Series(np.where(a.notna(), 1, np.where(b.notna(), 0, np.nan)), index=d.index)
    raw = (sq ** 2).round()
    p = pd.DataFrame({"site": d.site, "x": x, "y_raw": raw}).dropna(subset=["x", "y_raw"])
    p["y"] = np.log1p(p.y_raw)
    p["y_log"] = p["y"]
    p["y_sqrt"] = np.sqrt(p.y_raw)   # the transform ML1 analysed (released gambfalDV)
    out["P4"] = p

    # check file only: ML1's released coding (gambfalgroup / gambfalDV), which reproduces the published Q
    yy = num(d["gambfalDV"])
    pc = pd.DataFrame({"site": d.site, "x": d["gambfalgroup"], "y": yy}).dropna(subset=["y"])
    out["P4check"] = pc

    for k, p in out.items():
        p = p.copy()
        p["x"] = p["x"].astype(int)
        p.to_csv(OUT / f"{k}.csv", index=False)
        print(k, len(p), "sites", p.site.nunique(), "x counts", p.x.value_counts().to_dict())


if __name__ == "__main__":
    main()
