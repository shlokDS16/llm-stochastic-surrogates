"""Supplement Fig. S1 (key `s-validmass`): valid answer-path mass of the exact readout by model and item.

Reads runs/acme-L/outcomes/valid_mass.csv (written by analysis/acme/gate_g3.py / armL_outcomes.py): per model and item the median valid
mass over the prompts of the main variant, and the flag `excluded` of the valid-mass rule (valid mass below the threshold on more than
the allowed share of prompts). Cells are shaded by the median; a cross marks a pair that the rule removes. The threshold and the
allowed share are NUMBERS keys bm.vm.thr and bm.vm.frac and are written into the caption, not into the image.

Writes paper/acme/figures/fig-s-validmass.pdf (vector, fonts embedded), a 600 dpi PNG beside it, and fig-s-validmass.pdf.source.json.

Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_s_validmass.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SRC = "runs/acme-L/outcomes/valid_mass.csv"
OUT = ROOT / "paper" / "acme" / "figures" / "fig-s-validmass.pdf"
ITEMS = ["P1", "AF", "NR", "P3", "QA", "P2a", "P2b", "P2c", "P2d", "P4"]
CM = 1 / 2.54
FONT, FS = "Arial", 8.0
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT, "DejaVu Sans"], "font.size": FS, "axes.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600, "pdf.compression": 6,
})


def main() -> None:
    rows = list(csv.DictReader((ROOT / SRC).open(encoding="utf-8")))
    models = list(dict.fromkeys(r["model"] for r in rows))
    med = {(r["model"], r["item"]): float(r["median_valid"]) for r in rows}
    exc = {(r["model"], r["item"]): r["excluded"] == "True" for r in rows}
    assert len(med) == len(models) * len(ITEMS), (len(med), len(models))
    fig, ax = plt.subplots(figsize=(16.0 * CM, 6.4 * CM), constrained_layout=True)
    grid = [[min(1.0, med[(m, it)]) for it in ITEMS] for m in models]
    im = ax.imshow(grid, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    for i, m in enumerate(models):
        for j, it in enumerate(ITEMS):
            if exc[(m, it)]:
                ax.plot(j, i, marker="x", color=("black" if grid[i][j] > 0.75 else "white"), markersize=4.5, markeredgewidth=0.9)
    ax.set_xticks(range(len(ITEMS)), ITEMS)
    ax.set_yticks(range(len(models)), models)
    ax.tick_params(length=2, width=0.5)
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("Median valid mass", fontsize=FS)
    cb.ax.tick_params(length=2, width=0.5, labelsize=FS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    fig.savefig(OUT.with_suffix(".png"))
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        head = "unknown"
    meta = {"script": "analysis/acme/figures/fig_s_validmass.py", "git_head": head,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "inputs": {SRC: hashlib.sha256((ROOT / SRC).read_bytes()).hexdigest()}}
    for o in (OUT, OUT.with_suffix(".png")):
        Path(str(o) + ".source.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(models)} models, {len(ITEMS)} items, {sum(exc.values())} pairs removed)")


if __name__ == "__main__":
    main()
