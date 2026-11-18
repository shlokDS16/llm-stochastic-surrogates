"""Arm L: exact readout of every prompt in the frozen universe for one model (compute-plan 4.1-4.2 with amendments A-L1..A-L3).

    .venv/Scripts/python.exe -I analysis/acme/run_armL.py --model qwen2.5-0.5b-instruct [--items P1,AF] [--out runs/acme-L]

One fresh process per model (analysis/acme/queue_L.sh). Output runs/acme-L/<model>/<item>.jsonl, one record per prompt key
(item|W|O|x|variant), appended and flushed per chunk; keys already present are skipped (resumable). meta.json records versions,
revision and the prompt-manifest check. Readouts (all logits fp32 from the bf16 hidden state, stored at T = 1 with LSE per T):
  choice (P1), yesno (AF, NR x0): prefix probabilities of answer paths per option (scoring.choice_variants);
  yesno2 (NR x1): first-turn readout of the other-country question, then the US question conditional on each first answer;
  rating (P3, QA): next-token logits of the single-token digits 1-9 (with/without leading space);
  number (P2a-d, P4): digit tree (numtree.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import numtree  # noqa: E402
import prompts_acme as PA  # noqa: E402
import scoring  # noqa: E402

CHUNK = 16


def messages(pr, a1=None):
    msgs = [{"role": "system", "content": pr["system"]}]
    for role, text in pr["turns"]:
        msgs.append({"role": role, "content": text.replace("{A1}", a1) if a1 else text})
    return msgs


def paths_block(model, tok, rendered, labels, user_text, noun):
    paths = {L: scoring.choice_variants(tok, rendered, L, user_text, noun=noun) for L in labels}
    flat = [(L, t, c) for L in labels for t, c in paths[L]]
    sq = scoring.score_sequences(model, tok, rendered, [c for _, _, c in flat])
    out = {L: [] for L in labels}
    for (L, t, c), q in zip(flat, sq):
        out[L].append(dict(text=t, ids=c, tgt_logits=q["tgt_logits"], lse=q["lse"], finite=q["finite"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--items", default=",".join(PA.ITEMS))
    ap.add_argument("--wordings", default=",".join(PA.WORDINGS))
    ap.add_argument("--no-decoys", action="store_true")
    ap.add_argument("--no-baselines", action="store_true")
    ap.add_argument("--out", default="runs/acme-L")
    ap.add_argument("--common", help="override common.yaml (tests only)")
    a = ap.parse_args()
    import importlib.util
    for name, path in (("pm_acme", HERE / "prompt_manifest.py"), ("pm_pilot", ROOT / "analysis/pilot/prompt_manifest.py")):
        if not a.common:   # tests with an override common.yaml skip the freeze check
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            bad = mod.verify()
            if bad:
                sys.exit(f"{name}: prompt files changed after freezing: {bad}")
    m = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf8"))["models"][a.model]
    common = yaml.safe_load(Path(a.common).read_text(encoding="utf8")) if a.common else PA.load_common()
    out = ROOT / a.out / a.model
    out.mkdir(parents=True, exist_ok=True)
    items = a.items.split(",")
    allp = [p for p in PA.enumerate_prompts(items, a.wordings.split(","), decoys=not a.no_decoys, baselines=not a.no_baselines) if p["item"] in items]

    import torch
    import transformers
    t0 = time.time()
    model, tok = scoring.load(m)
    V = model.get_output_embeddings().weight.shape[0]
    voc = numtree.Vocab(tok, V)
    eot = scoring.end_of_turn_id(tok)
    meta = dict(model=a.model, repo=m["repo"], revision=m["revision"], quant=m["quant"], torch=torch.__version__,
                transformers=transformers.__version__, gpu=torch.cuda.get_device_name(0), load_seconds=round(time.time() - t0, 1),
                git_sha=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
                manifest_sha256=(hashlib.sha256((HERE / "prompts/MANIFEST.json").read_bytes()).hexdigest() if (HERE / "prompts/MANIFEST.json").exists() else None), temps=list(scoring.TEMPS),
                end_of_turn_id=eot, started=time.strftime("%Y-%m-%dT%H:%M:%S"), ram_after_load=scoring.free_ram_gb())
    (out / f"meta.{time.strftime('%Y%m%dT%H%M%S')}.json").write_text(json.dumps(meta, indent=1), encoding="utf8")
    digit_ids = {}
    probe = scoring.render(tok, common["system"], "x")
    for i in range(1, 10):
        for pre in ("", " "):
            c = scoring.continuation_ids(tok, probe, f"{pre}{i}")
            if c and len(c) == 1:
                digit_ids[f"{pre}{i}"] = c[0]
    dids = sorted(set(digit_ids.values()))

    for item in items:
        f = out / f"{item}.jsonl"
        done = set()
        if f.exists():
            done = {json.loads(l)["key"] for l in f.read_text(encoding="utf8").splitlines() if l.strip()}
        todo = [p for p in allp if p["item"] == item and p["key"] not in done]
        print(f"{a.model} {item}: {len(todo)} to do, {len(done)} done", flush=True)
        if not todo:
            continue
        ti = time.time()
        with f.open("a", encoding="utf8") as fo:
            for s in range(0, len(todo), CHUNK):
                chunk = todo[s:s + CHUNK]
                recs = []
                for p in chunk:
                    pr = PA.build_from(p, common)
                    rec = dict(key=p["key"], model=a.model, item=item, W=p["W"], O=p["O"], x=p["x"], variant=p["variant"],
                               readout=pr["readout"], system=pr["system"], turns=pr["turns"], labels=pr["labels"], sure_label=pr["sure_label"])
                    if pr["readout"] == "yesno2" and p["x"] == 1:
                        r1 = scoring.render(tok, pr["system"], pr["turns"][0][1])
                        rec["first"] = paths_block(model, tok, r1, pr["labels"], pr["turns"][0][1], noun=False)
                        rec["cond"] = {}
                        for A1 in pr["labels"]:
                            rr = tok.apply_chat_template(messages(pr, A1), add_generation_prompt=True, tokenize=False)
                            rec["cond"][A1] = paths_block(model, tok, rr, pr["labels"], pr["turns"][-1][1], noun=False)
                        rec["rendered_sha16"] = hashlib.sha256((r1 + "||" + rr).encode()).hexdigest()[:16]
                        recs.append(rec)
                        continue
                    rendered = tok.apply_chat_template(messages(pr), add_generation_prompt=True, tokenize=False)
                    rec["rendered_sha16"] = hashlib.sha256(rendered.encode()).hexdigest()[:16]
                    rec["n_prompt_tokens"] = len(tok(rendered, add_special_tokens=False)["input_ids"])
                    rec["_rendered"] = rendered
                    recs.append(rec)
                # batched readouts
                rt = [r for r in recs if "_rendered" in r]
                rating = [r for r in rt if r["readout"] == "rating"]
                for r in rating:   # ratings also as answer paths '1'..'9' with/without space (Mistral: space token, then digit)
                    r["paths"] = paths_block(model, tok, r["_rendered"], [str(i) for i in range(1, 10)], r["turns"][-1][1], noun=False)
                if rating:
                    res = scoring.score_first_token(model, tok, [r["_rendered"] for r in rating], dids)
                    for r, q in zip(rating, res):
                        r.update(digit_ids=digit_ids, cand_ids=dids, cand_logits=q["cand_logits"], lse=q["lse"], top5_ids=q["top5_ids"],
                                 top5_logits=q["top5_logits"], finite=q["finite"])
                num = [r for r in rt if r["readout"] == "number"]
                if num:
                    # tree_bs (models.yaml, optional): forward batch for tree expansion; absent = 32, the frozen default
                    trees = numtree.expand_trees(model, tok, [r["_rendered"] for r in num], voc, batch=int(m.get("tree_bs", 32)))
                    for r, tr in zip(num, trees):
                        r["tree"] = tr
                        r["summary_T1"] = numtree.summary(tr, 1.0)
                for r in rt:
                    if r["readout"] in ("choice", "yesno", "yesno2"):
                        r["paths"] = paths_block(model, tok, r["_rendered"], r["labels"], r["turns"][-1][1], noun=(r["readout"] == "choice"))
                for r in recs:
                    r.pop("_rendered", None)
                    fo.write(json.dumps(r, ensure_ascii=False) + "\n")
                fo.flush()
        print(f"{a.model} {item}: {len(todo)} prompts in {time.time() - ti:.1f}s, peak {torch.cuda.max_memory_allocated() / 2 ** 30:.2f} GiB", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
