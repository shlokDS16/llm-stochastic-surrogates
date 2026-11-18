import json,sys
# usage: python mk.py  < lines "id|E or N|element|conf|reason"
out=[]
for l in sys.stdin:
    l=l.strip()
    if not l: continue
    i,lab,el,c,r=l.split("|",4)
    lab={"E":"EQUIVALENT","N":"NOT-EQUIVALENT"}[lab]
    out.append(json.dumps({"id":i,"label":lab,"element":el if lab!="EQUIVALENT" else "none","confidence":int(c),"reason":r},ensure_ascii=False))
open("judge_A.jsonl","a",encoding="utf8").write("\n".join(out)+"\n")
print(len(out),"appended")
