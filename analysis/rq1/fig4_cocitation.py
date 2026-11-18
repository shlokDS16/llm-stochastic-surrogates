"""Figure 4: co-citation network of the most co-cited references of the liberal frame (protocol section 9).

    .venv/Scripts/python.exe -I analysis/rq1/fig4_cocitation.py [--no-fetch]

Method (all parameters in the run config):
  * Frame = liberal eligible records (abstract-decisions-v08), N = 2022. OpenAlex records get `referenced_works`
    (analysis/rq1/fig4_fetch_refs.py, cached in data/processed/references/frame-refs.jsonl; the fetch is resumable and is
    a no-op when the cache is complete). arXiv-only records (no OpenAlex ID) and OpenAlex records whose reference list is
    empty are NOT COVERED; coverage is reported overall and by year.
  * Duplicate records of one work are merged BEFORE nodes are chosen. Pool = references cited by at least POOL_MIN (4)
    covered records. Rule: two pool references are one work if their normalised titles match (lowercase, punctuation
    stripped; titles of 4 or more words that are not proceedings or series names; after the metadata corrections below, so an arXiv preprint and its published
    version merge) and, where both first authors are known, the surnames agree (groups failing the guard are listed, not
    merged). The merged node's citing set is the UNION of the members' citing records (a record citing both versions counts
    once). The canonical member is the one with most citing records (ties: smaller OpenAlex ID); every merge is listed in
    metrics.json. A work whose records all fall below POOL_MIN cannot be detected.
  * Nodes = merged references cited by at least K of the covered frame records, K = merged citation count of the 150th
    ranked reference (all ties at K are kept, so the node set is the top 150 plus ties). Citation count = number of covered
    frame records citing the work (each record counted once).
  * Edges = pairs of nodes cited together by at least EDGE_MIN covered frame records (co-citation count = edge weight).
    Nodes with no edge are dropped from the graph and listed in metrics.json.
  * Clusters = Louvain (networkx.community.louvain_communities, weight = co-citation count, resolution 1, seed 20261016);
    modularity reported; stability over 20 other seeds (modularity range, adjusted Rand index against the main partition).
  * Cluster label = the three most-cited member references as 'FirstAuthor Year'; no LLM labelling. Reference metadata comes
    from OpenAlex, except for records with the DOI-conflation signature (at least one Zenodo or Dagstuhl location; OpenAlex
    attaches wrong titles and DOIs to some well-known preprints). Those take title, first author and year from the arXiv API
    when the record has an arXiv location; otherwise they are 'unresolved': kept in the graph (their co-citation links are
    real) but never used in a cluster label.

Outputs: paper/figures/Fig4.{pdf,eps,png}; runs/rq1-cocitation/{config.json, fig4_cocitation.log, nodes.csv, edges.csv,
clusters.csv, coverage.csv, metrics.json}
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_common as C  # noqa: E402
import fig4_fetch_refs as F  # noqa: E402

RUN = C.ROOT / "runs/rq1-cocitation"
OUT = C.ROOT / "paper/figures/Fig4"
TOP_N = 150
EDGE_MIN = 5
DRAW_MIN = 5  # edges below this weight are not drawn (all graph edges are drawn at the current setting)
N_STABILITY_SEEDS = 20
POOL_MIN = 4  # references cited by at least this many covered records are fetched and checked for duplicates
HUB_W = 0.8  # layout-only gravity weight, on the sqrt scale used for the layout (graph edges have sqrt weight >= 2.2)


def surname(full: str | None) -> str:
    if not full:
        return "Unknown"
    if "," in full:  # 'Family, Given' form used by some OpenAlex records
        return full.split(",")[0].strip()
    parts = full.split()
    # OpenAlex display names are 'Given Family'; keep particles such as 'van', 'de' with the family name
    fam = [parts[-1]]
    i = len(parts) - 2
    while i >= 1 and parts[i].lower() in {"van", "von", "de", "der", "den", "da", "del", "di", "la", "le", "al"}:
        fam.insert(0, parts[i])
        i -= 1
    return " ".join(fam)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    log = C.setup_run(RUN, "fig4_cocitation")
    import networkx as nx
    from sklearn.metrics import adjusted_rand_score

    rows, views, manifest = C.load_frame(need_years=True)
    frame = views["A"]
    oa = [i for i in frame if i.startswith("https://openalex.org/")]
    log.info("frame N=%d; OpenAlex IDs %d; arXiv-only %d", len(frame), len(oa), len(frame) - len(oa))
    refs = F.fetch_refs(oa, log=log.info) if not a.no_fetch else F._cache(F.REFS)
    assert set(oa) <= set(refs), "reference cache incomplete; run without --no-fetch"

    # ---------- coverage ----------
    status = {}
    for i in frame:
        if not i.startswith("https://openalex.org/"):
            status[i] = "arxiv_only"
        elif not refs[i]["returned"]:
            status[i] = "openalex_not_returned"
        elif not refs[i]["referenced_works"]:
            status[i] = "openalex_no_references"
        else:
            status[i] = "covered"
    cov = Counter(status.values())
    covered = [i for i in frame if status[i] == "covered"]
    log.info("coverage: %s; covered share %.1f percent (%d of %d)", dict(cov), 100 * len(covered) / len(frame), len(covered), len(frame))
    by_year = defaultdict(Counter)
    for i in frame:
        by_year[rows[i]["year"]][status[i]] += 1
    with open(RUN / "coverage.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "frame_records", "covered", "openalex_no_references", "openalex_not_returned", "arxiv_only", "covered_share"])
        for y in sorted(by_year):
            c = by_year[y]
            n = sum(c.values())
            w.writerow([y, n, c["covered"], c["openalex_no_references"], c["openalex_not_returned"], c["arxiv_only"], round(c["covered"] / n, 3)])
        w.writerow(["all", len(frame), cov["covered"], cov["openalex_no_references"], cov["openalex_not_returned"], cov["arxiv_only"],
                    round(cov["covered"] / len(frame), 3)])
    log.info("coverage by year: %s", {y: f"{c['covered']}/{sum(c.values())}" for y, c in sorted(by_year.items())})

    # ---------- reference pool, metadata and merging of duplicate records of one work ----------
    cites_raw = Counter(w for i in covered for w in set(refs[i]["referenced_works"]))
    pool = sorted(w for w, c in cites_raw.items() if c >= POOL_MIN)
    log.info("distinct references %d; pool (cited by >= %d covered records) %d", len(cites_raw), POOL_MIN, len(pool))
    meta = F.fetch_meta(pool, log=log.info)
    suspect = {n for n in pool if meta[n].get("returned") and (meta[n].get("n_zenodo_loc", 0) or meta[n].get("n_dagstuhl_loc", 0))}
    arx = F.fetch_arxiv(sorted({meta[n]["arxiv_id"] for n in suspect if meta[n].get("arxiv_id")}), log=log.info)
    src, info = {}, {}
    for n in pool:
        m = meta[n]
        if n in suspect and m.get("arxiv_id") and arx.get(m["arxiv_id"], {}).get("title"):
            src[n], info[n] = "arxiv", arx[m["arxiv_id"]]
        elif n in suspect or not m.get("returned"):
            src[n], info[n] = "unresolved", {"first_author": None, "year": None, "title": None}
        else:
            src[n], info[n] = "openalex", m
    # merge rule: same normalised title (lowercase, punctuation stripped; after the arXiv corrections above) and, when both names
    # are known, the same first-author surname; titles of fewer than 4 words are never merged. Citing sets are united (a record
    # citing both versions counts once).
    groups = defaultdict(list)
    for n in pool:
        t = info[n].get("title")
        if src[n] != "unresolved" and t and len(C.norm_name(t).split()) >= 4:
            groups[C.norm_name(t)].append(n)
    citing = defaultdict(set)
    for i in covered:
        for w in set(refs[i]["referenced_works"]):
            citing[w].add(i)
    canon = {n: n for n in pool}
    merges, skipped = [], []
    for t, mem in sorted(groups.items()):
        if len(mem) < 2:
            continue
        sn = {surname(info[n]["first_author"]).casefold() for n in mem if info[n].get("first_author")}
        rec = {"normalised_title": t, "members": [{"id": n.rsplit("/", 1)[1], "year": info[n].get("year"), "n_citing": len(citing[n]),
                                                    "metadata_source": src[n]} for n in sorted(mem)]}
        if t.startswith(("advances in ", "proceedings of ")):  # a proceedings volume or series, not one work
            rec["skipped_reason"] = "title is a proceedings or series name"
            skipped.append(rec)
            continue
        if len(sn) > 1:
            rec["skipped_reason"] = f"first-author surnames differ: {sorted(sn)}"
            skipped.append(rec)
            continue
        head = sorted(mem, key=lambda n: (-len(citing[n]), n))[0]
        for n in mem:
            canon[n] = head
        union = set().union(*(citing[n] for n in mem))
        rec.update({"canonical": head.rsplit("/", 1)[1], "n_citing_sum": sum(len(citing[n]) for n in mem), "n_citing_union": len(union)})
        merges.append(rec)
        log.info("merge %s: members %s, citing sum %d -> union %d", t[:50], [m_["id"] for m_ in rec["members"]], rec["n_citing_sum"], len(union))
    merged_members = defaultdict(list)
    for n, h in canon.items():
        merged_members[h].append(n)
    cset = {h: set().union(*(citing[n] for n in mem)) for h, mem in merged_members.items()}
    cites = Counter({h: len(s) for h, s in cset.items()})
    log.info("merges made: %d groups (%d records merged away); skipped by author guard: %d", len(merges),
             sum(len(m_["members"]) - 1 for m_ in merges), len(skipped))

    # ---------- nodes and edges ----------
    ranked = sorted(cites.items(), key=lambda t: (-t[1], t[0]))
    K = ranked[TOP_N - 1][1]
    nodes = [w for w, c in ranked if c >= K]
    assert K >= POOL_MIN, "pool threshold below K: nodes could be missed"
    log.info("K (merged count of rank %d) = %d; nodes (ties kept) = %d", TOP_N, K, len(nodes))
    node_of = {m_: h for h in nodes for m_ in merged_members[h]}
    co = Counter()
    for i in covered:
        s = sorted({node_of[w] for w in refs[i]["referenced_works"] if w in node_of})
        for x, y in itertools.combinations(s, 2):
            co[(x, y)] += 1
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for (x, y), c in co.items():
        if c >= EDGE_MIN:
            G.add_edge(x, y, weight=c)
    isolated = [n for n in G if G.degree(n) == 0]
    G.remove_nodes_from(isolated)
    log.info("pairs with >=1 co-citation %d; edges with >=%d: %d; isolated nodes dropped %d; graph %d nodes, %d edges",
             len(co), EDGE_MIN, G.number_of_edges(), len(isolated), G.number_of_nodes(), G.number_of_edges())

    # ---------- clustering ----------
    comms = nx.community.louvain_communities(G, weight="weight", resolution=1, seed=C.SEED)
    Q = nx.community.modularity(G, comms, weight="weight")
    order = sorted(range(len(comms)), key=lambda k: (-sum(cites[n] for n in comms[k]), min(comms[k])))
    comms = [comms[k] for k in order]
    part = {n: k for k, cm in enumerate(comms) for n in cm}
    log.info("Louvain seed %d: %d clusters, modularity %.4f, sizes %s", C.SEED, len(comms), Q, [len(c) for c in comms])
    base = [part[n] for n in G.nodes]
    stab = []
    for s in range(1, N_STABILITY_SEEDS + 1):
        cs = nx.community.louvain_communities(G, weight="weight", resolution=1, seed=C.SEED + s)
        ps = {n: k for k, cm in enumerate(cs) for n in cm}
        stab.append({"seed": C.SEED + s, "n_clusters": len(cs), "modularity": nx.community.modularity(G, cs, weight="weight"),
                     "ari_vs_main": adjusted_rand_score(base, [ps[n] for n in G.nodes])})
    log.info("stability over %d seeds: modularity %.4f-%.4f, clusters %d-%d, ARI %.3f-%.3f (median %.3f)", N_STABILITY_SEEDS,
             min(s["modularity"] for s in stab), max(s["modularity"] for s in stab), min(s["n_clusters"] for s in stab),
             max(s["n_clusters"] for s in stab), min(s["ari_vs_main"] for s in stab), max(s["ari_vs_main"] for s in stab),
             sorted(s["ari_vs_main"] for s in stab)[len(stab) // 2])

    # ---------- labels of the final nodes ----------
    # year check: OpenAlex sometimes dates an old preprint with a much later DOI (e.g. 2025 for a 2017 paper). For nodes with an
    # arXiv location, fetch the arXiv first-version year; if OpenAlex is more than 3 years later, the label uses the arXiv year.
    arx_all = F.fetch_arxiv(sorted({meta[n]["arxiv_id"] for n in nodes if meta[n].get("arxiv_id")}), log=log.info)
    year_fix = {}
    for n in nodes:
        m = meta[n]
        ay = arx_all.get(m.get("arxiv_id") or "", {}).get("year")
        if src[n] == "openalex" and ay and m.get("year") and m["year"] - ay > 3:
            year_fix[n] = ay
            src[n] = "openalex_year_from_arxiv"
            info[n] = dict(m, year=ay)
            log.info("year fix %s: OpenAlex %s -> arXiv %s (%s)", n.rsplit("/", 1)[1], m["year"], ay, (m.get("title") or "")[:40])
    for n in nodes:
        if src[n] not in ("openalex", "openalex_year_from_arxiv"):
            log.info("metadata %s: %s [OpenAlex title %r] -> %s", n.rsplit("/", 1)[1], src[n], (meta[n].get("title") or "")[:50],
                     (info[n]["title"] or "")[:50])
    lab = {}
    for n in nodes:
        lab[n] = (f"{surname(info[n]['first_author'])} {info[n]['year'] or 'n.d.'}" if src[n] != "unresolved"
                  else f"unresolved {n.rsplit('/', 1)[1]}")
    dup = Counter(lab.values())
    seen = Counter()
    for n in sorted(nodes, key=lambda w: (-cites[w], w)):
        if dup[lab[n]] > 1:
            seen[lab[n]] += 1
            lab[n] = f"{lab[n]}{'abcdefghij'[seen[lab[n]] - 1]}"
    wdeg = dict(G.degree(weight="weight"))
    # duplicate-title groups left after merging (author guard or short titles), for the record
    left = defaultdict(list)
    for n in nodes:
        if src[n] != "unresolved" and info[n].get("title"):
            left[C.norm_name(info[n]["title"])].append(n)
    dup_groups = {k: [{"id": n.rsplit("/", 1)[1], "label": lab[n], "n_citing": cites[n]} for n in v] for k, v in left.items() if len(v) > 1}
    log.info("duplicate-title groups remaining among nodes: %d", len(dup_groups))

    # ---------- layout (fixed seed) ----------
    # a weak gravity hub keeps small disconnected components from drifting off the page; the hub is removed afterwards
    H = nx.Graph()
    H.add_weighted_edges_from((x, y, d["weight"] ** 0.5) for x, y, d in G.edges(data=True))
    H.add_edges_from(("__hub__", n, {"weight": HUB_W}) for n in G.nodes)
    pos = nx.spring_layout(H, weight="weight", seed=C.SEED, k=1.0 / (G.number_of_nodes() ** 0.5), iterations=500)
    pos.pop("__hub__")

    # ---------- tables ----------
    with open(RUN / "nodes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["openalex_id", "label", "metadata_source", "first_author", "year", "title", "openalex_title", "n_frame_records_citing", "cluster", "degree",
                    "weighted_degree", "x", "y", "in_graph", "merged_records"])
        for n in sorted(nodes, key=lambda x: (-cites[x], x)):
            m = meta[n]
            ing = n in G
            w.writerow([n, lab[n], src[n], info[n]["first_author"], info[n]["year"], info[n]["title"], m.get("title"), cites[n], (part[n] + 1) if ing else "",
                        G.degree(n) if ing else 0, wdeg.get(n, 0), round(float(pos[n][0]), 4) if ing else "",
                        round(float(pos[n][1]), 4) if ing else "", int(ing),
                        " ".join(m_.rsplit("/", 1)[1] for m_ in sorted(merged_members[n]) if m_ != n)])
    with open(RUN / "edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "source_label", "target_label", "cocitation_count", "same_cluster"])
        for x, y, d in sorted(G.edges(data=True), key=lambda e: (-e[2]["weight"], e[0], e[1])):
            w.writerow([x, y, lab[x], lab[y], d["weight"], int(part[x] == part[y])])
    ctab = []
    for k, cm in enumerate(comms):
        top3 = [n for n in sorted(cm, key=lambda n: (-cites[n], n)) if src[n] != "unresolved"][:3]
        inside = sum(d["weight"] for x, y, d in G.edges(data=True) if part[x] == k and part[y] == k)
        ctab.append({"cluster": k + 1, "n_nodes": len(cm), "n_internal_edges": sum(1 for x, y in G.edges if part[x] == k and part[y] == k),
                     "internal_cocitation_weight": inside, "total_citations_of_members": sum(cites[n] for n in cm),
                     "label_top3": "; ".join(lab[n] for n in top3), "top3_ids": " ".join(top3)})
    with open(RUN / "clusters.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ctab[0]))
        w.writeheader()
        w.writerows(ctab)
    for r in ctab:
        log.info("cluster %d: %d nodes, citations %d: %s", r["cluster"], r["n_nodes"], r["total_citations_of_members"], r["label_top3"])

    metrics = {
        "search_date": C.SEARCH_DATE, "frame_N": len(frame), "coverage": dict(cov), "covered_records": len(covered),
        "covered_share": round(len(covered) / len(frame), 4), "distinct_references": len(cites), "top_n": TOP_N, "K_min_citing_records": K,
        "n_nodes_selected": len(nodes), "edge_min_cocitation": EDGE_MIN, "draw_min_cocitation": DRAW_MIN, "n_nodes_in_graph": G.number_of_nodes(), "n_edges": G.number_of_edges(),
        "isolated_nodes_dropped": len(isolated), "louvain_seed": C.SEED, "n_clusters": len(comms), "modularity": round(Q, 4),
        "cluster_sizes": [len(c) for c in comms], "stability": {
            "n_seeds": N_STABILITY_SEEDS, "modularity_min": round(min(s["modularity"] for s in stab), 4),
            "modularity_max": round(max(s["modularity"] for s in stab), 4), "n_clusters_min": min(s["n_clusters"] for s in stab),
            "n_clusters_max": max(s["n_clusters"] for s in stab), "ari_min": round(min(s["ari_vs_main"] for s in stab), 3),
            "ari_median": round(sorted(s["ari_vs_main"] for s in stab)[len(stab) // 2], 3), "ari_max": round(max(s["ari_vs_main"] for s in stab), 3)},
        "metadata_source_counts": dict(Counter(src.values())),
        "merges": merges, "merge_groups_skipped_by_guard": skipped, "duplicate_title_groups_remaining": dup_groups,
        "pool_min": POOL_MIN, "pool_size": len(pool),
        "metadata_replaced_or_unresolved": {n.rsplit("/", 1)[1]: {"source": src[n], "openalex_title": meta[n].get("title"),
                                                                  "label": lab[n], "n_frame_records_citing": cites[n]}
                                            for n in nodes if src[n] != "openalex"},
        "year_fixed_from_arxiv": {n.rsplit("/", 1)[1]: year_fix[n] for n in year_fix},
    }
    (RUN / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")

    # ---------- figure ----------
    C.mpl_setup()
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    from matplotlib.lines import Line2D

    style = [(C.OI["blue"], "o"), (C.OI["verm"], "s"), (C.OI["green"], "^"), (C.OI["orange"], "D"), (C.OI["purple"], "v"),
             (C.OI["sky"], "P"), (C.OI["yellow"], "X"), ("#999999", "h")]
    assert len(comms) <= len(style), f"{len(comms)} clusters exceed the style list"
    ncl = len(comms)
    legend_rows = (ncl + 1) // 2
    fig_h = 104 + 6.0 * legend_rows
    fig = plt.figure(figsize=(C.W2, fig_h * C.MM))
    ax_h = 100 / fig_h
    ax = fig.add_axes([0.01, 1 - 1 / fig_h - ax_h, 0.98, ax_h])
    ax.set_axis_off()
    # rescale the layout to the unit square so the drawing uses the full panel
    x0, x1 = min(p[0] for p in pos.values()), max(p[0] for p in pos.values())
    y0, y1 = min(p[1] for p in pos.values()), max(p[1] for p in pos.values())
    P = {n: ((p[0] - x0) / (x1 - x0), (p[1] - y0) / (y1 - y0)) for n, p in pos.items()}
    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(-0.05, 1.05)
    drawn = [(x, y, d) for x, y, d in G.edges(data=True) if d["weight"] >= DRAW_MIN]
    wmax = max(d["weight"] for _, _, d in drawn)
    for x, y, d in sorted(drawn, key=lambda e: e[2]["weight"]):
        same = part[x] == part[y]
        t = d["weight"] / wmax
        ax.plot([P[x][0], P[y][0]], [P[x][1], P[y][1]], color="#444444" if same else "#8A8A8A", lw=0.2 + 1.2 * t,
                alpha=0.18 + 0.55 * t, zorder=1, solid_capstyle="round")
    log.info("edges drawn (weight >= %d): %d of %d", DRAW_MIN, len(drawn), G.number_of_edges())
    cmax = max(cites[n] for n in G)
    for k, cm in enumerate(comms):
        col, mk = style[k]
        ns = sorted(cm)
        ax.scatter([P[n][0] for n in ns], [P[n][1] for n in ns], s=[7 + 60 * cites[n] / cmax for n in ns], c=col, marker=mk,
                   edgecolors="#111111", linewidths=0.4, zorder=3)
    # in-figure labels: the three most-cited resolved references of each cluster; greedy placement against label boxes
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    to_disp = ax.transData.transform
    node_px = {n: to_disp(P[n]) for n in G}
    axbox = ax.get_window_extent()
    boxes = []
    unit = fig.dpi / 72.0

    def overlap(b1, b2, m=1.5):
        return not (b1[2] + m < b2[0] or b2[2] + m < b1[0] or b1[3] + m < b2[1] or b2[3] + m < b1[1])

    targets = []
    for k, cm in enumerate(comms):
        targets += [n for n in sorted(cm, key=lambda n: (-cites[n], n)) if src[n] != "unresolved"][:3]
    marker_boxes = [(node_px[n][0] - 5 * unit, node_px[n][1] - 5 * unit, node_px[n][0] + 5 * unit, node_px[n][1] + 5 * unit) for n in G]
    for n in sorted(targets, key=lambda n: -cites[n]):
        t = ax.text(0, 0, lab[n], fontsize=6.3, color="#111111", zorder=5, path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])
        bb = t.get_window_extent(rend)
        w_, h_ = bb.width, bb.height
        best = None
        px, py = node_px[n]
        for r in (6, 11, 17, 24, 32, 42):
            for ang in (0, 180, 90, 270, 45, 135, 225, 315):
                import math
                dx, dy = r * unit * math.cos(math.radians(ang)), r * unit * math.sin(math.radians(ang))
                cx, cy = px + dx, py + dy
                ha = "left" if dx > 1 else ("right" if dx < -1 else "center")
                x_lo = cx if ha == "left" else (cx - w_ if ha == "right" else cx - w_ / 2)
                y_lo = cy - h_ / 2
                box = (x_lo, y_lo, x_lo + w_, y_lo + h_)
                if box[0] < axbox.x0 or box[2] > axbox.x1 or box[1] < axbox.y0 or box[3] > axbox.y1:
                    continue
                cost = sum(overlap(box, o) for o in boxes) * 100 + sum(overlap(box, m_, 0) for m_ in marker_boxes) + r * 0.01
                if best is None or cost < best[0]:
                    best = (cost, box, ha, cx, cy, r)
            if best and best[0] < 1:
                break
        cost, box, ha, cx, cy, r = best
        if r >= 11:  # leader line from label anchor to its node
            nd = ax.transData.inverted().transform
            a_, b_ = nd((px, py)), nd((cx, cy))
            ax.plot([a_[0], b_[0]], [a_[1], b_[1]], color="#111111", lw=0.35, zorder=4)
        boxes.append(box)
        xd, yd = ax.transData.inverted().transform((cx, cy))
        t.set_position((xd, yd))
        t.set_ha(ha)
        t.set_va("center")
        if cost >= 100:
            log.info("WARNING label overlap for %s", lab[n])
    # legend: one row per cluster, label = three most-cited references
    handles = []
    for k, r in enumerate(ctab):
        col, mk = style[k]
        handles.append(Line2D([0], [0], marker=mk, color="none", markerfacecolor=col, markeredgecolor="#111111", markeredgewidth=0.4,
                              markersize=6, label=f"{r['cluster']}: {r['label_top3'].replace('; ', ', ')} ({r['n_nodes']} refs)"))
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, handletextpad=0.3, columnspacing=1.4, fontsize=6.5,
               bbox_to_anchor=(0.5, 0.0))
    C.save_fig(fig, OUT)
    plt.close(fig)
    log.info("saved %s.{pdf,eps,png}", C.rel(OUT))
    inputs = [C.P / "references/frame-refs.jsonl", F.META, F.ARXIV, C.P / "screen/abstract-decisions-v08.jsonl", C.P / "rq1/manifest.json",
              C.P / "records.jsonl", Path(__file__).resolve(), Path(F.__file__).resolve()]
    C.write_config(RUN, "analysis/rq1/fig4_cocitation.py", inputs, {
        "top_n": TOP_N, "edge_min": EDGE_MIN, "draw_min": DRAW_MIN, "ties_kept_at_cutoff": True, "louvain": {"resolution": 1, "weight": "cocitation_count", "seed": C.SEED},
        "stability_seeds": N_STABILITY_SEEDS, "layout": "networkx spring_layout, seed 20261016, weight = sqrt(co-citation count), weak hub (weight 0.8) for gravity", "hub_weight": HUB_W,
        "labels": "first author surname + year from OpenAlex; three most-cited members per cluster", "figure_width_mm": 174, "dpi_png": 600},
        {"packages": C.pkg_versions(["networkx", "matplotlib", "numpy", "scikit-learn"])})


if __name__ == "__main__":
    main()
