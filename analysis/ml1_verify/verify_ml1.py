"""Independent check of two claims about the released Many Labs 1 data (statistician, 2026-10-16).
Written from scratch; does not import or read the lab engineer's scripts.

    .venv/Scripts/python.exe -I analysis/ml1_verify/verify_ml1.py > runs/ml1-verify/verify_ml1.log

Part A: retrospective gambler's fallacy. Which question each respondent saw is taken from the RAW answer
        columns of Full_Dataset_De-Identified.sav (a non-'.' string in gamblerfallacya = three-6s question,
        in gamblerfallacyb = two-6s-and-a-3 question), NOT from the released condition variable.
Part B: anchoring. Item content (codebook text, anchor values, response magnitudes) versus the rows of
        published Table 3 (Q, I2 and the Condition x Country / Condition x Location F values).
"""
import sys
import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

D = "data/raw/ml1/extracted/data/Data/"
full, _ = pyreadstat.read_sav(D + "Full_Dataset_De-Identified.sav")
cl, _ = pyreadstat.read_sav(D + "CleanedDataset.sav")
assert cl.session_id.is_unique and full.session_id.is_unique
m = cl.merge(full[["session_id", "gamblerfallacya", "gamblerfallacyb"]], on="session_id", suffixes=("", "_raw"), validate="1:1")
assert len(m) == len(cl) == len(full) == 6344


# ---------------------------------------------------------------- effect size helpers
def d_syntax(y1, y0):
    """ML1 SPSS syntax: d = (mean1 - mean0) / sqrt(mean(var0, var1)); 1 = condition with higher expected outcome."""
    return (y1.mean() - y0.mean()) / np.sqrt((y1.var(ddof=1) + y0.var(ddof=1)) / 2)


def site_table(df, ycol, gcol):
    rows = []
    for s, g in df.groupby("referrer"):
        a, b = g.loc[g[gcol] == 1, ycol].dropna(), g.loc[g[gcol] == 0, ycol].dropna()
        if len(a) < 2 or len(b) < 2:
            continue
        d = d_syntax(a, b)
        n1, n0 = len(a), len(b)
        v = (n1 + n0) / (n1 * n0) + d ** 2 / (2 * (n1 + n0))
        rows.append((s, n1, n0, d, v))
    return pd.DataFrame(rows, columns=["site", "n1", "n0", "d", "v"])


def summarise(df, ycol, gcol, label):
    a, b = df.loc[df[gcol] == 1, ycol].dropna(), df.loc[df[gcol] == 0, ycol].dropna()
    t = stats.ttest_ind(a, b, equal_var=True)
    d_w = d_syntax(a, b)
    st = site_table(df, ycol, gcol)
    w = 1 / st.v
    dfx = np.sum(w * st.d) / w.sum()
    Q = float(np.sum(w * (st.d - dfx) ** 2))
    k = len(st)
    I2 = max(0.0, (Q - (k - 1)) / Q)
    print(f"{label:46s} n1={len(a):5d} n0={len(b):5d} t={t.statistic:6.2f} (df {len(a)+len(b)-2}) weighted d={d_w:.3f} "
          f"unweighted mean d={st.d.mean():.3f} median={st.d.median():.3f} sites={k} Q={Q:.2f} I2={I2:.3f}")
    return dict(n1=len(a), n0=len(b), t=t.statistic, d_weighted=d_w, d_unweighted=st.d.mean(), d_median=st.d.median(), Q=Q, I2=I2, k=k)


# ================================================================ PART A: gambler's fallacy
print("=" * 100)
print("PART A  retrospective gambler's fallacy")
sa = m.gamblerfallacya_raw.str.strip() != "."          # answered the three-6s question
sb = m.gamblerfallacyb_raw.str.strip() != "."          # answered the two-6s-and-a-3 question
m["saw"] = np.select([sa & ~sb, sb & ~sa, sa & sb], ["three6", "two6", "both"], "neither")
print("respondents by question actually answered (raw columns):", m.saw.value_counts().to_dict())
print(pd.crosstab(m.saw, m.gambfalgroup.rename("released gambfalgroup"), margins=True).to_string())
print()
hasdv = m.gambfalDV.notna()
print("with a valid released DV (gambfalDV, N = %d):" % hasdv.sum())
print(pd.crosstab(m.saw[hasdv], m.gambfalgroup[hasdv].rename("released gambfalgroup"), margins=True).to_string())

mis = m[hasdv & (m.saw == "three6") & (m.gambfalgroup == 0)]
print(f"\nvalid-DV respondents who saw the three-6s question but sit in released group 0 ('two6'): {len(mis)}")
print("  their released DV (sqrt scale) values:", mis.gambfalDV.round(6).value_counts().to_dict())
print("  their raw answer strings:", ascii(mis.gamblerfallacya_raw.value_counts().to_dict()))
print("  all released-group-0 respondents who saw the three-6s question (incl. no valid DV):",
      int(((m.saw == "three6") & (m.gambfalgroup == 0)).sum()),
      "| of which non-numeric text answers (DV missing):", int(((m.saw == "three6") & (m.gambfalgroup == 0) & ~hasdv).sum()))
rev = m[hasdv & (m.saw == "two6") & (m.gambfalgroup == 1)]
print("valid-DV respondents who saw the two-6s question but sit in group 1:", len(rev))
# the rule in Syntax.Manylabs.sps line 697: if gamblerfallacya GE 1 gambfalgroup=1 (a = numeric-converted raw column)
a_num = pd.to_numeric(m.gamblerfallacya_raw.str.strip().replace(".", np.nan), errors="coerce")
print("released gambfalgroup == (numeric raw gamblerfallacya >= 1) for how many of 6344 rows:",
      int(((a_num >= 1).astype(int) == m.gambfalgroup).sum()))
# rows where the cleaned column differs from numeric raw (text answers that SPSS converted)
diff = m[(m.saw == "three6") & hasdv & (a_num.isna() | (np.sqrt(a_num) - m.gamblerfallacya).abs().gt(1e-9))]
print("three-6s rows with valid DV where cleaned value is not sqrt(numeric raw):", len(diff), ascii(diff.gamblerfallacya_raw.tolist()), diff.gamblerfallacya.tolist())
tiny = m[hasdv & (m.saw == "three6") & (m.gambfalgroup == 0) & (m.gambfalDV > 0)]
print("the non-zero one:", ascii(tiny[["gamblerfallacya_raw", "gambfalDV"]].values.tolist()))

# --- effects. ML1 analysed sqrt(response); condition 1 = three 6s (higher expected estimate)
m["g_released"] = m.gambfalgroup
m["g_question"] = (m.saw == "three6").astype(int)
print("\nEffect sizes on the ML1 analysis scale (sqrt of response), valid DV only (N = %d):" % hasdv.sum())
sub = m[hasdv].copy()
r_rel = summarise(sub, "gambfalDV", "g_released", "released coding (gambfalgroup)")
r_q = summarise(sub, "gambfalDV", "g_question", "corrected: group = question answered")
# sensitivity: drop the 297 respondents entirely instead of re-assigning them
keep = ~sub.index.isin(mis.index)
r_drop = summarise(sub[keep], "gambfalDV", "g_question", "drop the 297 (neither group)")
# sensitivity: drop everybody who answered 0 (either question) from both arms
nz = sub[(sub.gambfalDV > 0)]
r_nz = summarise(nz, "gambfalDV", "g_question", "drop all answers of 0, correct coding")
# other scales
for nm, f in [("log(1+x)", lambda s: np.log1p(s ** 2)), ("raw x", lambda s: s ** 2)]:
    sub2 = sub.copy()
    sub2["y"] = f(sub2.gambfalDV)
    summarise(sub2, "y", "g_released", f"released coding, {nm}")
    summarise(sub2, "y", "g_question", f"corrected coding, {nm}")
print("\nPublished (Klein et al. 2014 Table 2, ML-_Summary_Statistics.xlsx row 'Retrospective gambler fallacy'): "
      "unweighted 0.59, median 0.61, weighted 0.61 [0.54, 0.68], t = 24.01, df 5940, N 5942; Table 3: Q 50.83, df 35, I2 .229.")

# cell means (for the explanation of the inflation)
print("\nmean sqrt-DV by released group / corrected group:")
print(sub.groupby("g_released").gambfalDV.agg(["count", "mean", "std"]).round(3).to_string())
print(sub.groupby("g_question").gambfalDV.agg(["count", "mean", "std"]).round(3).to_string())
print("zeros: released group 0 n_zero =", int(((sub.g_released == 0) & (sub.gambfalDV == 0)).sum()),
      "| correct two-6s group n_zero =", int(((sub.g_question == 0) & (sub.gambfalDV == 0)).sum()),
      "| correct three-6s group n_zero =", int(((sub.g_question == 1) & (sub.gambfalDV == 0)).sum()))

# ================================================================ PART B: anchoring
print("\n" + "=" * 100)
print("PART B  anchoring: item content versus Table 3 rows")
pub = {  # published Table 3 (ML-_Summary_Statistics.xlsx 'Table 3'), label -> (Q, I2, F US/intl, F lab/online)
    "Babies born": (59.71, 0.402, 0.157, 16.135),
    "Mt. Everest": (152.34, 0.754, 94.325, 119.555),
    "Chicago": (312.75, 0.913, 0.616, 32.954),
    "Distance to NYC": (88.16, 0.643, 9.348, 15.738),
}
cb = pd.read_excel(D + "Codebook.xlsx", header=None)
print("codebook text per item (first column = variable name):")
for i in range(1, 5):
    for suf in "ab":
        r = cb[cb[0] == f"anchoring{i}{suf}"]
        print(f"  anchoring{i}{suf}: {r.iloc[0, 1]}")
res = []
for i in range(1, 5):
    g, y, rk = f"anch{i}group", f"anchoring{i}", f"Ranch{i}"
    sub = m[m[g].notna() & m[rk].notna()].copy()
    sub["hi"] = (sub[g] == 1).astype(int)
    meds = sub.groupby("hi")[y].median().to_dict()
    # anchors present in the item text columns
    a_txt = m[f"anchoring{i}a"].dropna().astype(str).head(1).tolist()
    st = site_table(sub, rk, "hi")
    w = 1 / st.v
    dfx = (w * st.d).sum() / w.sum()
    Q = float((w * (st.d - dfx) ** 2).sum())
    I2 = max(0, (Q - (len(st) - 1)) / Q)
    sub["country"] = sub.us_or_international
    sub["loc"] = sub.lab_or_online
    mod = smf.ols(f"{rk} ~ C(hi, Sum) * C(country, Sum) * C(loc, Sum)", data=sub).fit()
    an = sm.stats.anova_lm(mod, typ=3)
    Fc = an.loc["C(hi, Sum):C(country, Sum)", "F"]
    Fl = an.loc["C(hi, Sum):C(loc, Sum)", "F"]
    res.append((i, len(sub), meds, Q, I2, Fc, Fl))
    print(f"data item {i}: N={len(sub)} median raw answer low/high anchor = {meds[0]:.0f}/{meds[1]:.0f}; "
          f"rank-scale Cochran Q = {Q:.2f}, I2 = {I2:.3f}; Cond x US/intl F = {Fc:.3f}; Cond x lab/online F = {Fl:.3f}")
print("\npublished rows (Q, I2, F US/intl, F lab/online):")
for k, v in pub.items():
    print(f"  {k:16s} {v}")
print("\nbest data item for each published row by (Q, F_country, F_location) distance:")
for k, v in pub.items():
    best = min(res, key=lambda r: abs(r[3] - v[0]) / v[0] + abs(r[5] - v[2]) / max(v[2], 1) + abs(r[6] - v[3]) / v[3])
    print(f"  published '{k}' <- data item {best[0]}")
