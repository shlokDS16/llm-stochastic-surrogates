"""Append SHA-256 rows to data/manifest.jsonl (append-only).

    python tools/manifest.py add <path> --source <url or doi> [--kind data|material|paper|model] [--note "..."] [--meta '{"k": "v"}']
    python tools/manifest.py list
Paths are stored relative to the project root. Re-adding an unchanged file with the same hash is skipped.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "data" / "manifest.jsonl"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rows():
    return [json.loads(x) for x in MAN.read_text(encoding="utf8").splitlines() if x.strip()] if MAN.exists() else []


def add(path: str, source: str, kind: str, note: str, meta: dict):
    p = (ROOT / path) if not Path(path).is_absolute() else Path(path)
    rel = p.relative_to(ROOT).as_posix()
    digest = sha256(p)
    if any(r["path"] == rel and r["sha256"] == digest for r in rows()):
        print("skip (already recorded)", rel)
        return
    row = dict(path=rel, sha256=digest, bytes=p.stat().st_size, kind=kind, source=source,
               retrieved=dt.datetime.now().astimezone().isoformat(timespec="seconds"), note=note, **meta)
    MAN.parent.mkdir(parents=True, exist_ok=True)
    with MAN.open("a", encoding="utf8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("added", rel, digest[:12])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("path", nargs="+")
    a.add_argument("--source", required=True)
    a.add_argument("--kind", default="data")
    a.add_argument("--note", default="")
    a.add_argument("--meta", default="{}")
    sub.add_parser("list")
    args = ap.parse_args()
    if args.cmd == "add":
        for pth in args.path:
            add(pth, args.source, args.kind, args.note, json.loads(args.meta))
    else:
        for r in rows():
            print(r["sha256"][:12], r["bytes"], r["path"])
