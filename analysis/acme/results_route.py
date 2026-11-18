"""Shared loaders for the route-table exhibits of Section 7 (Figs shares, agreement, yardsticks; Tables results-cr, results-num, s-routes, s-sens).

Reads only files under runs/ (through results_common.Tracker, so each input is hashed into <output>.source.json):
  runs/acme-gstudy/route-table/{route_table,sens_table,hypotheses_estimates}.csv      (analysis/acme/route_table.py, route_hypotheses.py)
  runs/acme-S-gstudy/{route-a,route-e-armS,sens-S-*}/components_<item>.csv            per-wording (leave-one-wording-out) values of Arm S
  runs/acme-gstudy/A1-route-e-armL/lowo.csv                                           per-wording values of (e)-Arm L
  runs/acme-gstudy/A1-route-{b-pertype,c-permodel}/yardsticks.csv, runs/acme-S-gstudy/route-a-yardsticks/{raw,drawcorr}/yardsticks.csv
  runs/acme-L/rosters.csv ; runs/human-ml1-acme/arml_scales.csv (item order)
Nothing numeric is typed here except the interpretation rule BIAS_RULE (E7a item 3, a rule and not a result).

Component groups.  The 15 variance terms of the four-facet decomposition are partitioned into the groups below.  Shares are fractions of one
total, so a group share is the sum of its terms.  A group of several terms has no frozen Arm L interval (gstudy.py gives intervals per term and
no bootstrap draws are stored), so Arm L marks of summed groups are points; the leave-one-wording-out range of a sum is the min and max over the
dropped wordings of the summed per-wording values (Arm S components files and lowo.csv carry them).
"""
from __future__ import annotations

import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402

ROOT = rc.ROOT
ROUTE = ROOT / "runs" / "acme-gstudy" / "route-table"
S_DIR = ROOT / "runs" / "acme-S-gstudy"
L_DIR = ROOT / "runs" / "acme-gstudy"
ARMS_DIR = {"(a)": S_DIR / "route-a", "(e)-ArmS": S_DIR / "route-e-armS"}
BIAS_RULE = 0.06          # E7a item 3: differences below this are not interpreted in the four-wording arrays (rule, not a result)
CR_ITEMS = ["P1", "P3", "AF", "QA", "NR"]            # choice and rating items (order of arml_scales.csv)
NUM_ITEMS = ["P2a", "P2b", "P2c", "P2d", "P4"]       # numeric items
TERM_ORDER = ["M", "O", "T", "MO", "MT", "OT", "MOT", "W", "MW", "WO", "WT", "MWO", "MWT", "WOT", "res", "draw"]
RES_NAMES = {"res", "res (remainder)"}


def canon(term: str) -> str:
    return "res" if term in RES_NAMES else term


# (key, label for text, label for tables, member test, short axis title)
GROUPS = [
    ("M", "M", "M", lambda t: t == "M"),
    ("O", "O, M×O", r"O, M$\times$O", lambda t: t in ("O", "MO")),
    ("W", "W", "W", lambda t: t == "W"),
    ("MW", "M×W", r"M$\times$W", lambda t: t == "MW"),
    ("WO", "W×O, M×W×O", r"W$\times$O, M$\times$W$\times$O", lambda t: t in ("WO", "MWO")),
    ("T", "T terms", "T terms", lambda t: "T" in t),
    ("res", "Residual", "Residual", lambda t: t == "res"),
    ("draw", "Draw", "Draw", lambda t: t == "draw"),
]
GROUP_KEYS = [g[0] for g in GROUPS]
GROUP_LABEL = {g[0]: g[1] for g in GROUPS}
GROUP_TEX = {g[0]: g[2] for g in GROUPS}
GROUP_TEST = {g[0]: g[3] for g in GROUPS}


def group_of(term: str) -> str:
    t = canon(term)
    hit = [k for k in GROUP_KEYS if GROUP_TEST[k](t)]
    assert len(hit) == 1, f"term {term!r} falls in {hit} groups (must be exactly one)"
    return hit[0]


for _t in TERM_ORDER:
    group_of(_t)       # the partition is exhaustive and disjoint over all terms


# ------------------------------------------------------------------------------------------------------------------ formatting
def fx(x: float, nd: int = 2) -> str:
    """Fixed decimals, half up, from the shortest repr (same rule as make_autonumbers._fx); a negative that rounds to zero loses its sign."""
    s = str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
    if float(s) == 0.0:
        s = s.lstrip("-")
    return s


def tx(x: float, nd: int = 2) -> str:
    """LaTeX number with a math minus."""
    s = fx(x, nd)
    return f"$-{s[1:]}$" if s.startswith("-") else s


def tex_escape(s: str) -> str:
    return s.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


# ------------------------------------------------------------------------------------------------------------------ loaders
class Route:
    """Route table, sensitivity table and hypotheses estimates, plus the per-wording files for the sums of Arm S and (e)-Arm L."""

    def __init__(self, tr: rc.Tracker) -> None:
        self.tr = tr
        self.rt = tr.csv(ROUTE / "route_table.csv", dtype={"item": str, "component": str, "column": str, "basis": str, "analysis": str})
        self.st = tr.csv(ROUTE / "sens_table.csv", dtype={"item": str, "component": str, "column": str, "basis": str, "sens": str})
        self.hy = tr.csv(ROUTE / "hypotheses_estimates.csv", dtype={"column": str, "hypothesis": str, "basis": str, "item_set": str})
        self._armS: dict[tuple[Path, str], pd.DataFrame] = {}
        self._lowoL: pd.DataFrame | None = None

    # ----- per-wording sources
    def comps_S(self, d: Path, item: str) -> pd.DataFrame:
        k = (d, item)
        if k not in self._armS:
            df = self.tr.csv(d / f"components_{item}.csv", dtype={"term": str})
            df["term"] = df["term"].map(canon)
            self._armS[k] = df.set_index("term")
        return self._armS[k]

    def lowo_L(self) -> pd.DataFrame:
        if self._lowoL is None:
            df = self.tr.csv(L_DIR / "A1-route-e-armL" / "lowo.csv", dtype={"item": str, "term": str})
            df["term"] = df["term"].map(canon)
            self._lowoL = df
        return self._lowoL

    # ----- one route column of one item -> group dict
    def info(self, column: str, item: str) -> dict:
        x = self.rt[(self.rt["column"] == column) & (self.rt["item"] == item)]
        if x.empty:
            return dict(decomposed=False, n_models=None, note="")
        comp = x[x["component"].notna()]
        if comp.empty:
            r = x.iloc[0]
            return dict(decomposed=False, n_models=None if pd.isna(r["n_models"]) else int(r["n_models"]), note=str(r["note"]))
        r = comp.iloc[0]
        temps = str(r["temps"])
        return dict(decomposed=True, n_models=int(r["n_models"]), n_wordings=int(r["n_wordings"]), temps=temps,
                    n_temps=len(temps.split(",")), facets=str(r["facets"]), note=str(r["note"]))

    def groups(self, column: str, item: str, basis: str = "E2") -> dict[str, dict] | None:
        """{group: dict(share, lo, hi, lmin, lmax)} for one route column (a, b, c, e-S, e-L) and item, or None when not decomposed.
        lo/hi: frozen A1 interval of Arm L, only for groups of a single term; lmin/lmax: leave-one-wording-out range (Arm S, (e)-Arm L)."""
        inf = self.info(column, item)
        if not inf["decomposed"]:
            return None
        out: dict[str, dict] = {}
        if column in ARMS_DIR:
            c = self.comps_S(ARMS_DIR[column], item)
            wcols = sorted(col for col in c.columns if col.startswith(f"{basis}_lowo_drop_W"))
            for g in GROUP_KEYS:
                terms = [t for t in c.index if group_of(t) == g and not pd.isna(c.at[t, f"{basis}_share"])]
                if not terms:
                    continue
                share = float(c.loc[terms, f"{basis}_share"].sum())
                per_w = c.loc[terms, wcols].sum(axis=0)
                out[g] = dict(share=share, lo=None, hi=None, lmin=float(per_w.min()), lmax=float(per_w.max()), nterms=len(terms))
            # cross-check against the route table (single-term groups: share and LOWO min/max must be identical)
            x = self.rt[(self.rt["column"] == column) & (self.rt["item"] == item) & (self.rt["basis"] == basis) & self.rt["component"].notna()]
            for r in x.itertuples(index=False):
                g = group_of(r.component)
                if out[g]["nterms"] == 1:
                    assert abs(out[g]["share"] - r.share) < 1e-9 and abs(out[g]["lmin"] - r.lowo_min) < 1e-9 and abs(out[g]["lmax"] - r.lowo_max) < 1e-9, \
                        (column, item, r.component)
            assert abs(sum(v["share"] for v in out.values()) - 1.0) < 1e-9, (column, item, "shares do not sum to 1")
        else:
            x = self.rt[(self.rt["column"] == column) & (self.rt["item"] == item) & (self.rt["analysis"] == "4facet") & self.rt["component"].notna()].copy()
            x["g"] = x["component"].map(group_of)
            lw = self.lowo_L() if column == "(e)-ArmL" else None
            for g, y in x.groupby("g"):
                single = len(y) == 1
                d = dict(share=float(y["share"].sum()), lo=float(y["share_lo"].iloc[0]) if single else None,
                         hi=float(y["share_hi"].iloc[0]) if single else None, lmin=None, lmax=None, nterms=len(y))
                if lw is not None:
                    z = lw[lw["item"] == item]
                    z = z[z["term"].map(group_of) == g]
                    wcols = sorted(col for col in z.columns if col.startswith("lowo_drop_W"))
                    per_w = z[wcols].sum(axis=0)
                    d["lmin"], d["lmax"] = float(per_w.min()), float(per_w.max())
                    if single:
                        assert abs(d["lmin"] - y["lowo_min"].iloc[0]) < 1e-9 and abs(d["lmax"] - y["lowo_max"].iloc[0]) < 1e-9, (column, item, g)
                out[g] = d
            assert abs(sum(v["share"] for v in out.values()) - 1.0) < 1e-9, (column, item, "shares do not sum to 1")
        return out

    def draw_share(self, column: str, item: str) -> float | None:
        x = self.rt[(self.rt["column"] == column) & (self.rt["item"] == item) & self.rt["component"].notna()]
        return None if x.empty or pd.isna(x["draw_share"].iloc[0]) else float(x["draw_share"].iloc[0])

    # ----- terms (not groups) of a column, for the agreement figure
    def terms(self, column: str, item: str, basis: str) -> dict[str, float]:
        x = self.rt[(self.rt["column"] == column) & (self.rt["item"] == item) & (self.rt["basis"] == basis) & self.rt["component"].notna()]
        if column == "(e)-ArmL":
            x = x[x["analysis"] == "4facet"]
        return {canon(r.component): float(r.share) for r in x.itertuples(index=False)}


def items_order(tr: rc.Tracker, items: list[str]) -> list[str]:
    sc = tr.csv(rc.HUMAN / "arml_scales.csv", dtype={"item": str})
    order = [i for i in sc["item"] if i in items]
    assert set(order) == set(items), f"items without a human scale: {set(items) - set(order)}"
    return order


def base_guard(outs: list[Path], out_explicit: bool) -> None:
    """The route-table directory (under runs/) is the model input; output under paper/ is allowed, never under runs/."""
    rc.guard([Path(o) for o in outs], out_explicit, ROUTE)


def table_footer_tag(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
