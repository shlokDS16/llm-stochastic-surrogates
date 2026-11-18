"""Part 3: anchoring Table 3 rows. Reproduce Q (rank scale, Hedges g) and the Condition x Country / Condition x Location F
for each DATA item and compare with the published rows.
    .venv/Scripts/python.exe -I analysis/ml1_verify/verify_ml1_part3.py > runs/ml1-verify/verify_ml1_part3.log
"""
import numpy as np, pandas as pd, pyreadstat, openpyxl
import statsmodels.api as sm, statsmodels.formula.api as smf
D = "data/raw/ml1/extracted/data/Data/"
m, _ = pyreadstat.read_sav(D + "CleanedDataset.sav")
pubT3 = {"Babies": (59.71, 0.157, 16.135, 0.402), "Everest": (152.34, 94.325, 119.555, 0.754), "Chicago": (312.75, 0.616, 32.954, 0.913), "NYC": (88.16, 9.348, 15.738, 0.643)}
pubT2 = {"Babies": (2.60, 2.42, 5609), "Everest": (2.45, 2.23, 5627), "Chicago": (2.05, 1.79, 5284), "NYC": (1.27, 1.17, 5362)}  # unweighted, weighted, N
content = {1: "NYC", 2: "Chicago", 3: "Everest", 4: "Babies"}  # from codebook text of anchoringNa/b
out = {}
for i in range(1, 5):
    g, rk = f"anch{i}group", f"Ranch{i}"
    s = m[m[g].notna() & m[rk].notna()].copy()
    s["hi"] = (s[g] == 1).astype(int)
    rows = []
    for site, x in s.groupby("referrer"):
        a, b = x.loc[x.hi == 1, rk], x.loc[x.hi == 0, rk]
        n1, n0 = len(a), len(b)
        if n1 < 2 or n0 < 2: continue
        sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n0 - 1) * b.var(ddof=1)) / (n1 + n0 - 2))
        J = 1 - 3 / (4 * (n1 + n0 - 2) - 1)
        gg = J * (a.mean() - b.mean()) / sp
        dsyn = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        rows.append((site, n1, n0, gg, dsyn))
    st = pd.DataFrame(rows, columns=["site", "n1", "n0", "g", "dsyn"])
    v = 1 / st.n1 + 1 / st.n0 + st.g ** 2 / (2 * (st.n1 + st.n0))
    w = 1 / v; mu = (w * st.g).sum() / w.sum(); Q = float((w * (st.g - mu) ** 2).sum())
    a, b = s.loc[s.hi == 1, rk], s.loc[s.hi == 0, rk]
    dw = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    F = {}
    for typ in (2, 3):
        mod = smf.ols(f"{rk} ~ C(hi, Sum) * C(us_or_international, Sum) * C(lab_or_online, Sum)", data=s).fit()
        an = sm.stats.anova_lm(mod, typ=typ)
        F[typ] = (an.loc["C(hi, Sum):C(us_or_international, Sum)", "F"], an.loc["C(hi, Sum):C(lab_or_online, Sum)", "F"],
                  an.loc["C(hi, Sum):C(us_or_international, Sum)", "sum_sq"] / (an.loc["C(hi, Sum):C(us_or_international, Sum)", "sum_sq"] + an.loc["Residual", "sum_sq"]))
    out[i] = dict(N=len(s), Q=Q, dw=dw, du=st.dsyn.mean(), F=F)
    print(f"data item {i} ({content[i]}): N={len(s)} Q(Hedges, rank scale)={Q:.2f} weighted d={dw:.3f} unweighted d={st.dsyn.mean():.3f} | "
          f"type III F(cond x country)={F[3][0]:.3f} F(cond x location)={F[3][1]:.3f} partial eta2={F[3][2]:.3f} | type II F={F[2][0]:.3f}, {F[2][1]:.3f}")
print("\npublished Table 2 (unweighted d, weighted d, N) and Table 3 (Q, F country, F location, I2) by LABEL:")
for k in pubT2: print(f"  {k:8s} T2 {pubT2[k]}  T3 {pubT3[k]}")
print("\nreading: Table 2 columns (d, N) belong to the item of the same content; Table 3 Q belongs to the item whose Q is nearest:")
for k in pubT3:
    best = min(out, key=lambda i: abs(out[i]['Q'] - pubT3[k][0]))
    bestF = min(out, key=lambda i: abs(np.log((out[i]['F'][3][0] + .01) / (pubT3[k][1] + .01))))
    t2 = min(out, key=lambda i: abs(out[i]['dw'] - pubT2[k][1]) + abs(out[i]['N'] - pubT2[k][2]) / 1000)
    print(f"  label {k:8s}: Table 2 (d, N) -> data item {t2} [{content[t2]}]; Table 3 Q -> data item {best} [{content[best]}]; Table 3 F(cond x country) -> data item {bestF} [{content[bestF]}]")
