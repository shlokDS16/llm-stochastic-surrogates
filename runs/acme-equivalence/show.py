import json,sys
r=[json.loads(l) for l in open('runs/acme-equivalence/pairs.jsonl',encoding='utf8')]
a,b=int(sys.argv[1]),int(sys.argv[2])
for p in r[a-1:b]:
    print(f"##### {p['id']} #####\n[A]\n{p['A']}\n[B]\n{p['B']}\n")
