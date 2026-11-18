"""Pilot harness: sample LLM responses to the Many Labs 1 paradigms under the crossed perturbation design.

    .venv/Scripts/python.exe -I analysis/pilot/run_pilot.py --model olmo2-1b-instruct --paradigms P1 [--n 50]
        [--wordings W0,W1] [--formats F0,F1] [--temps 0.7,1.0] [--orders sure_first] [--no-greedy]
        [--out runs/pilot] [--limit-batches K] [--dry-run]

Design (pilot-design v0.4): cells = W x F x T (x O for P1); n independent sampled responses per cell and condition,
each with its own recorded RNG seed; plus one greedy (T=0) response per prompt (descriptive only).
Output: runs/pilot/<model>/<paradigm>.jsonl (one line per response: prompt, setting, seed, raw output, parse),
        runs/pilot/<model>/<paradigm>.batches.jsonl (per-batch timing, tokens, peak VRAM),
        runs/pilot/<model>/meta.json (environment, config hash, git sha, prompt-manifest check).
Resumable: a response key (paradigm, W, F, T, O, x, r) already in the jsonl is skipped.
Per-response sampling noise: Gumbel-max with one torch.Generator per response seeded with the recorded seed,
so a response's sampling randomness does not depend on its batch neighbours (logits can still differ at the
numerical level with batch composition under bf16 / NF4; this is recorded as a limitation, not hidden).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import parsers  # noqa: E402
import prompt_manifest  # noqa: E402

PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]


# ----------------------------------------------------------------------------- prompts
def load_yaml(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf8"))


def load_prompts():
    common = load_yaml(HERE / "prompts/common.yaml")
    words = {}
    for w in ("W0", "W1", "W2", "W3"):
        for pid in PARADIGMS:
            words[(w, pid)] = load_yaml(HERE / f"prompts/{w}/{pid}.yaml")
    return common, words


def build_prompt(common, words, paradigm, W, F, x, O=None):
    """Return dict(system, user, labels, sure_label) for one prompt."""
    d = words[(W, paradigm)]
    rtype = d["response_type"]
    fmt = common["formats"][F][rtype]
    labels, sure_label = None, None
    if paradigm == "P1":
        fr = d["frames"][f"x{x}"]
        first, second = fr["labels"]
        if O == "sure_first":
            lines = [(first, fr["sure"]), (second, fr["risky"])]
            sure_label = first
        elif O == "risky_first":
            lines = [(first, fr["risky"]), (second, fr["sure"])]
            sure_label = second
        else:
            raise ValueError(O)
        body = d["stem"] + "\n" + "\n".join(t.replace("{L}", l) for l, t in lines) + "\n" + d["question"]
        labels = [first, second]
    elif paradigm.startswith("P2"):
        body = d["intro"] + "\n\n" + d["conditions"][f"x{x}"]
    elif paradigm == "P3":
        body = d["conditions"][f"x{x}"] + "\n" + d["scale"]
    else:
        body = d["conditions"][f"x{x}"]
    return dict(system=common["system"], user=body + "\n\n" + fmt, labels=labels, sure_label=sure_label, response_type=rtype)


def seed_for(model, paradigm, W, F, T, O, x, r):
    s = f"{model}|{paradigm}|{W}|{F}|{T}|{O}|{x}|{r}".encode()
    return int(hashlib.sha256(s).hexdigest()[:8], 16) % (2 ** 31 - 1)


def enumerate_items(model, paradigm, cfg, n, wordings, formats, temps, orders, greedy):
    orders = orders if paradigm == "P1" else [None]
    items = []
    for W, F, T, O in itertools.product(wordings, formats, temps, orders):
        for x in (1, 0):
            for r in range(n):
                items.append(dict(paradigm=paradigm, W=W, F=F, T=T, O=O, x=x, r=r))
    if greedy:
        for W, F, O in itertools.product(wordings, formats, orders):
            for x in (1, 0):
                items.append(dict(paradigm=paradigm, W=W, F=F, T=0.0, O=O, x=x, r=0))
    for it in items:
        it["seed"] = seed_for(model, paradigm, it["W"], it["F"], it["T"], it["O"], it["x"], it["r"])
        it["key"] = f'{it["paradigm"]}|{it["W"]}|{it["F"]}|{it["T"]}|{it["O"]}|{it["x"]}|{it["r"]}'
    return items


# ----------------------------------------------------------------------------- model
def load_model(mcfg):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    path = ROOT / mcfg["path"]
    tok = AutoTokenizer.from_pretrained(path)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = dict(device_map={"": 0})
    if mcfg["quant"] == "nf4":
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
                                                       bnb_4bit_use_double_quant=False)
        kw["dtype"] = torch.bfloat16
    else:  # bf16, or a saved NF4 checkpoint (its quantization_config is stored with the weights)
        kw["dtype"] = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(path, **kw)
    model.eval()
    return model, tok


class GumbelSampler:
    """LogitsProcessor: scores/T + Gumbel noise from per-row generators; greedy argmax over it samples from softmax(scores/T).
    Rows with T == 0 are left untouched (plain argmax)."""

    def __init__(self, seeds, temps, device):
        import torch
        self.torch = torch
        self.temps = temps
        self.gens = []
        for s in seeds:
            g = torch.Generator(device=device)
            g.manual_seed(int(s))
            self.gens.append(g)
        self.device = device

    def __call__(self, input_ids, scores):
        torch = self.torch
        out = scores.float()
        V = out.shape[-1]
        for i, (g, T) in enumerate(zip(self.gens, self.temps)):
            if T > 0:
                u = torch.rand(V, generator=g, device=self.device, dtype=torch.float32).clamp_min_(1e-20)
                out[i] = out[i] / T - torch.log(-torch.log(u))
        return out


def eos_ids(model, tok):
    ids = set()
    gc = model.generation_config.eos_token_id
    if gc is not None:
        ids |= set(gc if isinstance(gc, (list, tuple)) else [gc])
    if tok.eos_token_id is not None:
        ids.add(tok.eos_token_id)
    for t in ("<|im_end|>", "<|end_of_text|>", "<|endoftext|>", "<|eot_id|>", "<end_of_turn>"):
        i = tok.convert_tokens_to_ids(t)
        if isinstance(i, int) and i >= 0 and i != tok.unk_token_id:
            ids.add(i)
    return sorted(ids)


def generate_batch(model, tok, rendered, seeds, temps, max_new_tokens, eos):
    import torch
    from transformers import GenerationConfig, LogitsProcessorList
    enc = tok(rendered, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
    gc = GenerationConfig(do_sample=False, max_new_tokens=max_new_tokens, pad_token_id=tok.pad_token_id, eos_token_id=eos,
                          repetition_penalty=1.0, num_beams=1, temperature=None, top_p=None, top_k=None)
    proc = LogitsProcessorList([GumbelSampler(seeds, temps, "cuda")])
    torch.cuda.synchronize()
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**enc, generation_config=gc, logits_processor=proc)
    torch.cuda.synchronize()
    dt = time.time() - t0
    new = out[:, enc["input_ids"].shape[1]:].cpu()
    texts, ntoks, fin = [], [], []
    eos_set = set(eos)
    for row in new.tolist():
        n = len(row)
        done = False
        for j, t in enumerate(row):
            if t in eos_set:
                n, done = j, True
                break
        ntoks.append(n)
        fin.append(done)
        texts.append(tok.decode(row[:n], skip_special_tokens=True))
    return texts, ntoks, fin, dt, int(enc["input_ids"].shape[1])


def generate_safe(model, tok, rendered, seeds, temps, mnt, eos):
    """generate_batch with recursive halving on CUDA out-of-memory (per-row seeds make the split harmless)."""
    import torch
    try:
        return generate_batch(model, tok, rendered, seeds, temps, mnt, eos)
    except (torch.OutOfMemoryError, torch.AcceleratorError) as e:
        if len(rendered) == 1 or "out of memory" not in str(e).lower():
            raise
        torch.cuda.empty_cache()
        h = len(rendered) // 2
        print(f"OOM at batch {len(rendered)}: splitting", flush=True)
        a = generate_safe(model, tok, rendered[:h], seeds[:h], temps[:h], mnt, eos)
        b = generate_safe(model, tok, rendered[h:], seeds[h:], temps[h:], mnt, eos)
        return a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3], max(a[4], b[4])


# ----------------------------------------------------------------------------- main
def git_sha():
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--paradigms", default=",".join(PARADIGMS))
    ap.add_argument("--n", type=int)
    ap.add_argument("--wordings")
    ap.add_argument("--formats")
    ap.add_argument("--temps")
    ap.add_argument("--orders")
    ap.add_argument("--no-greedy", action="store_true")
    ap.add_argument("--out", default="runs/pilot")
    ap.add_argument("--config", default=str(HERE / "config.yaml"))
    ap.add_argument("--batch-size", type=int)
    ap.add_argument("--limit-batches", type=int)
    ap.add_argument("--dry-run", action="store_true")
    # Amendment A1.9: regenerate only the listed unfinished F1 responses (same seed) at a longer limit.
    # Writes <paradigm>.topup<N>.jsonl next to the originals, which stay unchanged.
    ap.add_argument("--topup", help="JSONL of {model, paradigm, key} to regenerate (runs/pilot-topup/topup_keys.jsonl)")
    ap.add_argument("--topup-tokens", type=int, default=512)
    a = ap.parse_args()

    bad = prompt_manifest.verify()
    if bad:
        sys.exit(f"prompt files changed after freezing: {bad}")
    cfg = load_yaml(a.config)
    des = cfg["design"]
    mcfg = cfg["models"][a.model]
    n = a.n or des["n"]
    wordings = a.wordings.split(",") if a.wordings else des["wordings"]
    formats = a.formats.split(",") if a.formats else des["formats"]
    temps = [float(t) for t in a.temps.split(",")] if a.temps else des["temps"]
    orders = a.orders.split(",") if a.orders else des["orders_P1"]
    greedy = des["greedy"] and not a.no_greedy
    mnt = dict(cfg["generation"]["max_new_tokens"])
    suffix = ""
    topup = None
    if a.topup:
        topup = {(r["paradigm"], r["key"]) for r in map(json.loads, Path(a.topup).read_text(encoding="utf8").splitlines())
                 if r.get("model") == a.model}
        mnt["F1"] = a.topup_tokens
        suffix = f".topup{a.topup_tokens}"
    bs = a.batch_size or mcfg["batch_size"]
    outdir = ROOT / a.out / a.model
    outdir.mkdir(parents=True, exist_ok=True)
    common, words = load_prompts()

    plan = {}
    for p in a.paradigms.split(","):
        items = enumerate_items(a.model, p, cfg, n, wordings, formats, temps, orders, greedy)
        if topup is not None:
            items = [it for it in items if (p, it["key"]) in topup]
        done = set()
        f = outdir / f"{p}{suffix}.jsonl"
        if f.exists():
            for line in f.read_text(encoding="utf8").splitlines():
                if line.strip():
                    done.add(json.loads(line)["key"])
        todo = [it for it in items if it["key"] not in done]
        plan[p] = (items, todo)
        print(f"{a.model} {p}: {len(items)} planned, {len(items) - len(todo)} done, {len(todo)} to do")
    if a.dry_run:
        return

    import torch
    import transformers
    model, tok = load_model(mcfg)
    eos = eos_ids(model, tok)
    cfg_hash = hashlib.sha256(Path(a.config).read_bytes()).hexdigest()[:16]
    meta = dict(model=a.model, repo=mcfg["repo"], revision=mcfg["revision"], quant=mcfg["quant"], batch_size=bs,
                torch=torch.__version__, transformers=transformers.__version__, cuda=torch.version.cuda,
                gpu=torch.cuda.get_device_name(0), git_sha=git_sha(), config_sha256_16=cfg_hash, n=n, wordings=wordings,
                formats=formats, temps=temps, orders=orders, greedy=greedy, max_new_tokens=mnt, eos_ids=eos,
                prompt_manifest="verified", started=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    (outdir / f"meta{suffix}.json").write_text(json.dumps(meta, indent=2), encoding="utf8")

    nb = 0
    for p, (items, todo) in plan.items():
        if not todo:
            continue
        # render prompts once per unique (W, F, O, x)
        cache = {}
        for it in todo:
            k = (it["W"], it["F"], it["O"], it["x"])
            if k not in cache:
                pr = build_prompt(common, words, p, it["W"], it["F"], it["x"], it["O"])
                msgs = [{"role": "system", "content": pr["system"]}, {"role": "user", "content": pr["user"]}]
                pr["rendered"] = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
                pr["n_prompt_tokens"] = len(tok(pr["rendered"], add_special_tokens=False)["input_ids"])
                cache[k] = pr
        # batches: group by format (different max_new_tokens), sort by prompt length
        todo.sort(key=lambda it: (it["F"], cache[(it["W"], it["F"], it["O"], it["x"])]["n_prompt_tokens"], it["key"]))
        batches = []
        for F, grp in itertools.groupby(todo, key=lambda it: it["F"]):
            grp = list(grp)
            batches += [grp[i:i + bs] for i in range(0, len(grp), bs)]
        fout = (outdir / f"{p}{suffix}.jsonl").open("a", encoding="utf8")
        fbat = (outdir / f"{p}{suffix}.batches.jsonl").open("a", encoding="utf8")
        t_start = time.time()
        for bi, batch in enumerate(batches):
            if a.limit_batches and nb >= a.limit_batches:
                break
            nb += 1
            F = batch[0]["F"]
            prs = [cache[(it["W"], it["F"], it["O"], it["x"])] for it in batch]
            torch.cuda.reset_peak_memory_stats()
            texts, ntoks, fin, dt, plen = generate_safe(model, tok, [pr["rendered"] for pr in prs], [it["seed"] for it in batch],
                                                        [it["T"] for it in batch], mnt[F], eos)
            peak = torch.cuda.max_memory_allocated() / 2 ** 30
            for it, pr, txt, nt, fi in zip(batch, prs, texts, ntoks, fin):
                res = parsers.parse_response(pr["response_type"], txt, F, labels=pr["labels"])
                y = res["value"]
                if pr["response_type"] == "choice" and res["valid"]:
                    y = 1.0 if res["value"] == pr["sure_label"] else 0.0
                rec = dict(key=it["key"], model=a.model, paradigm=p, W=it["W"], F=F, T=it["T"], O=it["O"], x=it["x"], r=it["r"],
                           greedy=(it["T"] == 0.0), seed=it["seed"], system=pr["system"], user=pr["user"], labels=pr["labels"],
                           sure_label=pr["sure_label"], n_prompt_tokens=pr["n_prompt_tokens"], raw=txt, n_new_tokens=nt,
                           finished=fi, parsed=res["value"], valid=res["valid"], parse_method=res["method"], parse_note=res["note"], y=y)
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            nv = sum(1 for t in texts)
            fbat.write(json.dumps(dict(paradigm=p, F=F, batch=bi, rows=len(batch), seconds=round(dt, 3), new_tokens=int(sum(ntoks)),
                                       padded_prompt_len=plen, peak_vram_gib=round(peak, 3))) + "\n")
            fbat.flush()
            if bi % 5 == 0 or bi == len(batches) - 1:
                print(f"{p} batch {bi + 1}/{len(batches)} F={F} rows={len(batch)} {dt:.1f}s {sum(ntoks) / dt:.0f} tok/s peak {peak:.2f} GiB "
                      f"elapsed {time.time() - t_start:.0f}s", flush=True)
        fout.close()
        fbat.close()
    print("done")


if __name__ == "__main__":
    main()
