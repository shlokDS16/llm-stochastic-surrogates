"""Classifier B for screening: a local open-weight instruction model (protocol amendment v0.4).

    .venv/Scripts/python -I analysis/screening/local_screen.py --stage title --model <hf-repo> \
        --revision <sha> [--four-bit] [--batch 16] [--limit N]

Reads `data/processed/records.jsonl` (stage title) or `data/processed/screen/stage2-input.jsonl`
(stage abstract) and the frozen criteria `research/protocol/screening/criteria.md`. For each record
it scores the next-token log-probability of the three labels after the prompt (no sampling, so
the run is deterministic) and writes one JSON line per record to
`data/processed/screen/<stage>.local.jsonl`: id, label, p_include, p_maybe, p_exclude.
Resumable: records already in the output file are skipped.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parents[2]
LABELS = ["INCLUDE", "MAYBE", "EXCLUDE"]


def prompt_for(rec: dict, stage: str, criteria: str) -> list[dict]:
    body = f"Title: {rec.get('title') or ''}"
    if stage == "abstract":
        body += f"\nAbstract: {(rec.get('abstract') or '')[:2500]}"
    return [{"role": "system", "content": criteria},
            {"role": "user", "content": f"{body}\n\nAnswer with one word: INCLUDE, MAYBE or EXCLUDE."}]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["title", "abstract"], required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--four-bit", action="store_true")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tag", default="", help="output <stage>.local-<tag>.jsonl (amendment v0.8 third rater)")
    a = ap.parse_args()

    src = ROOT / ("data/processed/records.jsonl" if a.stage == "title" else "data/processed/screen/stage2-input.jsonl")
    out = ROOT / f"data/processed/screen/{a.stage}.local{'-' + a.tag if a.tag else ''}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines()} if out.exists() else set()
    recs = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]
    recs = [r for r in recs if r["id"] not in done][: a.limit]
    criteria = (ROOT / "research/protocol/screening/criteria.md").read_text(encoding="utf-8")

    tok = AutoTokenizer.from_pretrained(a.model, revision=a.revision)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                           bnb_4bit_compute_dtype=torch.bfloat16) if a.four_bit else None
    # quantization_config must be left out (not None) for an already-quantised checkpoint such as models/q4/...
    qkw = {"quantization_config": q} if q is not None else {}
    model = AutoModelForCausalLM.from_pretrained(a.model, revision=a.revision, torch_dtype=torch.bfloat16,
                                                 device_map="cuda", **qkw)
    model.eval()
    # First token of each label as the model would write it after the assistant prefix.
    label_ids = [tok.encode(l, add_special_tokens=False)[0] for l in LABELS]
    if len(set(label_ids)) != 3:
        raise SystemExit(f"label first tokens collide for this tokenizer: {label_ids}")

    t0 = time.time()
    with out.open("a", encoding="utf-8") as fh, torch.inference_mode():
        for i in range(0, len(recs), a.batch):
            chunk = recs[i:i + a.batch]
            texts = [tok.apply_chat_template(prompt_for(r, a.stage, criteria), tokenize=False,
                                             add_generation_prompt=True) for r in chunk]
            enc = tok(texts, return_tensors="pt", padding=True).to("cuda")
            logits = model(**enc, logits_to_keep=1).logits[:, -1, :].float()   # last position only: saves VRAM, same values
            lp = torch.log_softmax(logits[:, label_ids], dim=-1).exp().cpu().tolist()
            for r, p in zip(chunk, lp):
                fh.write(json.dumps({"id": r["id"], "label": LABELS[max(range(3), key=p.__getitem__)],
                                     "p_include": round(p[0], 4), "p_maybe": round(p[1], 4),
                                     "p_exclude": round(p[2], 4), "model": a.model,
                                     "revision": a.revision}) + "\n")
            fh.flush()
            if (i // a.batch) % 50 == 0:
                print(f"{i + len(chunk)}/{len(recs)} {(i + len(chunk)) / (time.time() - t0):.2f} rec/s", flush=True)


if __name__ == "__main__":
    main()
