"""Download a Hugging Face model at its current commit into models/raw/<slug>, verify, and record it.

    python tools/fetch_model.py <repo_id> <slug> [--revision SHA]

Steps: query the Hub API (gated flag, licence tag, commit sha, file sizes and LFS sha256); refuse gated models;
check free disk against the 30 GB model cap (models/ total); snapshot_download at the pinned sha; verify every
LFS file's SHA-256 against the Hub; append rows to data/manifest.jsonl (kind=model) and runs/models/MODELS.jsonl.
"""
import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
CAP_GB = 83.0  # models/ total; project cap 90 GB since 2026-11-06 (D0024), about 7 GB of other project files


def api(repo):
    return json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}?blobs=true"))


def dir_gb(p: Path):
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e9 if p.exists() else 0.0


def sha256(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def curl_get(repo, rev, s, dest: Path) -> bool:
    """Resumable single-file download to dest/<rfilename> through <rfilename>.part. True when the file is complete."""
    import subprocess
    p = dest / s["rfilename"]
    size = s.get("size")
    if p.is_file() and (size is None or p.stat().st_size == size):
        return True
    p.parent.mkdir(parents=True, exist_ok=True)
    part = p.with_name(p.name + ".part")
    if size is not None and part.is_file() and part.stat().st_size > size:
        part.unlink()  # longer than the file: corrupt, start over
    if size is not None and part.is_file() and part.stat().st_size == size:
        part.replace(p)
        return True
    url = f"https://huggingface.co/{repo}/resolve/{rev}/{s['rfilename']}"
    r = subprocess.run(["curl", "-L", "-sS", "--fail", "-C", "-", "--connect-timeout", "30", "--speed-limit", "2000",
                        "--speed-time", "90", "-o", str(part), url])
    got = part.stat().st_size if part.is_file() else 0
    if size is not None and got == size:
        part.replace(p)
        return True
    if size is None and r.returncode == 0:
        part.replace(p)
        return True
    print(f"partial {s['rfilename']}: {got / 1e9:.2f} of {(size or 0) / 1e9:.2f} GB (curl exit {r.returncode})", flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("slug")
    ap.add_argument("--revision")
    ap.add_argument("--transient", action="store_true", help="bf16 download that is quantised and deleted right after: quantise and delete the bf16 copy before the next large download (models/ cap 62 GB, project cap 70 GB)")
    a = ap.parse_args()
    d = api(a.repo)
    if d.get("gated"):
        sys.exit(f"{a.repo} is gated: refusing")
    lic = [t for t in d.get("tags", []) if t.startswith("license:")]
    rev = a.revision or d["sha"]
    # 2026-11-06: only the transformers weights and their config/tokenizer files. Some repos also carry export formats
    # (SmolLM2: 19 GB of onnx/) and training logs; when safetensors exist, duplicate .bin/.pt weights are skipped too.
    skip_dirs = ("onnx/", "runs/", "openvino/", "coreml/", "flax/", "tf/")
    skip_ext = (".gguf", ".onnx", ".onnx_data", ".msgpack", ".h5", ".ot", ".tflite", ".mlmodel")
    files = [s for s in d["siblings"] if not s["rfilename"].startswith(skip_dirs) and not s["rfilename"].endswith(skip_ext)]
    if any(s["rfilename"].endswith(".safetensors") for s in files):
        files = [s for s in files if not (s["rfilename"].endswith((".pt", ".pth")) or
                                          (s["rfilename"].endswith(".bin") and "model" in s["rfilename"]))]
    # 2026-11-06: Mistral repos also carry consolidated.safetensors (mistral_inference format, a second full copy);
    # transformers reads the sharded model-*.safetensors, so the consolidated copy is skipped when shards exist.
    if any(s["rfilename"].startswith("model-") and s["rfilename"].endswith(".safetensors") for s in files):
        files = [s for s in files if not s["rfilename"].startswith("consolidated.")]
    need_gb = sum(s.get("size") or 0 for s in files) / 1e9
    used = dir_gb(MODELS)
    free = shutil.disk_usage(ROOT).free / 1e9
    print(f"{a.repo} sha={rev} lic={lic} need={need_gb:.1f} GB used_in_models={used:.1f} GB free_disk={free:.0f} GB")
    cap = CAP_GB  # transient bf16 copies also count against the 70 GB project cap
    have_gb = dir_gb(MODELS / "raw" / a.slug)  # bytes of this model already on disk (resumed download) count once
    if used + max(0.0, need_gb - have_gb) > cap:
        sys.exit(f"would exceed the {cap} GB model cap ({used:.1f} + {need_gb:.1f})")
    dest = MODELS / "raw" / a.slug
    # 2026-11-05: huggingface_hub 1.33 writes every attempt to a new uuid-named temp file and deletes it on failure,
    # so an interrupted download restarts from byte 0. curl -C - continues a fixed <file>.part across attempts and
    # process restarts; the SHA-256 check below verifies every LFS file.
    from concurrent.futures import ThreadPoolExecutor
    workers = int(__import__("os").environ.get("CRP_HF_WORKERS", "2"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        failed = [n for n, ok in zip([s["rfilename"] for s in files], ex.map(lambda s: curl_get(a.repo, rev, s, dest), files)) if not ok]
    if failed:
        sys.exit(f"download incomplete (partial files kept, rerun to continue): {failed}")
    bad = []
    rows = []
    for s in files:
        p = dest / s["rfilename"]
        lfs = s.get("lfs")
        h = sha256(p) if p.suffix in (".safetensors", ".bin", ".json", ".model", ".txt") or lfs else None
        if lfs and h != lfs["sha256"]:
            bad.append(s["rfilename"])
        rows.append((p, h))
    if bad:
        sys.exit(f"SHA-256 mismatch: {bad}")
    sys.path.insert(0, str(ROOT / "tools"))
    import manifest
    for p, h in rows:
        if p.suffix in (".safetensors", ".bin"):
            manifest.add(str(p), f"https://huggingface.co/{a.repo}/tree/{rev}", "model", f"{a.repo}@{rev}", {"repo": a.repo, "revision": rev})
    rec = dict(slug=a.slug, repo=a.repo, revision=rev, license=lic, gated=d.get("gated"), size_gb=round(need_gb, 2),
               downloaded=dt.datetime.now().astimezone().isoformat(timespec="seconds"), path=dest.relative_to(ROOT).as_posix(),
               params=d.get("safetensors", {}).get("total"))
    (ROOT / "runs" / "models").mkdir(parents=True, exist_ok=True)
    with (ROOT / "runs" / "models" / "MODELS.jsonl").open("a", encoding="utf8") as f:
        f.write(json.dumps(rec) + "\n")
    print("done", rec)


if __name__ == "__main__":
    main()
