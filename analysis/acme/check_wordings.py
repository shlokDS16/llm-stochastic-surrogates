"""Hard-gate invariants for the ACME wording universe (P1-CONTRACT.md, "Invariants").

    .venv/Scripts/python.exe -I analysis/acme/check_wordings.py [--out runs/acme-wordings/invariants.json]

For every paraphrase (W4-W9 of the 7 pilot items, W1-W9 of AF, QA, NR) and every overlay field (P2 `baseline`, P3 `scale_reversed`
of the pilot's frozen W0-W3) the script checks against W0 of the same item:
  * every numeral (digits, commas, fractions such as 1/3) and every number word of W0 appears in the paraphrase, and no new
    numeral or number word appears (set equality per pooled field group);
  * labels, `{L}` placeholders, option lists, frame names and condition names are unchanged;
  * AF keeps the forbid / allow verb in the right condition; QA keeps the quote text and the speaker names; NR keeps North Korea
    and which country is the subject of which question;
  * direction words of anchors (upper / lower bound), the scale end points of P3 and QA (forward and reversed), P2 baselines
    carry no anchor numeral;
  * hygiene: ASCII only, no tabs, no double or edge spaces; the 10 wordings of an item are pairwise different.
The pilot's frozen W1-W3 files are checked too, but only as information (they cannot be regenerated); their overlay fields are
part of the gate. Decoys get schema checks (they change meaning on purpose). Exit code 1 if any gate check fails.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter
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
PILOT_FROZEN = {"W0", "W1", "W2", "W3"}
OVERLAY_FIELDS = {"baseline", "scale_reversed"}

QUOTE = '"I have sworn to only live free, even if I find bitter the taste of death."'

# --------------------------------------------------------------------------- text helpers
WORD_NUMS = ("zero one two three four five six seven eight nine ten eleven twelve twenty hundred thousand million billion "
             "half halves third thirds quarter quarters twice double triple both pair dozen").split()
WORD_RE = re.compile(r"\b(" + "|".join(WORD_NUMS) + r")\b", re.I)


def numerals(text: str) -> set:
    """Digit numerals plus number words (the pronoun in 'no one' is not a number)."""
    t = re.sub(r"\bno one\b", "nobody", text, flags=re.I)
    digits = set(re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?", t))
    return digits | {w.lower() for w in WORD_RE.findall(t)}


def words(text: str) -> Counter:
    return Counter(re.findall(r"[a-z']+|\d+", text.lower()))


def has(pat: str, text: str) -> bool:
    return re.search(pat, text, re.I) is not None


def scale_labels(text: str) -> dict:
    """Text following each standalone numeral up to the next numeral, pooled per numeral."""
    pos = [(m.start(), m.group()) for m in re.finditer(r"(?<![\d,/])\d+(?![\d,/])", text)]
    out: dict = {}
    for i, (s, n) in enumerate(pos):
        end = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        out[n] = out.get(n, "") + " " + text[s + len(n):end]
    return out


# --------------------------------------------------------------------------- loading
def _yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf8"))


def path_of(item: str, w: str) -> Path:
    if item in PILOT_ITEMS and w in PILOT_FROZEN:
        return PILOT / w / f"{item}.yaml"
    return ACME / w / f"{item}.yaml"


def load(item: str, w: str) -> dict:
    d = _yaml(path_of(item, w))
    ov = ACME / "overlay" / w / f"{item}.yaml"
    if item in PILOT_ITEMS and w in PILOT_FROZEN and ov.exists():
        d.update(_yaml(ov))
    return d


def load_decoy(item: str, k: int) -> dict:
    return _yaml(ACME / "decoys" / f"{item}_D{k}.yaml")


# --------------------------------------------------------------------------- field maps and groups
def fields(item: str, d: dict) -> dict:
    if item == "P1":
        f = {"stem": d["stem"], "question": d["question"]}
        for x in ("x1", "x0"):
            f[f"{x}.sure"] = d["frames"][x]["sure"]
            f[f"{x}.risky"] = d["frames"][x]["risky"]
        return f
    if item.startswith("P2"):
        f = {"intro": d["intro"], "x1": d["conditions"]["x1"], "x0": d["conditions"]["x0"]}
        if "baseline" in d:
            f["baseline"] = d["baseline"]
        return f
    if item == "P3":
        f = {"x1": d["conditions"]["x1"], "x0": d["conditions"]["x0"], "scale": d["scale"]}
        if "scale_reversed" in d:
            f["scale_reversed"] = d["scale_reversed"]
        return f
    if item in ("P4", "AF"):
        return {"x1": d["conditions"]["x1"], "x0": d["conditions"]["x0"]}
    if item == "QA":
        return {"x1": d["conditions"]["x1"], "x0": d["conditions"]["x0"], "question": d["question"],
                "scale": d["scale"], "scale_reversed": d["scale_reversed"]}
    if item == "NR":
        return {"q_us": d["q_us"], "q_other": d["q_other"]}
    raise KeyError(item)


GROUPS = {"P1": [["stem", "question"], ["x1.sure"], ["x1.risky"], ["x0.sure"], ["x0.risky"]]}


def groups(item: str, fnames) -> list:
    g = GROUPS.get(item)
    if g:
        return g
    return [[n] for n in fnames]


def all_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from all_strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from all_strings(v)


# --------------------------------------------------------------------------- rules
UP = r"\b(shorter|less|fewer|under|below|smaller|lower)\b"
LOW = r"\b(longer|more|greater|over|above|larger|higher|taller)\b"
GAIN = r"sav|rescu|spared"
DIE = r"\b(die|dies|perish|death|deaths|dead|killed)\b"
US = r"United States|U\.S\."
GO = r"\b(game|match|attend\w*|go)\b"
HOME = r"\bhome\b"

P2_KEYS = {
    "P2a": [r"San Francisco", r"New York", r"miles"],
    "P2b": [r"Chicago"],
    "P2c": [r"Everest", r"feet"],
    "P2d": [US, r"babies|infants|newborns"],
}


def scale_dir_ok(item: str, text: str, reversed_: bool) -> str | None:
    """None if the scale text has the right end-point orientation, else a message."""
    L = scale_labels(text)
    l1, l9 = L.get("1", ""), L.get("9", "")
    if item == "P3":
        a, b = (GO, HOME) if reversed_ else (HOME, GO)   # what 1 and 9 mean
        if has(a, l1) and not has(b, l1) and has(b, l9) and not has(a, l9):
            return None
        return f"scale end points not oriented as {'reversed' if reversed_ else 'forward'} (1->{a}, 9->{b})"
    if item == "QA":
        pos = lambda s: has(r"(?<!dis)agree", s)       # noqa: E731
        neg = lambda s: has(r"disagree", s)            # noqa: E731
        ok1 = (neg(l1) and not pos(l1)) if reversed_ else (pos(l1) and not neg(l1))
        ok9 = (pos(l9) and not neg(l9)) if reversed_ else (neg(l9) and not pos(l9))
        if ok1 and ok9 and has(r"neither", L.get("5", "")):
            return None
        return "scale end points not oriented as " + ("reversed" if reversed_ else "forward")
    return "no scale rule"


def rules(item: str, d: dict, base: dict, w: str):
    """Yield (field, rule, ok, detail) for dict d against base (W0 of the item)."""
    f, fb = fields(item, d), fields(item, base)
    out = []

    def R(field, rule, ok, detail=""):
        out.append((field, rule, bool(ok), "" if ok else detail))

    # --- structure
    R("*", "keys", set(d) == set(base), f"keys {sorted(set(d) ^ set(base))}")
    R("*", "paradigm", d.get("paradigm") == base.get("paradigm"))
    R("*", "wording_id", d.get("wording") == w, f"wording={d.get('wording')}")
    R("*", "response_type", d.get("response_type") == base.get("response_type"))
    for k in ("condition_names", "options", "order_note"):
        if k in base:
            R("*", k, d.get(k) == base[k], f"{k} changed")
    if item == "P1":
        for x in ("x1", "x0"):
            R("*", f"frames.{x}.name_labels", d["frames"][x]["name"] == base["frames"][x]["name"]
              and d["frames"][x]["labels"] == base["frames"][x]["labels"], "frame name or labels changed")
    # --- hygiene
    for s in all_strings(d):
        if not s.isascii() or "\t" in s or "  " in s or s != s.strip() or "\n" in s:
            R("*", "hygiene", False, f"bad characters or spacing in {s[:50]!r}")
            break
    else:
        R("*", "hygiene", True)
    # --- numerals and number words
    for g in groups(item, f):
        g = [n for n in g if n in f and n in fb]
        if not g:
            continue
        a = set().union(*[numerals(f[n]) for n in g])
        b = set().union(*[numerals(fb[n]) for n in g])
        R("+".join(g), "numerals_equal_W0", a == b, f"missing {sorted(b - a)} new {sorted(a - b)}")
    # --- item specific
    if item == "P1":
        for x, kind in (("x1", "gain"), ("x0", "loss")):
            for line in ("sure", "risky"):
                n = f"{x}.{line}"
                t = f[n]
                R(n, "placeholder_L_once", t.count("{L}") == 1 and not re.search(r"\{(?!L\})", t), "needs exactly one {L}")
                R(n, "no_literal_label", not has(r"Program [A-D]\b", t), "literal program letter")
                R(n, "program_word", has(r"Program \{L\}", t), "'Program {L}' missing")
                if kind == "gain":
                    R(n, "gain_verb", has(GAIN, t) and not has(DIE, t), "gain frame must say saved, not die")
                else:
                    R(n, "loss_verb", has(DIE, t) and not has(GAIN, t), "loss frame must say die, not saved")
                if line == "risky":
                    R(n, "probability_word", has(r"probab|chance|likel|odds", t), "no probability word")
        R("stem", "united_states", has(US, f["stem"]))
        R("stem", "kill", has(r"kill|die|death|fatal|perish", f["stem"]))
        R("question", "is_question", f["question"].endswith("?"))
    elif item.startswith("P2"):
        for n in ("x1", "x0", "baseline"):
            if n not in f:
                continue
            for kp in P2_KEYS[item]:
                R(n, f"keyword[{kp}]", has(kp, f[n]), f"missing {kp}")
        R("x1", "upper_bound_direction", has(UP, f["x1"]) and not has(LOW, f["x1"]), "high anchor must be an upper bound")
        R("x0", "lower_bound_direction", has(LOW, f["x0"]) and not has(UP, f["x0"]), "low anchor must be a lower bound")
        R("intro", "no_numeral_in_intro", not numerals(f["intro"]))
        if "baseline" in f:
            R("baseline", "no_anchor_numeral", not numerals(f["baseline"]) and not re.search(r"\d", f["baseline"]),
              "baseline contains a numeral")
            R("baseline", "is_question", f["baseline"].endswith("?"))
        for n in ("x1", "x0"):
            R(n, "is_question", f[n].endswith("?"))
    elif item == "P3":
        R("x1", "paid", has(r"\bpaid\b", f["x1"]) and not has(r"\bfree\b", f["x1"]), "paid ticket condition")
        R("x0", "free_friend", has(r"\bfree\b", f["x0"]) and has(r"\bfriend\b", f["x0"]) and not has(r"\bpaid\b", f["x0"]),
          "free ticket condition")
        for n in ("x1", "x0"):
            R(n, "scenario", has("football", f[n]) and has(r"\b(game|match)\b", f[n]) and has("cold", f[n]) and has("ticket", f[n]),
              "football / game / cold / ticket missing")
            R(n, "ends_what_do_you_do", f[n].endswith("What do you do?"))
        m = scale_dir_ok("P3", f["scale"], False)
        R("scale", "direction_forward", m is None, m or "")
        if "scale_reversed" in f:
            m = scale_dir_ok("P3", f["scale_reversed"], True)
            R("scale_reversed", "direction_reversed", m is None, m or "")
            R("scale_reversed", "same_words_as_scale", words(f["scale"]) == words(f["scale_reversed"]), "word multiset differs")
    elif item == "P4":
        for n in ("x1", "x0"):
            R(n, "scenario", has("dice", f[n]) and has("casino", f[n]) and has("how many times", f[n]) and has(r"\bbefore\b", f[n]),
              "dice / casino / how many times / before missing")
    elif item == "AF":
        x1, x0 = f["x1"], f["x0"]
        R("x1", "verb_forbid", has("forbid", x1) and not has("allow", x1), "x1 must use forbid only")
        R("x0", "verb_allow", has("allow", x0) and not has("forbid", x0), "x0 must use allow only")
        for n in ("x1", "x0"):
            R(n, "topic", has(r"speech|address|talk", f[n]) and has("democracy", f[n]) and has(US + "|America", f[n]) and f[n].endswith("?"),
              "speeches / democracy / United States / question mark")
    elif item == "QA":
        x1, x0 = f["x1"], f["x0"]
        R("x1", "quote_verbatim", QUOTE in x1)
        R("x0", "quote_verbatim", QUOTE in x0)
        R("x1", "speaker_washington", "George Washington" in x1 and "Osama" not in x1)
        R("x0", "speaker_bin_laden", "Osama Bin Laden" in x0 and "Washington" not in x0)
        R("x1", "text_outside_quote_equal_between_conditions", x1.replace("George Washington", "{S}") == x0.replace("Osama Bin Laden", "{S}"),
          "conditions differ by more than the speaker")
        R("question", "agree_question", has(r"(?<!dis)agree", f["question"]) and has(r"quote|statement|saying", f["question"])
          and f["question"].endswith("?"))
        for n, rv in (("scale", False), ("scale_reversed", True)):
            m = scale_dir_ok("QA", f[n], rv)
            R(n, "direction_" + ("reversed" if rv else "forward"), m is None, m or "")
            R(n, "scale_points", set(scale_labels(f[n])) == {"1", "5", "9"}, "scale must name 1, 5 and 9")
        R("scale_reversed", "same_words_as_scale", words(f["scale"]) == words(f["scale_reversed"]), "word multiset differs")
    elif item == "NR":
        a, b = f["q_us"], f["q_other"]
        R("q_us", "us_asks_about_nk_reporters", has(US, a) and "North Korea" in a and not has("American", a) and not has("North Korean", a)
          and has(r"(reporters|journalists)\s+from\s+North Korea", a) and not has(r"from (the )?(United States|America)", a),
          "United States must be the host and North Korean reporters the visitors")
        R("q_other", "nk_asked_about_american_reporters", "North Korea" in b and not has("North Korean", b)
          and has(r"American (\w+ ){0,2}(reporters|journalists)", b) and not has(r"(reporters|journalists)\s+from\s+North Korea", b),
          "North Korea must be the host and American reporters the visitors")
        for n in ("q_us", "q_other"):
            R(n, "news_question", has("news", f[n]) and f[n].endswith("?"))
    return out


# --------------------------------------------------------------------------- driver
def check_one(item: str, w: str, kind: str, base: dict):
    d = load(item, w)
    res = rules(item, d, base, w)
    if kind.startswith("pilot_frozen"):
        gate = [r for r in res if r[0] in OVERLAY_FIELDS]
        info = [r for r in res if r[0] not in OVERLAY_FIELDS]
    else:
        gate, info = res, []
    return d, gate, info


def check_decoy(item: str, k: int, base: dict):
    d = load_decoy(item, k)
    res = []
    keys_ok = set(d) == set(base) | {"decoy_change"}
    res.append(("*", "keys", keys_ok, "" if keys_ok else f"keys {sorted(set(d) ^ (set(base) | {'decoy_change'}))}"))
    dc = d.get("decoy_change")
    res.append(("*", "decoy_change", isinstance(dc, str) and len(dc) > 10, "decoy_change missing"))
    res.append(("*", "wording_id", d.get("wording") == f"D{k}", f"wording={d.get('wording')}"))
    res.append(("*", "paradigm", d.get("paradigm") == base["paradigm"] and d.get("response_type") == base["response_type"],
                "paradigm or response_type changed"))
    b = {x: y for x, y in d.items() if x not in ("decoy_change", "wording")}
    differs = b != {x: y for x, y in base.items() if x != "wording"}
    res.append(("*", "differs_from_W0", differs, "decoy equals W0"))
    if item == "P1":
        ok = all(d["frames"][x][y].count("{L}") == 1 for x in ("x1", "x0") for y in ("sure", "risky"))
        res.append(("*", "placeholder_L_once", ok, "{L} count"))
    if item == "AF":
        res.append(("x1/x0", "verbs_kept", has("forbid", d["conditions"]["x1"]) and has("allow", d["conditions"]["x0"]), "decoy should keep verbs"))
    hy = all(s.isascii() for s in all_strings(d))
    res.append(("*", "hygiene", hy, "non-ASCII"))
    return d, res


def run() -> dict:
    files, summary = [], {}
    for item in ITEMS:
        base = load(item, "W0")
        texts = {}
        for w in WORDINGS:
            if item in PILOT_ITEMS and w in PILOT_FROZEN:
                kind = "pilot_frozen" if w != "W0" else "pilot_frozen_base"
            elif item in NEW_ITEMS and w == "W0":
                kind = "base_new"
            else:
                kind = "paraphrase"
            d, gate, info = check_one(item, w, kind, base)
            texts[w] = json.dumps(fields(item, d), sort_keys=True)
            files.append({"item": item, "wording": w, "kind": kind, "path": str(path_of(item, w).relative_to(ROOT)).replace("\\", "/"),
                          "gate_rules": len(gate), "gate_failed": [{"field": a, "rule": b, "detail": c} for a, b, ok, c in gate if not ok],
                          "info_rules": len(info), "info_failed": [{"field": a, "rule": b, "detail": c} for a, b, ok, c in info if not ok]})
        # pairwise distinctness of the 10 wordings
        dup = [(a, b) for a in WORDINGS for b in WORDINGS if a < b and texts[a] == texts[b]]
        files.append({"item": item, "wording": "ALL", "kind": "distinct", "path": "", "gate_rules": 1,
                      "gate_failed": [{"field": "*", "rule": "wordings_pairwise_distinct", "detail": str(dup)}] if dup else [],
                      "info_rules": 0, "info_failed": []})
        for k in (1, 2):
            d, res = check_decoy(item, k, base)
            files.append({"item": item, "wording": f"D{k}", "kind": "decoy", "path": f"analysis/acme/prompts/decoys/{item}_D{k}.yaml",
                          "gate_rules": len(res), "gate_failed": [{"field": a, "rule": b, "detail": c} for a, b, ok, c in res if not ok],
                          "info_rules": 0, "info_failed": []})
    for item in ITEMS:
        fs = [x for x in files if x["item"] == item]
        summary[item] = {
            "files": len(fs),
            "gate_rules": sum(x["gate_rules"] for x in fs),
            "gate_failed": sum(len(x["gate_failed"]) for x in fs),
            "files_with_gate_failure": sum(1 for x in fs if x["gate_failed"]),
            "paraphrase_files": sum(1 for x in fs if x["kind"] == "paraphrase"),
            "paraphrase_files_passing": sum(1 for x in fs if x["kind"] == "paraphrase" and not x["gate_failed"]),
            "info_failed_pilot_frozen": sum(len(x["info_failed"]) for x in fs),
        }
    tot = {k: sum(v[k] for v in summary.values()) for k in ("files", "gate_rules", "gate_failed", "files_with_gate_failure",
                                                              "paraphrase_files", "paraphrase_files_passing", "info_failed_pilot_frozen")}
    return {"generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "total": tot, "per_item": summary, "files": files}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "runs/acme-wordings/invariants.json"))
    a = ap.parse_args(argv)
    rep = run()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1), encoding="utf8")
    t = rep["total"]
    print(f"gate rules {t['gate_rules']}, gate failures {t['gate_failed']} in {t['files_with_gate_failure']} files; "
          f"paraphrase files passing {t['paraphrase_files_passing']}/{t['paraphrase_files']}; "
          f"informational flags on frozen pilot W1-W3: {t['info_failed_pilot_frozen']}")
    for x in rep["files"]:
        for f in x["gate_failed"]:
            print("FAIL", x["item"], x["wording"], f["field"], f["rule"], f["detail"])
    return 1 if t["gate_failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
