"""Judge B: run Codex CLI read-only on batches of blinded pairs. Saves prompts/raw outputs under codex/, parses to judge_B.jsonl."""
import json, re, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
CODEX = HERE / "codex"
WORK = CODEX / "work"
WORK.mkdir(parents=True, exist_ok=True)
proto = (HERE / "PROTOCOL.md").read_text(encoding="utf8")
instr = proto.split("<!-- JUDGE-BEGIN -->")[1].split("<!-- JUDGE-END -->")[0].strip()
pairs = [json.loads(l) for l in (HERE / "pairs.jsonl").read_text(encoding="utf8").splitlines()]
NB = 6
size = -(-len(pairs) // NB)
batches = [pairs[i:i + size] for i in range(0, len(pairs), size)]
exe = shutil.which("codex.cmd") or shutil.which("codex")
rec = {}
for bi, b in enumerate(batches, 1):
    ids = [p["id"] for p in b]
    body = "\n\n".join(f"########## PAIR {p['id']} ##########\n\n==== TEXT A ====\n{p['A']}\n\n==== TEXT B ====\n{p['B']}" for p in b)
    prompt = f"{instr}\n\nPairs in this batch ({len(b)}): {', '.join(ids)}\n\n{body}\n\nNow output the {len(b)} JSON lines."
    pf, rf, of = CODEX / f"batch{bi}.prompt.txt", CODEX / f"batch{bi}.raw.log", CODEX / f"batch{bi}.out.txt"
    pf.write_text(prompt, encoding="utf8")
    for attempt in (1, 2):
        cmd = [exe, "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--color", "never", "--ephemeral",
               "-C", str(WORK), "-o", str(of), "-"]
        t0 = time.time()
        r = subprocess.run(cmd, input=prompt, capture_output=True, cwd=str(WORK), text=True, encoding="utf-8", errors="replace", timeout=1500)
        rf.write_text((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""), encoding="utf8")
        got = {}
        if of.exists():
            for line in of.read_text(encoding="utf8").splitlines():
                m = re.search(r"\{.*\}", line)
                if m:
                    try:
                        o = json.loads(m.group(0))
                        if o.get("id") in ids:
                            got[o["id"]] = o
                    except Exception:
                        pass
        print(f"batch {bi} attempt {attempt}: exit {r.returncode}, {len(got)}/{len(ids)} parsed, {time.time()-t0:.0f}s", flush=True)
        if len(got) == len(ids):
            break
        of.rename(CODEX / f"batch{bi}.out.attempt{attempt}.txt") if of.exists() else None
    rec.update(got)
with open(HERE / "judge_B.jsonl", "w", encoding="utf8") as f:
    for p in pairs:
        if p["id"] in rec:
            f.write(json.dumps(rec[p["id"]], ensure_ascii=False) + "\n")
print("judge_B written:", len(rec), "of", len(pairs))
