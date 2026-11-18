"""Arm S for the new items AF, QA, NR (stages S3 and the new-item part of S2; compute-plan 4.4, prereg section 8).
The pilot items (S1, S2 on pilot items) run through analysis/pilot/run_pilot.py with analysis/acme/config_S.yaml.

    .venv/Scripts/python.exe -I analysis/acme/run_armS.py --model M --stage S3      (W0-W3, both orders, T 0.7/1.0, n 50, F0)
    .venv/Scripts/python.exe -I analysis/acme/run_armS.py --model M --stage S2new   (W0-W3, both orders, T 1.0, n 25, F1)

Sampler, seeds and batching as run_pilot.py (Gumbel-max, one generator per response, repetition_penalty 1.0). NR with x1 is two
turns: the first answer (other-country question) is sampled with its own seed, kept verbatim as the assistant turn, then the US
question is sampled; the outcome is the parsed answer to the US question. Output runs/acme-S/<model>/<item>.<stage>.jsonl,
resumable by key; a GPU above 87 C pauses the run between batches until it is at 80 C.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis/pilot"))
import parsers_acme  # noqa: E402
import prompts_acme as PA  # noqa: E402
import run_pilot as RP  # noqa: E402
import scoring  # noqa: E402

STAGES = {"S3": dict(F="F0", temps=[0.7, 1.0], n=50, bs="bs_f0"), "S2new": dict(F="F1", temps=[1.0], n=25, bs="bs_f1")}
MNT = {"F0": 24, "F1": 256}


def thermal_wait(hi=87, lo=80):
    t = scoring.gpu_telemetry().get("temp_c", 0)
    if t and t > hi:
        print(f"GPU {t} C, pausing", flush=True)
        while t and t > lo:
            time.sleep(30)
            t = scoring.gpu_telemetry().get("temp_c", 0)


def seed_for(model, item, W, F, T, O, x, r, turn):
    return RP.seed_for(model, f"{item}#{turn}", W, F, T, O, x, r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--stage", required=True, choices=list(STAGES))
    ap.add_argument("--items", default="AF,QA,NR")
    ap.add_argument("--out", default="runs/acme-S")
    ap.add_argument("--limit-batches", type=int)
    a = ap.parse_args()
    st = STAGES[a.stage]
    m = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf8"))["models"][a.model]
    common = PA.load_common()
    out = ROOT / a.out / a.model
    out.mkdir(parents=True, exist_ok=True)
    import torch
    import transformers
    model, tok = scoring.load(m)   # same weights and dtype as run_pilot.load_model, plus the memory cap and embed_cpu option
    eos = RP.eos_ids(model, tok)
    bs = m[st["bs"]]
    (out / f"meta.{a.stage}.{time.strftime('%Y%m%dT%H%M%S')}.json").write_text(json.dumps(dict(
        model=a.model, repo=m["repo"], revision=m["revision"], stage=a.stage, batch_size=bs, eos_ids=eos, torch=torch.__version__,
        transformers=transformers.__version__, git_sha=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                                                        text=True).stdout.strip(), **{k: st[k] for k in ("F", "temps", "n")}), indent=1), encoding="utf8")
    nb = 0
    for item in a.items.split(","):
        f = out / f"{item}.{a.stage}.jsonl"
        done = {json.loads(l)["key"] for l in f.read_text(encoding="utf8").splitlines() if l.strip()} if f.exists() else set()
        todo = []
        for W, O, T, x in itertools.product(["W0", "W1", "W2", "W3"], PA.ORDERS[item], st["temps"], (1, 0)):
            for r in range(st["n"]):
                k = f"{item}|{W}|{st['F']}|{T}|{O}|{x}|{r}"
                if k not in done:
                    todo.append(dict(item=item, W=W, O=O, T=T, x=x, r=r, key=k))
        print(f"{a.model} {item} {a.stage}: {len(todo)} to do, {len(done)} done", flush=True)
        if not todo:
            continue
        cache = {}
        for it in todo:
            ck = (it["W"], it["O"], it["x"])
            if ck not in cache:
                cache[ck] = PA.build(item, it["W"], it["x"], it["O"], F=st["F"], common=common)
        todo.sort(key=lambda it: (it["W"], it["O"], it["x"], it["T"], it["r"]))
        with f.open("a", encoding="utf8") as fo:
            for s in range(0, len(todo), bs):
                if a.limit_batches and nb >= a.limit_batches:
                    break
                nb += 1
                thermal_wait()
                batch = todo[s:s + bs]
                prs = [cache[(it["W"], it["O"], it["x"])] for it in batch]
                first = [None] * len(batch)
                two = [i for i, pr in enumerate(prs) if len(pr["turns"]) == 3]
                if two:   # NR x1: sample the first answer
                    rend = [tok.apply_chat_template([{"role": "system", "content": prs[i]["system"]}, {"role": "user", "content": prs[i]["turns"][0][1]}],
                                                    add_generation_prompt=True, tokenize=False) for i in two]
                    tx, _, _, _, _ = RP.generate_safe(model, tok, rend, [seed_for(a.model, item, batch[i]["W"], st["F"], batch[i]["T"], batch[i]["O"], 1, batch[i]["r"], 1) for i in two],
                                                      [batch[i]["T"] for i in two], MNT[st["F"]], eos)
                    for i, t in zip(two, tx):
                        first[i] = t
                rendered = []
                for i, (it, pr) in enumerate(zip(batch, prs)):
                    msgs = [{"role": "system", "content": pr["system"]}]
                    for role, text in pr["turns"]:
                        msgs.append({"role": role, "content": text.replace("{A1}", first[i]) if first[i] is not None else text})
                    rendered.append(tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False))
                seeds = [seed_for(a.model, item, it["W"], st["F"], it["T"], it["O"], it["x"], it["r"], 2 if first[i] is not None else 0) for i, it in enumerate(batch)]
                torch.cuda.reset_peak_memory_stats()
                texts, ntoks, fin, dt, plen = RP.generate_safe(model, tok, rendered, seeds, [it["T"] for it in batch], MNT[st["F"]], eos)
                peak = torch.cuda.max_memory_allocated() / 2 ** 30
                for i, (it, pr, txt, nt, fi) in enumerate(zip(batch, prs, texts, ntoks, fin)):
                    rtype = "rating" if item == "QA" else "yesno"
                    res = parsers_acme.parse(rtype, txt, st["F"])
                    rec = dict(key=it["key"], model=a.model, item=item, stage=a.stage, W=it["W"], F=st["F"], T=it["T"], O=it["O"], x=it["x"], r=it["r"],
                               seed=seeds[i], first_answer=first[i], first_parsed=(parsers_acme.parse("yesno", first[i], st["F"])["value"] if first[i] else None),
                               raw=txt, n_new_tokens=nt, finished=fi, parsed=res["value"], valid=res["valid"], parse_method=res["method"], parse_note=res["note"])
                    fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fo.flush()
                if nb % 10 == 1:
                    print(f"{item} batch {s // bs + 1}/{(len(todo) + bs - 1) // bs} rows={len(batch)} {dt:.1f}s peak {peak:.2f} GiB", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
