"""Part 2: site-level cross-check of the released gambler coding against the authors' published per-site summary
(ML-_Summary_Statistics.xlsx, sheet "Gambler's Fallacy"), and heterogeneity (Q, I2, tau2 REML-free DL) under both codings.
    .venv/Scripts/python.exe -I analysis/ml1_verify/verify_ml1_part2.py > runs/ml1-verify/verify_ml1_part2.log
"""
import numpy as np, pandas as pd, pyreadstat, openpyxl
from scipy import stats
D = "data/raw/ml1/extracted/data/Data/"
full, _ = pyreadstat.read_sav(D + "Full_Dataset_De-Identified.sav")
cl, _ = pyreadstat.read_sav(D + "CleanedDataset.sav")
m = cl.merge(full[["session_id", "gamblerfallacya_raw" if False else "gamblerfallacya"]], on="session_id", suffixes=("", "_raw"))
m["three6"] = (m.gamblerfallacya_raw.str.strip() != ".").astype(int)
m = m[m.gambfalDV.notna()].copy()
pub = pd.read_excel("data/raw/ml1/docs/ML-_Summary_Statistics.xlsx", sheet_name="Gambler's Fallacy", header=0)
pub = pub.iloc[2:].rename(columns={pub.columns[0]: "site", pub.columns[1]: "n3", pub.columns[2]: "n2", pub.columns[13]: "es"})
pub = pub[["site", "n3", "n2", "es"]].dropna()
pub["n3"] = pub.n3.astype(int); pub["n2"] = pub.n2.astype(int); pub["es"] = pub.es.astype(float)
print("published per-site rows:", len(pub))
rel = m.groupby(["referrer", "gambfalgroup"]).size().unstack(fill_value=0).rename(columns={0.0: "n2_rel", 1.0: "n3_rel"})
cor = m.groupby(["referrer", "three6"]).size().unstack(fill_value=0).rename(columns={0: "n2_cor", 1: "n3_cor"})
t = pub.merge(rel, left_on="site", right_index=True, how="left").merge(cor, left_on="site", right_index=True, how="left")
print("sites where published (N three6, N two6) == released-coding Ns:", int(((t.n3 == t.n3_rel) & (t.n2 == t.n2_rel)).sum()), "of", len(t))
print("sites where published Ns == corrected-coding Ns:", int(((t.n3 == t.n3_cor) & (t.n2 == t.n2_cor)).sum()), "of", len(t))
print("sum published N three6/two6:", t.n3.sum(), t.n2.sum(), "| released:", t.n3_rel.sum(), t.n2_rel.sum(), "| corrected:", t.n3_cor.sum(), t.n2_cor.sum())

def per_site(df, g):
    out = []
    for s, x in df.groupby("referrer"):
        a, b = x.loc[x[g] == 1, "gambfalDV"], x.loc[x[g] == 0, "gambfalDV"]
        n1, n0 = len(a), len(b)
        d_mean = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n0 - 1) * b.var(ddof=1)) / (n1 + n0 - 2))
        J = 1 - 3 / (4 * (n1 + n0 - 2) - 1)
        g_h = J * (a.mean() - b.mean()) / sp
        out.append((s, n1, n0, d_mean, g_h))
    return pd.DataFrame(out, columns=["site", "n1", "n0", "d_mean", "g_h"])

def het(df, g, label):
    st = per_site(df, g)
    res = {}
    for nm, col, vt in [("d(syntax) + var 1/n1+1/n0+d2/2N", "d_mean", 0), ("Hedges g + var 1/n1+1/n0+g2/2N", "g_h", 0), ("Hedges g + var (n1+n0)/(n1 n0)+g2/(2(n1+n0-2))", "g_h", 1)]:
        y = st[col].values; n1 = st.n1.values; n0 = st.n0.values
        v = 1 / n1 + 1 / n0 + y ** 2 / (2 * (n1 + n0)) if vt == 0 else 1 / n1 + 1 / n0 + y ** 2 / (2 * (n1 + n0 - 2))
        w = 1 / v; mu = (w * y).sum() / w.sum(); Q = (w * (y - mu) ** 2).sum(); k = len(y)
        I2 = max(0, (Q - (k - 1)) / Q)
        c = w.sum() - (w ** 2).sum() / w.sum(); tau2 = max(0, (Q - (k - 1)) / c)
        print(f"{label:34s} {nm:48s} k={k} FE mu={mu:.3f} Q={Q:.2f} I2={I2:.3f} tau(DL)={np.sqrt(tau2):.3f}")
        res[nm] = Q
    return st

print("\nHeterogeneity (published Table 3: Q 50.83, I2 .229, df 35):")
st_rel = het(m, "gambfalgroup", "released coding")
st_cor = het(m, "three6", "corrected coding")
# site effects correlation
print("\nper-site d: published 'ES from means' vs my released-coding d (max abs diff):",
      float(np.abs(pub.sort_values('site').es.values - st_rel.sort_values('site').d_mean.values).max()))
print("per-site d under corrected coding: min/median/max", st_cor.d_mean.min().round(3), st_cor.d_mean.median().round(3), st_cor.d_mean.max().round(3))
