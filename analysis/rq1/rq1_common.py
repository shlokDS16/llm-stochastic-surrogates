"""Shared loaders and helpers for the RQ1 scripts (tables, Fig 1-3). No analysis happens here.

Views (protocol v0.9 item 2; neither is the headline):
  A = liberal frame (abstract-decisions-v08 liberal == eligible; 2,022)
  B = coder-flagged subset of A (meets_criteria_on_abstract == "yes")
  S = strict frame (strict == eligible; 1,470), sensitivity column only
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import logging
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data/processed"
SEED = 20261016
FAMILIES = ["HB", "JDM", "RE", "TOM", "MEM", "LANG", "LEARN", "NUM", "MOR", "DEV", "OTH"]
FAMILY_NAMES = {
    "HB": "Heuristics and biases", "JDM": "Judgement and decision making", "RE": "Reasoning",
    "TOM": "Theory of mind and social cognition", "MEM": "Memory and attention",
    "LANG": "Language and psycholinguistics", "LEARN": "Learning and categorisation",
    "NUM": "Numerical cognition", "MOR": "Moral judgement", "DEV": "Developmental tasks", "OTH": "Other",
}
MODEL_FAMILIES = ["GPT", "Claude", "Gemini", "Llama", "Mistral", "Qwen", "OLMo", "other"]
PERIODS = ["2018-2023", "2024", "2025-2026"]
SEARCH_DATE = "2026-10-16"  # OpenAlex S2 run 2026-10-16T06:16, arXiv S2 run 2026-10-16T06:18 (search-log.md)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def read_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def code_files() -> list[Path]:
    return [Path(p) for p in sorted(glob.glob(str(P / "rq1/rq1-batch-*.jsonl")))]


def period_of(year: int) -> str:
    return "2018-2023" if year <= 2023 else ("2024" if year == 2024 else "2025-2026")


def first_family(row: dict) -> str:
    """First paradigm family listed by the coder ('none' if no paradigm named); as in the sample design (v0.9.1)."""
    return row["paradigms"][0]["family"] if row["paradigms"] else "none"


def load_frame(need_years: bool = True):
    """Return (rows, views, manifest): rows = id -> RQ1 code row (+ year, title) for the liberal frame."""
    manifest = json.loads((P / "rq1/manifest.json").read_text(encoding="utf-8"))
    codes = {}
    for f in code_files():
        for r in read_jsonl(f):
            assert r["id"] not in codes, f"duplicate id {r['id']}"
            codes[r["id"]] = r
    dec = {d["id"]: d for d in read_jsonl(P / "screen/abstract-decisions-v08.jsonl")}
    lib = {i for i, d in dec.items() if d["liberal"] == "eligible"}
    strict = {i for i, d in dec.items() if d["strict"] == "eligible"}
    assert len(codes) == manifest["total"], (len(codes), manifest["total"])
    assert len(lib) == manifest["frame_liberal"], (len(lib), manifest["frame_liberal"])
    assert lib <= set(codes), "liberal frame record without an RQ1 code"
    assert len(set(codes) - lib) == manifest["pilot_not_in_frame"]
    assert strict <= lib
    rows = {i: codes[i] for i in lib}
    if need_years:
        want = set(rows)
        for rec in read_jsonl(P / "records.jsonl"):
            if rec["id"] in want:
                rows[rec["id"]]["year"] = rec["year"]
                rows[rec["id"]]["title"] = rec["title"]
                rows[rec["id"]]["rec_abstract"] = rec.get("abstract") or ""
        missing = [i for i in rows if rows[i].get("year") is None]
        assert not missing, f"{len(missing)} frame records without year"
    views = {
        "A": sorted(lib),
        "B": sorted(i for i in lib if rows[i]["meets_criteria_on_abstract"] == "yes"),
        "S": sorted(strict),
    }
    return rows, views, manifest


VIEW_LABEL = {
    "A": "A: liberal frame",
    "B": "B: coder-flagged yes within A",
    "S": "S: strict frame (sensitivity)",
}


def setup_run(run_dir: Path, name: str):
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / f"{name}.log"
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(message)s",
        handlers=[logging.FileHandler(log, mode="w", encoding="utf-8"), logging.StreamHandler(sys.stdout)],
        force=True,
    )
    return logging.getLogger(name)


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def write_config(run_dir: Path, script: str, inputs: list[Path], params: dict, extra: dict | None = None,
                 filename: str = "config.json"):
    cfg = {
        "script": script,
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "git_sha": git_sha(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "seed": SEED,
        "params": params,
        "inputs": {rel(p): sha256(p) for p in inputs},
    }
    if extra:
        cfg.update(extra)
    body = json.dumps(cfg, indent=1, sort_keys=True)
    cfg["config_hash_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    (run_dir / filename).write_text(json.dumps(cfg, indent=1, sort_keys=True), encoding="utf-8")
    return cfg


def pkg_versions(names: list[str]) -> dict:
    from importlib import metadata
    out = {}
    for n in names:
        try:
            out[n] = metadata.version(n)
        except Exception:
            out[n] = None
    return out


def norm_name(s: str) -> str:
    """Light normalisation of a paradigm name: lowercase, hyphens/slashes to space, strip other punctuation."""
    s = s.lower().replace("-", " ").replace("/", " ").replace("_", " ")
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def pct(k: int, n: int) -> float:
    return round(100 * k / n, 1) if n else float("nan")


# ---- figure style (Springer: no in-figure titles, embedded fonts, RGB, colour-blind-safe) ----
MM = 1 / 25.4
W1, W2 = 84 * MM, 174 * MM
# Okabe-Ito
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7", "black": "#000000", "grey": "#999999"}
TEXT = "#111111"


def mpl_setup():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib as mpl
    from matplotlib import font_manager as fm
    names = {f.name for f in fm.fontManager.ttflist}
    fam = "Arial" if "Arial" in names else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": fam, "font.size": 7, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 6.5, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": TEXT, "ytick.color": TEXT,
        "savefig.facecolor": "white", "figure.facecolor": "white", "hatch.linewidth": 0.5,
    })
    return fam


def save_fig(fig, stem: Path, dpi: int = 600):
    for ext in ("pdf", "eps"):
        fig.savefig(stem.with_suffix("." + ext), format=ext)
    fig.savefig(stem.with_suffix(".png"), format="png", dpi=dpi)
