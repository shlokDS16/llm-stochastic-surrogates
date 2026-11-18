"""Pooled gambler effects with 95 and 99 percent intervals (Hedges-Olkin large-sample SE), released vs corrected coding."""
import numpy as np, pyreadstat
D="data/raw/ml1/extracted/data/Data/"
full,_=pyreadstat.read_sav(D+"Full_Dataset_De-Identified.sav"); cl,_=pyreadstat.read_sav(D+"CleanedDataset.sav")
m=cl.merge(full[["session_id","gamblerfallacya"]],on="session_id",suffixes=("","_raw")); m=m[m.gambfalDV.notna()]
m["q"]=(m.gamblerfallacya_raw.str.strip()!=".").astype(int)
for lab,g in [("released","gambfalgroup"),("corrected","q")]:
    a=m.loc[m[g]==1,"gambfalDV"]; b=m.loc[m[g]==0,"gambfalDV"]
    d=(a.mean()-b.mean())/np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2); n1,n0=len(a),len(b)
    se=np.sqrt((n1+n0)/(n1*n0)+d**2/(2*(n1+n0)))
    print(lab,"d=%.3f se=%.4f 95%%CI [%.3f, %.3f] 99%%CI [%.3f, %.3f]"%(d,se,d-1.96*se,d+1.96*se,d-2.576*se,d+2.576*se))
