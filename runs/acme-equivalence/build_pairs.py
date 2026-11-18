"""Build blinded pair texts for the meaning-equivalence check. Reads frozen wording files only (read-only).
Outputs: pairs.jsonl (id, A, B: participant-facing text, no labels), key.json (id -> item, wording, kind) kept apart."""
import json, random, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/acme"))
import prompts_acme as pa

OUT = Path(__file__).resolve().parent
common = pa.load_common()

def render(item, W, variant="main"):
    """Participant-facing text of one wording: every condition (and reversed scale / baseline where the file has them)."""
    parts = []
    def one(label, **kw):
        p = pa.build(item, W, kw.pop("x"), kw.pop("O"), variant, common=common, **kw)
        txt = "\n\n[next turn, after the participant's reply]\n".join(t for r, t in p["turns"] if r == "user")
        parts.append(f"--- {label} ---\n{txt}")
    O = {"P1": ("sure_first", None), "P3": ("forward", "reversed"), "QA": ("forward", "reversed"),
         "AF": ("yes_first", None), "NR": ("yes_first", None)}.get(item, (None, None))
    d = pa.load_wording(item, W, variant)
    names = {1: "condition 1", 0: "condition 2"}
    if item == "NR":
        names = {1: "version 1 (two questions asked in this order)", 0: "version 2 (this question asked alone)"}
    for x in (1, 0):
        one(names[x], x=x, O=O[0])
    if O[1]:
        one("condition 1 with the reversed rating scale", x=1, O=O[1])
    if item.startswith("P2") and "baseline" in d:
        one("no-anchor version", x=1, O=None, baseline=True)
    fl = pa.fmt_line(common, pa.READOUT[item], "F0", O[0])
    body = "\n\n".join(parts).replace("\n\n" + fl, "")
    return body + f"\n\n[Identical answer-format instruction appended to every version above: \"{fl}\"]"

pairs = []
for it in pa.ITEMS:
    w0 = render(it, "W0")
    for k in range(1, 10):
        pairs.append((it, f"W{k}", "paraphrase", w0, render(it, f"W{k}")))
    for v in ("D1", "D2"):
        pairs.append((it, v, "decoy", w0, render(it, "W0", variant=v)))
rng = random.Random(20261106)
rng.shuffle(pairs)
rows, key = [], {}
for i, (it, w, kind, a, b) in enumerate(pairs, 1):
    pid = f"E{i:03d}"
    if rng.random() < 0.5:
        a, b, side = b, a, "W0_is_B"
    else:
        side = "W0_is_A"
    rows.append({"id": pid, "A": a, "B": b})
    key[pid] = {"item": it, "wording": w, "kind": kind, "side": side}
(OUT / "pairs.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf8")
(OUT / "key.json").write_text(json.dumps(key, indent=1), encoding="utf8")
print(len(rows), "pairs")
