"""Print every sentence tagged FINAL-CHECK (or any pattern) with its number macros expanded, for checking prose against values.

    python tools/render_checks.py [--tag FINAL-CHECK] [--files paper/common/*.tex]
"""
import argparse
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BS = chr(92)


def macros():
    pat = re.compile(re.escape(BS + "newcommand{" + BS) + r"([A-Za-z]+)\}\{([^}]*)\}")
    d = {}
    for f in ["paper/common/autonumbers.tex", "paper/common/macros.tex"]:
        for line in open(ROOT / f, encoding="utf-8"):
            m = pat.match(line)
            if m:
                d[m.group(1)] = m.group(2).replace("{,}", ",").replace(BS + "ensuremath{-}", "-")
    return d


def render(t, v):
    g = lambda s: v.get(s, "?" + s)  # noqa: E731
    helpers = {
        "rqci": lambda s: f"{g(s + 'Est')} percent ({g(s + 'Lo')} to {g(s + 'Hi')})",
        "rqest": lambda s: f"{g(s + 'Est')} percent",
        "rqkn": lambda s: f"{g(s + 'K')} of {g(s + 'N')}",
        "rqbnd": lambda s: f"bounds {g(s + 'BoundLo')} to {g(s + 'BoundHi')} percent",
        "rqpair": lambda s: f"{g(s + 'ClaudeEst')} percent by Claude and {g(s + 'CodexEst')} percent by Codex",
        "rqslash": lambda s: f"{g(s + 'ClaudeEst')} / {g(s + 'CodexEst')}",
    }
    for h, fn in helpers.items():
        t = re.sub(re.escape(BS + h) + r"\{([A-Za-z]+)\}", lambda m: fn(m.group(1)), t)
    t = re.sub(re.escape(BS) + r"([A-Za-z]+)\{\}", lambda m: v.get(m.group(1), BS + m.group(1)), t)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="FINAL-CHECK")
    ap.add_argument("--files", nargs="*", default=sorted(glob.glob(str(ROOT / "paper/common/*.tex"))))
    a = ap.parse_args()
    v = macros()
    for f in a.files:
        if f.endswith(("autonumbers.tex", "macros.tex")):
            continue
        lines = open(f, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines, 1):
            if a.tag in line:
                body = re.split(r"(?<!" + re.escape(BS) + r")%", line, maxsplit=1)[0].strip()
                prev = re.split(r"(?<!" + re.escape(BS) + r")%", lines[i - 2], maxsplit=1)[0].strip() if i > 1 else ""
                print(f"--- {Path(f).name}:{i}")
                if prev and not prev.startswith(BS + "begin"):
                    print("  [prev] " + render(prev, v))
                print("  " + render(body, v))


if __name__ == "__main__":
    main()
