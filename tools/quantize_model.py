"""Quantise a downloaded bf16 model to bitsandbytes NF4 (no double quant, bf16 compute), save it, verify it reloads,
record the files in data/manifest.jsonl, and (with --delete-raw) remove the bf16 download to respect the disk cap.

    python tools/quantize_model.py <slug> [--delete-raw] [--out-slug <slug>-nf4]

Input  models/raw/<slug>   Output models/q4/<slug>
The saved checkpoint is what run_pilot.py loads (config quant: nf4_saved). The source repo and commit are in
runs/models/MODELS.jsonl and the manifest rows.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import manifest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--delete-raw", action="store_true")
    ap.add_argument("--no-manifest", action="store_true", help="test run: do not record in data/manifest.jsonl")
    ap.add_argument("--out-root", default="models/q4")
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    src = ROOT / "models/raw" / a.slug
    dst = ROOT / a.out_root / a.slug
    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=False)
    tok = AutoTokenizer.from_pretrained(src)
    model = AutoModelForCausalLM.from_pretrained(src, quantization_config=q, dtype=torch.bfloat16, device_map={"": 0})
    print("loaded 4-bit; GPU GiB", round(torch.cuda.memory_allocated() / 2 ** 30, 2))
    dst.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(dst)
    tok.save_pretrained(dst)
    del model
    torch.cuda.empty_cache()
    # reload check + five tokens of generation, in a fresh process. 2026-11-06: in-process, Windows still held the bf16
    # source mapping, and reloading Mistral-7B failed with os error 1455 (commit limit); a fresh process loads it fine.
    import subprocess
    chk = ("import sys; from transformers import AutoModelForCausalLM, AutoTokenizer; p = sys.argv[1]; "
           "tok = AutoTokenizer.from_pretrained(p); m = AutoModelForCausalLM.from_pretrained(p, device_map={'': 0}); "
           "enc = tok('The capital of France is', return_tensors='pt').to('cuda'); "
           "print('reload ok:', tok.decode(m.generate(**enc, max_new_tokens=5, do_sample=False)[0], skip_special_tokens=True))")
    r = subprocess.run([sys.executable, "-c", chk, str(dst)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0 or "reload ok:" not in r.stdout:
        sys.exit(f"reload check failed (raw kept): {r.stderr.strip()[-800:]}")
    rec = [json.loads(x) for x in (ROOT / "runs/models/MODELS.jsonl").read_text().splitlines() if x.strip() and json.loads(x)["slug"] == a.slug][-1]
    for f in ([] if a.no_manifest else sorted(dst.glob("*.safetensors"))):
        manifest.add(str(f), f"quantised from {rec['repo']}@{rec['revision']} with bitsandbytes NF4 (no double quant, bf16 compute)", "model",
                     "saved NF4 checkpoint", {"repo": rec["repo"], "revision": rec["revision"], "quant": "nf4"})
    if a.delete_raw:
        shutil.rmtree(src)
        print("deleted", src)
    size = sum(f.stat().st_size for f in dst.rglob("*") if f.is_file()) / 1e9
    print(f"saved {dst} {size:.2f} GB")


if __name__ == "__main__":
    main()
