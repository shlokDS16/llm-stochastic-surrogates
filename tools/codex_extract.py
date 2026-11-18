"""Independent Codex extraction for the extraction-form pilot (protocol section 7).

    python tools/codex_extract.py <order> [<order> ...] [--timeout 1500]

For each record, Codex (read-only sandbox, project root as working directory) gets the frozen brief
`research/protocol/fulltext-extraction-brief.md`, the template and the path of the record's markdown full text, and
returns the JSON object as its final message. The JSON is validated and written to
`data/processed/extraction/codex/<order:03d>.json`; prompt, raw log and timing go to `runs/extraction-pilot/codex/`.
Codex never sees the Claude extraction or any screening label.
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
LIST = ROOT / "data/processed/fulltext/reading-list.jsonl"
OUT = ROOT / "data/processed/extraction/codex"
RUN = ROOT / "runs/extraction-pilot/codex"
BRIEF = ROOT / "research/protocol/fulltext-extraction-brief.md"
TEMPLATE = ROOT / "research/protocol/extraction-template.json"

PROMPT = """You are an independent data extractor for a PRISMA systematic review. Follow the brief below exactly.
Everything you need is in this prompt: the brief, the extraction form, the template and the complete full text of the
record. Do NOT run shell commands, do not open files and do not use the web. Read the whole full text below. Your
FINAL message must be the JSON object only (no prose, no code fence).

Record: order {order}, study_id {sid}
Full text (markdown): {md}
Today: {date}. Set G.extractor to "codex ({model})".

===== BRIEF =====
{brief}

===== EXTRACTION FORM (research/protocol/extraction-form.md) =====
{form}

===== TEMPLATE =====
{template}

===== FULL TEXT ({md}) =====
{text}
===== END OF FULL TEXT =====
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("orders", nargs="+", type=int)
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RUN.mkdir(parents=True, exist_ok=True)
    rows = {d["order"]: d for d in map(json.loads, LIST.read_text(encoding="utf-8").splitlines())}
    exe = shutil.which("codex.cmd") or shutil.which("codex")
    if not exe:
        sys.exit("codex CLI not found on PATH")
    lock = RUN / "codex.lock"  # the Windows sandbox helper fails when two Codex runs overlap
    if lock.exists():
        sys.exit(f"another codex_extract run holds {lock}; run records one at a time")
    lock.write_text(str(time.time()))
    try:
        run_all(a, rows, exe)
    finally:
        lock.unlink(missing_ok=True)


def run_all(a, rows, exe) -> None:
    for o in a.orders:
        r = rows[o]
        if not r.get("md"):
            print(f"{o}: no markdown full text; skipped")
            continue
        prompt = PROMPT.format(order=o, sid=r["id"], md=r["md"].replace("\\", "/"), date=time.strftime("%Y-%m-%d"),
                               model=a.model or "default", brief=BRIEF.read_text(encoding="utf-8"),
                               form=(ROOT / "research/protocol/extraction-form.md").read_text(encoding="utf-8"),
                               template=TEMPLATE.read_text(encoding="utf-8"),
                               text=(ROOT / r["md"]).read_text(encoding="utf-8", errors="replace"))
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
        if obj is not None and "eligibility" not in obj:  # e.g. {"error": ...}: a failed run, not an extraction
            obj = None
        tok = re.search(r"tokens used[:\s]*([\d,]+)", p.stdout + p.stderr, re.I)
        meta = {"order": o, "exit": p.returncode, "seconds": secs, "ok": obj is not None,
                "tokens": tok.group(1) if tok else None,
                "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()}
        (RUN / f"{o:03d}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        if obj is not None:
            obj.setdefault("G", {})["minutes"] = round(secs / 60, 1)
            (OUT / f"{o:03d}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{o}: ok={obj is not None} exit={p.returncode} {secs}s tokens={meta['tokens']}", flush=True)


if __name__ == "__main__":
    main()
