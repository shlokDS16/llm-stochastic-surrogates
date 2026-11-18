"""Hash the frozen prompt files. `python analysis/pilot/prompt_manifest.py write` creates prompts/MANIFEST.json;
`verify` (also called by run_pilot.py) exits non-zero if any prompt file changed after freezing."""
import hashlib
import json
import sys
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent / "prompts"
MAN = PROMPTS / "MANIFEST.json"


def hashes():
    out = {}
    for p in sorted(PROMPTS.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            out[p.relative_to(PROMPTS).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def verify():
    cur, ref = hashes(), json.loads(MAN.read_text(encoding="utf8"))["files"]
    bad = [k for k in set(cur) | set(ref) if cur.get(k) != ref.get(k)]
    return sorted(bad)


if __name__ == "__main__":
    if sys.argv[1] == "write":
        import datetime as dt
        MAN.write_text(json.dumps({"frozen": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                                   "note": "W1-W3 and common.yaml written before any model output was generated",
                                   "files": hashes()}, indent=2), encoding="utf8")
        print("written", len(hashes()), "files")
    else:
        bad = verify()
        print("OK" if not bad else f"MISMATCH: {bad}")
        sys.exit(1 if bad else 0)
