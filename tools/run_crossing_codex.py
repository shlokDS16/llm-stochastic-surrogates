"""Independent Codex pass for the crossing coding (X1 crossed, X2 decomposed, X3 interaction).

    python tools/run_crossing_codex.py [<order> ...] [--timeout 1500] [--model M] [--redo] [--dry-run]

With no orders, every study in data/processed/crossing/eligible.json is coded (the eligible set of the Claude extraction pass).
For each record Codex (read-only sandbox, project root as working directory) gets `research/protocol/crossing-codex-prompt.md`
(the frozen coding brief plus the instruction) and the complete markdown full text, and returns the JSON object as its final
message. The JSON is validated against the brief and written to `data/processed/crossing/codex/<order:03d>.json`; prompt, raw
log and timing go to `runs/crossing/codex/`. Codex never sees the Claude coding, the Claude extraction or any screening label.
Existing outputs are skipped unless --redo is given. Run one record at a time (the Windows sandbox helper fails when two Codex
runs overlap); a lock file enforces that. --dry-run writes the prompt of the first selected record and stops, without calling
Codex.

Modelled on tools/codex_extract.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELIGIBLE = ROOT / "data/processed/crossing/eligible.json"
OUT = ROOT / "data/processed/crossing/codex"
RUN = ROOT / "runs/crossing/codex"
PROMPT = ROOT / "research/protocol/crossing-codex-prompt.md"

SOURCES = set("MWOTPRX")
X1_VALUES = {"yes", "partial", "no", "not_reported"}
X23_VALUES = {"yes", "no", "not_reported"}
X2_TYPES = {"variance_share", "anova_or_mixed_term", "effect_change"}


def build_prompt(o: int, rec: dict) -> str:
    text = (ROOT / rec["full_text"]).read_text(encoding="utf-8", errors="replace")
    head = (PROMPT.read_text(encoding="utf-8")
            .replace("{order:03d}", f"{o:03d}").replace("{order}", str(o))
            .replace("{study_id}", rec["study_id"]).replace("{md}", rec["full_text"]))
    return f"{head}\nToday: {time.strftime('%Y-%m-%d')}.\n\n===== FULL TEXT ({rec['full_text']}) =====\n{text}\n===== END OF FULL TEXT =====\n"


def valid(obj: dict) -> str | None:
    """Return an error string, or None when the object follows the brief."""
    try:
        if obj["X1"]["value"] not in X1_VALUES or obj["X2"]["value"] not in X23_VALUES or obj["X3"]["value"] not in X23_VALUES:
            return "bad value"
        if not set(obj["sources_varied"]) <= SOURCES or not set(obj["X1"]["sources_crossed"]) <= SOURCES:
            return "bad source code"
        if not set(obj["X2"]["x2_types"]) <= X2_TYPES:
            return "bad x2_types"
        if obj["X1"]["value"] == "yes" and len(obj["X1"]["sources_crossed"]) < 2:
            return "X1 yes needs two crossed sources"
        if obj["X3"]["value"] == "yes" and obj["X1"]["value"] not in {"yes", "partial"}:
            return "X3 yes needs two varied sources"
    except (KeyError, TypeError):
        return "missing key"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("orders", nargs="*", type=int)
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--model", default=None)
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    elig = json.loads(ELIGIBLE.read_text(encoding="utf-8"))["studies"]
    recs = {int(r["order"]): r for r in elig}
    orders = a.orders or sorted(recs)
    missing = [o for o in orders if o not in recs]
    if missing:
        sys.exit(f"orders not in the eligible set: {missing}")
    if not a.redo:
        orders = [o for o in orders if not (OUT / f"{o:03d}.json").exists()]
    if not orders:
        print("nothing to do")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    RUN.mkdir(parents=True, exist_ok=True)
    if a.dry_run:
        o = orders[0]
        (RUN / f"{o:03d}.prompt.txt").write_text(build_prompt(o, recs[o]), encoding="utf-8")
        print(f"dry run: wrote {RUN / f'{o:03d}.prompt.txt'}; {len(orders)} studies would be coded")
        return
    exe = shutil.which("codex.cmd") or shutil.which("codex")
    if not exe:
        sys.exit("codex CLI not found on PATH")
    lock = RUN / "codex.lock"
    if lock.exists():
        sys.exit(f"another Codex run holds {lock}; run records one at a time")
    lock.write_text(str(time.time()))
    try:
        for o in orders:
            run_one(o, recs[o], exe, a)
    finally:
        lock.unlink(missing_ok=True)


def run_one(o: int, rec: dict, exe: str, a: argparse.Namespace) -> None:
    prompt = build_prompt(o, rec)
    pf, last, raw = RUN / f"{o:03d}.prompt.txt", RUN / f"{o:03d}.last.txt", RUN / f"{o:03d}.raw.log"
    pf.write_text(prompt, encoding="utf-8")
    cmd = [exe, "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--color", "never",
           "-C", str(ROOT), "-o", str(last)] + (["-m", a.model] if a.model else []) + ["-"]
    t0 = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, cwd=str(ROOT), text=True, encoding="utf-8",
                       errors="replace", timeout=a.timeout)
    secs = round(time.time() - t0, 1)
    raw.write_text((p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""), encoding="utf-8")
    text = last.read_text(encoding="utf-8") if last.exists() else ""
    m = re.search(r"\{.*\}", text, re.S)
    try:
        obj = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        obj = None
    err = valid(obj) if obj is not None else "no JSON"
    tok = re.search(r"tokens used[:\s]*([\d,]+)", (p.stdout or "") + (p.stderr or ""), re.I)
    meta = {"order": o, "exit": p.returncode, "seconds": secs, "ok": err is None, "error": err,
            "tokens": tok.group(1) if tok else None, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()}
    (RUN / f"{o:03d}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    if err is None:
        obj.update({"order": o, "study_id": rec["study_id"], "pass": "codex", "full_text": rec["full_text"]})
        (OUT / f"{o:03d}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{o}: ok={err is None} ({err or 'valid'}) exit={p.returncode} {secs}s tokens={meta['tokens']}", flush=True)


if __name__ == "__main__":
    main()
