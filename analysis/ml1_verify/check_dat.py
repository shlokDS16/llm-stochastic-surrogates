import pandas as pd, pyreadstat
D="data/raw/ml1/extracted/data/Data/"
cl,_=pyreadstat.read_sav(D+"CleanedDataset.sav")
for f in ["Tab.delimited.Cleaned.dataset.WITH.variable.values.dat","Tab.delimited.Cleaned.dataset.WITH.variable.labels.dat"]:
    t=pd.read_csv(D+f,sep="\t",dtype=str,encoding="latin-1",low_memory=False)
    mm=cl[["session_id","gambfalDV"]].assign(session_id=cl.session_id.astype(str)).merge(t[["session_id","gambfalgroup","gambfalDV"]].rename(columns={"gambfalDV":"dv2"}),on="session_id")
    print(f[:60],len(t),mm.gambfalgroup.value_counts(dropna=False).to_dict())
    print((pd.to_numeric(mm.dv2,errors="coerce").round(6).fillna(-1)==mm.gambfalDV.round(6).fillna(-1)).mean())
