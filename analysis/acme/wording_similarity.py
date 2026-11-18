"""Cosine similarity of every wording (W1-W9, decoys D1-D2) to W0 of the same item, field by field and for the pooled text (field ALL).

    .venv/Scripts/python.exe -I analysis/acme/wording_similarity.py

Model: BAAI/bge-small-en-v1.5 from models/hf-cache, CPU, offline (no download). Writes runs/acme-wordings/similarity.csv with columns
item, wording, field, cosine, and runs/acme-wordings/similarity_summary.json (min, median, max of ALL per item for the
paraphrases W1-W9 and for the decoys).
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_wordings as C  # noqa: E402

ROOT = C.ROOT
OUT = ROOT / "runs/acme-wordings"


def pooled(item, d):
    return " ".join(C.fields(item, d).values())


def main():
    import torch
    torch.set_num_threads(2)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu", cache_folder=str(ROOT / "models/hf-cache"))
    rows, texts = [], []   # texts: (item, wording, field, text_w, text_w0)
    for item in C.ITEMS:
        base = C.load(item, "W0")
        fb = C.fields(item, base)
        targets = [(w, C.load(item, w)) for w in C.WORDINGS if w != "W0"] + [(f"D{k}", C.load_decoy(item, k)) for k in (1, 2)]
        for w, d in targets:
            fw = C.fields(item, d)
            for name in fb:
                if name in fw:
                    texts.append((item, w, name, fw[name], fb[name]))
            texts.append((item, w, "ALL", pooled(item, d), pooled(item, base)))
    uniq = sorted({t for r in texts for t in (r[3], r[4])})
    emb = model.encode(uniq, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    idx = {t: i for i, t in enumerate(uniq)}
    for item, w, name, a, b in texts:
        cos = float(emb[idx[a]] @ emb[idx[b]])
        rows.append((item, w, name, round(cos, 4)))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "similarity.csv").open("w", newline="", encoding="utf8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["item", "wording", "field", "cosine"])
        wr.writerows(rows)
    summ = {}
    for item in C.ITEMS:
        for kind, sel in (("paraphrases_W1_W9", lambda w: w.startswith("W")), ("decoys", lambda w: w.startswith("D"))):
            v = [c for i, w, f, c in rows if i == item and f == "ALL" and sel(w)]
            summ.setdefault(item, {})[kind] = {"n": len(v), "min": min(v), "median": round(statistics.median(v), 4), "max": max(v)}
    (OUT / "similarity_summary.json").write_text(json.dumps({"model": "BAAI/bge-small-en-v1.5", "device": "cpu", "per_item": summ}, indent=1),
                                                 encoding="utf8")
    for item, s in summ.items():
        print(item, s["paraphrases_W1_W9"], s["decoys"])


if __name__ == "__main__":
    main()
