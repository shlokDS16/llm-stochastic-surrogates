"""Arm L readout: exact next-token and teacher-forced sequence log-probabilities from one forward pass (compute-plan 4.1-4.2).

Everything is stored at T = 1 as raw logits plus the full-vocabulary log-sum-exp at each analysis temperature, so any tempered
probability is exact afterwards:  log p_T(token) = logit / T - LSE_T,  LSE_T = logsumexp(all logits / T).
Prompts are rendered by the model's own chat template (pilot rule) and tokenised with add_special_tokens=False; padding is on the
left and position_ids are rebuilt from the attention mask, as generate() does.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPS = (0.3, 0.7, 1.0, 1.5)


def load(mcfg, mem_fraction=0.88):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.cuda.set_per_process_memory_fraction(mem_fraction, 0)
    path = ROOT / mcfg["path"]
    tok = AutoTokenizer.from_pretrained(path)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map={"": 0})
    if mcfg.get("embed_cpu"):
        # 13-14B NF4: the bf16 input-embedding table (1.0-1.5 GB) moves to CPU; the lookup runs there (exact row copy) and the
        # result goes back to the GPU. No accelerate offload (that copies the table to the GPU on every call).
        e = model.get_input_embeddings()
        assert not getattr(model.config, "tie_word_embeddings", False), "tied embeddings: CPU table would split the head"
        model.set_input_embeddings(_make_cpu_embedding()(e.weight.detach().to("cpu")))
        del e
        torch.cuda.empty_cache()
    model.eval()
    return model, tok


def _make_cpu_embedding():
    import torch

    class _CpuEmbedding(torch.nn.Module):
        """Input embedding with its table on CPU as a plain tensor (not a parameter, so model.device stays cuda).
        F.embedding is an exact row copy, so the hidden states equal the all-GPU path."""

        def __init__(self, w):
            super().__init__()
            self.w = w
            self.num_embeddings, self.embedding_dim = w.shape

        def forward(self, ids):
            return torch.nn.functional.embedding(ids.to("cpu"), self.w).to("cuda", non_blocking=False)

    return _CpuEmbedding


def render(tok, system, user):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)


def end_of_turn_id(tok, system="s", user="u"):
    """First token the template writes after an assistant message (the model's own answer terminator)."""
    for sysmsg in ([{"role": "system", "content": system}], []):   # Mistral v0.3 moves the system text to the last user turn
        base = tok.apply_chat_template(sysmsg + [{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)
        full = tok.apply_chat_template(sysmsg + [{"role": "user", "content": user}, {"role": "assistant", "content": "7"}], tokenize=False)
        if full.startswith(base):
            break
    else:
        raise AssertionError("template does not extend the generation prompt")
    tail = full[len(base):]
    i = tail.index("7") + 1
    ids = tok(tail[i:], add_special_tokens=False)["input_ids"]
    return ids[0] if ids else tok.eos_token_id


def continuation_ids(tok, rendered, text):
    """Ids appended by `text` after the rendered prompt; None if appending changes the prompt's own tokens."""
    a = tok(rendered, add_special_tokens=False)["input_ids"]
    b = tok(rendered + text, add_special_tokens=False)["input_ids"]
    return b[len(a):] if b[: len(a)] == a else None


class fp32_head:
    """Context manager: the output layer is recomputed in float32 from the model's own bf16 final hidden state (vocabulary chunks,
    so a 14B model fits). Removes the bf16 rounding of the logits (one bf16 step is 0.125 at |logit| 16-32), which otherwise makes
    ties and caps the resolution of the exact probabilities. Model-specific scaling after lm_head (Granite logits_scaling) still runs."""

    def __init__(self, model, chunk=8192):
        import torch
        self.head = model.get_output_embeddings()
        if type(self.head) is not torch.nn.Linear:
            raise TypeError(f"output layer is {type(self.head).__name__}, not a plain Linear (quantised lm_head?)")
        self.chunk = chunk

    def _hook(self, mod, inp, out):
        import torch
        h = inp[0].float()
        W = mod.weight
        parts = [torch.nn.functional.linear(h, W[i:i + self.chunk].float(), None if mod.bias is None else mod.bias[i:i + self.chunk].float())
                 for i in range(0, W.shape[0], self.chunk)]
        return torch.cat(parts, -1)

    def __enter__(self):
        self.h = self.head.register_forward_hook(self._hook)
        return self

    def __exit__(self, *a):
        self.h.remove()


def _forward(model, tok, id_lists, keep=1):
    """Left-padded forward pass; float32 logits [B, keep, V] for the last `keep` positions (fp32 output layer)."""
    import torch
    L = max(len(x) for x in id_lists)
    pad = tok.pad_token_id
    ids = torch.full((len(id_lists), L), pad, dtype=torch.long)
    att = torch.zeros((len(id_lists), L), dtype=torch.long)
    for i, x in enumerate(id_lists):
        o = L - len(x)
        ids[i, o:] = torch.tensor(x)
        att[i, o:] = 1
    ids, att = ids.cuda(), att.cuda()
    pos = (att.cumsum(-1) - 1).clamp_min(0)
    with torch.no_grad(), fp32_head(model):
        out = model(input_ids=ids, attention_mask=att, position_ids=pos, use_cache=False, logits_to_keep=keep)
    return out.logits.float()


def bf16_ulp(v):
    import math
    return 2.0 ** (math.floor(math.log2(abs(v))) - 7) if v else 0.0


def lse_temps(logits_vec, temps=TEMPS):
    import torch
    return {str(T): float(torch.logsumexp(logits_vec / T, -1)) for T in temps}


def score_first_token(model, tok, rendered_list, cand_ids, temps=TEMPS):
    """Next-token readout at the first answer position (fp32 logits). Also reports the argmax and top-2 gap after rounding the
    logits to bf16, i.e. what a bf16 lm_head (the pilot's generate()) would have seen; a gap within one bf16 step is a tie."""
    import torch
    id_lists = [tok(r, add_special_tokens=False)["input_ids"] for r in rendered_list]
    last = _forward(model, tok, id_lists, keep=1)[:, -1, :]
    res = []
    idx = torch.tensor(cand_ids, device=last.device)
    for i in range(last.shape[0]):
        v = last[i]
        vb = v.to(torch.bfloat16).float()
        top = torch.topk(v, 5)
        tb = torch.topk(vb, 2)
        gap_b = float(tb.values[0] - tb.values[1])
        res.append(dict(finite=bool(torch.isfinite(v).all()), cand_logits=[float(x) for x in v[idx]], lse=lse_temps(v, temps),
                        argmax_id=int(top.indices[0]), top5_ids=[int(x) for x in top.indices], top5_logits=[float(x) for x in top.values],
                        argmax_bf16=int(tb.indices[0]), gap12_bf16=gap_b, bf16_tie=gap_b <= bf16_ulp(float(tb.values[0])) + 1e-9,
                        n_prompt_tokens=len(id_lists[i])))
    return res


def score_sequences(model, tok, rendered, cont_id_lists, temps=TEMPS, batch=16):
    """Teacher-forced scoring of several continuations of one prompt (fp32 logits). For each continuation: per-position raw logit
    of the target token and per-position LSE at each temperature, so tempered sequence log-probs are exact:
    log p_T(seq) = sum_t (logit_t / T - LSE_T,t)."""
    import torch
    base = tok(rendered, add_special_tokens=False)["input_ids"]
    out = []
    for s in range(0, len(cont_id_lists), batch):
        chunk = cont_id_lists[s:s + batch]
        K = max(len(c) for c in chunk) + 1
        logits = _forward(model, tok, [base + c for c in chunk], keep=K)   # right-aligned: position K-1 is each sequence's last token
        for i, c in enumerate(chunk):
            rows = logits[i, K - 1 - len(c): K - 1, :]                     # rows predicting each continuation token
            tgt = torch.tensor(c, device=rows.device)
            tl = rows.gather(1, tgt[:, None])[:, 0]
            out.append(dict(finite=bool(torch.isfinite(rows).all()), tgt_logits=[float(x) for x in tl],
                            lse={str(T): [float(x) for x in torch.logsumexp(rows / T, -1)] for T in temps}))
        del logits
    return out


def seq_logp(rec, T=1.0):
    return sum(t / T - l for t, l in zip(rec["tgt_logits"], rec["lse"][str(T)]))


def choice_variants(tok, rendered, label, user_text, noun=True):
    """Answer paths that commit to option `label`: the bare label (with and without a leading space, and lower/upper case for
    words) and, if noun=True, '<noun> <label>' where the noun is the word the prompt puts before the label (e.g. 'Program A').
    Paths are prefix probabilities (no terminator). A path whose ids extend another path's ids is dropped (already counted),
    so the kept paths are disjoint events."""
    import re
    texts = [label, " " + label]
    if len(label) > 1:
        texts += [label.lower(), " " + label.lower(), label.upper(), " " + label.upper()]
    if noun:
        m = re.search(r"(\w+) " + re.escape(label) + r"(?![A-Za-z0-9])", user_text)
        if m:
            n = m.group(1)
            texts += [f"{n} {label}", f" {n} {label}", f"{n.lower()} {label}", f"{n.upper()} {label}"]
    cands = []
    for t in texts:
        c = continuation_ids(tok, rendered, t)
        if c and all(c != d for _, d in cands):
            cands.append((t, c))
    keep = [(t, c) for t, c in cands if not any(len(d) < len(c) and c[:len(d)] == d for _, d in cands)]
    return keep


def token_texts(tok, V):
    """Surface text of every token id in context (decode '7' + token, drop the '7'), padded to the logits width V."""
    base = tok("7", add_special_tokens=False)["input_ids"][-1]
    n = len(tok)
    texts = tok.batch_decode([[base, i] for i in range(n)])
    b = tok.decode([base])
    texts = [t[len(b):] if t.startswith(b) else t for t in texts]
    return texts + [""] * (V - n)


def gpu_telemetry():
    import subprocess
    try:
        s = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,temperature.gpu,power.draw", "--format=csv,noheader,nounits"],
                                    text=True, timeout=20).strip()
        mu, te, pw = [x.strip() for x in s.split(",")]
        return dict(mem_used_mib=float(mu), temp_c=float(te), power_w=float(pw) if pw not in ("[N/A]", "N/A") else None,
                    t=time.strftime("%Y-%m-%dT%H:%M:%S"))
    except Exception as e:
        return dict(error=str(e)[:100])


def free_ram_gb():
    """Free physical memory and free commit charge (GB), Windows only."""
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    if os.name != "nt":
        return None
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return dict(avail_phys_gb=round(m.ullAvailPhys / 2 ** 30, 2), avail_commit_gb=round(m.ullAvailPageFile / 2 ** 30, 2))
