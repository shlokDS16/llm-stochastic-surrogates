"""RQ2-RQ4 analysis of the full-text sample (protocol section 9; amendments v0.9.1, v0.11, v0.12, v0.12.1). Re-runnable.

    .venv/Scripts/python -I analysis/fulltext/rq234_analysis.py [--out runs/rq234-interim] [--no-prisma] [--draw-adjudication]

Reads (never edits) the sample, the reading list and the extraction files; copies the parseable extraction files into
`<out>/input-snapshot/` first so that one run sees one consistent set (hashes in config.json). Rules implemented, nothing else:
- Strata = sample.jsonl `stratum`; weights N_h / n_analysed_h; response-propensity weights within stratum, so a respondent
  carries N_g / r_g (r = analysed records with a full text AND a usable extraction by that coder). Amendment v0.12.1 item 1: a
  stratum with fewer than 2 RESPONDENTS (which includes fewer than 2 analysed) is merged with the same paradigm family's adjacent
  period (later period first; a family with no adjacent period is collapsed into OTH), repeated while a merged group still has
  fewer than 2 respondents. The merged groups are the units for the variance AND for the response-propensity weights N_g / r_g.
  `sensitivity_merge.csv` compares the main estimates with the original strata (limited comparison: a stratum with < 2
  respondents contributes no variance term; a stratum with 0 respondents has no weight and is left out of the point estimate and
  of its denominator).
- Amendment v0.12.1 item 2: per-coder RQ4 year trends only for items with >= 10 events and >= 10 non-events among the eligible
  records in the item's domain; items below are listed in `trend_descriptive_only.csv`.
- Amendment v0.12.1 item 3: the blinded adjudication sample is drawn ONLY with `--draw-adjudication` (off by default; run it
  after the final extraction).
- `fig_inputs/` holds tidy inputs for figures (no new estimation).
- Domain (eligible studies) estimator = ratio of stratified totals; Taylor linearised variance with collapsed-stratum
  variance and finite-population correction (1 - r_g / N_g); t interval with df = sum(r_g - 1); logit interval alongside.
- Claude is primary, Codex reported separately (own eligibility decisions, own coded set).
- Labels from `derive_labels.derive` (imported, not re-implemented).
- Agreement rule (v0.12 item 3): kappa >= 0.6 when every category has >= 5 records in each coder's coding, else percent >= 0.80.
- Orders 17 and 54 (one-page abstracts) are INELIGIBLE (E5) for both coders, flagged pending human confirmation; 67 and 120 keep
  the extractor's decision, flagged (runs/extraction-log/adjudication-notes.md).
- Model generation (RQ2 "by paradigm family and model generation", protocol sections 2 and 9; DESCRIPTIVE ONLY). Fixed before any
  RQ2 result by generation was inspected. G1 = pre-instruction-era and early instruction models; G2 = 2023-era chat models;
  G3 = 2024 and later; "unknown" = no rule applies. For each effect row, in this order:
    1. NAME FIRST: the first row of `model_generation.csv` (columns pattern, generation, rule note; patterns are case-insensitive
       regular expressions searched in the lower-cased model name, rows tried top to bottom, first match wins) that matches the
       row's `model` string (source "name"). NAME TOKENS ONLY; no internet, no paper text.
    2. Only if the name gives no generation ("unknown"): if a B.models[] entry whose name equals the row's `model` string states a
       release_date containing a four-digit year (2017 to 2026) and all such entries for that name state the same year:
       year <= 2022 -> G1, 2023 -> G2, >= 2024 -> G3 (source "release_date").
       Reason for this order (coordinator decision, taken without looking at any label-by-generation result): extractor
       release_date values are sometimes the query or version date of the study (orders 077 and 087 give 2024 dates for GPT-3.5 and
       GPT-4 original), not the model's release. Rows where both exist and disagree are counted as a diagnostic only.
    3. Else "unknown" (source "none"); also when `model` is empty. Unknown rows are counted and listed in
       `rq2_generation_names.csv`.
  Outputs: `rq2_by_generation.csv` and `fig_inputs/rq2_by_generation.csv` (outcome_kind x derived label x generation: unweighted
  row counts and numbers of studies, per coder, plus label "ALL"), `rq2_generation_names.csv` (every model string with its
  generation, source and counts), `rq2_generation_summary.json`, `rq2_by_generation.md`. No test, no weighting and no interval:
  effect rows are not a design sample (several rows per study, rows chosen by the extractors), and a study can appear in several
  generations, so the study counts are not additive across generations.
Interim: records with no open full text or no usable extraction are non-respondents / pending; rerunning updates everything.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import derive_labels as DL  # noqa: E402
import pilot_kappa as PK  # noqa: E402

CODERS = ("claude", "codex")
PERIODS = ["2018-2023", "2024", "2025-2026"]
OVERRIDE_INELIGIBLE = {17: "abstract-only (E5; pending human confirmation)", 54: "abstract-only (E5; pending human confirmation)"}
FLAG_PENDING = {67: "borderline exclusion (not-english), pending human confirmation",
                120: "borderline exclusion (questionnaire-only), pending human confirmation"}
SEED = 20261016
KINDS = ["effect", "accuracy", "agreement"]
DTYPES = ["none", "own_sample", "published_norms", "replication_dataset", "crowd_norms"]
OUTTYPES = ["accuracy", "bias_magnitude", "effect_size", "choice_distribution", "human_correlation", "other"]
ROBCATS = ["survived", "weakened", "reversed", "mixed", "not_reported"]
ADJ_FIELDS = ["D.primary_type", "F.f1", "F.f3", "F.f4", "F.f5", "F.f6", "F.f8", "F.f10", "F.f12", "F.robustness_outcome",
              "F.perturbations_tested"]
log = logging.getLogger("rq234")


# ----------------------------------------------------------------------------------------------------------------- utils
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def low(v) -> str:
    return str(v).strip().lower() if v is not None else ""


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def clopper(k: int, n: int):
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else stats.beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(0.975, k + 1, n - k)
    return (float(lo), float(hi))


def fmt_ci(e, lo, hi, pct=True, nd=1):
    if e is None or (isinstance(e, float) and math.isnan(e)):
        return "NA"
    s = 100 if pct else 1
    lo_s = "NA" if lo is None or math.isnan(lo) else f"{lo * s:.{nd}f}"
    hi_s = "NA" if hi is None or math.isnan(hi) else f"{hi * s:.{nd}f}"
    return f"{e * s:.{nd}f} ({lo_s} to {hi_s})"


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if (isinstance(v, float) and math.isnan(v)) else v) for k, v in r.items()})


def md_table(rows: list[dict], cols: list[str] | None = None) -> str:
    if not rows:
        return "(no rows)\n"
    cols = cols or list(rows[0])
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------------------------------------------- inputs
def load_inputs(out: Path):
    sample = jl(ROOT / "data/processed/fulltext-sample/sample.jsonl")
    reading = {r["order"]: r for r in jl(ROOT / "data/processed/fulltext/reading-list.jsonl")}
    records = {}
    ids = {s["id"] for s in sample}
    for r in jl(ROOT / "data/processed/records.jsonl"):
        if r["id"] in ids:
            records[r["id"]] = r
    snap = out / "input-snapshot"
    if snap.exists():
        shutil.rmtree(snap)
    ext: dict[str, dict[int, dict]] = {c: {} for c in CODERS}
    bad = []
    for c in CODERS:
        (snap / c).mkdir(parents=True)
        for f in sorted((ROOT / "data/processed/extraction" / c).glob("[0-9][0-9][0-9].json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                assert d["eligibility"]["decision"]
            except Exception as e:  # partially written or malformed: treated as not yet extracted
                bad.append((rel(f), repr(e)))
                continue
            shutil.copy2(f, snap / c / f.name)
            ext[c][int(f.stem)] = d
    return sample, reading, records, ext, bad, snap


def build_units(sample, reading, records, ext):
    units = []
    for s in sample:
        if not s["analysed"]:
            continue
        o = s["order"]
        r = reading[o]
        fam, per = s["stratum"].split("|")
        md = r.get("md")
        ft = bool(md) and r.get("status") != "no_open_copy" and (ROOT / md).exists() and (r.get("md_chars") or 0) > 0
        u = dict(order=o, stratum=s["stratum"], family=fam, period=per, N=s["N_h"], flag=s["flag"], year=r.get("year"),
                 vtype=records.get(s["id"], {}).get("type") or "unknown", ft=ft, md=md, status=r.get("status"), id=s["id"])
        for c in CODERS:
            d = ext[c].get(o) if ft else None
            raw = low(d["eligibility"]["decision"]).upper() if d else None
            el, why = raw, None
            if d and o in OVERRIDE_INELIGIBLE:
                el, why = "NO", OVERRIDE_INELIGIBLE[o]
            u[c] = dict(d=d, raw=raw, elig=el, why=why or FLAG_PENDING.get(o),
                        failed=(OVERRIDE_INELIGIBLE[o] if why else (d["eligibility"].get("failed_criterion") if d else None)))
            if not ft:
                u[c]["state"] = "no_full_text"
            elif d is None:
                u[c]["state"] = "pending_extraction"
            else:
                u[c]["state"] = {"YES": "coded_eligible", "NO": "coded_ineligible"}.get(el, "coded_unclear")
            u[c]["resp"] = u[c]["state"] in ("coded_eligible", "coded_ineligible")
        units.append(u)
    return units


# ----------------------------------------------------------------------------------------------------------------- strata
def build_groups(units, coder, merge_log):
    """Merge strata with < 2 analysed or < 2 respondents (see module docstring); returns stratum -> group id."""
    strata = sorted({u["stratum"] for u in units})
    N = {u["stratum"]: u["N"] for u in units}
    a, r = Counter(), Counter()
    for u in units:
        a[u["stratum"]] += 1
        r[u["stratum"]] += u[coder]["resp"]
    fam = {s: s.split("|")[0] for s in strata}
    per = {s: s.split("|")[1] for s in strata}
    grp = {s: i for i, s in enumerate(strata)}

    def members(g):
        return [s for s in strata if grp[s] == g]

    def cnt(g, c):
        return sum(c[s] for s in members(g))

    def neighbour(g):
        ms = members(g)
        for s in ms:
            if per[s] in PERIODS:
                i = PERIODS.index(per[s])
                for j in list(range(i + 1, 3)) + list(range(i - 1, -1, -1)):  # later first, then earlier
                    t = f"{fam[s]}|{PERIODS[j]}"
                    if t in grp and grp[t] != g:
                        return grp[t], f"adjacent period {t}"
        for s in ms:
            cands = [t for t in strata if fam[t] == "OTH" and grp[t] != g]
            same = [t for t in cands if per[t] == per[s]]
            if cands:
                return grp[(same or cands)[0]], "OTH"
        others = [x for x in set(grp.values()) if x != g]
        if not others:
            return None, ""
        return min(others, key=lambda x: (cnt(x, r), x)), "smallest other group (fallback)"

    while True:
        gs = sorted(set(grp.values()))
        bad = [g for g in gs if cnt(g, a) < 2 or cnt(g, r) < 2]
        if not bad or len(gs) == 1:
            break
        g = min(bad, key=lambda x: (cnt(x, r), cnt(x, a), x))
        t, why = neighbour(g)
        if t is None:
            break
        merge_log.append(dict(coder=coder, merged=",".join(members(g)), into=",".join(members(t)), reason=why,
                              a=cnt(g, a), r=cnt(g, r)))
        for s in members(g):
            grp[s] = t
    return grp, N, a, r


def identity_groups(units, coder):
    strata = sorted({u["stratum"] for u in units})
    N = {u["stratum"]: u["N"] for u in units}
    a, r = Counter(), Counter()
    for u in units:
        a[u["stratum"]] += 1
        r[u["stratum"]] += u[coder]["resp"]
    return {s: i for i, s in enumerate(strata)}, N, a, r


class Design:
    """Respondent arrays and group structure for one coder."""

    def __init__(self, units, coder, merge_log, merge=True):
        self.coder = coder
        if merge:
            grp, N, a, r = build_groups(units, coder, merge_log)
        else:  # original strata (sensitivity comparison only)
            grp, N, a, r = identity_groups(units, coder)
        self.grp, self.Nh, self.a, self.r = grp, N, a, r
        gids = sorted(set(grp.values()))
        self.Ng = {g: sum(N[s] for s in grp if grp[s] == g) for g in gids}
        self.rg = {g: sum(r[s] for s in grp if grp[s] == g) for g in gids}
        self.ag = {g: sum(a[s] for s in grp if grp[s] == g) for g in gids}
        self.resp = [u for u in units if u[coder]["resp"]]
        self.gi = np.array([grp[u["stratum"]] for u in self.resp])
        self.w = np.array([self.Ng[g] / self.rg[g] for g in self.gi], dtype=float)
        self.df = sum(max(self.rg[g] - 1, 0) for g in gids)
        self.Ntot = sum(N.values())
        self.Ntot_est = sum(self.Ng[g] for g in gids if self.rg[g] >= 1)  # frame size covered by groups with a respondent
        self.n_var_dropped = [g for g in gids if self.rg[g] == 1]  # contribute to the point estimate, not to the variance
        self.n_no_resp = [g for g in gids if self.rg[g] == 0]  # no weight possible: outside the point estimate
        self.gids = gids

    def var_total(self, z: np.ndarray) -> float:
        """Collapsed-stratum variance of sum_i w_i z_i over respondents, with FPC (1 - r_g / N_g)."""
        v = 0.0
        for g in self.gids:
            m = self.gi == g
            n = int(m.sum())
            if n < 2:
                continue
            u = self.w[m] * z[m]
            v += (1 - n / self.Ng[g]) * n / (n - 1) * float(((u - u.mean()) ** 2).sum())
        return v

    def ratio(self, x: np.ndarray, y: np.ndarray) -> dict:
        """Domain proportion = sum w y / sum w x (x = domain indicator, y = outcome within domain)."""
        tx, ty = float((self.w * x).sum()), float((self.w * y).sum())
        res = dict(n_domain=int(x.sum()), k=int(y.sum()), N_hat_domain=tx, est=float("nan"), se=float("nan"),
                   lo=float("nan"), hi=float("nan"), lo_logit=float("nan"), hi_logit=float("nan"), cp_lo=float("nan"),
                   cp_hi=float("nan"), note="")
        if tx <= 0:
            res["note"] = "empty domain"
            return res
        R = ty / tx
        z = y - R * x
        se = math.sqrt(self.var_total(z)) / tx
        res.update(est=R, se=se)
        t = stats.t.ppf(0.975, max(self.df, 1))
        res["lo"], res["hi"] = max(0.0, R - t * se), min(1.0, R + t * se)
        if 0 < R < 1 and se > 0:
            s = t * se / (R * (1 - R))
            lg = math.log(R / (1 - R))
            res["lo_logit"], res["hi_logit"] = 1 / (1 + math.exp(-(lg - s))), 1 / (1 + math.exp(-(lg + s)))
        if se == 0 or R in (0.0, 1.0):
            res["note"] = "zero-variance estimate; unweighted exact interval in cp_lo/cp_hi"
            res["cp_lo"], res["cp_hi"] = clopper(res["k"], res["n_domain"])
        return res

    def paired(self, x: np.ndarray, ya: np.ndarray, yb: np.ndarray) -> dict:
        """Paired difference of two domain proportions over the SAME studies: D = sum w (ya - yb) / sum w x (ratio estimator,
        linearised z = (ya - yb) - D x, same collapsed-stratum variance with FPC and t interval as `ratio`)."""
        d = ya - yb
        tx = float((self.w * x).sum())
        res = dict(est=float("nan"), se=float("nan"), lo=float("nan"), hi=float("nan"))
        if tx <= 0:
            return res
        D = float((self.w * d).sum()) / tx
        se = math.sqrt(self.var_total(d - D * x)) / tx
        t = stats.t.ppf(0.975, max(self.df, 1))
        res.update(est=D, se=se, lo=D - t * se, hi=D + t * se)
        return res

    def share_of_frame(self, x: np.ndarray) -> dict:
        tx = float((self.w * x).sum())
        se = math.sqrt(self.var_total(x.astype(float))) / self.Ntot_est
        e = tx / self.Ntot_est
        t = stats.t.ppf(0.975, max(self.df, 1))
        return dict(est=e, se=se, lo=max(0.0, e - t * se), hi=min(1.0, e + t * se), N_hat=tx)

    def logit_trend(self, x_dom: np.ndarray, y: np.ndarray, year: np.ndarray) -> dict:
        """Design-weighted logistic regression of y on (year - 2024) in the domain; sandwich with collapsed strata."""
        dom = x_dom > 0
        nd, ev = int(dom.sum()), int(y[dom].sum())
        res = dict(n_domain=nd, events=ev, non_events=nd - ev, beta=float("nan"), se=float("nan"), OR_per_year=float("nan"),
                   or_lo=float("nan"), or_hi=float("nan"), note="")
        if ev < 10 or nd - ev < 10:
            res["note"] = "not estimated (fewer than 10 events or 10 non-events)"
            return res
        X = np.column_stack([np.ones(len(y)), year - 2024.0])
        w = self.w * dom
        w = w / w[dom].mean()
        beta = np.zeros(2)
        for _ in range(100):
            p = 1 / (1 + np.exp(-(X @ beta)))
            W = w * p * (1 - p)
            H = X.T @ (X * W[:, None])
            step = np.linalg.solve(H + 1e-10 * np.eye(2), X.T @ (w * (y - p)))
            beta += step
            if np.abs(step).max() < 1e-9:
                break
        p = 1 / (1 + np.exp(-(X @ beta)))
        A = X.T @ (X * (w * p * (1 - p))[:, None])
        U = X * (w * (y - p))[:, None]
        B = np.zeros((2, 2))
        for g in self.gids:
            m = self.gi == g
            n = int(m.sum())
            if n < 2:
                continue
            Ug = U[m] - U[m].mean(axis=0)
            B += (1 - n / self.Ng[g]) * n / (n - 1) * Ug.T @ Ug
        Ai = np.linalg.inv(A)
        V = Ai @ B @ Ai
        se = math.sqrt(max(V[1, 1], 0.0))
        t = stats.t.ppf(0.975, max(self.df, 1))
        res.update(beta=float(beta[1]), se=se, OR_per_year=math.exp(beta[1]), or_lo=math.exp(beta[1] - t * se),
                   or_hi=math.exp(beta[1] + t * se))
        if abs(beta[1]) > 10:
            res["note"] = "possible separation"
        return res


# ----------------------------------------------------------------------------------------------------------------- features
def num(v):
    try:
        return float(str(v).replace(",", "").strip().split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def study_features(d: dict, rows: list[dict]) -> tuple[set, set]:
    """Names true for this eligible study, and names whose domain it is outside of."""
    on, out = set(), set()
    for r in rows:
        on.add(f"rq2|{r['outcome_kind']}|ANY")
        on.add(f"rq2|{r['outcome_kind']}|{r['derived_label']}")
    D = d.get("D", {})
    types = [low(t) for t in (D.get("types") or [])] or ["none"]
    for t in types:
        on.add(f"rq3|types_any|{t}")
    on.add(f"rq3|primary_type|{low(D.get('primary_type')) or 'none'}")
    hn = num(D.get("human_n"))
    if hn is not None:
        on.add("rq3|human_n|reported")
    for t in (d.get("E", {}).get("outcome_types") or []):
        on.add(f"rq3|outcome_types|{low(t)}")
    F = d.get("F", {})
    for i in range(1, 13):
        on.add(f"rq4|f{i}|{low(F.get(f'f{i}')) or 'null'}")
    if low(F.get("f6")) == "na":
        out.add("rq4|f6_applicable|yes")
    elif low(F.get("f6")) == "yes":
        on.add("rq4|f6_applicable|yes")
    perts = [low(t) for t in (F.get("perturbations_tested") or [])]
    for t in perts:
        on.add(f"rq4|perturbation|{t}")
    if not perts:
        on.add("rq4|perturbation|none_listed")
    ro = low(F.get("robustness_outcome")) or "null"
    on.add(f"rq4|robustness_outcome|{ro}")
    if ro != "na":
        on.add("rq4|robustness_tested|yes")
        on.add(f"rq4|robustness_outcome_among_tested|{ro}")
    else:
        out.update(f"rq4|robustness_outcome_among_tested|{c}" for c in ROBCATS)
    return on, out


FIXED = ([f"rq2|{k}|ANY" for k in KINDS] + [f"rq3|types_any|{t}" for t in DTYPES] + [f"rq3|primary_type|{t}" for t in DTYPES]
         + ["rq3|human_n|reported"] + [f"rq3|outcome_types|{t}" for t in OUTTYPES]
         + [f"rq4|f{i}|{v}" for i in range(1, 13) for v in ("yes", "no", "na")] + ["rq4|f6_applicable|yes"]
         + [f"rq4|perturbation|{t}" for t in PK.PERTS + ["none_listed"]]
         + [f"rq4|robustness_outcome|{c}" for c in ROBCATS + ["na"]] + ["rq4|robustness_tested|yes"]
         + [f"rq4|robustness_outcome_among_tested|{c}" for c in ROBCATS])


def agreement_key(name: str):
    """Agreement-table field that governs a feature name."""
    p = name.split("|")
    if p[0] == "rq2":
        return "E.outcome_kind" if p[2] == "ANY" else "E.derived_label (script)"
    if p[1] == "types_any":
        return f"D.types[{p[2]}]"
    if p[1] == "primary_type":
        return "D.primary_type"
    if p[1] == "human_n":
        return "D.human_n_reported"
    if p[1] == "outcome_types":
        return f"E.outcome_types[{p[2]}]"
    if p[1].startswith("f") and p[1][1:].isdigit():
        return f"F.{p[1]}"
    if p[1] == "f6_applicable":
        return "F.f6"
    if p[1] == "perturbation":
        return "F.perturbations_tested[none_listed]" if p[2] == "none_listed" else f"F.perturbations_tested[{p[2]}]"
    if p[1] in ("robustness_outcome", "robustness_outcome_among_tested"):
        return "F.robustness_outcome"
    if p[1] == "robustness_tested":
        return "F.robustness_tested (robustness_outcome != na)"
    return None


def rows_by_order(coder: str, snap: Path, keep: set[int]):
    DL.EXT = snap  # the snapshot, so labels and estimates come from the same files
    by = defaultdict(list)
    for r in DL.rows_for(coder):
        if r["order"] in keep:
            by[r["order"]].append(r)
    return by


def feature_table(units, coder, snap):
    keep = {u["order"] for u in units if u[coder]["elig"] == "YES" and u[coder]["resp"]}
    rows = rows_by_order(coder, snap, keep)
    feats = {}
    for u in units:
        if u[coder]["resp"] and u[coder]["elig"] == "YES":
            feats[u["order"]] = study_features(u[coder]["d"], rows.get(u["order"], []))
    return feats, rows


def estimate_all(units, coder, des: Design, feats, names):
    elig = np.array([1.0 if (u["order"] in feats) else 0.0 for u in des.resp])
    out = {}
    for n in names:
        x = elig.copy()
        y = np.zeros(len(des.resp))
        for i, u in enumerate(des.resp):
            if u["order"] in feats:
                on, off = feats[u["order"]]
                if n in off:
                    x[i] = 0.0
                if n in on and x[i] > 0:
                    y[i] = 1.0
        out[n] = des.ratio(x, y)
        out[n]["_x"], out[n]["_y"] = x, y
    return out


# ----------------------------------------------------------------------------------------------------------------- model generation
GENERATIONS = ["G1", "G2", "G3", "unknown"]
GEN_CSV = HERE / "model_generation.csv"
_YEAR = re.compile(r"(?<!\d)(20[12]\d)(?!\d)")


def load_generation_table():
    with GEN_CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        assert r["generation"] in GENERATIONS, r
    return [(re.compile(r["pattern"]), r["generation"], r["pattern"]) for r in rows]


def year_generation(y: int) -> str:
    return "G1" if y <= 2022 else "G2" if y == 2023 else "G3"


def name_generation(name, table):
    """(generation, index of the matching table row or None) from the model name alone."""
    n = low(name)
    if not n:
        return "unknown", None
    for i, (rx, g, _) in enumerate(table):
        if rx.search(n):
            return g, i
    return "unknown", None


def row_generation(r: dict, d: dict, table):
    """(generation, source, name_only_generation, date_only_generation). Name first, release year only when the name is unknown."""
    ng, _ = name_generation(r.get("model"), table)
    years = set()
    for m in d.get("B", {}).get("models", []):
        if m.get("name") == r.get("model") and r.get("model"):
            for y in _YEAR.findall(str(m.get("release_date") or "")):
                if 2017 <= int(y) <= 2026:
                    years.add(int(y))
    dg = year_generation(next(iter(years))) if len(years) == 1 else "unknown"
    if ng != "unknown":
        return ng, "name", ng, dg
    if dg != "unknown":
        return dg, "release_date", ng, dg
    return "unknown", "none", ng, dg


def attach_generation(units, lab_rows):
    table = load_generation_table()
    dmap = {c: {u["order"]: u[c]["d"] for u in units if u[c]["d"]} for c in CODERS}
    for c in CODERS:
        for o, rs in lab_rows[c].items():
            for r in rs:
                (r["generation"], r["generation_source"], r["generation_name_only"],
                 r["generation_date_only"]) = row_generation(r, dmap[c][o], table)
    return table


def generation_outputs(out: Path, lab_rows, table):
    cells, studies = defaultdict(int), defaultdict(set)
    for c in CODERS:
        for o, rs in lab_rows[c].items():
            for r in rs:
                for lab in (r["derived_label"], "ALL"):
                    k = (c, r["outcome_kind"], lab, r["generation"])
                    cells[k] += 1
                    studies[k].add(o)
    labels = defaultdict(set)
    for (c, kind, lab, g) in cells:
        labels[(c, kind)].add(lab)
    tidy = []
    for c in CODERS:
        for kind in KINDS:
            for lab in sorted(labels[(c, kind)], key=lambda x: (x != "ALL", x)):
                tot = sum(cells[(c, kind, lab, g)] for g in GENERATIONS)
                for g in GENERATIONS:
                    k = (c, kind, lab, g)
                    tidy.append(dict(coder=c, outcome_kind=kind, derived_label=lab, generation=g, rows=cells[k], studies=len(studies[k]),
                                     rows_in_label_all_generations=tot,
                                     basis="unweighted row counts; descriptive only; studies not additive across generations"))
    write_csv(out / "rq2_by_generation.csv", tidy)
    (out / "fig_inputs").mkdir(exist_ok=True)
    # figure input: row share of each generation within kind x label (descriptive; no interval)
    fig = [dict(t, share_of_label_rows=round(t["rows"] / t["rows_in_label_all_generations"], 4) if t["rows_in_label_all_generations"] else None)
           for t in tidy]
    write_csv(out / "fig_inputs" / "rq2_by_generation.csv", fig)
    # per model string audit
    nm = defaultdict(lambda: dict(rows=0, orders=set()))
    for c in CODERS:
        for o, rs in lab_rows[c].items():
            for r in rs:
                k = (c, r.get("model") or "", r["generation"], r["generation_source"], r["generation_name_only"], r["generation_date_only"])
                nm[k]["rows"] += 1
                nm[k]["orders"].add(o)
    name_rows = [dict(coder=k[0], model=k[1], generation=k[2], source=k[3], name_only_generation=k[4],
                      date_only_generation=k[5],
                      date_disagrees_with_name=(k[4] != "unknown" and k[5] != "unknown" and k[4] != k[5]), rows=v["rows"], studies=len(v["orders"]))
                 for k, v in sorted(nm.items(), key=lambda kv: (kv[0][0], kv[0][2] != "unknown", kv[0][2], kv[0][1]))]
    write_csv(out / "rq2_generation_names.csv", name_rows)
    # summary
    summ = {}
    for c in CODERS:
        rows = [r for rs in lab_rows[c].values() for r in rs]
        g = Counter(r["generation"] for r in rows)
        src = Counter(r["generation_source"] for r in rows)
        both = [r for r in rows if r["generation_name_only"] != "unknown" and r["generation_date_only"] != "unknown"]
        used = {i for i in (name_generation(r.get("model"), table)[1] for r in rows) if i is not None}
        summ[c] = dict(rows=len(rows), studies=len({r["order"] for r in rows}),
                       rows_per_generation={x: g.get(x, 0) for x in GENERATIONS},
                       studies_per_generation={x: len({r["order"] for r in rows if r["generation"] == x}) for x in GENERATIONS},
                       unknown_share=round(g.get("unknown", 0) / len(rows), 4) if rows else None,
                       rows_by_source=dict(src),
                       rows_per_generation_name_rule_only={x: sum(r['generation_name_only'] == x for r in rows) for x in GENERATIONS},
                       rows_with_name_and_release_year=len(both),
                       release_date_rows_disagreeing_with_name_rule=sum(r["generation_name_only"] != r["generation_date_only"] for r in both),
                       distinct_unknown_model_strings=len({r.get("model") or "" for r in rows if r["generation"] == "unknown"}),
                       table_rows_never_matched=[table[i][2] for i in range(len(table)) if i not in used])
    (out / "rq2_generation_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    md = ["# RQ2 by model generation (descriptive)", "",
          "Generation of an effect row: the first matching row of `analysis/fulltext/model_generation.csv` applied to the model name "
          "only; only if the name gives none, the release_date year of the matching B.models entry if stated; else unknown (name first "
          "because extractor release dates are sometimes query or version dates; rule fixed before any result by generation "
          "was inspected; see the docstring of `rq234_analysis.py`). G1 = pre-instruction-era and early instruction models, G2 = 2023-era chat "
          "models, G3 = 2024 and later. Unweighted counts of extracted effect rows and of studies; no test, no weights, no interval (rows are not a "
          "design sample and a study can contribute rows to several generations, so study counts are not additive).", ""]
    for c in CODERS:
        s_ = summ[c]
        md += [f"## {c}", "", f"Rows {s_['rows']} in {s_['studies']} studies; unknown share {100 * s_['unknown_share']:.1f}%; "
               f"source: {s_['rows_by_source']}.", ""]
        by = defaultdict(dict)
        for t in tidy:
            if t["coder"] == c:
                by[(t["outcome_kind"], t["derived_label"])][t["generation"]] = f"{t['rows']} ({t['studies']})"
        tbl = [dict(outcome_kind=k[0], derived_label=k[1], **{f"{g} rows (studies)": v.get(g, "") for g in GENERATIONS})
               for k, v in by.items()]
        md += [md_table(tbl)]
    (out / "rq2_by_generation.md").write_text("\n".join(md), encoding="utf-8")
    return summ


# ----------------------------------------------------------------------------------------------------------------- agreement
def rule(ca: Counter, cb: Counter, k, po):
    if po is None or (isinstance(po, float) and math.isnan(po)):
        return None, "none"
    cats = set(ca) | set(cb)
    if cats and all(ca[c] >= 5 and cb[c] >= 5 for c in cats) and k is not None:
        return bool(k >= 0.6), "kappa>=0.6"
    return bool(po >= 0.8), "percent>=0.80"


def agreement(units, ext):
    pairs = {o: (ext["claude"][o], ext["codex"][o]) for o in ext["claude"] if o in ext["codex"]
             and any(u["order"] == o for u in units)}
    ftu = {u["order"] for u in units if u["ft"]}
    pairs = {o: p for o, p in pairs.items() if o in ftu}
    yes = {o: p for o, p in pairs.items() if all(PK.norm(d["eligibility"]["decision"]) == "yes" for d in p)}
    rows, dis = [], []

    def add(field, level, items, adj=False):
        a, b = [x[1] for x in items], [x[2] for x in items]
        k, po = PK.kappa(a, b)
        ca, cb = Counter(a), Counter(b)
        ok, basis = rule(ca, cb, k, po if items else None)
        rows.append(dict(field=field, level=level, n=len(items), percent_agreement=round(100 * po, 1) if items else None,
                         kappa=None if k is None else round(k, 3), claude_counts="; ".join(f"{c}={ca[c]}" for c in sorted(ca)),
                         codex_counts="; ".join(f"{c}={cb[c]}" for c in sorted(cb)), rule_basis=basis, passes_v012_rule=ok))
        if adj:
            dis.extend((u, field, x, y) for u, x, y in items if x != y)

    N = PK.norm
    add("eligibility.decision", "all pairs (raw coder decisions)", [(o, N(c["eligibility"]["decision"]), N(x["eligibility"]["decision"]))
                                                                     for o, (c, x) in pairs.items()])
    add("A.peer_reviewed", "all pairs (not used for analysis in v1.1)", [(o, N(c["A"].get("peer_reviewed")), N(x["A"].get("peer_reviewed")))
                                                                         for o, (c, x) in pairs.items()])
    add("D.primary_type", "yes-both", [((o, ""), N(c["D"].get("primary_type")), N(x["D"].get("primary_type"))) for o, (c, x) in yes.items()],
        adj=True)
    dt = lambda d: {low(t) for t in (d["D"].get("types") or [])} or {"none"}  # noqa: E731
    for t in DTYPES:
        add(f"D.types[{t}]", "yes-both (binary per study)", [(o, str(t in dt(c)), str(t in dt(x))) for o, (c, x) in yes.items()])
    add("D.human_n_reported", "yes-both (binary per study)", [(o, str(num(c["D"].get("human_n")) is not None),
                                                               str(num(x["D"].get("human_n")) is not None)) for o, (c, x) in yes.items()])
    ot = lambda d: {low(t) for t in (d["E"].get("outcome_types") or [])}  # noqa: E731
    for t in OUTTYPES:
        add(f"E.outcome_types[{t}]", "yes-both (binary per study)", [(o, str(t in ot(c)), str(t in ot(x))) for o, (c, x) in yes.items()])
    for i in range(1, 13):
        add(f"F.f{i}", "yes-both", [((o, ""), N(c["F"].get(f"f{i}")), N(x["F"].get(f"f{i}"))) for o, (c, x) in yes.items()],
            adj=f"F.f{i}" in ADJ_FIELDS)
    add("F.robustness_outcome", "yes-both", [((o, ""), N(c["F"].get("robustness_outcome")), N(x["F"].get("robustness_outcome")))
                                             for o, (c, x) in yes.items()], adj=True)
    add("F.robustness_tested (robustness_outcome != na)", "yes-both (binary per study)",
        [(o, str(N(c["F"].get("robustness_outcome")) != "na"), str(N(x["F"].get("robustness_outcome")) != "na"))
         for o, (c, x) in yes.items()])
    fam = lambda d: {p.get("family") for p in d["C"].get("paradigms", [])}  # noqa: E731
    add("C.family_presence (pooled)", "yes-both x family", [(f"{o}:{f}", str(f in fam(c)), str(f in fam(x)))
                                                           for o, (c, x) in yes.items() for f in PK.FAMILIES])
    pt = lambda d: {low(t) for t in (d["F"].get("perturbations_tested") or [])}  # noqa: E731
    add("F.perturbations_tested (pooled)", "yes-both x type", [(f"{o}:{t}", str(t in pt(c)), str(t in pt(x)))
                                                              for o, (c, x) in yes.items() for t in PK.PERTS])
    for t in PK.PERTS:
        add(f"F.perturbations_tested[{t}]", "yes-both (binary per study)",
            [((o, t), "listed" if t in pt(c) else "not listed", "listed" if t in pt(x) else "not listed") for o, (c, x) in yes.items()],
            adj=True)
    add("F.perturbations_tested[none_listed]", "yes-both (binary per study)", [(o, str(not pt(c)), str(not pt(x))) for o, (c, x) in yes.items()])
    matched, unmatched = {}, 0
    for o, (c, x) in yes.items():
        kc, kx = PK.effect_keys(c), PK.effect_keys(x)
        unmatched += len(set(kc) ^ set(kx))
        for key in set(kc) & set(kx):
            matched[(o, key)] = (kc[key], kx[key])

    def has_h(d):
        types = [low(t) for t in d.get("D", {}).get("types", [])]
        return any(t and t != "none" for t in types) or low(d.get("D", {}).get("primary_type")) not in ("", "none")

    for fld in ("outcome_kind", "basis", "model_effect_present", "human_effect_present", "direction", "model_vs_human",
                "authors_comparison", "label"):
        mode = lambda rs: Counter(N(r.get(fld)) for r in rs).most_common(1)[0][0]  # noqa: E731
        add(f"E.{fld}" if fld != "label" else "E.label (coder-assigned)", "matched (paradigm family x model family; modal value)",
            [(f"{o}:{k[0]}/{k[1]}", mode(rc), mode(rx)) for (o, k), (rc, rx) in matched.items()])
    items = []
    for (o, k), (rc, rx) in matched.items():
        dl = lambda rs, d: Counter(DL.derive(r, has_h(d))[0] for r in rs if "outcome_kind" in r).most_common(1)  # noqa: E731
        a, b = dl(rc, yes[o][0]), dl(rx, yes[o][1])
        if a and b:
            items.append((f"{o}:{k[0]}/{k[1]}", a[0][0], b[0][0]))
    add("E.derived_label (script)", "matched keys with v1.1 rows (modal derived label)", items)
    for r in rows:
        r["matched_keys_note"] = f"matched {len(matched)}, unmatched {unmatched}" if r["field"].startswith("E.") else ""
    return rows, dis, dict(pairs=len(pairs), yes_both=len(yes), matched=len(matched), unmatched=unmatched)


# ----------------------------------------------------------------------------------------------------------------- main
FINAL = False  # set by --final in main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/rq234-interim")
    ap.add_argument("--no-prisma", action="store_true")
    ap.add_argument("--draw-adjudication", action="store_true",
                    help="draw the blinded adjudication sample (v0.12.1 item 3); off by default, run only after the final extraction")
    ap.add_argument("--final", action="store_true",
                    help="final run: full-text retrieval and extraction complete; writes interim: false (CRP-S05)")
    a = ap.parse_args()
    global FINAL
    FINAL = bool(a.final)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.FileHandler(out / "log.txt", mode="w", encoding="utf-8"), logging.StreamHandler()])
    sample, reading, records, ext, bad, snap = load_inputs(out)
    units = build_units(sample, reading, records, ext)
    log.info("analysed units %d; extraction files claude %d codex %d; unparseable %s", len(units), len(ext["claude"]),
             len(ext["codex"]), bad)

    # ---- config
    inputs = {rel(p): sha(p) for p in [ROOT / "data/processed/fulltext-sample/sample.jsonl",
                                       ROOT / "data/processed/fulltext/reading-list.jsonl", ROOT / "data/processed/records.jsonl",
                                       ROOT / "analysis/fulltext/derive_labels.py", ROOT / "analysis/fulltext/pilot_kappa.py",
                                       ROOT / "analysis/fulltext/rq234_analysis.py",
                                       ROOT / "research/protocol/fulltext-extraction-brief.md",
                                       ROOT / "runs/extraction-log/adjudication-notes.md"]}
    for c in CODERS:
        for o in sorted(ext[c]):
            p = snap / c / f"{o:03d}.json"
            inputs[f"extraction/{c}/{o:03d}.json"] = sha(p)
    status = {c: dict(Counter(u[c]["state"] for u in units)) for c in CODERS}
    cfg = dict(run=out.name, interim=not FINAL, protocol_amendment="v0.12.1", draw_adjudication=bool(a.draw_adjudication),
               trend_min_events_and_nonevents=10, seed_adjudication=SEED, n_analysed=len(units),
               n_full_text_obtained=sum(u["ft"] for u in units), reading_list_status=dict(Counter(u["status"] for u in units)),
               records_per_status=status, overrides_ineligible=OVERRIDE_INELIGIBLE, flags_pending_confirmation=FLAG_PENDING,
               unparseable_extraction_files=bad, input_sha256=inputs,
               python=sys.version.split()[0], numpy=np.__version__)
    (out / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")

    merge_log: list[dict] = []
    des = {c: Design(units, c, merge_log) for c in CODERS}
    write_csv(out / "strata-groups.csv", [dict(coder=c, stratum=s, group=g, N_h=d.Nh[s], n_analysed=d.a[s], n_respondents=d.r[s],
                                               N_group=d.Ng[g], n_analysed_group=d.ag[g], n_respondents_group=d.rg[g])
                                          for c, d in des.items() for s, g in sorted(d.grp.items())])
    write_csv(out / "strata-merges.csv", merge_log)

    # ---- 1 eligibility
    elig_rows = []
    for s in sorted({u["stratum"] for u in units}):
        us = [u for u in units if u["stratum"] == s]
        row = dict(stratum=s, N_h=us[0]["N"], n_analysed=len(us), n_full_text=sum(u["ft"] for u in us),
                   n_no_open_copy=sum(not u["ft"] for u in us))
        for c in CODERS:
            cnt = Counter(u[c]["elig"] for u in us if u["ft"] and u[c]["d"])
            row.update({f"{c}_eligible": cnt["YES"], f"{c}_ineligible": cnt["NO"], f"{c}_unclear": cnt["UNCLEAR"],
                        f"{c}_pending_extraction": sum(u[c]["state"] == "pending_extraction" for u in us),
                        f"{c}_ineligibility_rate": (round(cnt["NO"] / (cnt["YES"] + cnt["NO"]), 3)
                                                    if cnt["YES"] + cnt["NO"] else None)})
        row["claude_group"] = des["claude"].grp[s]
        elig_rows.append(row)
    tot = dict(stratum="TOTAL", N_h=sum(r["N_h"] for r in elig_rows))
    for k in elig_rows[0]:
        if k not in ("stratum", "N_h", "claude_group") and not k.endswith("rate"):
            tot[k] = sum(r[k] for r in elig_rows)
    for c in CODERS:
        d_ = tot[f"{c}_eligible"] + tot[f"{c}_ineligible"]
        tot[f"{c}_ineligibility_rate"] = round(tot[f"{c}_ineligible"] / d_, 3) if d_ else None
    write_csv(out / "eligibility.csv", elig_rows + [tot])

    # ---- 2-4 estimation
    feats, lab_rows, est = {}, {}, {}
    for c in CODERS:
        feats[c], lab_rows[c] = feature_table(units, c, snap)
    gen_table = attach_generation(units, lab_rows)
    gen_summary = generation_outputs(out, lab_rows, gen_table)
    log.info("model generation (rows per generation): %s", {c: gen_summary[c]["rows_per_generation"] for c in CODERS})
    names = list(dict.fromkeys(FIXED + sorted({n for c in CODERS for on, _ in feats[c].values() for n in on})))
    for c in CODERS:
        est[c] = estimate_all(units, c, des[c], feats[c], names)
    agr_rows, dis, agr_meta = agreement(units, ext)
    write_csv(out / "agreement.csv", agr_rows)
    agr = {r["field"]: r for r in agr_rows}

    def agr_info(name):
        k = agreement_key(name)
        r = agr.get(k)
        if not r:
            return dict(agreement_field=k, kappa=None, percent_agreement=None, n_agreement=None, passes_v012_rule=None, rule_basis=None)
        return dict(agreement_field=k, kappa=r["kappa"], percent_agreement=r["percent_agreement"], n_agreement=r["n"],
                    passes_v012_rule=r["passes_v012_rule"], rule_basis=r["rule_basis"])

    def side_by_side(prefix_names):
        rows = []
        for n in prefix_names:
            row = dict(feature=n)
            for c in CODERS:
                e = est[c].get(n)
                if e is None:
                    continue
                row.update({f"{c}_n_domain": e["n_domain"], f"{c}_k": e["k"], f"{c}_est_pct": round(100 * e["est"], 2) if e["est"] == e["est"] else None,
                            f"{c}_lo_pct": round(100 * e["lo"], 2) if e["lo"] == e["lo"] else None,
                            f"{c}_hi_pct": round(100 * e["hi"], 2) if e["hi"] == e["hi"] else None,
                            f"{c}_lo_logit_pct": round(100 * e["lo_logit"], 2) if e["lo_logit"] == e["lo_logit"] else None,
                            f"{c}_hi_logit_pct": round(100 * e["hi_logit"], 2) if e["hi_logit"] == e["hi_logit"] else None,
                            f"{c}_N_hat_domain": round(e["N_hat_domain"], 1), f"{c}_note": e["note"]})
                row[f"{c}_cp_unweighted_pct"] = (f"{100 * e['cp_lo']:.1f}-{100 * e['cp_hi']:.1f}" if e["cp_lo"] == e["cp_lo"] else "")
            row.update(agr_info(n))
            rows.append(row)
        return rows

    allnames = list(dict.fromkeys(n for c in CODERS for n in est[c]))
    # RQ2
    n2 = [n for n in allnames if n.startswith("rq2|")]
    n2.sort(key=lambda n: (KINDS.index(n.split("|")[1]), n.split("|")[2] != "ANY", n))
    rq2 = side_by_side(n2)
    for r in rq2:
        _, kind, lab = r["feature"].split("|")
        r.update(outcome_kind=kind, label=lab)
    write_csv(out / "rq2.csv", rq2)
    # row-level descriptive
    desc = []
    for c in CODERS:
        cnt = Counter()
        for o, rs in lab_rows[c].items():
            for r in rs:
                cnt[(r["paradigm_family"] or "?", r["outcome_kind"], r["derived_label"])] += 1
        desc += [dict(coder=c, paradigm_family=k[0], outcome_kind=k[1], derived_label=k[2], rows=v) for k, v in sorted(cnt.items())]
    write_csv(out / "rq2-rows-by-family.csv", desc)
    unclass = {c: Counter(r["derived_label"] for rs in lab_rows[c].values() for r in rs) for c in CODERS}

    # RQ3
    n3 = [n for n in allnames if n.startswith("rq3|")]
    rq3 = side_by_side(n3)
    write_csv(out / "rq3.csv", rq3)
    hn = {}
    for c in CODERS:
        vals, vals_own, w_, w_own = [], [], [], []
        for u, wi in zip(des[c].resp, des[c].w):
            if u["order"] in feats[c]:
                v = num(u[c]["d"]["D"].get("human_n"))
                if v is not None:
                    vals.append(v)
                    w_.append(wi)
                    if low(u[c]["d"]["D"].get("primary_type")) == "own_sample":
                        vals_own.append(v)
                        w_own.append(wi)

        def wq(v, w, q):
            if not v:
                return None
            i = np.argsort(v)
            v_, w_s = np.array(v)[i], np.array(w)[i]
            cw = np.cumsum(w_s) / w_s.sum()
            return float(v_[np.searchsorted(cw, q)])

        def summ(v, w):
            if not v:
                return dict(n=0)
            return dict(n=len(v), min=min(v), q1=float(np.percentile(v, 25)), median=float(np.median(v)), q3=float(np.percentile(v, 75)),
                        max=max(v), weighted_median_point_only=wq(v, w, 0.5))
        hn[c] = dict(all_reported=summ(vals, w_), primary_type_own_sample=summ(vals_own, w_own))
    metric_freq = {}
    for c in CODERS:
        m = Counter(low(u[c]["d"]["D"].get("metric")) or "null" for u in des[c].resp if u["order"] in feats[c])
        es = Counter(low(r.get("es_metric")) or "null" for u in des[c].resp if u["order"] in feats[c]
                     for r in u[c]["d"]["E"].get("effects", []) if "outcome_kind" in r)
        metric_freq[c] = (m.most_common(25), es.most_common(25))
    (out / "rq3-human-n.json").write_text(json.dumps(hn, indent=1), encoding="utf-8")

    # RQ4
    n4 = [n for n in allnames if n.startswith("rq4|")]
    rq4 = side_by_side(n4)
    for r in rq4:
        r["display"] = ("design-based estimate per coder" if r["passes_v012_rule"] else
                        "coder-specific prevalence side by side (coder-sensitivity display, not an uncertainty interval)"
                        if r["passes_v012_rule"] is False else "agreement not available")
    write_csv(out / "rq4.csv", rq4)
    trend = []
    for c in CODERS:
        year = np.array([float(u["year"]) if u["year"] else 2024.0 for u in des[c].resp])
        for n in trend_items(n4):
            e = est[c][n]
            tr = des[c].logit_trend(e["_x"], e["_y"], year)
            info = agr_info(n)
            trend.append(dict(coder=c, feature=n, **tr,
                              status=("fitted" if tr["OR_per_year"] == tr["OR_per_year"] else "descriptive_only"),
                              agreement_field=info["agreement_field"],
                              passes_v012_rule=info["passes_v012_rule"],
                              label="sensitivity analysis (per coder; no presence or absence of a trend is claimed)"))
    write_csv(out / "rq4_trend.csv", trend)
    write_csv(out / "trend_descriptive_only.csv", [
        dict(coder=t["coder"], feature=t["feature"], n_eligible_in_domain=t["n_domain"], events=t["events"], non_events=t["non_events"],
             shortfall=" and ".join(x for x, f in (("events < 10", t["events"] < 10), ("non-events < 10", t["non_events"] < 10)) if f),
             rule="descriptive-only (v0.12.1 item 2: a trend needs >= 10 events and >= 10 non-events among eligible records)")
        for t in trend if t["status"] == "descriptive_only"])

    # ---- nonresponse
    nr = nonresponse(units, des, est, feats)
    (out / "nonresponse.md").write_text(nr["md"], encoding="utf-8")
    write_csv(out / "eligibility-estimates.csv", nr["elig_est"])
    write_csv(out / "nonresponse_bounds.csv", nr["bounds"])

    # ---- v0.12.2 descriptive additions (statistician brief 2026-10-17): paired like-for-like contrasts, zero-event bounds
    pc_rows = paired_contrasts(units, des, est, feats, agr_info)
    write_csv(out / "paired_contrasts.csv", pc_rows)
    (out / "paired_contrasts.md").write_text(paired_md(pc_rows), encoding="utf-8")
    ze_rows = zero_event_bounds(des, est)
    write_csv(out / "zero_event_bounds.csv", ze_rows)
    (out / "zero_event_bounds.md").write_text(zero_event_md(ze_rows), encoding="utf-8")

    # ---- sensitivity: merged groups versus original strata (v0.12.1 item 1)
    sens = sensitivity_merge(units, des, est, feats, names)
    write_csv(out / "sensitivity_merge.csv", sens)
    (out / "sensitivity_merge.md").write_text(sensitivity_md(sens, merge_log), encoding="utf-8")

    # ---- tidy inputs for figures
    write_fig_inputs(out, units, des, est, feats, names, agr_info, trend_items(n4))

    # ---- adjudication (v0.12.1 item 3: drawn only on request, after the final extraction)
    pool = sorted(dis, key=lambda t: (t[0][0], t[1], t[0][1]))
    if a.draw_adjudication:
        rng = random.Random(SEED)
        chosen = rng.sample(pool, min(20, len(pool)))
        arows, akey = [], {}
        for i, ((o, item), fld, vc, vx) in enumerate(chosen, 1):
            swap = rng.random() < 0.5
            A_, B_ = (vx, vc) if swap else (vc, vx)
            rid = f"ADJ{i:02d}"
            arows.append(dict(id=rid, order=o, field=fld, item=item, value_A=A_, value_B=B_,
                              source_md=next(u["md"] for u in units if u["order"] == o)))
            akey[rid] = dict(A="codex" if swap else "claude", B="claude" if swap else "codex")
        (out / "adjudication-sample.jsonl").write_text("\n".join(json.dumps(r) for r in arows) + "\n", encoding="utf-8")
        (out / "adjudication-key.json").write_text(json.dumps(dict(seed=SEED, pool_size=len(pool), mapping=akey), indent=1), encoding="utf-8")
    else:
        for f in ("adjudication-sample.jsonl", "adjudication-key.json"):
            (out / f).unlink(missing_ok=True)
        log.info("adjudication NOT drawn (use --draw-adjudication after the final extraction); pool size %d", len(pool))
    pool_by_field = Counter(t[1] for t in pool)

    # ---- prisma
    if not a.no_prisma:
        write_prisma(units)

    # ---- markdown
    write_md(out, units, des, est, feats, rq2, rq3, rq4, trend, agr_rows, agr_meta, desc, unclass, hn, metric_freq, merge_log,
             pool_by_field, cfg, elig_rows + [tot], nr)
    log.info("done")


# ----------------------------------------------------------------------------------------------------------------- v0.12.1 outputs
def trend_items(n4):
    """RQ4 features for which a per-coder year trend is considered (unchanged selection rule)."""
    out_ = []
    for n in n4:
        keep = n.endswith("|yes") or n.split("|")[1] in ("perturbation", "robustness_outcome_among_tested")
        if not keep or n.endswith("none_listed") or n.endswith("|not_reported"):
            continue
        out_.append(n)
    return out_


def _pct(v):
    return round(100 * v, 3) if isinstance(v, float) and v == v else None


def sensitivity_merge(units, des, est, feats, names):
    """Main estimates under the merged groups versus the original strata (limited comparison, see module docstring)."""
    rows = []
    sel = ["ELIGIBLE_SHARE"] + [n for n in names if (n.startswith("rq2|") and n.endswith("|ANY")) or n.startswith("rq4|")]
    for c in CODERS:
        d_m = des[c]
        d_o = Design(units, c, [], merge=False)
        info = dict(strata_original=len(d_o.gids), groups_merged=len(d_m.gids),
                    orig_strata_one_respondent_no_variance=len(d_o.n_var_dropped),
                    orig_strata_zero_respondents_outside_point_estimate=len(d_o.n_no_resp),
                    orig_frame_N_in_point_estimate=d_o.Ntot_est, frame_N=d_o.Ntot, df_merged=d_m.df, df_original=d_o.df)
        x_el = np.array([1.0 if u["order"] in feats[c] else 0.0 for u in d_m.resp])
        e_m_share, e_o_share = d_m.share_of_frame(x_el), d_o.share_of_frame(x_el)
        est_o = estimate_all(units, c, d_o, feats[c], [n for n in sel if n != "ELIGIBLE_SHARE"])
        for n in sel:
            if n == "ELIGIBLE_SHARE":
                em = dict(e_m_share, n_domain=len(d_m.resp), k=int(x_el.sum()))
                eo = dict(e_o_share, n_domain=len(d_m.resp), k=int(x_el.sum()))
                estimand = "eligible share of frame"
            else:
                em, eo = est[c][n], est_o[n]
                estimand = "RQ2 any row by outcome kind" if n.startswith("rq2|") else "RQ4 item prevalence among eligible"
            width_m = em["hi"] - em["lo"] if em["est"] == em["est"] else float("nan")
            width_o = eo["hi"] - eo["lo"] if eo["est"] == eo["est"] else float("nan")
            both = em["est"] == em["est"] and eo["est"] == eo["est"]
            rows.append(dict(coder=c, estimand=estimand, feature=n, n_domain=em["n_domain"], k=em["k"],
                             merged_est_pct=_pct(em["est"]), merged_lo_pct=_pct(em["lo"]), merged_hi_pct=_pct(em["hi"]),
                             merged_df=d_m.df,
                             limited_comparison_orig_est_pct=_pct(eo["est"]), limited_comparison_orig_lo_pct=_pct(eo["lo"]),
                             limited_comparison_orig_hi_pct=_pct(eo["hi"]), limited_comparison_orig_df=d_o.df,
                             diff_est_pct_points=_pct(em["est"] - eo["est"]) if both else None,
                             ci_width_ratio_merged_over_orig=(round(width_m / width_o, 3) if width_o == width_o and width_m == width_m and width_o > 0 else None),
                             **info))
    return rows


def sensitivity_md(sens, merge_log):
    md = ["# Sensitivity: merged groups versus original strata (amendment v0.12.1 item 1)\n",
          "Merged = the main analysis (strata with fewer than 2 respondents merged with the same family's adjacent period, later first; "
          "weights N_g / r_g and variance on the merged groups). Original = the 32 sampling strata as drawn. The original-strata columns "
          "are a LIMITED COMPARISON: a stratum with exactly 1 respondent carries its weight N_h / 1 in the point estimate but contributes "
          "no variance term (dropped from the variance only); a stratum with 0 respondents has no weight and is left out of the point "
          "estimate and of the frame denominator (so the original eligible share refers to the frame minus those strata). The original "
          "intervals therefore understate the variance and are not a validated alternative.\n",
          "\n## Merged strata\n\n" + md_table(merge_log, ["coder", "merged", "into", "reason", "a", "r"])]
    for c in CODERS:
        r0 = next(r for r in sens if r["coder"] == c)
        md.append(f"\n{c}: {r0['strata_original']} original strata, {r0['groups_merged']} merged groups; original strata with 1 respondent "
                  f"(no variance term): {r0['orig_strata_one_respondent_no_variance']}; with 0 respondents (outside the point estimate): "
                  f"{r0['orig_strata_zero_respondents_outside_point_estimate']}; frame covered by the original point estimate "
                  f"{r0['orig_frame_N_in_point_estimate']} of {r0['frame_N']}; df merged {r0['df_merged']}, original {r0['df_original']}.\n")
    keys = ["coder", "estimand", "feature", "k", "n_domain", "merged_est_pct", "merged_lo_pct", "merged_hi_pct", "limited_comparison_orig_est_pct",
            "limited_comparison_orig_lo_pct", "limited_comparison_orig_hi_pct", "diff_est_pct_points", "ci_width_ratio_merged_over_orig"]
    head = [r for r in sens if r["estimand"] != "RQ4 item prevalence among eligible" or r["feature"].endswith("|yes")
            or r["feature"].startswith("rq4|robustness_tested")]
    md.append("\n## Main estimates (percent); all RQ4 features are in sensitivity_merge.csv\n\n" + md_table(head, keys))
    return "\n".join(md)


def write_fig_inputs(out, units, des, est, feats, names, agr_info, trend_names):
    fd = out / "fig_inputs"
    fd.mkdir(exist_ok=True)

    def long_row(c, n, **extra):
        e = est[c][n]
        zero = e["cp_lo"] == e["cp_lo"]
        info = agr_info(n)
        return dict(**extra, coder=c, weighted_pct=_pct(e["est"]),
                    ci_lo_pct=_pct(e["cp_lo"] if zero else e["lo"]), ci_hi_pct=_pct(e["cp_hi"] if zero else e["hi"]),
                    ci_method=("exact unweighted Clopper-Pearson (zero-variance estimate)" if zero else "design-based t, linearised, merged groups"),
                    k=e["k"], denominator=e["n_domain"], passes_agreement=info["passes_v012_rule"], agreement_field=info["agreement_field"],
                    kappa=info["kappa"], percent_agreement=info["percent_agreement"], rule_basis=info["rule_basis"])

    n4 = [n for n in names if n.startswith("rq4|")]
    write_csv(fd / "rq4_items_by_coder.csv", [long_row(c, n, item=n.replace("rq4|", "")) for n in n4 for c in CODERS])
    r2 = []
    for n in names:
        if not n.startswith("rq2|"):
            continue
        _, kind, lab = n.split("|")
        for c in CODERS:
            r2.append(long_row(c, n, outcome_kind=kind, derived_label=lab))
    r2.sort(key=lambda r: (KINDS.index(r["outcome_kind"]), r["derived_label"] != "ANY", r["derived_label"], r["coder"]))
    write_csv(fd / "rq2_labels.csv", r2)
    r3 = []
    for n in names:
        p = n.split("|")
        if p[0] == "rq3" and p[1] in ("types_any", "primary_type"):
            for c in CODERS:
                r3.append(long_row(c, n, comparison_basis=p[1], comparison_type=p[2]))
    write_csv(fd / "rq3_comparisons.csv", r3)
    # RQ4 items by paradigm family: Claude, unweighted; a study counts in every family it lists in C.paradigms
    c = "claude"
    fam_of = {}
    for u in units:
        o = u["order"]
        if o in feats[c]:
            fam_of[o] = sorted({p.get("family") for p in u[c]["d"].get("C", {}).get("paradigms", []) if p.get("family")}) or ["none_listed"]
    rows = []
    for n in n4:
        for fam in sorted({f for fs in fam_of.values() for f in fs}):
            os_ = [o for o, fs in fam_of.items() if fam in fs and n not in feats[c][o][1]]
            k = sum(n in feats[c][o][0] for o in os_)
            lo, hi = wilson(k, len(os_))
            rows.append(dict(item=n.replace("rq4|", ""), paradigm_family=fam, coder=c, k=k, n=len(os_),
                             share=round(k / len(os_), 4) if os_ else None,
                             wilson_lo=None if lo != lo else round(lo, 4), wilson_hi=None if hi != hi else round(hi, 4),
                             basis="unweighted; eligible Claude studies listing the family in C.paradigms (a study with several families "
                                   "counts in each, so shares are not additive across families)"))
    write_csv(fd / "rq4_items_by_family.csv", rows)
    tr = []
    for c in CODERS:
        d = des[c]
        year = np.array([int(u["year"]) if u["year"] else 2024 for u in d.resp])
        for n in trend_names:
            e = est[c][n]
            dom = e["_x"] > 0
            ev_tot = int(e["_y"][dom].sum())
            ne_tot = int(dom.sum()) - ev_tot
            for y in sorted(set(year[dom])):
                m = dom & (year == y)
                tr.append(dict(year=int(y), item=n.replace("rq4|", ""), coder=c, n_eligible=int(m.sum()), n_yes=int(e["_y"][m].sum()),
                               item_events_all_years=ev_tot, item_non_events_all_years=ne_tot,
                               descriptive_only=bool(ev_tot < 10 or ne_tot < 10)))
    write_csv(fd / "rq4_trend.csv", tr)


# ----------------------------------------------------------------------------------------------------------------- nonresponse
def perm_p(cats, resp, B=5000, seed=SEED):
    """Monte-Carlo permutation p for association between category and respondent status (secondary, not a headline)."""
    cats = np.array(cats)
    resp = np.array(resp, dtype=int)
    lv = sorted(set(cats))
    if len(lv) < 2 or resp.min() == resp.max():
        return float("nan")

    def stat(rv):
        s = 0.0
        pr = rv.mean()
        for l in lv:
            m = cats == l
            n = m.sum()
            s += n * (rv[m].mean() - pr) ** 2
        return s
    obs = stat(resp)
    rg = np.random.default_rng(seed)
    cnt = sum(stat(rg.permutation(resp)) >= obs - 1e-12 for _ in range(B))
    return (cnt + 1) / (B + 1)


def nonresponse(units, des, est, feats):
    md = ["# Nonresponse (protocol v0.9.1): respondents vs nonrespondents\n",
          "Respondent = full text obtained (open copy now; eGateway copies will be added on rerun). Nonrespondent = no full text. "
          "Interim run. Response rates are unweighted counts with Wilson 95% intervals; the permutation p-value (5,000 permutations, "
          "seed 20261016) is a secondary descriptive column, not a result.\n"]
    ytxt = lambda y: "<=2023" if y is None or y <= 2023 else str(y)  # noqa: E731
    dims = {"flag (RQ1 abstract coder)": lambda u: u["flag"], "paradigm family (stratum)": lambda u: u["family"],
            "year": lambda u: ytxt(u["year"]), "venue type (OpenAlex type)": lambda u: u["vtype"]}
    for name, fn in dims.items():
        cats = sorted({fn(u) for u in units})
        rows = []
        for cat in cats:
            us = [u for u in units if fn(u) == cat]
            k = sum(u["ft"] for u in us)
            lo, hi = wilson(k, len(us))
            rows.append({name: cat, "analysed": len(us), "respondents (full text)": k, "nonrespondents": len(us) - k,
                         "response %": f"{100 * k / len(us):.1f}", "Wilson 95% (%)": f"{100 * lo:.1f} to {100 * hi:.1f}"})
        p = perm_p([fn(u) for u in units], [u["ft"] for u in units])
        md.append(f"\n## By {name}\n\n" + md_table(rows) + f"\nPermutation p (secondary): {p:.3f}\n")
    # eligible share and bounds
    elig_est, b_rows, b_num = [], [], []
    for c in CODERS:
        d = des[c]
        x = np.array([1.0 if u["order"] in feats[c] else 0.0 for u in d.resp])
        sh = d.share_of_frame(x)
        wa = {u["order"]: u["N"] / d.a[u["stratum"]] for u in units}
        S_x = sum(wa[u["order"]] for u in units if u["order"] in feats[c])
        M = sum(wa[u["order"]] for u in units if not (u[c]["resp"]))
        Ntot = d.Ntot
        n_unknown = sum(not u[c]["resp"] for u in units)
        elig_est.append(dict(coder=c, n_analysed=len(units), n_respondents=len(d.resp), n_eligible_respondents=int(x.sum()),
                             n_unknown_status=n_unknown, est_share_of_frame_pct=round(100 * sh["est"], 2),
                             lo_pct=round(100 * sh["lo"], 2), hi_pct=round(100 * sh["hi"], 2),
                             N_hat_eligible=round(sh["N_hat"], 1), frame_N=Ntot,
                             bound_all_unknown_ineligible_pct=round(100 * S_x / Ntot, 2),
                             bound_all_unknown_eligible_pct=round(100 * (S_x + M) / Ntot, 2)))
        # prevalence bounds
        for n in [m for m in est[c] if m.startswith(("rq3|", "rq4|"))]:  # every RQ3 and RQ4 row of rq3.csv / rq4.csv
            e = est[c][n]
            S_y = sum(wa[u["order"]] for u in d.resp if u["order"] in feats[c]
                      and _in_dom_on(feats[c][u["order"]], n))
            S_xx = sum(wa[u["order"]] for u in d.resp if u["order"] in feats[c] and n not in feats[c][u["order"]][1])
            if n.startswith("rq4|f6_applicable"):
                pass
            if S_xx <= 0:
                continue
            p_in = S_y / S_xx
            lo, hi = S_y / (S_xx + M), (S_y + M) / (S_xx + M)
            b_rows.append(dict(coder=c, feature=n, n_domain=e["n_domain"], k=e["k"],
                               est_pct=f"{100 * e['est']:.1f}", all_unknown_ineligible_pct=f"{100 * p_in:.1f}",
                               all_unknown_eligible_none_have_outcome_pct=f"{100 * lo:.1f}",
                               all_unknown_eligible_all_have_outcome_pct=f"{100 * hi:.1f}",
                               overall_bounds_pct=f"{100 * min(lo, p_in):.1f} to {100 * max(hi, p_in):.1f}"))
            b_num.append(dict(coder=c, feature=n, n_domain=e["n_domain"], k=e["k"], est_pct=100 * e["est"],
                              p_all_unknown_ineligible_pct=100 * p_in, p_all_unknown_eligible_none_pct=100 * lo,
                              p_all_unknown_eligible_all_pct=100 * hi, bound_lo_pct=100 * min(lo, p_in),
                              bound_hi_pct=100 * max(hi, p_in), sum_w_domain_observed=S_xx, sum_w_unknown=M))
    md.append("\n## Pending and unresolved records (interim)\n\n" + md_table(
        [dict(coder=c, **{k: v for k, v in Counter(u[c]["state"] for u in units).items()}) for c in CODERS]) +
        "\nIn this interim run records with a full text but no usable extraction (pending_extraction) and records with an unresolved "
        "eligibility decision (coded_unclear) are treated like nonrespondents (their weight is redistributed within stratum; "
        "they enter the bounds as unknown).\n")
    md.append("\n## Eligible share of the frame (2,022 liberal-eligible records)\n\n" + md_table(elig_est))
    md.append("\nPoint estimate: design-weighted with within-stratum response-propensity weights (N_g / r_g). Bounds: unadjusted "
              "sampling weights N_h / n_analysed_h; lower = every unknown-status analysed record ineligible, upper = every one eligible.\n")
    md.append("\n## Bounds on prevalences among eligible studies (every RQ3 and RQ4 row: items, perturbation types, comparison types, robustness outcomes)\n\n"
              "Scenario A: all unknown-status records ineligible (prevalence among observed eligible, sampling weights only). "
              "Scenario B: all unknown-status records eligible, with none / all of them having the outcome. "
              "Overall bounds are the minimum and maximum of the three.\n\n" + md_table(b_rows))
    return dict(md="\n".join(md), elig_est=elig_est, bounds=b_num)


# ----------------------------------------------------------------------------------------------------------------- paired contrasts
# DESCRIPTIVE ONLY. Fixed by the statistician brief of 2026-10-17 before any paired result was computed (red-team F1 and the framework
# v2 "unresolved" list). Like-for-like means both items are of the same kind: both VARIED (F.perturbations_tested, or the item-based
# f5 and f7 that ask whether a variation was done) or both REPORTED (f1, f2, f4: a statement is present). Prevalences are over the same
# eligible studies, so the difference is paired. No hypothesis test is made (none was prespecified).
PAIRS = [
    ("varied", "rq4|perturbation|wording", "rq4|perturbation|decoding", "wording vs decoding"),
    ("varied", "rq4|perturbation|wording", "rq4|perturbation|option_order", "wording vs option order"),
    ("varied", "rq4|perturbation|wording", "rq4|perturbation|seeds", "wording vs seeds"),
    ("varied", "rq4|perturbation|wording", "rq4|perturbation|model_version", "wording vs model version"),
    ("reported", "rq4|f2|yes", "rq4|f4|yes", "f2 decoding stated vs f4 prompts published"),
    ("reported", "rq4|f1|yes", "rq4|f2|yes", "f1 model version stated vs f2 decoding stated"),
    ("varied_supplementary", "rq4|f5|yes", "rq4|f7|yes", "f5 wordings compared vs f7 sampling settings compared"),
]


def paired_contrasts(units, des, est, feats, agr_info):
    rows = []
    for c in CODERS:
        d = des[c]
        wa = {u["order"]: u["N"] / d.a[u["stratum"]] for u in units}
        M = sum(wa[u["order"]] for u in units if not u[c]["resp"])
        for kind, A, B, label in PAIRS:
            ea, eb = est[c][A], est[c][B]
            x = ea["_x"] * eb["_x"]
            ya, yb = ea["_y"] * x, eb["_y"] * x
            pc = d.paired(x, ya, yb)
            m = x > 0
            both = int(((ya > 0) & (yb > 0)).sum())
            only_a, only_b = int(((ya > 0) & (yb == 0)).sum()), int(((ya == 0) & (yb > 0)).sum())
            neither = int(m.sum()) - both - only_a - only_b
            # nonresponse bounds on the paired difference (v0.9.1 logic, sampling weights): unknown-status records all ineligible,
            # or all eligible with (A yes, B no) / (A no, B yes)
            wv = np.array([wa[u["order"]] for u in d.resp])
            S_x, S_d = float((wv * x).sum()), float((wv * (ya - yb)).sum())
            p_in = S_d / S_x if S_x > 0 else float("nan")
            b_lo, b_hi = (S_d - M) / (S_x + M), (S_d + M) / (S_x + M)
            ia, ib = agr_info(A), agr_info(B)
            both_pass = bool(ia["passes_v012_rule"]) and bool(ib["passes_v012_rule"])
            rows.append(dict(
                kind=kind, contrast=label, item_a=A.replace("rq4|", ""), item_b=B.replace("rq4|", ""), coder=c,
                n_domain=int(m.sum()), n_both=both, n_a_only=only_a, n_b_only=only_b, n_neither=neither,
                a_est_pct=_pct(ea["est"]), b_est_pct=_pct(eb["est"]), diff_a_minus_b_pct_points=_pct(pc["est"]),
                diff_lo_pct=_pct(pc["lo"]), diff_hi_pct=_pct(pc["hi"]), diff_se_pct=_pct(pc["se"]), df=d.df,
                interval_excludes_zero=bool(pc["lo"] > 0 or pc["hi"] < 0),
                nr_bound_lo_pct=_pct(min(b_lo, p_in)), nr_bound_hi_pct=_pct(max(b_hi, p_in)),
                kappa_a=ia["kappa"], pass_a=ia["passes_v012_rule"], kappa_b=ib["kappa"], pass_b=ib["passes_v012_rule"],
                both_items_pass_v012_rule=both_pass,
                label="descriptive; paired difference over the same eligible studies; design-based t interval (linearised, merged groups); "
                      "no hypothesis test (none prespecified); nonresponse bounds are worst-case (every unknown-status record eligible "
                      "with the extreme pair pattern)"))
    return rows


def paired_md(rows):
    md = ["# Like-for-like paired contrasts (DESCRIPTIVE; red-team F1, framework v2 unresolved list)\n",
          "Difference = item A minus item B, in percentage points of eligible studies, over the SAME eligible studies (paired). Design-based: "
          "ratio estimator of stratified totals, Taylor linearised variance with collapsed merged groups and finite-population correction, "
          "t interval with the run's df (same machinery as every other estimate in this run). The interval states the precision of the "
          "paired difference; it is not a test and no hypothesis was prespecified. VARIED = the study varied that perturbation "
          "(F.perturbations_tested); REPORTED = the study states the information. Rows of kind `varied_supplementary` are item-based "
          "(f5, f7) and added as a cross-check of the perturbation-list contrasts.\n",
          "`both_items_pass_v012_rule` = both underlying fields passed the v0.12 inter-coder rule; where False, read the two coders as a "
          "coder-sensitivity display. Nonresponse bounds are the extreme values of the difference if every unknown-status record were "
          "ineligible, or eligible with an extreme pair pattern (A yes and B no; A no and B yes): they are wide by construction.\n"]
    cols = ["kind", "contrast", "coder", "n_domain", "n_both", "n_a_only", "n_b_only", "a_est_pct", "b_est_pct",
            "diff_a_minus_b_pct_points", "diff_lo_pct", "diff_hi_pct", "nr_bound_lo_pct", "nr_bound_hi_pct", "both_items_pass_v012_rule"]
    t = []
    for r in rows:
        r2 = {k: r[k] for k in cols}
        for k in ("a_est_pct", "b_est_pct", "diff_a_minus_b_pct_points", "diff_lo_pct", "diff_hi_pct", "nr_bound_lo_pct", "nr_bound_hi_pct"):
            r2[k] = f"{r[k]:.1f}"
        t.append(r2)
    md.append(md_table(t, cols))
    return "\n".join(md)


# ----------------------------------------------------------------------------------------------------------------- zero-event bounds
def zero_event_bounds(des, est):
    """Exact (Clopper-Pearson, two-sided 95%, UNWEIGHTED) upper bound for every feature with zero events among eligible studies.
    Sensitivity: the same bound with n replaced by the Kish effective sample size of the domain weights (the weights are unequal, so
    the unweighted n is optimistic); an approximation, not an exact design-based interval."""
    rows = []
    for c in CODERS:
        d = des[c]
        for n, e in est[c].items():
            nd, k = e["n_domain"], e["k"]
            if nd == 0 or k != 0:
                continue
            wd = d.w * (e["_x"] > 0)
            neff = float(wd.sum() ** 2 / (wd ** 2).sum())
            lo, hi = clopper(0, nd)
            rows.append(dict(coder=c, feature=n, n_domain=nd, events=0, upper_cp_pct=_pct(hi), rule_of_three_pct=_pct(3 / nd),
                             n_eff_kish=round(neff, 1), upper_cp_neff_pct=_pct(1 - 0.025 ** (1 / neff)),
                             design_based_est_pct=_pct(e["est"]), design_based_ci_hi_pct=_pct(e["hi"]),
                             note="design-based linearised interval is degenerate [0, 0] at zero events; use the exact bound"))
    rows.sort(key=lambda r: (r["feature"], r["coder"]))
    return rows


def zero_event_md(rows):
    md = ["# Exact upper bounds for prevalences with zero events among eligible studies\n",
          "Clopper-Pearson two-sided 95% upper limit = 1 - 0.025^(1/n), UNWEIGHTED (n = eligible studies in the domain). Column "
          "`upper_cp_neff_pct` repeats it with n replaced by the Kish effective sample size of the design weights (an approximation that "
          "allows for unequal weights; a sensitivity, not an exact design-based interval). The design-based linearised interval is [0, 0] "
          "when no study has the feature, so it must not be read as certainty of absence.\n",
          md_table(rows, ["coder", "feature", "n_domain", "events", "upper_cp_pct", "rule_of_three_pct", "n_eff_kish", "upper_cp_neff_pct"])]
    return "\n".join(md)


def _in_dom_on(fe, n):
    on, off = fe
    return n in on and n not in off


# ----------------------------------------------------------------------------------------------------------------- PRISMA
def write_prisma(units):
    p = ROOT / "data/processed/prisma-fulltext.json"
    cur = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    c = "claude"
    coded = [u for u in units if u[c]["state"].startswith("coded")]
    reasons = Counter(u[c]["failed"] or "other" for u in coded if u[c]["elig"] == "NO")
    cur.update({
        "fulltext_sought": len(units),
        "fulltext_assessed": len(coded),
        "fulltext_not_retrievable": sum(not u["ft"] for u in units),
        "excluded_fulltext_total": sum(reasons.values()),
        "excluded_fulltext_reasons": dict(sorted(reasons.items())),
        "included_rq2_rq4": sum(u[c]["elig"] == "YES" for u in coded),
        "fulltext_pending_assessment": sum(u[c]["state"] == "pending_extraction" for u in units),
        "fulltext_unresolved_unclear": sum(u[c]["state"] == "coded_unclear" for u in units),
        "interim": not FINAL,
        "_interim_note": "Claude primary coder, eligibility from the Claude extraction; orders 17 and 54 counted as excluded "
                         "(abstract-only, E5) pending human confirmation; 67 and 120 keep the extractor's decision, flagged. "
                         "Written by analysis/fulltext/rq234_analysis.py; rerun to update.",
    })
    p.write_text(json.dumps(cur, indent=1), encoding="utf-8")


# ----------------------------------------------------------------------------------------------------------------- markdown
def write_md(out, units, des, est, feats, rq2, rq3, rq4, trend, agr_rows, agr_meta, desc, unclass, hn, metric_freq, merge_log,
             pool_by_field, cfg, elig_rows, nr):
    def cell(r, c):
        if f"{c}_est_pct" not in r or r.get(f"{c}_est_pct") is None:
            return "NA"
        lo, hi = r[f"{c}_lo_pct"], r[f"{c}_hi_pct"]
        s = f"{r[f'{c}_est_pct']:.1f} ({'NA' if lo is None else f'{lo:.1f}'} to {'NA' if hi is None else f'{hi:.1f}'})"
        return s + (" *" if r.get(f"{c}_note") else "")

    def den(r, c):
        return f"{r.get(f'{c}_k', '')}/{r.get(f'{c}_n_domain', '')}"

    def pf(r):
        v = r.get("passes_v012_rule")
        return "NA" if v is None else ("pass" if v else "FAIL")

    head = ("Design-weighted domain estimates (percent of eligible studies; 95% t-interval, linearised stratified variance on merged "
            "strata; * = zero-variance estimate, see csv for exact unweighted interval). k/n = unweighted studies with the feature / "
            "unweighted eligible respondents. Interim run.\n")
    for c in CODERS:
        pass
    sizes = "; ".join(f"{c}: {len(des[c].resp)} respondents, {int(sum(1 for u in des[c].resp if u['order'] in feats[c]))} eligible, "
                      f"{len(des[c].gids)} estimation groups, df {des[c].df}" for c in CODERS)
    # rq2
    t2 = []
    for r in rq2:
        t2.append({"kind": r["outcome_kind"], "label": r["label"], "Claude % (95% CI)": cell(r, "claude"), "Claude k/n": den(r, "claude"),
                   "Codex % (95% CI)": cell(r, "codex"), "Codex k/n": den(r, "codex")})
    ak = lambda f: next((a for a in agr_rows if a["field"] == f), {})  # noqa: E731
    md = [f"# RQ2 (interim): share of eligible studies with at least one row of each derived label\n\n{head}\n{sizes}\n",
          "Outcome kinds are reported separately and never pooled (amendment v0.11). `ANY` = at least one row of that kind. Labels are "
          "derived by `derive_labels.derive`; UNCLASSIFIED-* are the script's explicit non-label codes. Full-sample agreement of the "
          f"fields behind these rows: E.outcome_kind kappa {ak('E.outcome_kind').get('kappa')} / {ak('E.outcome_kind').get('percent_agreement')}% "
          f"({pf(ak('E.outcome_kind'))}); E.derived_label (script) kappa {ak('E.derived_label (script)').get('kappa')} / "
          f"{ak('E.derived_label (script)').get('percent_agreement')}% ({pf(ak('E.derived_label (script)'))}), on matched "
          f"(paradigm family x model family) keys.\n\n",
          md_table(t2)]
    md.append("\n## Rows by paradigm family x derived label (unweighted row counts, descriptive; family = coder's family of the paradigm)\n")
    for c in CODERS:
        for kind in KINDS:
            dd = [x for x in desc if x["coder"] == c and x["outcome_kind"] == kind]
            if not dd:
                md.append(f"\n{c} / {kind}: no rows\n")
                continue
            labs = sorted({x["derived_label"] for x in dd})
            fams = sorted({x["paradigm_family"] for x in dd})
            tab = []
            for f in fams:
                row = {"family": f}
                for l in labs:
                    row[l] = sum(x["rows"] for x in dd if x["paradigm_family"] == f and x["derived_label"] == l) or ""
                row["total rows"] = sum(x["rows"] for x in dd if x["paradigm_family"] == f)
                tab.append(row)
            md.append(f"\n**{c} / {kind}** ({sum(x['rows'] for x in dd)} rows)\n\n" + md_table(tab))
    (out / "rq2.md").write_text("\n".join(md), encoding="utf-8")

    # rq3
    t3 = [{"feature": r["feature"].replace("rq3|", ""), "Claude % (95% CI)": cell(r, "claude"), "Claude k/n": den(r, "claude"),
           "Codex % (95% CI)": cell(r, "codex"), "Codex k/n": den(r, "codex"), "kappa": r["kappa"], "agree %": r["percent_agreement"],
           "rule": pf(r)} for r in rq3]
    md = [f"# RQ3 (interim): human comparison types, human sample sizes, metrics\n\n{head}\n{sizes}\n",
          "`types_any` = share of eligible studies listing the type among D.types (a study can list several); `primary_type` = the "
          "type the main results rest on; `human_n|reported` = a numeric human_n is given; `outcome_types` = E.outcome_types.\n\n",
          md_table(t3), "\n## human_n (participants), unweighted summary among eligible studies reporting it; weighted median is a point value only\n\n"]
    hrows = []
    for c in CODERS:
        for k, v in hn[c].items():
            hrows.append({"coder": c, "subset": k, **{kk: (round(vv, 1) if isinstance(vv, float) else vv) for kk, vv in v.items()}})
    md.append(md_table(hrows))
    for c in CODERS:
        md.append(f"\n### {c}: D.metric strings (lower-cased, unweighted counts among eligible respondents; top 25)\n\n"
                  + md_table([{"metric": k, "studies": v} for k, v in metric_freq[c][0]]))
        md.append(f"\n### {c}: es_metric strings on v1.1 effect rows (unweighted rows; top 25)\n\n"
                  + md_table([{"es_metric": k, "rows": v} for k, v in metric_freq[c][1]]))
    (out / "rq3.md").write_text("\n".join(md), encoding="utf-8")

    # rq4
    t4 = [{"feature": r["feature"].replace("rq4|", ""), "Claude % (95% CI)": cell(r, "claude"), "Claude k/n": den(r, "claude"),
           "Codex % (95% CI)": cell(r, "codex"), "Codex k/n": den(r, "codex"), "kappa": r["kappa"], "agree %": r["percent_agreement"],
           "n pairs": r["n_agreement"], "rule": pf(r)} for r in rq4]
    md = [f"# RQ4 (interim): reporting items and robustness checks\n\n{head}\n{sizes}\n",
          "For fields that FAIL the full-sample rule the two coder columns are a coder-sensitivity display, explicitly not an "
          "uncertainty interval (amendment v0.12 item 4). `f6_applicable` = f6 yes among studies with f6 not na; "
          "`robustness_outcome_among_tested` has only studies with robustness_outcome not na as denominator; `robustness_tested` "
          "= robustness_outcome not na (derived here as the headline of the six-type robustness judgement).\n\n", md_table(t4)]
    tt = [{"coder": r["coder"], "feature": r["feature"].replace("rq4|", ""), "n": r["n_domain"], "events": r["events"],
           "OR per year (95% CI)": ("NA" if r["OR_per_year"] != r["OR_per_year"] else
                                    f"{r['OR_per_year']:.2f} ({r['or_lo']:.2f} to {r['or_hi']:.2f})"),
           "note": r["note"], "field rule": ("pass" if r["passes_v012_rule"] else "FAIL" if r["passes_v012_rule"] is False else "NA")}
          for r in trend]
    md.append("\n## Year trends: design-weighted logistic regression of the item on publication year (odds ratio per year), "
              "per coder. SENSITIVITY ANALYSIS: neither the presence nor the absence of a trend is claimed. Needs at least 10 events "
              "and 10 non-events in the domain; sandwich variance on merged strata; t interval.\n\n" + md_table(tt))
    (out / "rq4.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
