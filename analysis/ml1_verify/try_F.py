import numpy as np, pandas as pd, pyreadstat, itertools
import statsmodels.api as sm, statsmodels.formula.api as smf
D = "data/raw/ml1/extracted/data/Data/"
m, _ = pyreadstat.read_sav(D + "CleanedDataset.sav")
target = {1: (9.348, 15.738), 2: (0.616, 32.954), 3: (94.325, 119.555), 4: (0.157, 16.135)}  # by content, if F follows content
for i in range(1, 5):
    g = f"anch{i}group"
    for dvn, dv in [("rank", f"Ranch{i}"), ("raw", f"anchoring{i}")]:
        s = m[m[g].notna() & m[dv].notna() & m[f"Ranch{i}"].notna()].copy()
        s["hi"] = s[g]
        for form_name, form in [("full", f"{dv} ~ C(hi, Sum)*C(us_or_international, Sum)*C(lab_or_online, Sum)"),
                                ("noint3", f"{dv} ~ C(hi, Sum)*C(us_or_international, Sum) + C(hi, Sum)*C(lab_or_online, Sum) + C(us_or_international, Sum)*C(lab_or_online, Sum)")]:
            mod = smf.ols(form, data=s).fit()
            for typ in (1, 2, 3):
                an = sm.stats.anova_lm(mod, typ=typ)
                fc = an.loc["C(hi, Sum):C(us_or_international, Sum)", "F"]; fl = an.loc["C(hi, Sum):C(lab_or_online, Sum)", "F"]
                print(f"item {i} {dvn:4s} {form_name:7s} type{typ}: F_country={fc:9.3f} F_loc={fl:9.3f}   target(content) {target[i]}")
