"""Hash the frozen ACME prompt files. `python analysis/acme/prompt_manifest.py write` creates prompts/MANIFEST.json (freeze);
`verify` exits non-zero if any prompt file changed after freezing. Importable: `freeze()` and `verify()` (list of mismatching files)."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent / "prompts"
MAN = PROMPTS / "MANIFEST.json"
NOTE = "written before any model output on these wordings was generated"


def hashes():
    out = {}
    for p in sorted(PROMPTS.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json" and "__pycache__" not in p.parts:
            out[p.relative_to(PROMPTS).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def freeze():
    h = hashes()
    MAN.write_text(json.dumps({"frozen": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                               "note": NOTE, "files": h}, indent=2), encoding="utf8")
    return len(h)


def verify():
    cur, ref = hashes(), json.loads(MAN.read_text(encoding="utf8"))["files"]
    return sorted(k for k in set(cur) | set(ref) if cur.get(k) != ref.get(k))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "write":
        print("written", freeze(), "files")
    else:
        bad = verify()
        print("OK" if not bad else f"MISMATCH: {bad}")
        sys.exit(1 if bad else 0)
