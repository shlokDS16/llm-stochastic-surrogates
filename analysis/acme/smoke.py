"""GPU smoke test, one model per process (gate G2, compute-plan 7.2). Run through analysis/acme/smoke_queue.sh.

    .venv/Scripts/python.exe -I analysis/acme/smoke.py --model qwen2.5-0.5b-instruct [--bs-f0 N --bs-f1 N] [--out runs/acme-smoke]

Checks, all on the frozen pilot prompts (W0-W3, F0 and F1; no new wordings are read):
  (a) forward-pass argmax at the first answer position equals the first token of greedy generate() in this process
      (padding / position-id pipeline of the Arm L scorer);
  (b) pilot models only: that argmax equals the first token of the pilot's own greedy response (G2 ii, at least 98 percent);
      also the restricted readout (letters for P1, digits for P3) against the pilot's parsed greedy answer;
  (c) valid mass on the answer tokens (letters for P1, digits 1-9 for P3) and digit/number mass for P2/P4;
  (d) teacher-forced sequence scoring of a small number grid, finite and normalisable;
  (e) peak VRAM of generation at the F1 maximum length (256 new tokens forced) at bs_f1, and at F0 (24) at bs_f0 (G2 iii, <= 10.5 GiB);
  (f) no NaN / inf anywhere (G2 iv).
Exit code 0 pass, 2 out of memory in (e) (driver halves the batch and retries), 1 other failure.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis/pilot"))
import scoring  # noqa: E402

PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
VRAM_LIMIT = 10.5
ANS = ["A", "B", "C", "D", "Yes", "No", "yes", "no"] + [str(i) for i in range(1, 10)]


def pilot_prompts():
    import prompt_manifest
    import run_pilot
    bad = prompt_manifest.verify()
    if bad:
        sys.exit(f"pilot prompt files changed: {bad}")
    common, words = run_pilot.load_prompts()
    out = []
    for p in PARADIGMS:
        for W in ("W0", "W1", "W2", "W3"):
            for O in (["sure_first", "risky_first"] if p == "P1" else [None]):
                for x in (1, 0):
                    for F in ("F0", "F1"):
                        pr = run_pilot.build_prompt(common, words, p, W, F, x, O)
                        out.append(dict(paradigm=p, W=W, O=O, x=x, F=F, key=f"{p}|{W}|{F}|0.0|{O}|{x}|0", **pr))
    return out


def gen(model, tok, rendered, n_new, force=False):
    import torch
    enc = tok(rendered, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
    # repetition_penalty=1.0 overrides the 1.05-1.1 in Qwen's generation_config, as the pilot did (run_pilot.generate_batch)
    kw = dict(do_sample=False, max_new_tokens=n_new, pad_token_id=tok.pad_token_id, temperature=None, top_p=None, top_k=None,
              repetition_penalty=1.0, num_beams=1)
    if force:
        kw["min_new_tokens"] = n_new
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**enc, **kw)
    torch.cuda.synchronize()
    return out[:, enc["input_ids"].shape[1]:].cpu(), time.time() - t0, torch.cuda.max_memory_allocated() / 2 ** 30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--bs-f0", type=int)
    ap.add_argument("--bs-f1", type=int)
    ap.add_argument("--out", default="runs/acme-smoke")
    a = ap.parse_args()
    m = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf8"))["models"][a.model]
    bs0, bs1 = a.bs_f0 or m["bs_f0"], a.bs_f1 or m["bs_f1"]
    out = ROOT / a.out / a.model
    out.mkdir(parents=True, exist_ok=True)
    rep = dict(model=a.model, repo=m["repo"], revision=m["revision"], quant=m["quant"], bs_f0=bs0, bs_f1=bs1,
               started=time.strftime("%Y-%m-%dT%H:%M:%S"), ram_before=scoring.free_ram_gb(), gpu_before=scoring.gpu_telemetry())
    fails = []
    import torch
    import transformers
    rep.update(torch=torch.__version__, transformers=transformers.__version__)
    t0 = time.time()
    model, tok = scoring.load(m)
    rep["load_seconds"] = round(time.time() - t0, 1)
    rep["ram_after_load"] = scoring.free_ram_gb()
    rep["vram_after_load_gib"] = round(torch.cuda.memory_allocated() / 2 ** 30, 3)
    rep["end_of_turn_id"] = eot = scoring.end_of_turn_id(tok)
    rep["end_of_turn_piece"] = tok.convert_ids_to_tokens([eot])[0]

    prompts = pilot_prompts()
    for pr in prompts:
        pr["rendered"] = scoring.render(tok, pr["system"], pr["user"])
    probe = scoring.render(tok, prompts[0]["system"], prompts[0]["user"])
    cand = {}
    for s in ANS:
        for pre in ("", " "):
            c = scoring.continuation_ids(tok, probe, pre + s)
            if c is not None and len(c) == 1:
                cand[pre + s] = c[0]
    rep["answer_token_ids"] = cand
    cid = sorted(set(cand.values()))
    pos = {t: i for i, t in enumerate(cid)}

    # (a)-(c): forward-pass readout vs greedy first token, F0 prompts. Comparisons use the bf16-rounded argmax (what the pilot's
    # bf16 lm_head saw); a prompt whose bf16 top-2 gap is within one bf16 step is a tie and is reported, not counted.
    import math
    f0 = [p for p in prompts if p["F"] == "F0"]
    recs, n_fin = [], 0
    tf = time.time()
    cb = min(16, bs0)
    for s in range(0, len(f0), cb):
        chunk = f0[s:s + cb]
        res = scoring.score_first_token(model, tok, [p["rendered"] for p in chunk], cid)
        torch.cuda.empty_cache()
        g = torch.cat([gen(model, tok, [p["rendered"] for p in chunk[k:k + 4]], 1)[0] for k in range(0, len(chunk), 4)], 0)
        for p, r, gi in zip(chunk, res, g[:, 0].tolist()):
            n_fin += r["finite"]
            lse = r["lse"]["1.0"]
            pm = lambda keys: sum(math.exp(r["cand_logits"][pos[t]] - lse) for t in {cand[k] for k in keys if k in cand})  # unique ids (Phi maps " 5" and "5" to one id)
            rec = dict(key=p["key"], paradigm=p["paradigm"], argmax_id=r["argmax_id"], argmax_bf16=r["argmax_bf16"],
                       argmax_piece=tok.convert_ids_to_tokens([r["argmax_id"]])[0], gen_first_id=gi,
                       fwd_eq_gen=(r["argmax_bf16"] == gi), bf16_tie=r["bf16_tie"], gap12_bf16=r["gap12_bf16"], finite=r["finite"],
                       top5=[(tok.convert_ids_to_tokens([t])[0], round(l, 3)) for t, l in zip(r["top5_ids"], r["top5_logits"])],
                       mass_digits=pm([str(i) for i in range(1, 10)] + [" " + str(i) for i in range(1, 10)]),
                       restricted_digit=max(range(1, 10), key=lambda i: max(r["cand_logits"][pos[cand[v]]] for v in (str(i), " " + str(i)) if v in cand)))
            if p["labels"]:   # choice readout over answer paths ('A', ' A', 'Program A', ...), teacher-forced
                paths = {L: scoring.choice_variants(tok, p["rendered"], L, p["user"]) for L in p["labels"]}
                flat = [(L, t, c) for L in p["labels"] for t, c in paths[L]]
                sq = scoring.score_sequences(model, tok, p["rendered"], [c for _, _, c in flat])
                mass = {L: 0.0 for L in p["labels"]}
                for (L, t, c), q in zip(flat, sq):
                    mass[L] += math.exp(scoring.seq_logp(q))
                    n_fin += 0 if q["finite"] else -1
                rec.update(paths={L: [t for t, _ in paths[L]] for L in p["labels"]}, mass_letters_first_token=pm(p["labels"] + [" " + l for l in p["labels"]]),
                           mass_letters=sum(mass.values()), p_label={L: mass[L] / sum(mass.values()) for L in mass},
                           restricted_letter=max(mass, key=mass.get))
            recs.append(rec)
    rep["forward_seconds_per_prompt"] = round((time.time() - tf) / len(f0) / 2, 4)  # includes the generate(1) and path scoring
    rep["n_f0_prompts"] = len(f0)
    nt = [r for r in recs if not r["bf16_tie"]]
    rep["n_bf16_ties"] = len(recs) - len(nt)
    rep["fwd_eq_gen_rate_all"] = sum(r["fwd_eq_gen"] for r in recs) / len(recs)
    rep["fwd_eq_gen_rate_nontie"] = sum(r["fwd_eq_gen"] for r in nt) / len(nt)
    rep["fwd_gen_mismatches"] = [dict(key=r["key"], tie=r["bf16_tie"], gap12_bf16=r["gap12_bf16"], top5=r["top5"],
                                      gen=tok.convert_ids_to_tokens([r["gen_first_id"]])[0]) for r in recs if not r["fwd_eq_gen"]]
    if rep["fwd_eq_gen_rate_nontie"] < 0.98:
        fails.append(f"forward argmax != generate first token on {1 - rep['fwd_eq_gen_rate_nontie']:.3f} of non-tie prompts")
    by = lambda p: [r for r in recs if r["paradigm"] == p]
    for k, P in (("mass_letters", "P1"), ("mass_letters_first_token", "P1"), ("mass_digits", "P3")):
        v = [r[k] for r in by(P)]
        rep[f"{k}_{P}"] = dict(min=round(min(v), 4), mean=round(sum(v) / len(v), 4), share_below_0p9=round(sum(x < 0.9 for x in v) / len(v), 4))
    rep["argmax_pieces_numeric"] = sorted({r["argmax_piece"] for r in recs if r["paradigm"] in ("P2a", "P2b", "P2c", "P2d", "P4")})

    # (b) pilot parity (G2 ii): first token of the pilot's greedy response vs the bf16 argmax here
    if m.get("pilot"):
        pil = {}
        for p in PARADIGMS:
            for line in (ROOT / f"runs/pilot/{a.model}/{p}.jsonl").open(encoding="utf8"):
                row = json.loads(line)
                if row["greedy"] and row["F"] == "F0":
                    pil[row["key"]] = row
        n = eq = n_nt = eq_nt = eq_r = n_r = 0
        mism = []
        for r, p in zip(recs, f0):
            row = pil.get(r["key"])
            if row is None:
                continue
            assert row["user"] == p["user"] and row["system"] == p["system"], r["key"]
            n += 1
            piece = tok.decode([r["argmax_bf16"]])
            ok = row["raw"].startswith(piece) if piece.strip() else row["raw"].startswith(piece.strip())
            eq += ok
            if not r["bf16_tie"]:
                n_nt += 1
                eq_nt += ok
            if not ok:
                mism.append(dict(key=r["key"], argmax=piece, pilot_raw=row["raw"][:40], tie=r["bf16_tie"], gap12_bf16=r["gap12_bf16"], top5=r["top5"]))
            if p["paradigm"] == "P1" and row["valid"] and not r["bf16_tie"]:
                n_r += 1
                eq_r += r["restricted_letter"] == row["parsed"]
            if p["paradigm"] == "P3" and row["valid"] and row["raw"].strip().isdigit() and not r["bf16_tie"]:
                n_r += 1
                eq_r += r["restricted_digit"] == int(row["parsed"])
        rep["pilot_parity"] = dict(n=n, first_token_match_all=eq / n, n_nontie=n_nt, first_token_match_nontie=eq_nt / n_nt,
                                   restricted_n=n_r, restricted_match=(eq_r / n_r if n_r else None), mismatches=mism)
        if eq_nt / n_nt < 0.98:
            fails.append(f"pilot greedy parity on non-tie prompts {eq_nt / n_nt:.3f} < 0.98")

    # (d) sequence scoring of a small grid (P2a W0 x1 prompt)
    pr = next(p for p in f0 if p["paradigm"] == "P2a" and p["W"] == "W0" and p["x"] == 1)
    grid = ["1500", "2000", "2500", "2900", "3000", "4000", "6000"]
    conts = [scoring.continuation_ids(tok, pr["rendered"], g) + [eot] for g in grid]
    sq = scoring.score_sequences(model, tok, pr["rendered"], conts)
    import math
    lp = [sum(t - l for t, l in zip(s["tgt_logits"], s["lse"]["1.0"])) for s in sq]
    rep["grid_test"] = dict(grid=grid, n_tokens=[len(c) for c in conts], logp=[round(x, 3) for x in lp], Z=sum(math.exp(x) for x in lp),
                            finite=all(s["finite"] for s in sq))

    # (e) VRAM at the maximum lengths
    f1 = sorted([p for p in prompts if p["F"] == "F1"], key=lambda p: -len(tok(p["rendered"], add_special_tokens=False)["input_ids"]))
    try:
        b = [f1[i % len(f1)]["rendered"] for i in range(bs1)]
        g1, dt1, pk1 = gen(model, tok, b, 256, force=True)
        rep["vram_f1"] = dict(batch=bs1, new_tokens=256, seconds=round(dt1, 2), tok_per_s=round(bs1 * 256 / dt1), peak_gib=round(pk1, 3))
        b = [f0[i % len(f0)]["rendered"] for i in range(bs0)]
        g0, dt0, pk0 = gen(model, tok, b, 24, force=True)
        rep["vram_f0"] = dict(batch=bs0, new_tokens=24, seconds=round(dt0, 2), tok_per_s=round(bs0 * 24 / dt0), peak_gib=round(pk0, 3))
    except (torch.OutOfMemoryError, torch.AcceleratorError) as e:
        rep["oom"] = str(e)[:300]
        rep["status"] = "oom"
        (out / "smoke.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf8")
        print(f"{a.model}: OOM at bs_f0={bs0} bs_f1={bs1}")
        sys.exit(2)
    for k in ("vram_f1", "vram_f0"):
        if rep[k]["peak_gib"] > VRAM_LIMIT:
            fails.append(f"{k} peak {rep[k]['peak_gib']} GiB > {VRAM_LIMIT}")
    nonfinite = len(recs) - n_fin + (0 if rep["grid_test"]["finite"] else 1)
    rep["nonfinite"] = nonfinite
    if nonfinite:
        fails.append(f"{nonfinite} non-finite readouts")
    rep["gpu_after"] = scoring.gpu_telemetry()
    rep["fails"] = fails
    rep["status"] = "pass" if not fails else "fail"
    rep["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (out / "smoke.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf8")
    (out / "readout_f0.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf8")
    s = {k: rep.get(k) for k in ("status", "fails", "load_seconds", "n_bf16_ties", "fwd_eq_gen_rate_nontie", "mass_letters_P1",
                                 "mass_letters_first_token_P1", "mass_digits_P3")}
    s["pilot"] = {k: v for k, v in rep.get("pilot_parity", {}).items() if k != "mismatches"}
    s["vram"] = (rep["vram_f0"]["peak_gib"], rep["vram_f1"]["peak_gib"])
    s["Z"] = round(rep["grid_test"]["Z"], 4)
    print(a.model, json.dumps(s))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
