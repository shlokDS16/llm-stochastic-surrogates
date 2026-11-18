"""CPU-only smoke part 1: chat templates and answer-token splits for every roster model (tokenizers only, no weights).

    .venv/Scripts/python.exe -I analysis/acme/template_check.py [--out runs/acme-smoke]

Writes <out>/templates.json (one record per model) and <out>/templates.md (summary). Checks:
  - the pilot message pair (system + user) renders; whether the system text survives (Mistral v0.3 has no system role);
  - BOS handling: the rendered string already carries BOS, so prompts are tokenised with add_special_tokens=False (pilot rule);
  - how each answer string (A-D, Yes/No, digits 1-9, numbers) tokenises right after the generation prompt (with/without space);
  - parity across the OLMo-2 1B post-training ladder (SFT, DPO, instruct): template hash and rendered prompt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEM = "You are taking part in a short study. Answer the question as yourself."
USER = "Which program would you choose?\n\nAnswer with only the program letter."
ANSWERS = ["A", "B", "C", "D", "Yes", "No", "yes", "no"] + [str(i) for i in range(1, 10)] + ["10", "250", "1500", "2500", "6000"]


def cont_ids(tok, rendered, s):
    """Token ids added by appending s to the rendered prompt, or None if the prompt's own tokens change (merge)."""
    a = tok(rendered, add_special_tokens=False)["input_ids"]
    b = tok(rendered + s, add_special_tokens=False)["input_ids"]
    if b[: len(a)] != a:
        return None
    return b[len(a):]


def check(name, m):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(ROOT / m["path"])
    tmpl = tok.chat_template or ""
    rec = dict(model=name, template_sha256_16=hashlib.sha256(tmpl.encode()).hexdigest()[:16], bos=tok.bos_token, eos=tok.eos_token,
               pad=tok.pad_token, vocab=len(tok))
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]
    try:
        r = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        rec["system_role"] = "ok"
    except Exception as e:  # template refuses a system turn
        rec["system_role"] = f"error: {type(e).__name__}: {str(e)[:160]}"
        r = tok.apply_chat_template([{"role": "user", "content": SYSTEM + "\n\n" + USER}], add_generation_prompt=True, tokenize=False)
    rec["system_text_present"] = SYSTEM in r
    rec["system_before_user"] = r.find(SYSTEM) < r.find(USER) if SYSTEM in r else None
    rec["rendered"] = r
    rec["rendered_sha256_16"] = hashlib.sha256(r.encode()).hexdigest()[:16]
    ids = tok(r, add_special_tokens=False)["input_ids"]
    ids_sp = tok(r)["input_ids"]
    rec["starts_with_bos"] = bool(tok.bos_token_id is not None and ids and ids[0] == tok.bos_token_id)
    rec["double_bos_if_add_special"] = bool(tok.bos_token_id is not None and len(ids_sp) > 1 and ids_sp[0] == ids_sp[1] == tok.bos_token_id)
    rec["n_prompt_tokens"] = len(ids)
    rec["tail"] = r[-60:]
    toks = {}
    for s in ANSWERS:
        for pre in ("", " "):
            c = cont_ids(tok, r, pre + s)
            toks[repr(pre + s)] = None if c is None else dict(ids=c, pieces=tok.convert_ids_to_tokens(c))
    rec["answer_tokens"] = toks
    single = lambda s: (toks[repr(s)] is not None and len(toks[repr(s)]["ids"]) == 1)
    rec["single_token"] = {k: single(k) for k in ["A", "B", "C", "D", "Yes", "No"] + [str(i) for i in range(1, 10)]}
    rec["single_token_space"] = {k: single(" " + k) for k in ["A", "B", "C", "D", "Yes", "No"] + [str(i) for i in range(1, 10)]}
    rec["digits_split_individually"] = all(toks[repr(n)] is not None and len(toks[repr(n)]["ids"]) == len(n) for n in ["250", "1500", "6000"])
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/acme-smoke")
    a = ap.parse_args()
    roster = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf8"))["models"]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    recs = [check(n, m) for n, m in roster.items()]
    by = {r["model"]: r for r in recs}
    ladder = ["olmo2-1b-sft", "olmo2-1b-dpo", "olmo2-1b-instruct"]
    parity = dict(models=ladder, template_hashes={k: by[k]["template_sha256_16"] for k in ladder},
                  rendered_hashes={k: by[k]["rendered_sha256_16"] for k in ladder},
                  rendered_identical=len({by[k]["rendered"] for k in ladder}) == 1,
                  answer_tokens_identical=len({json.dumps(by[k]["answer_tokens"], sort_keys=True) for k in ladder}) == 1,
                  vocab_identical=len({by[k]["vocab"] for k in ladder}) == 1)
    (out / "templates.json").write_text(json.dumps(dict(models=recs, olmo_ladder_parity=parity), indent=1, ensure_ascii=False), encoding="utf8")
    lines = ["| model | system role | system text kept | BOS in render | double BOS if add_special | A-D,Yes/No,1-9 single (no space) | same with space | digits split | prompt tokens |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in recs:
        st, sp = r["single_token"], r["single_token_space"]
        lines.append(f'| {r["model"]} | {r["system_role"][:40]} | {r["system_text_present"]} | {r["starts_with_bos"]} | {r["double_bos_if_add_special"]} | '
                     f'{sum(st.values())}/{len(st)} | {sum(sp.values())}/{len(sp)} | {r["digits_split_individually"]} | {r["n_prompt_tokens"]} |')
    lines += ["", "OLMo-2 1B ladder parity: " + json.dumps(parity)]
    for r in recs:
        lines += ["", f'### {r["model"]}', "```", r["rendered"], "```"]
    (out / "templates.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines[: len(recs) + 4]))


if __name__ == "__main__":
    main()
