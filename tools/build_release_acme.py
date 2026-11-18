"""Build the ACME data-and-code release folder for the Zenodo deposit (10.5281/zenodo.24046587). Creates nothing online.

    python tools/build_release_acme.py [--out submission/release-acme]

ACME version of tools/build_release.py (that AIR-era builder is kept unchanged). Same rules: third-party texts, raw downloads,
model weights, environments, secrets and PDFs are excluded; any "abstract" field or column is removed; a file matching a secret
pattern is refused; MANIFEST.sha256 and SIZE.txt are written. ACME additions: the ACME paper numbers and exhibits
(paper/acme/autonumbers.tex, figures, tables), the frozen plan and its errata, and extra exclusions (program binaries in
tools/bin, the library access log, the unfinished screening-audit sheet, project-management notes).
Then zip the folder with --zip.
"""
import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_release import ROOT, SECRET, TEXT, strip_abstract  # noqa: E402

INCLUDE = [
    "analysis", "tools", "research/protocol", "research/ledgers/claims.jsonl", "research/ledgers/datasets.jsonl",
    "research/relaunch/PREREG-acme.md", "research/relaunch/PREREG-acme-ERRATA.md", "research/relaunch/EXPLORATORY-acme.md",
    "data/processed", "runs",
    "paper/acme/autonumbers.tex", "paper/acme/figures", "paper/acme/tables",
]
EXCL_DIR = {"__pycache__", ".venv", "models", "sources", ".git", ".codex", ".claude", "bin", "audit", "acme-style",
            "gate-audits", "acme-P1-queue", "release_templates", "docx_build"}
EXCL_NAME = re.compile(r"(\.prompt\.txt$|\.raw\.log$|\.pdf$|^\.env|\.tsv$|^abstracts\.jsonl$|\.pyc$|\.eps$|^egateway-log\.csv$"
                       r"|\.exe$|\.dll$|\.jar$|\.zip$|\.pt$|\.safetensors$|\.bin$|\.gguf$"
                       r"|^protocol\.md$|^human_audit\.py$|^audit_sample\.py$|^build_agents\.py$|^vault_knowledge\.py$|^flatten_air\.py$|^adjudication-notes\.md$)", re.I)
# protocol.md (AIR-era frozen review protocol) is left out unedited: it is not promised by the data statement and it names the
# earlier target journal and a screening step that was not completed; the supplement's amendment table documents the versions.


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="submission/release-acme")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    out = ROOT / a.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    copied, skipped, refused, stripped = [], [], [], []
    for inc in INCLUDE:
        src = ROOT / inc
        if not src.exists():
            skipped.append(f"MISSING {inc}")
            continue
        files = [src] if src.is_file() else [f for f in src.rglob("*") if f.is_file()]
        for f in files:
            rel = f.relative_to(ROOT)
            if any(part in EXCL_DIR for part in rel.parts) or EXCL_NAME.search(f.name):
                skipped.append(str(rel))
                continue
            data = f.read_bytes()
            if f.suffix.lower() in TEXT:
                if SECRET.search(data.decode("utf-8", "ignore")):
                    refused.append(str(rel))
                    continue
                if f.suffix in (".jsonl", ".csv") and b"abstract" in data[:20000]:
                    new = strip_abstract(f, data)
                    if new != data:
                        stripped.append(str(rel))
                        data = new
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            copied.append((str(rel).replace("\\", "/"), hashlib.sha256(data).hexdigest(), len(data)))
    tpl = ROOT / "tools/release_templates/acme"
    for name in ["README.md", "CITATION.cff", "LICENSE", "requirements.txt"]:
        if (tpl / name).exists():
            shutil.copy2(tpl / name, out / name)
    (out / "MANIFEST.sha256").write_text("".join(f"{h}  {p}\n" for p, h, _ in sorted(copied)), encoding="utf-8")
    total = sum(n for _, _, n in copied)
    rep = [f"files {len(copied)}, total {total / 1e6:.1f} MB", f"skipped by rule {len(skipped)}",
           f"abstract field removed in {len(stripped)} files", f"refused (secret pattern) {len(refused)}: {refused}"]
    by_top = {}
    for p, _, n in copied:
        k = "/".join(p.split("/")[:2])
        by_top[k] = by_top.get(k, 0) + n
    rep += [f"  {k}: {v / 1e6:.1f} MB" for k, v in sorted(by_top.items(), key=lambda x: -x[1])]
    (out / "SIZE.txt").write_text("\n".join(rep) + "\nstripped:\n" + "\n".join(stripped) + "\n", encoding="utf-8")
    print("\n".join(rep))
    if a.zip:
        zp = out.with_suffix(".zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in sorted(out.rglob("*")):
                if f.is_file():
                    z.write(f, Path("llm-surrogates-acme") / f.relative_to(out))
        print(f"zip: {zp} {zp.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
