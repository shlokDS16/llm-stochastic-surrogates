"""Generate the supplement long tables paper/acme/tables/tab-s-routes.tex (full route table) and tab-s-sens.tex (sensitivities S-a to S-e).

Both files are bodies of a longtable set up by \\acmelongtable in paper/acme/floats.tex (caption, label, header and column spec live there; the body
starts a row with \\multicolumn, as the macro requires).  Every cell is read from runs/acme-gstudy/route-table/{route_table,sens_table}.csv; nothing
is typed in.  One row per (item, variance term), the term labels of gstudy.py, shares untruncated, two decimals.

tab-s-routes.tex  Part A: the four-facet analysis, columns (a) E2, (a) E1, (b), (c), (e) Arm S E2, (e) Arm S E1, (e) Arm L.
                  Part B: Arm L with T = 1.0 only (analysis T1), columns (b), (c), (e) Arm L (the other cells are empty).
                  Arm S cell: share (range over the leave-one-wording-out values; fragility, not an interval).  Arm L cell: share [frozen A1 interval].
                  Item header lines give the models, wordings and temperatures per column and the draw share of Arm S; column (d), counts only, is in the
                  header line; an item that is not decomposed in a column has an empty cell and its reason in the header line.
tab-s-sens.tex    columns: (a) E2 reference, S-a loose roster, S-b valid cells only, S-c T = 1.0 only, S-d logit scale (binary items), S-e without W0.
                  Cell: E2 share (leave-one-wording-out range).  Item header lines give the models per sensitivity and the S-d clip rate.

    .venv/Scripts/python.exe -I analysis/acme/make_tab_s_routes.py [--outdir paper/acme/tables]
Writes both files and <file>.source.json for each.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import results_common as rc  # noqa: E402
import results_route as R  # noqa: E402

ITEMS_ALL = ["P1", "P3", "AF", "QA", "NR", "P2a", "P2b", "P2c", "P2d", "P4"]
TERM_TEX = {"M": "M", "O": "O", "T": "T", "MO": r"M$\times$O", "MT": r"M$\times$T", "OT": r"O$\times$T", "MOT": r"M$\times$O$\times$T", "W": "W",
            "MW": r"M$\times$W", "WO": r"W$\times$O", "WT": r"W$\times$T", "MWO": r"M$\times$W$\times$O", "MWT": r"M$\times$W$\times$T", "WOT": r"W$\times$O$\times$T",
            "res": "Residual", "draw": "Draw"}
ITEM_TEX = {"P1": "P1 framing", "P3": "P3 sunk cost", "AF": "AF allow/forbid", "QA": "QA quote", "NR": "NR reciprocity",
            "P2a": "P2a anchor, miles", "P2b": "P2b anchor, people", "P2c": "P2c anchor, feet", "P2d": "P2d anchor, births", "P4": "P4 gambler"}


def pl(n) -> str:
    n = int(n)
    return f"{n} model" + ("" if n == 1 else "s")


def s_cell(r) -> str:
    """Arm S cell: share (lowo min, lowo max)."""
    return rf"{R.tx(r.share)}\,({R.tx(r.lowo_min)}, {R.tx(r.lowo_max)})"


def l_cell(r) -> str:
    """Arm L cell: share [frozen interval]; the (e)-Arm L cell has the leave-one-wording-out range instead of the (not interpreted) interval."""
    if r.column == "(e)-ArmL":
        if pd.isna(r.lowo_min):
            return R.tx(r.share)
        return rf"{R.tx(r.share)}\,({R.tx(r.lowo_min)}, {R.tx(r.lowo_max)})"
    return rf"{R.tx(r.share)}\,[{R.tx(r.share_lo)}, {R.tx(r.share_hi)}]" if not pd.isna(r.share_lo) else R.tx(r.share)


def lookup(df: pd.DataFrame, col: str, item: str, analysis: str | None, basis: str | None) -> dict:
    x = df[(df["column"] == col) & (df["item"] == item) & df["component"].notna()]
    if analysis is not None:
        x = x[x["analysis"] == analysis]
    if basis is not None:
        x = x[x["basis"] == basis]
    return {R.canon(r.component): r for r in x.itertuples(index=False)}


def item_note(df: pd.DataFrame, item: str, cols: list[tuple[str, str]]) -> str:
    """Header line of an item: models (and the wordings and temperatures) per column, or the reason it is not decomposed."""
    parts = []
    for col, label in cols:
        x = df[(df["column"] == col) & (df["item"] == item)]
        if x.empty:
            continue
        c = x[x["component"].notna()]
        if c.empty:
            n = x["n_models"].iloc[0]
            parts.append(f"{label}: not decomposed" + (f" ({pl(n)})" if pd.notna(n) else ""))
        else:
            r = c.iloc[0]
            parts.append(f"{label}: {pl(r['n_models'])}, {int(r['n_wordings'])} wordings, T {r['temps'].replace(',', '/')}")
    return "; ".join(parts)


def header_row(ncols: int, text: str) -> str:
    # a fixed-width paragraph cell: an unbroken text would set the width of the whole longtable
    return rf"\multicolumn{{{ncols}}}{{@{{}}>{{\raggedright\arraybackslash}}p{{15.3cm}}}}{{\textbf{{{R.tex_escape(text)}}}}} \\" + "\n"


def build_routes(rt: pd.DataFrame) -> str:
    cols = [("(a)", "A1-S", "E2", s_cell), ("(a)", "A1-S", "E1", s_cell), ("(b)", "4facet", "A1", l_cell), ("(c)", "4facet", "A1", l_cell),
            ("(e)-ArmS", "A1-S", "E2", s_cell), ("(e)-ArmS", "A1-S", "E1", s_cell), ("(e)-ArmL", "4facet", "A1", l_cell)]
    n = 1 + len(cols)
    out = [
        "% GENERATED by analysis/acme/make_tab_s_routes.py from runs/acme-gstudy/route-table/route_table.csv. Do not edit by hand; rerun the script.\n",
        "% Body rows of a longtable (caption, label and header: \\TabSRoutes in floats.tex). Arm S: share (leave-one-wording-out range); Arm L: share [frozen A1 interval].\n",
    ]
    first = True
    for it in ITEMS_ALL:
        label = f"{ITEM_TEX[it]}. " + item_note(rt, it, [("(a)", "(a)"), ("(b)", "(b)"), ("(c)", "(c)"), ("(e)-ArmS", "(e) Arm S"), ("(e)-ArmL", "(e) Arm L")])
        d = rt[(rt["column"] == "(d)") & (rt["item"] == it)]
        label += f"; (d) per-model roster: {pl(d['n_models'].iloc[0])} (count only)"
        draw = rt[(rt["column"] == "(a)") & (rt["item"] == it) & rt["draw_share"].notna()]
        out.append(header_row(n, label) if first else r"\midrule" + "\n" + header_row(n, label))
        first = False
        looked = [lookup(rt, c, it, an, ba) for c, an, ba, _ in cols]
        terms = [t for t in R.TERM_ORDER if any(t in lk for lk in looked)]
        for t in terms:
            cells = [fn(lk[t]) if t in lk else "" for lk, (_, _, _, fn) in zip(looked, cols)]
            out.append(f"{TERM_TEX[t]} & " + " & ".join(cells) + r" \\" + "\n")
    # Part B: T = 1.0 only, Arm L columns
    out.append(r"\midrule" + "\n" + header_row(n, "Arm L with T = 1.0 only (three-facet analysis T1): columns (b), (c) and (e) Arm L; cell: share [frozen A1 interval]"))
    colsB = [("(b)", "T1", "A1", l_cell), ("(c)", "T1", "A1", l_cell), ("(e)-ArmL", "T1", "A1", l_cell)]
    slot = {"(b)": 3, "(c)": 4, "(e)-ArmL": 7}
    for it in ITEMS_ALL:
        looked = {c: lookup(rt, c, it, an, ba) for c, an, ba, _ in colsB}
        if not any(looked.values()):
            continue
        out.append(header_row(n, ITEM_TEX[it]))
        terms = [t for t in R.TERM_ORDER if any(t in lk for lk in looked.values())]
        for t in terms:
            cells = [""] * len(cols)
            for c, an, ba, fn in colsB:
                if t in looked[c]:
                    r = looked[c][t]
                    cells[slot[c] - 1] = (rf"{R.tx(r.share)}\,[{R.tx(r.share_lo)}, {R.tx(r.share_hi)}]")
            out.append(f"{TERM_TEX[t]} & " + " & ".join(cells) + r" \\" + "\n")
    return "".join(out)


def build_sens(st: pd.DataFrame, rt: pd.DataFrame) -> str:
    tags = ["S-a", "S-b", "S-c", "S-d", "S-e"]
    n = 2 + len(tags)
    out = [
        "% GENERATED by analysis/acme/make_tab_s_routes.py from runs/acme-gstudy/route-table/sens_table.csv and route_table.csv (column (a)). Do not edit by hand.\n",
        "% Body rows of a longtable (caption, label and header: \\TabSSens in floats.tex). Cell: E2 share (leave-one-wording-out range).\n",
    ]
    first = True
    for it in ITEMS_ALL:
        parts = []
        ref = rt[(rt["column"] == "(a)") & (rt["item"] == it) & rt["component"].notna()]
        parts.append(f"(a): {pl(ref['n_models'].iloc[0])}" if not ref.empty else "(a): not decomposed")
        clip = None
        for tg in tags:
            x = st[(st["sens"] == tg) & (st["item"] == it)]
            if x.empty:
                parts.append(f"{tg}: not run for this item")
                continue
            c = x[x["component"].notna()]
            if c.empty:
                parts.append(f"{tg}: not decomposed")
                continue
            parts.append(f"{tg}: {pl(c['n_models'].iloc[0])}, {int(c['n_wordings'].iloc[0])} wordings")
            if tg == "S-d":
                m = re.search(r"clip rate ([0-9.]+)", " ".join(str(v) for v in c["note"].dropna().unique()))
                clip = m.group(1) if m else None
        if clip is not None:
            parts.append(f"S-d clip rate {R.fx(float(clip), 2)}")
        label = f"{ITEM_TEX[it]}. " + "; ".join(parts)
        out.append(header_row(n, label) if first else r"\midrule" + "\n" + header_row(n, label))
        first = False
        looked = [lookup(rt, "(a)", it, "A1-S", "E2")] + [lookup(st[st["sens"] == tg], f"sens-{tg}", it, None, "E2") for tg in tags]
        terms = [t for t in R.TERM_ORDER if any(t in lk for lk in looked)]
        for t in terms:
            cells = [s_cell(lk[t]) if t in lk else "" for lk in looked]
            out.append(f"{TERM_TEX[t]} & " + " & ".join(cells) + r" \\" + "\n")
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", default=None)
    a = ap.parse_args()
    outdir = rc.resolve_arg(a.outdir, rc.ROOT / "paper" / "acme" / "tables")
    f1, f2 = outdir / "tab-s-routes.tex", outdir / "tab-s-sens.tex"
    R.base_guard([f1, f2], a.outdir is not None)
    tr = rc.Tracker()
    route = R.Route(tr)
    outdir.mkdir(parents=True, exist_ok=True)
    f1.write_text(build_routes(route.rt), encoding="utf8")
    f2.write_text(build_sens(route.st, route.rt), encoding="utf8")
    rc.write_source([f1, f2], "analysis/acme/make_tab_s_routes.py", R.ROUTE, tr, extra=dict(items=ITEMS_ALL))


if __name__ == "__main__":
    main()
