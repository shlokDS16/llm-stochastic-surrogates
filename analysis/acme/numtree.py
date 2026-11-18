"""Exact numeric-answer readout by best-first expansion of the model's digit tree (replaces the plan's 15-value grid; amendment
A-L2 in research/relaunch/PREREG-acme.md, reason: the smoke test found plain-digit grid mass Z of 0.001-0.004).

From the answer position, tokens that start a number (optional single leading space, then a digit) open the tree; below a node,
tokens that start with a digit, ',' or '.' extend the number. A token with non-numeric text after its numeric part ends the number
(e.g. '0 miles'); the mass of all non-extending tokens at an expanded node is that node's termination mass. The number of a
terminal is its digit string with commas removed and a trailing '.'/',' dropped (so '3,000 miles' -> 3000).
Stored per node, at T = 1: parent, token, raw logit, digit string; per expanded node the full-vocabulary LSE and the exact
extension mass at each temperature, so the tree's distribution is exact at every analysis temperature (coverage reported).
"""
from __future__ import annotations

import heapq
import math
import re

import scoring

NUM_START = re.compile(r"^ ?[0-9]|^ $")   # ' ' alone: SentencePiece models (Mistral) emit the space, then the digit
DIGIT = re.compile(r"^[0-9]")
EXT = re.compile(r"^[0-9.,]")
NUMPART = re.compile(r"^[0-9.,]*")


class Vocab:
    def __init__(self, tok, V, device="cuda"):
        import torch
        self.texts = scoring.token_texts(tok, V)
        self.root = torch.tensor([bool(NUM_START.match(t)) for t in self.texts], device=device)
        self.ext = torch.tensor([bool(EXT.match(t)) for t in self.texts], device=device)
        self.digit = torch.tensor([bool(DIGIT.match(t)) for t in self.texts], device=device)


def _split(text, root):
    t = text[1:] if root and text.startswith(" ") else text
    nm = NUMPART.match(t).group(0)
    return nm, t[len(nm):]


def value(digits):
    s = digits.rstrip(".,").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def expand_trees(model, tok, rendered_list, voc, temps=scoring.TEMPS, max_exp=1024, stop_unresolved=0.01, min_prob=1e-5,
                 thresh=12.0, min_child=1e-7, batch=32):
    """Best-first expansion for several prompts at once. Returns one tree dict per prompt."""
    import torch
    base = [tok(r, add_special_tokens=False)["input_ids"] for r in rendered_list]
    trees = [dict(nodes=[dict(parent=-1, tok=None, logit=None, digits="", ids=[], kind="root", p1=1.0)], exp={}, n_exp=0)
             for _ in rendered_list]
    heaps = [[(-1.0, 0)] for _ in rendered_list]          # root first
    done = [False] * len(rendered_list)
    root_num1 = [None] * len(rendered_list)

    def unresolved(i):
        tr = trees[i]
        u = sum(n["p1"] for j, n in enumerate(tr["nodes"]) if n["kind"] == "internal" and j not in tr["exp"])
        u += sum(e["rest1"] for e in tr["exp"].values())
        return u

    while not all(done):
        work = []
        for i in range(len(rendered_list)):
            if done[i]:
                continue
            if not heaps[i] or trees[i]["n_exp"] >= max_exp:
                done[i] = True
                continue
            negp, j = heaps[i][0]
            if j != 0 and (-negp < min_prob or unresolved(i) <= stop_unresolved * max(root_num1[i], 1e-12)):
                done[i] = True
                continue
            heapq.heappop(heaps[i])
            work.append((i, j))
        for s in range(0, len(work), batch):
            chunk = work[s:s + batch]
            logits = scoring._forward(model, tok, [base[i] + trees[i]["nodes"][j]["ids"] for i, j in chunk], keep=1)[:, -1, :]
            for (i, j), v in zip(chunk, logits):
                tr = trees[i]
                node = tr["nodes"][j]
                isroot = j == 0
                spacenode = (not isroot) and node["digits"] == ""          # lone-space child of the root: a digit must follow
                mask = voc.root if isroot else (voc.digit if spacenode else voc.ext)
                lse = {str(T): float(torch.logsumexp(v / T, -1)) for T in temps}
                extm = {str(T): float(torch.exp(torch.logsumexp(v[mask] / T, -1) - lse[str(T)])) if bool(mask.any()) else 0.0 for T in temps}
                mx = float(v.max())
                ci = torch.nonzero(mask & (v >= mx - thresh)).flatten()
                cand, clog = ci.tolist(), v[ci].tolist()          # one device transfer
                p_here = node["p1"]
                kept1 = 0.0
                for t, lg in zip(cand, clog):
                    pt = math.exp(lg - lse["1.0"])
                    if p_here * pt < min_child:
                        continue
                    nm, rem = _split(voc.texts[t], isroot)
                    if isroot and voc.texts[t] == " ":
                        nm, rem = "", ""
                    child = dict(parent=j, tok=t, logit=lg, digits=node["digits"] + nm, ids=node["ids"] + [t], p1=p_here * pt,
                                 kind="leaf" if rem else "internal")
                    tr["nodes"].append(child)
                    kept1 += pt
                    if child["kind"] == "internal":
                        heapq.heappush(heaps[i], (-child["p1"], len(tr["nodes"]) - 1))
                tr["exp"][j] = dict(lse=lse, extm=extm, rest1=max(p_here * (extm["1.0"] - kept1), 0.0))
                tr["n_exp"] += 1
                if isroot:
                    root_num1[i] = extm["1.0"]
            del logits
    for tr in trees:
        tr["exp"] = {str(k): v for k, v in tr["exp"].items()}
        for n in tr["nodes"]:
            n.pop("ids")
    return trees


def distribution(tree, T=1.0, max_exp=None):
    """Number distribution of a stored tree at temperature T: dict(values {number: mass}, numeric_mass, resolved, unresolved,
    unparseable, open_prefixes). max_exp: use only the first max_exp expansions (insertion order = best-first order), to measure
    truncation error (analysis/acme/tree_truncation.py)."""
    T = str(T)
    nodes, exp = tree["nodes"], tree["exp"]
    if max_exp is not None:
        keep = list(exp)[:max_exp]
        exp = {k: exp[k] for k in keep}
        alive = [False] * len(nodes)
        alive[0] = True
        for j, n in enumerate(nodes):
            if j and alive[n["parent"]] and str(n["parent"]) in exp:
                alive[j] = True
        nodes = [n if alive[j] else dict(n, kind="dead") for j, n in enumerate(nodes)]
    prob = [0.0] * len(nodes)
    prob[0] = 1.0
    vals, unparse, unres, opens = {}, 0.0, 0.0, {}
    for j, n in enumerate(nodes):
        if j == 0 or n["kind"] == "dead":
            continue
        pe = exp[str(n["parent"])]
        prob[j] = prob[n["parent"]] * math.exp(n["logit"] / float(T) - pe["lse"][T])
    for j, n in enumerate(nodes):
        if j == 0 or n["kind"] == "dead":
            continue
        term = None
        if n["kind"] == "leaf":
            term = prob[j]
        elif str(j) in exp:
            term = prob[j] * (1.0 - exp[str(j)]["extm"][T])
        else:
            unres += prob[j]
            xo = value(n["digits"])
            if xo is not None:
                opens[xo] = opens.get(xo, 0.0) + prob[j]
        if term is not None:
            x = value(n["digits"])
            if x is None:
                unparse += term
            else:
                vals[x] = vals.get(x, 0.0) + term
    for j, e in exp.items():   # extension mass below the storage threshold (never expanded)
        kept = sum(prob[c] for c, n in enumerate(nodes) if n["parent"] == int(j) and n["kind"] != "dead")
        unres += max(prob[int(j)] * e["extm"][T] - kept, 0.0)
    numeric = exp["0"]["extm"][T]
    resolved = sum(vals.values()) + unparse
    return dict(values=vals, numeric_mass=numeric, resolved=resolved, unresolved=unres, unparseable=unparse, open_prefixes=opens)


def summary(tree, T=1.0):
    d = distribution(tree, T)
    v = {x: m for x, m in d["values"].items() if x > 0}
    tot = sum(v.values())
    if tot <= 0:
        return dict(E_log=None, coverage=0.0, **{k: d[k] for k in ("numeric_mass", "unresolved", "unparseable")})
    e = sum(m * math.log(x) for x, m in v.items()) / tot
    xs = sorted(v)
    c, med = 0.0, None
    for x in xs:
        c += v[x] / tot
        if c >= 0.5:
            med = x
            break
    mode = max(v, key=v.get)
    return dict(E_log=e, median=med, mode=mode, p_mode=v[mode] / tot, coverage=(d["resolved"] / d["numeric_mass"]) if d["numeric_mass"] else 0.0,
                numeric_mass=d["numeric_mass"], unresolved=d["unresolved"], unparseable=d["unparseable"], n_values=len(v))
