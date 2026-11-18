"""Build the public data-and-code release folder (GitHub repository + Zenodo deposit). Creates nothing online.

    python tools/build_release.py [--out submission/release]

Included: analysis/ and tools/ (code); research/protocol, prereg, ledgers, debates, reports (protocol, decisions, logged
critiques); data/processed (screening labels, codings, extraction, design files); runs/ (every run output, including the
pilot's 76,800 raw responses); the generated paper numbers (paper/common/autonumbers.tex) and figures.
Excluded: third-party texts (research/sources, Codex prompt files that embed full-text passages, screening input .tsv files
with abstracts, data/processed/abstracts.jsonl), raw downloads (data/raw: OpenAlex responses with publisher abstracts; the
Many Labs 1 release, cited instead), model weights (models/), environments (.venv), secrets (.env*), PDFs anywhere, review
drafts, outreach e-mails, and the author's working notes. Any "abstract" field in .json/.jsonl and any "abstract" column in
.csv is removed. A file is refused if it matches a secret pattern. Writes MANIFEST.sha256 and SIZE.txt in the release root.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ["analysis", "tools", "research/protocol", "research/prereg", "research/ledgers", "research/debates", "research/reports",
           "data/processed", "runs", "paper/common/autonumbers.tex", "paper/common/autonumbers-index.md", "paper/figures",
           "paper/tables", "paper/esm"]
EXCL_DIR = {"__pycache__", ".venv", "models", "sources", ".git", ".codex", ".claude"}
EXCL_NAME = re.compile(r"(\.prompt\.txt$|\.raw\.log$|\.pdf$|^\.env|\.tsv$|^abstracts\.jsonl$|\.pyc$|\.eps$)", re.I)
SECRET = re.compile(r"(sk-ant-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})")
TEXT = {".py", ".md", ".json", ".jsonl", ".csv", ".txt", ".tex", ".yaml", ".yml", ".log", ".sh", ".toml", ".cfg", ".bib"}


def strip_abstract(p: Path, data: bytes) -> bytes:
    if p.suffix == ".jsonl":
        out = []
        for line in data.decode("utf-8").splitlines():
            if line.strip().startswith("{"):
                r = json.loads(line)
                if isinstance(r, dict):
                    r.pop("abstract", None)
                line = json.dumps(r, ensure_ascii=False)
            out.append(line)
        return ("\n".join(out) + "\n").encode("utf-8")
    if p.suffix == ".csv":
        text = data.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        if rows and any(h.strip().lower() == "abstract" for h in rows[0]):
            k = [i for i, h in enumerate(rows[0]) if h.strip().lower() != "abstract"]
            buf = io.StringIO()
            csv.writer(buf, lineterminator="\n").writerows([[r[i] for i in k if i < len(r)] for r in rows])
            return buf.getvalue().encode("utf-8")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="submission/release")
    a = ap.parse_args()
    out = ROOT / a.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    copied, skipped, refused, stripped = [], [], [], []
    for inc in INCLUDE:
        src = ROOT / inc
        files = [src] if src.is_file() else [f for f in src.rglob("*") if f.is_file()]
        for f in files:
            rel = f.relative_to(ROOT)
            if any(part in EXCL_DIR for part in rel.parts) or EXCL_NAME.search(f.name):
                skipped.append(str(rel))
                continue
            data = f.read_bytes()
            if f.suffix.lower() in TEXT:
                head = data[:5_000_000].decode("utf-8", "ignore")
                if SECRET.search(head):
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
    for name in ["README.md", "LICENSE", "LICENSE-DATA", "CITATION.cff", "requirements.txt"]:
        tpl = ROOT / "tools/release_templates" / name
        if tpl.exists():
            shutil.copy2(tpl, out / name)
    (out / "MANIFEST.sha256").write_text("".join(f"{h}  {p}\n" for p, h, _ in sorted(copied)), encoding="utf-8")
    total = sum(n for _, _, n in copied)
    rep = [f"files {len(copied)}, total {total / 1e6:.1f} MB", f"skipped by rule {len(skipped)}", f"abstract field removed in {len(stripped)} files",
           f"refused (secret pattern) {len(refused)}: {refused}"]
    by_top = {}
    for p, _, n in copied:
        k = "/".join(p.split("/")[:2])
        by_top[k] = by_top.get(k, 0) + n
    rep += [f"  {k}: {v / 1e6:.1f} MB" for k, v in sorted(by_top.items(), key=lambda x: -x[1])]
    (out / "SIZE.txt").write_text("\n".join(rep) + "\nstripped:\n" + "\n".join(stripped) + "\n", encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
