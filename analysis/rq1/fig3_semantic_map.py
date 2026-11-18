"""Figure 3: semantic map of the liberal frame (2,022 records), protocol section 9.

    .venv/Scripts/python.exe -I analysis/rq1/fig3_semantic_map.py [--smoke] [--n-boot 50]

Pipeline (all parameters fixed before the run; seed 20261016):
  1. text = title + ". " + abstract (abstracts.jsonl, else records.jsonl; title only if no abstract exists);
     BAAI/bge-small-en-v1.5 via sentence-transformers on CPU, normalised, cached as embeddings.npy.
  2. UMAP 5-D (cosine, n_neighbors 15, min_dist 0) for clustering; UMAP 2-D (cosine, n_neighbors 15, min_dist 0.1) for display.
  3. HDBSCAN (sklearn, euclidean on the 5-D map, min_cluster_size 25, min_samples 10, 'eom'); label -1 = unclustered.
  4. Stability: B bootstrap resamples of records (with replacement); duplicates dropped, so each refit uses the ~63 % unique
     records; UMAP 5-D + HDBSCAN refit with the same parameters; adjusted Rand index (ARI) against the full-sample labels
     on the records in the resample. Primary ARI treats unclustered (-1) as one label; secondary ARI keeps only records
     clustered in both solutions. Median and IQR reported.
  5. Cluster labels: top c-TF-IDF terms per cluster (no LLM labelling).
CPU only (CUDA_VISIBLE_DEVICES is blanked before torch is imported).
Outputs: runs/rq1-semantic-map/{config.json, fig3_semantic_map.log, embeddings.npy, ids.json, umap2d.npy, clusters.csv,
         assignments.csv, stability.json, sensitivity.json}; paper/figures/Fig3.{pdf,eps,png}
"""
from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU only: the GPU is shared and has crashed the laptop

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import warnings

import numpy as np

warnings.filterwarnings("ignore", message="n_jobs value 1 overridden")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_common as C  # noqa: E402

MODEL = "BAAI/bge-small-en-v1.5"
PARAMS = {"umap5": dict(n_components=5, n_neighbors=15, min_dist=0.0, metric="cosine"),
          "umap2": dict(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine"),
          "hdbscan": dict(min_cluster_size=25, min_samples=10, cluster_selection_method="eom"),
          "n_boot": 50, "tfidf_top_terms": 6, "max_seq_length": 512}
SENS = [(15, 5), (25, 10), (40, 10)]  # (min_cluster_size, min_samples) sensitivity on the full-sample 5-D map

# family colours and markers (Okabe-Ito; marker shape is the second cue)
FAM_STYLE = {
    "LANG": (C.OI["blue"], "o"), "JDM": (C.OI["orange"], "s"), "TOM": (C.OI["green"], "^"), "OTH": (C.OI["purple"], "D"),
    "RE": (C.OI["sky"], "v"), "HB": (C.OI["verm"], "P"), "MOR": (C.OI["yellow"], "X"), "LEARN": (C.OI["blue"], "*"),
    "MEM": (C.OI["orange"], "<"), "DEV": (C.OI["green"], ">"), "NUM": (C.OI["purple"], "h"), "none": ("#8C8C8C", "."),
}
FAM_ORDER = ["LANG", "JDM", "TOM", "OTH", "RE", "HB", "MOR", "LEARN", "MEM", "DEV", "NUM", "none"]
# categorical colours for clusters (Okabe-Ito then darker/lighter variants); numbers on the map are the non-colour cue
CL_COLS = [C.OI["blue"], C.OI["orange"], C.OI["green"], C.OI["verm"], C.OI["purple"], C.OI["sky"], "#B8A800", "#6B6B6B",
           "#004F7A", "#9A6700", "#006B4F", "#8C3A00", "#8E4A72", "#2E86AB", "#E0C500", "#3A3A3A", "#7FB3D5", "#F5B041", "#58D68D", "#E59866"]


def get_texts(rows, ids):
    ab = {}
    want = set(ids)
    for d in C.read_jsonl(C.P / "abstracts.jsonl"):
        if d["id"] in want and d.get("abstract"):
            ab[d["id"]] = d["abstract"]
    texts, src = [], Counter()
    for i in ids:
        a = ab.get(i) or rows[i].get("rec_abstract") or ""
        src["abstracts.jsonl" if i in ab else ("records.jsonl" if a else "title_only")] += 1
        texts.append((rows[i]["title"].strip() + ". " + a.strip()).strip())
    return texts, dict(src)


def embed(texts, log, cache_dir):
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    model = SentenceTransformer(MODEL, device="cpu", cache_folder=str(cache_dir))
    model.max_seq_length = PARAMS["max_seq_length"]
    emb = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
    log.info("embedded %d texts, dim %d, %.1f s", len(texts), emb.shape[1], time.time() - t0)
    rev = None
    try:
        rev = Path(model._first_module().auto_model.config._name_or_path).name
        from huggingface_hub import snapshot_download
        rev = Path(snapshot_download(MODEL, cache_dir=str(cache_dir), local_files_only=True)).name
    except Exception as e:  # noqa: BLE001
        log.info("revision lookup failed: %s", e)
    return emb.astype(np.float32), rev


def umap_fit(emb, p, seed):
    import umap
    q = dict(p)
    q["n_neighbors"] = min(q["n_neighbors"], max(2, len(emb) - 1))
    return umap.UMAP(random_state=seed, **q).fit_transform(emb)


def hdb(X, mcs, ms):
    from sklearn.cluster import HDBSCAN
    return HDBSCAN(min_cluster_size=mcs, min_samples=ms, cluster_selection_method="eom", copy=True).fit_predict(X)


def ctfidf(texts, labels, top):
    from sklearn.feature_extraction.text import CountVectorizer
    ks = sorted(k for k in set(labels) if k >= 0)
    docs = [" ".join(t for t, l in zip(texts, labels) if l == k) for k in ks]
    cv = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=3, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+(?:-[a-zA-Z]+)*\b")
    X = cv.fit_transform(docs).toarray().astype(float)
    tf = X / X.sum(1, keepdims=True)
    A = X.sum() / len(ks)
    idf = np.log(1 + A / X.sum(0))
    S = tf * idf
    vocab = np.array(cv.get_feature_names_out())
    out = {}
    for r, k in enumerate(ks):
        chosen, words = [], set()
        for j in np.argsort(-S[r]):
            term = vocab[j]
            w = set(term.split())
            if w & words:
                continue
            chosen.append(term)
            words |= w
            if len(chosen) == top:
                break
        out[k] = chosen
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n-boot", type=int, default=PARAMS["n_boot"])
    a = ap.parse_args()
    run = C.ROOT / ("runs/rq1-semantic-map-smoke" if a.smoke else "runs/rq1-semantic-map")
    log = C.setup_run(run, "fig3_semantic_map")
    rows, views, manifest = C.load_frame()
    ids = list(views["A"])
    rng = np.random.default_rng(C.SEED)
    P5, P2, PH = dict(PARAMS["umap5"]), dict(PARAMS["umap2"]), dict(PARAMS["hdbscan"])
    n_boot = a.n_boot
    if a.smoke:
        ids = sorted(rng.choice(ids, size=max(20, round(0.01 * len(ids))), replace=False).tolist())
        PH.update(min_cluster_size=3, min_samples=2)
        P5["n_components"] = 3
        n_boot = 3
        log.info("SMOKE: %d records, scaled HDBSCAN, 3 bootstraps", len(ids))
    log.info("n records %d; params %s", len(ids), json.dumps({"umap5": P5, "umap2": P2, "hdbscan": PH, "n_boot": n_boot}))
    texts, src = get_texts(rows, ids)
    log.info("text sources %s", src)

    cache = C.ROOT / "models/hf-cache"
    snaps = sorted((cache / "models--BAAI--bge-small-en-v1.5/snapshots").glob("*")) if (cache / "models--BAAI--bge-small-en-v1.5/snapshots").exists() else []
    rev = snaps[-1].name if snaps else None
    emb_path = run / "embeddings.npy"
    if emb_path.exists() and json.loads((run / "ids.json").read_text()) == ids:
        emb = np.load(emb_path)
        log.info("loaded cached embeddings %s", emb.shape)
    else:
        emb, rev2 = embed(texts, log, cache)
        rev = rev2 or rev
        np.save(emb_path, emb)
        (run / "ids.json").write_text(json.dumps(ids), encoding="utf-8")

    t0 = time.time()
    X5 = umap_fit(emb, P5, C.SEED)
    X2 = umap_fit(emb, P2, C.SEED)
    np.save(run / "umap2d.npy", X2)
    log.info("UMAP 5-D and 2-D fitted, %.1f s", time.time() - t0)
    labels = hdb(X5, PH["min_cluster_size"], PH["min_samples"])
    ks = sorted(k for k in set(labels) if k >= 0)
    n_noise = int((labels == -1).sum())
    log.info("HDBSCAN: %d clusters, %d unclustered (%.1f%%)", len(ks), n_noise, 100 * n_noise / len(ids))

    # sensitivity of the cluster solution to HDBSCAN settings (same 5-D map)
    from sklearn.metrics import adjusted_rand_score as ari
    sens = []
    for mcs, ms in ([] if a.smoke else SENS):
        l2 = hdb(X5, mcs, ms)
        sens.append({"min_cluster_size": mcs, "min_samples": ms, "n_clusters": int(len(set(l2) - {-1})), "n_unclustered": int((l2 == -1).sum()),
                     "ARI_vs_main_noise_as_label": round(float(ari(labels, l2)), 4)})
        log.info("sensitivity %s", sens[-1])
    (run / "sensitivity.json").write_text(json.dumps(sens, indent=1), encoding="utf-8")

    # bootstrap stability
    aris, aris2, ncl, shared = [], [], [], []
    t0 = time.time()
    for b in range(n_boot):
        brng = np.random.default_rng(C.SEED + 1000 + b)
        idx = np.unique(brng.integers(0, len(ids), size=len(ids)))
        Xb = umap_fit(emb[idx], P5, C.SEED + 1000 + b)
        lb = hdb(Xb, PH["min_cluster_size"], PH["min_samples"])
        ref = labels[idx]
        aris.append(float(ari(ref, lb)))
        both = (ref >= 0) & (lb >= 0)
        aris2.append(float(ari(ref[both], lb[both])) if both.sum() > 1 and len(set(ref[both])) > 0 else float("nan"))
        ncl.append(int(len(set(lb) - {-1})))
        shared.append(int(len(idx)))
        log.info("boot %d/%d: unique %d, clusters %d, ARI %.3f, ARI(clustered in both) %.3f, %.0f s elapsed", b + 1, n_boot, len(idx), ncl[-1], aris[-1], aris2[-1], time.time() - t0)

    def q(x):
        x = np.array([v for v in x if v == v])
        return {"median": round(float(np.median(x)), 4), "q1": round(float(np.percentile(x, 25)), 4), "q3": round(float(np.percentile(x, 75)), 4),
                "min": round(float(x.min()), 4), "max": round(float(x.max()), 4), "n": int(len(x))}

    stab = {"n_boot": n_boot, "ARI_noise_as_label": q(aris), "ARI_clustered_in_both": q(aris2), "n_clusters_in_bootstrap": q(ncl),
            "unique_records_per_resample": q(shared), "n_clusters_full": len(ks), "n_unclustered_full": n_noise,
            "ARI_values": [round(v, 4) for v in aris], "ARI_clustered_in_both_values": [round(v, 4) if v == v else None for v in aris2]}
    (run / "stability.json").write_text(json.dumps(stab, indent=1), encoding="utf-8")
    log.info("stability %s", json.dumps({k: v for k, v in stab.items() if "values" not in k}))

    # cluster table
    terms = ctfidf(texts, labels, PARAMS["tfidf_top_terms"]) if ks else {}
    # renumber clusters 1..K by size (descending) for display
    order = sorted(ks, key=lambda k: -(labels == k).sum())
    ren = {k: i + 1 for i, k in enumerate(order)}
    disp = np.array([ren.get(l, 0) for l in labels])  # 0 = unclustered
    fam_first = np.array([C.first_family(rows[i]) for i in ids])
    flag = np.array([rows[i]["meets_criteria_on_abstract"] for i in ids])
    year = np.array([rows[i]["year"] for i in ids])
    ctab = []
    for k in order:
        m = labels == k
        fc = Counter(fam_first[m]).most_common(3)
        ctab.append({"cluster": ren[k], "n": int(m.sum()), "pct_of_frame": round(100 * m.sum() / len(ids), 1), "top_terms": "; ".join(terms[k]),
                     "dominant_first_families": "; ".join(f"{f} {n}" for f, n in fc), "flag_yes_share_pct": round(100 * float((flag[m] == "yes").mean()), 1),
                     "median_year": float(np.median(year[m]))})
    ctab.append({"cluster": 0, "n": n_noise, "pct_of_frame": round(100 * n_noise / len(ids), 1), "top_terms": "(unclustered)",
                 "dominant_first_families": "; ".join(f"{f} {n}" for f, n in Counter(fam_first[labels == -1]).most_common(3)),
                 "flag_yes_share_pct": round(100 * float((flag[labels == -1] == "yes").mean()), 1) if n_noise else "", "median_year": float(np.median(year[labels == -1])) if n_noise else ""})
    with open(run / "clusters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ctab[0].keys()))
        w.writeheader()
        w.writerows(ctab)
    with open(run / "assignments.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "cluster", "umap2_x", "umap2_y", "first_family", "flag", "year"])
        for j, i in enumerate(ids):
            w.writerow([i, int(disp[j]), round(float(X2[j, 0]), 4), round(float(X2[j, 1]), 4), fam_first[j], flag[j], int(year[j])])
    log.info("cluster table: %s", [(c["cluster"], c["n"], c["top_terms"]) for c in ctab])

    # figure
    if not a.smoke:
        make_figure(ids, X2, disp, fam_first, ctab, stab, len(ks), n_noise, log)
    inputs = C.code_files() + [C.P / "rq1/manifest.json", C.P / "screen/abstract-decisions-v08.jsonl", C.P / "records.jsonl", C.P / "abstracts.jsonl",
                               Path(__file__).resolve(), Path(__file__).resolve().parent / "rq1_common.py"]
    C.write_config(run, "analysis/rq1/fig3_semantic_map.py" + (" --smoke" if a.smoke else ""), inputs,
                   {"model": MODEL, "model_revision": rev, "device": "cpu", "n_records": len(ids), "text_sources": src, **{k: v for k, v in PARAMS.items() if k not in ("umap5", "hdbscan")},
                    "umap5": P5, "hdbscan": PH, "n_boot": n_boot},
                   {"packages": C.pkg_versions(["sentence-transformers", "umap-learn", "scikit-learn", "numpy", "torch", "transformers", "matplotlib", "numba"])})


def make_figure(ids, X2, disp, fam_first, ctab, stab, K, n_noise, log):
    C.mpl_setup()
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    import matplotlib.patheffects as pe

    n_rows_key = (K + 2) // 2          # K cluster lines + one 'unclustered' line, two columns
    h_key = 4.4 * n_rows_key + 3
    H = h_key + 11 + 84
    fig = plt.figure(figsize=(C.W2, H * C.MM))
    ax1 = fig.add_axes([0.042, (h_key + 11) / H, 0.445, 80 / H])
    ax2 = fig.add_axes([0.545, (h_key + 11) / H, 0.445, 80 / H])
    for ax in (ax1, ax2):
        ax.set_xticks([])
        ax.set_yticks([])
        for s_ in ax.spines.values():
            s_.set_linewidth(0.6)
        ax.set_xlim(X2[:, 0].min() - 0.5, X2[:, 0].max() + 0.5)
        ax.set_ylim(X2[:, 1].min() - 0.5, X2[:, 1].max() + 0.5)
        ax.set_xlabel("UMAP 1", labelpad=1)
        ax.set_ylabel("UMAP 2", labelpad=1)
    # (a) clusters
    m0 = disp == 0
    ax1.scatter(X2[m0, 0], X2[m0, 1], s=3.0, c="#C8C8C8", marker=".", linewidths=0, zorder=1)
    for k in range(1, K + 1):
        m = disp == k
        ax1.scatter(X2[m, 0], X2[m, 1], s=4.0, c=CL_COLS[(k - 1) % len(CL_COLS)], marker="o", linewidths=0, zorder=2)
    for k in range(1, K + 1):
        m = disp == k
        cx, cy = np.median(X2[m, 0]), np.median(X2[m, 1])
        ax1.text(cx, cy, str(k), ha="center", va="center", fontsize=7.5, fontweight="bold", color="#000000", zorder=5,
                 path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])
    # (b) families
    for fam in FAM_ORDER[::-1]:
        m = fam_first == fam
        if not m.any():
            continue
        col, mk = FAM_STYLE[fam]
        ax2.scatter(X2[m, 0], X2[m, 1], s=(9 if mk in "*P" else 5.5), c=col, marker=mk, linewidths=0.15, edgecolors=("#222222" if mk != "." else "none"), zorder=2)
    handles = [Line2D([], [], marker=FAM_STYLE[f][1], color="none", markerfacecolor=FAM_STYLE[f][0], markeredgecolor="#222222", markeredgewidth=0.3, markersize=5.2,
                      label=("none named" if f == "none" else f)) for f in FAM_ORDER]
    fig.legend(handles=handles, loc="lower right", ncol=12, frameon=False, handletextpad=0.1, columnspacing=0.9, fontsize=6.5,
               bbox_to_anchor=(0.995, (h_key + 2.2) / H), borderaxespad=0)
    fig.text(0.012, (h_key + 4.6) / H, "Family (b):", fontsize=6.5, ha="left", va="center")
    for ax, t in ((ax1, "a"), (ax2, "b")):
        ax.text(0.0, 1.015, t, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="bottom")
    # cluster key (two columns of text under the panels)
    kx = [0.012, 0.52]
    y0 = (h_key - 0.8) / H
    dy = 4.4 / H
    keyrows = [c for c in ctab if c["cluster"] > 0]
    for j, c in enumerate(keyrows):
        col, row = j // n_rows_key, j % n_rows_key
        yy = y0 - row * dy
        fig.text(kx[col], yy, f"{c['cluster']}", fontsize=6.8, fontweight="bold", ha="left", va="top")
        fig.text(kx[col] + 0.018, yy, f"{c['top_terms']}  (n = {c['n']})", fontsize=6.5, ha="left", va="top")
    j = len(keyrows)
    col, row = j // n_rows_key, j % n_rows_key
    yy = y0 - row * dy
    fig.text(kx[col] + 0.002, yy, "•", fontsize=9, color="#A8A8A8", ha="left", va="top")
    fig.text(kx[col] + 0.018, yy, f"unclustered, grey in panel a  (n = {n_noise})", fontsize=6.5, ha="left", va="top")
    C.save_fig(fig, C.ROOT / "paper/figures/Fig3")
    plt.close(fig)
    log.info("saved paper/figures/Fig3.{pdf,eps,png}")


if __name__ == "__main__":
    main()
