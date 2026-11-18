"""Record finished Arm L outputs: SHA-256 of each jsonl into data/manifest.jsonl (append-only, no duplicates)
and a small per-model SUMMARY.json (files, rows, bytes, hashes; no outcome values). Finished = run_armL job in jobs.done."""
import hashlib, json, os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DONE = os.path.join(ROOT, "runs/acme-P1-queue/jobs.done")
MAN = os.path.join(ROOT, "data/manifest.jsonl")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
have = set()
for line in open(MAN, encoding="utf-8"):
    try: d = json.loads(line); have.add((d["path"], d["sha256"]))
    except Exception: pass
models = []
for line in open(DONE, encoding="utf-8"):
    m = re.search(r"run_armL\.py --model (\S+)(?:\s+--out (\S+))?", line.strip())
    if m: models.append((m.group(1), m.group(2) or "runs/acme-L"))
now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
new = []
for model, out in models:
    d = os.path.join(ROOT, out, model)
    files = sorted(f for f in os.listdir(d) if f.endswith(".jsonl"))
    summ = {"model": model, "dir": f"{out}/{model}", "recorded": now, "files": []}
    for f in files:
        p = os.path.join(d, f); rel = f"{out}/{model}/{f}"
        h = sha(p); n = sum(1 for _ in open(p, "rb")); b = os.path.getsize(p)
        summ["files"].append({"file": f, "rows": n, "bytes": b, "sha256": h})
        if (rel, h) not in have:
            new.append({"path": rel, "sha256": h, "bytes": b, "kind": "run_output", "source": f"analysis/acme/run_armL.py --model {model} (P1 queue)", "retrieved": now, "note": f"Arm L output, {n} rows"})
    json.dump(summ, open(os.path.join(d, "SUMMARY.json"), "w", encoding="utf-8"), indent=1)
    print(model, len(files), "files")
with open(MAN, "a", encoding="utf-8") as fh:
    for r in new: fh.write(json.dumps(r) + "\n")
print("manifest rows added:", len(new))
