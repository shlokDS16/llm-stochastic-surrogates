"""Prompt universe for the ACME benchmark (research/relaunch/P1-CONTRACT.md).

W0-W3 of the 7 pilot items come from the frozen pilot files (analysis/pilot/prompts, hash-checked) plus overlay fields
(analysis/acme/prompts/overlay); W4-W9 and the new items AF, QA, NR from analysis/acme/prompts/W*/; decoys from prompts/decoys.
Each prompt is a list of chat turns; the readout is attached by run_armL.py.
"""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PILOT = ROOT / "analysis/pilot/prompts"
ACME = HERE / "prompts"
PILOT_ITEMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
NEW_ITEMS = ["AF", "QA", "NR"]
ITEMS = PILOT_ITEMS + NEW_ITEMS
WORDINGS = [f"W{i}" for i in range(10)]
ORDERS = {"P1": ["sure_first", "risky_first"], "P3": ["forward", "reversed"], "QA": ["forward", "reversed"],
          "AF": ["yes_first", "no_first"], "NR": ["yes_first", "no_first"]}   # others: [None]
READOUT = {"P1": "choice", "P2a": "number", "P2b": "number", "P2c": "number", "P2d": "number", "P3": "rating", "P4": "number",
           "AF": "yesno", "QA": "rating", "NR": "yesno2"}


def _y(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf8"))


def load_common():
    return _y(ACME / "common.yaml")


def load_wording(item, W, variant="main"):
    """variant: main | D1 | D2 (decoys exist for W0 only)."""
    if variant != "main":
        return _y(ACME / f"decoys/{item}_{variant}.yaml")
    if item in PILOT_ITEMS and W in ("W0", "W1", "W2", "W3"):
        d = _y(PILOT / f"{W}/{item}.yaml")
        ov = ACME / f"overlay/{W}/{item}.yaml"
        if ov.exists():
            d = {**d, **{k: v for k, v in _y(ov).items() if k not in d}}
        return d
    return _y(ACME / f"{W}/{item}.yaml")


def fmt_line(common, rtype, F, O):
    f = common["formats"][F]
    if rtype in ("yesno", "yesno2"):
        return f["yesno_no_first" if O == "no_first" else "yesno"]
    return f[{"choice": "choice", "number": "number", "rating": "rating"}[rtype]]


def build(item, W, x, O, variant="main", F="F0", common=None, baseline=False):
    """Return dict(turns=[(role, text), ...] ending with a user turn, labels, sure_label, meta) for one prompt.
    For NR with x1 the conversation has two user turns; the assistant's first answer is filled in by the caller
    ('{A1}' placeholder) so the conditional readout can be marginalised exactly."""
    common = common or load_common()
    d = load_wording(item, W, variant)
    rt = READOUT[item]
    sysm = common["system"]
    labels = sure_label = None
    if item == "P1":
        fr = d["frames"][f"x{x}"]
        first, second = fr["labels"]
        if O == "sure_first":
            lines, sure_label = [(first, fr["sure"]), (second, fr["risky"])], first
        else:
            lines, sure_label = [(first, fr["risky"]), (second, fr["sure"])], second
        body = d["stem"] + "\n" + "\n".join(t.replace("{L}", l) for l, t in lines) + "\n" + d["question"]
        labels = [first, second]
    elif item.startswith("P2"):
        body = d["intro"] + "\n\n" + (d["baseline"] if baseline else d["conditions"][f"x{x}"])
    elif item == "P3":
        body = d["conditions"][f"x{x}"] + "\n" + (d["scale_reversed"] if O == "reversed" else d["scale"])
    elif item == "P4":
        body = d["conditions"][f"x{x}"]
    elif item == "AF":
        body = d["conditions"][f"x{x}"]
        labels = list(d.get("options", ["Yes", "No"]))
    elif item == "QA":
        body = d["conditions"][f"x{x}"] + "\n" + d["question"] + "\n" + (d["scale_reversed"] if O == "reversed" else d["scale"])
    elif item == "NR":
        labels = list(d.get("options", ["Yes", "No"]))
        fl = fmt_line(common, rt, F, O)
        if x == 1:   # other-country question first; outcome = answer to the US question (second turn)
            turns = [("user", d["q_other"] + "\n\n" + fl), ("assistant", "{A1}"), ("user", d["q_us"] + "\n\n" + fl)]
        else:
            turns = [("user", d["q_us"] + "\n\n" + fl)]
        return dict(system=sysm, turns=turns, labels=labels, sure_label=None, readout=rt)
    else:
        raise KeyError(item)
    user = body + "\n\n" + fmt_line(common, rt, F, O)
    return dict(system=sysm, turns=[("user", user)], labels=labels, sure_label=sure_label, readout=rt)


def enumerate_prompts(items=ITEMS, wordings=WORDINGS, decoys=True, baselines=True):
    """All Arm L prompts: item x W x O x x (+ P2 no-anchor baselines per W and O, + decoys D1, D2 at W0)."""
    out = []
    for it in items:
        for W in wordings:
            for O in ORDERS.get(it, [None]):
                for x in (1, 0):
                    out.append(dict(item=it, W=W, O=O, x=x, variant="main"))
                if baselines and it.startswith("P2"):
                    out.append(dict(item=it, W=W, O=O, x=None, variant="baseline"))
        if decoys:
            for v in ("D1", "D2"):
                for O in ORDERS.get(it, [None]):
                    for x in (1, 0):
                        out.append(dict(item=it, W="W0", O=O, x=x, variant=v))
    for p in out:
        p["key"] = f'{p["item"]}|{p["W"]}|{p["O"]}|{p["x"]}|{p["variant"]}'
    return out


def build_from(p, common=None):
    if p["variant"] == "baseline":
        return build(p["item"], p["W"], 1, p["O"], "main", common=common, baseline=True)
    return build(p["item"], p["W"], p["x"], p["O"], p["variant"], common=common)
