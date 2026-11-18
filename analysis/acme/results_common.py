"""Shared helpers for the results figures (Figs 9 to 11) and Table 8: output guard, input tracking, provenance files, loaders, style.

Written before any real outcome exists and tested on synthetic data only. Reads gstudy.py output directories (runs/acme-gstudy/A1) and
the human Many Labs 1 inputs (runs/human-ml1-acme/); it contains no result value.

Guard (rule from Shlok, 2026-11-07):
  * nothing is written under <project>/runs/ by the figure and table scripts (dstudy_boot.py is the one producer that may write beside a
    gstudy directory, allow_runs=True, and it refuses paper/);
  * a path under <project>/paper/ is written only when the gstudy directory (and every other model-derived input) resolves to a path under
    <project>/runs/; a scratch or synthetic directory may write only to an explicit --out outside paper/ (no --out means the default
    paper/ path, which is then refused);
  * beside every output, <output>.source.json lists the gstudy directory, the SHA-256 of every input file read, the git HEAD, the
    timestamp and the script, so that the gate-auditor can check that a figure or table came from the real run.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUMAN = ROOT / "runs" / "human-ml1-acme"
DEFAULT_GSTUDY = ROOT / "runs" / "acme-gstudy" / "A1"
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ------------------------------------------------------------------------------------------------------------------ guard
def _under(p: Path, parent: Path) -> bool:
    try:
        p.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return p.relative_to(ROOT.resolve()).as_posix() if _under(p, ROOT) else str(p)


def resolve_arg(p: str | Path | None, default: Path | None = None) -> Path | None:
    if p is None:
        return default
    p = Path(p)
    return p if p.is_absolute() else (Path.cwd() / p)


def guard(outs: list[Path], out_explicit: bool, gstudy: Path, model_inputs: list[Path] = (), forbid_paper: bool = False, allow_runs: bool = False) -> None:
    """Refuse (SystemExit with a message, non-zero status) any combination that would put scratch or synthetic numbers into paper/ or
    write into runs/."""
    runs, paper = ROOT / "runs", ROOT / "paper"
    real = _under(gstudy, runs) and all(_under(Path(m), runs) for m in model_inputs)
    for o in outs:
        o = Path(o)
        if _under(o, runs) and not allow_runs:
            raise SystemExit(f"REFUSED: {o} is under {runs}; the figure and table scripts never write into runs/.")
        if _under(o, paper):
            if forbid_paper:
                raise SystemExit(f"REFUSED: this script never writes under paper/ ({o}).")
            if not real:
                bad = [str(x) for x in [gstudy, *model_inputs] if not _under(Path(x), runs)]
                raise SystemExit(
                    f"REFUSED: output {o} is under paper/ but these inputs are not under {runs}: {bad}. A scratch or synthetic input may "
                    f"write only to an explicit --out outside paper/ (out given explicitly: {out_explicit}).")


class Tracker:
    """Records every input file that is read, so that source.json can hash them."""

    def __init__(self) -> None:
        self.files: dict[str, Path] = {}

    def add(self, p: Path) -> Path:
        p = Path(p).resolve()
        if not p.is_file():
            raise SystemExit(f"missing input file: {p}")
        self.files[str(p)] = p
        return p

    def csv(self, p: Path, **kw):
        import pandas as pd
        return pd.read_csv(self.add(p), **kw)

    def json(self, p: Path):
        return json.loads(self.add(p).read_text(encoding="utf8"))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"unavailable: {e}"


def write_source(outputs: list[Path], script: str, gstudy: Path, tracker: Tracker, extra: dict | None = None) -> None:
    """Write <output>.source.json beside every output file."""
    meta = dict(
        script=script, gstudy_dir=rel(gstudy), gstudy_dir_resolved=str(Path(gstudy).resolve()),
        git_head=git_head(), timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        inputs={rel(p): sha256(p) for p in sorted(tracker.files.values())},
    )
    if extra:
        meta.update(extra)
    for o in outputs:
        o = Path(o)
        Path(str(o) + ".source.json").write_text(json.dumps(meta, indent=1), encoding="utf8")
        print("wrote", o, "and", o.name + ".source.json")


# ------------------------------------------------------------------------------------------------------------------ loaders
SHORT = {  # short effect labels for panel titles (text only)
    "P1": "framing", "P2a": "anchor, miles", "P2b": "anchor, people", "P2c": "anchor, feet", "P2d": "anchor, births",
    "P3": "sunk cost", "P4": "gambler", "AF": "allow/forbid", "QA": "quote", "NR": "reciprocity",
}
COMP_ORDER = ["M", "O", "MO", "W", "MW", "WO", "res"]
COMP_TEXT = {"M": "M", "O": "O", "MO": "M×O", "W": "W", "MW": "M×W", "WO": "W×O", "res": "residual"}


def estimator_info(summary: dict) -> dict:
    """Interval kind and share rule of the run, from summary.json and gstudy.ESTIMATORS (read, not retyped)."""
    import gstudy
    cfg = summary["config"]
    est = gstudy.get_estimator(cfg["estimator"])
    mode = cfg.get("share_mode") or est["share_mode"]
    return dict(name=cfg["estimator"], interval=est["interval"], share_mode=mode, B=int(cfg["B"]))


def interval_word(info: dict) -> str:
    return "studentized" if info["interval"] == "student" else ("centred" if info["interval"] == "centered" else "percentile")


def items_in_order(tr: Tracker, present: list[str]) -> list[str]:
    sc = tr.csv(HUMAN / "arml_scales.csv", dtype={"item": str})
    order = [i for i in sc["item"] if i in present]
    extra = [i for i in present if i not in order]
    if extra:
        raise SystemExit(f"items in the gstudy output that have no human yardstick: {extra}")
    return order


def short_model(m: str) -> str:
    for suf in ("-instruct", "-chat", "-it", "-Instruct"):
        m = m.replace(suf, "")
    return m


# ------------------------------------------------------------------------------------------------------------------ style
def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": 8, "axes.labelsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.titlesize": 8, "legend.fontsize": 8, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.0, "pdf.fonttype": 42,
        "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 600, "pdf.compression": 6,
    })
    return plt


CM = 1 / 2.54
TEXT_WIDTH_CM = 455.24408 / 72.27 * 2.54       # \textwidth of the ACME wrapper (sn-jnl, iicol)
INK, GREY, BAND = "#222222", "#6B6B6B", "#EFEFEF"
BLUE, VERMILION, SKY, GREEN, ORANGE, PURPLE = "#0072B2", "#D55E00", "#56B4E9", "#009E73", "#E69F00", "#CC79A7"   # Okabe and Ito 2008


def save_figure(fig, pdf: Path) -> list[Path]:
    pdf = Path(pdf)
    pdf.parent.mkdir(parents=True, exist_ok=True)
    png = pdf.with_suffix(".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=600)
    return [pdf, png]


# ------------------------------------------------------------------------------------------------------------------ recorded reads
# For the figure and table scripts that read their inputs through ordinary open() calls (directly or inside make_autonumbers, which runs
# at import): install the recorder BEFORE importing make_autonumbers, then call write_source_recorded() after the output is written.
# The inputs hashed are the project files that were opened for reading during the run, except build products (aux, log, pyc, build
# folders), the outputs of the generators and version-control files; the compiled .aux file (section and equation numbers) is read by
# two drawing scripts and asserted equal to a fallback in the script, so it is listed under "unhashed_inputs" instead.
class _Recorder:
    def __init__(self) -> None:
        self.paths: set[Path] = set()
        self.unhashed: set[str] = set()

    def note(self, f) -> None:
        try:
            p = Path(f).resolve()
        except Exception:  # noqa: BLE001
            return
        self.paths.add(p)


_REC: _Recorder | None = None


def record_reads() -> _Recorder:
    """Start recording every file opened for reading (idempotent)."""
    global _REC
    if _REC is not None:
        return _REC
    import builtins
    import io
    import os

    rec = _Recorder()
    orig = io.open

    def _open(file, mode="r", *a, **k):
        if isinstance(file, (str, bytes, os.PathLike)) and not any(c in mode for c in "wax+"):
            rec.note(file)
        return orig(file, mode, *a, **k)

    io.open = _open
    builtins.open = _open
    _REC = rec
    return rec


_SKIP_PARTS = {".git", ".venv", "__pycache__", "build", "build-check", "build-typeset", "node_modules"}
_SKIP_SUFFIX = {".pyc", ".aux", ".log", ".pyd", ".dll", ".source.json"}


def write_source_recorded(outputs: list[Path], script: str, rec: _Recorder, gstudy: str = "", extra: dict | None = None) -> None:
    """Write <output>.source.json (same keys as write_source) from the recorded reads."""
    outs = {Path(o).resolve() for o in outputs}
    inputs, unhashed = {}, []
    for p in sorted(rec.paths):
        if not p.is_file() or not _under(p, ROOT):
            continue
        parts = set(p.relative_to(ROOT).parts)
        if parts & _SKIP_PARTS or p.suffix in _SKIP_SUFFIX or p.name.endswith(".source.json") or p in outs or p.suffix == ".py":
            if p.suffix == ".aux":
                unhashed.append(rel(p))
            continue
        if _under(p, ROOT / "paper" / "acme" / "tables") or _under(p, ROOT / "paper" / "acme" / "figures"):
            continue
        inputs[rel(p)] = sha256(p)
    meta = dict(script=script, gstudy_dir=gstudy or "n/a", gstudy_dir_resolved=str((ROOT / gstudy).resolve()) if gstudy else "n/a",
                git_head=git_head(), timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), inputs=inputs)
    if unhashed:
        meta["unhashed_inputs"] = sorted(set(unhashed))
    if extra:
        meta.update(extra)
    for o in outputs:
        Path(str(o) + ".source.json").write_text(json.dumps(meta, indent=1), encoding="utf8")
        print("wrote", o, "and", Path(o).name + ".source.json")
