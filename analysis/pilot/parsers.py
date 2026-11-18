"""Response parsers for the pilot. Every parser returns a dict:
   {value, valid, method, note}
value : parsed answer (letter for choices, float for numbers) or None
valid : bool, the response is usable as an observation
method: how the value was found ('answer_line', 'bare', 'prose', 'none', ...)
note  : short reason when invalid or when something unusual was accepted

Rules (fixed before any model output was seen):
* F0 (answer only): the answer must be the first thing in the text (leading markdown, quotes, brackets and the
  words "Program", "Answer", "about", "approximately", "around", "roughly", "~" are skipped).
  For choices a prose form "I would choose Program X" / "I choose X" is also accepted (method 'prose').
* F1 (reason, then "Answer: <x>"): the LAST "Answer:" marker is used; the value must follow it. A reply with no
  marker is invalid (no scanning of the reasoning text), because the format asked for the marker.
* Choices: exactly one letter from the labels shown in that prompt; letters from the other frame, or two
  different letters, are invalid.
* Numbers: first number after the skipped prefix; thousands separators (comma, thin space, underscore) removed;
  "k", "thousand", "million", "billion" multipliers applied; ranges ("2,000-3,000", "2,000 to 3,000") are
  invalid (midpoint is stored in note for sensitivity analysis); negative numbers invalid.
* Ratings: number between 1 and 9 inclusive (decimals allowed and noted).
"""
from __future__ import annotations

import re

_PREFIX = r"""^[\s\*\_\#\>\"'`\(\[\{:]*(?:-\s+)?[\s\*\_\#\>\"'`\(\[\{:]*(?:(?:the\s+)?(?:final\s+)?answer\s*(?:is)?\s*[:\-]?\s*)?[\s\*\_\"'`\(\[\{]*(?:(?:i\s+(?:would\s+)?(?:estimate|guess|say|think)(?:\s+(?:it|that|there)\s+(?:is|are|were|was))?(?:\s+about)?)\s*:?\s*)?(?:about|approximately|around|roughly|nearly|almost|~|≈|circa|ca\.)?\s*[\s\*\_\"'`\(\[\{]*"""
_PREFIX_RE = re.compile(_PREFIX, re.I)

_NUM = r"(?P<num>\d{1,3}(?:[,_   ]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
_MULT = r"(?:\s*(?P<mult>k\b|thousand\b|million\b|billion\b|m\b))?"
_NUM_RE = re.compile(_NUM + _MULT, re.I)
_RANGE_RE = re.compile(_NUM + _MULT + r"\s*(?:-|–|—|to|and|or)\s*" + r"(?P<num2>\d[\d,\.]*)" + r"(?:\s*(?P<mult2>k\b|thousand\b|million\b|billion\b))?", re.I)
_MULTS = {"k": 1e3, "thousand": 1e3, "million": 1e6, "m": 1e6, "billion": 1e9}
_ANSWER_MARK = re.compile(r"answer\s*:\s*", re.I)


def _to_float(num: str) -> float:
    s = re.sub(r"[,_   ]", "", num)
    return float(s)


def _strip(text: str) -> str:
    return (text or "").replace("’", "'").strip()


def final_segment(text: str, mode: str):
    """Return (segment, method). mode F0: whole text. F1: text after the last 'Answer:' marker."""
    t = _strip(text)
    if mode == "F0":
        return t, "bare"
    ms = list(_ANSWER_MARK.finditer(t))
    if not ms:
        return None, "none"
    seg = t[ms[-1].end():]
    # the answer is on that marker's line; later lines are ignored
    seg = seg.split("\n", 1)[0] if seg.split("\n", 1)[0].strip() else seg.strip().split("\n", 1)[0]
    return seg.strip(), "answer_line"


# ----------------------------------------------------------------------------- choices
def parse_choice(text: str, labels, mode: str):
    labels = [l.upper() for l in labels]
    seg, method = final_segment(text, mode)
    if seg is None:
        return dict(value=None, valid=False, method="none", note="no 'Answer:' marker")
    if not seg:
        return dict(value=None, valid=False, method=method, note="empty")
    s = _PREFIX_RE.sub("", seg, count=1)
    alt = "|".join(re.escape(l) for l in labels)
    # strict: label (optionally preceded by 'program') right at the start, followed by a non-letter or end
    m = None
    if s:
        # explicit 'Program X' (any case), or an upper-case letter followed by end/punctuation/newline, or a lone letter
        m = (re.match(r"program\s+([A-Za-z])(?![A-Za-z0-9])", s, re.I)
             or re.match(r"([A-Z])(?=\s*$|\s*[\.\,\:\;\!\)\]\*\"'_\-–—\n])", s)
             or re.match(r"([A-Za-z])$", s))
    if m:
        letter = m.group(1).upper()
        if letter in labels:
            return dict(value=letter, valid=True, method=method, note="")
        return dict(value=None, valid=False, method=method, note=f"label {letter} not offered")
    if mode == "F0":
        pm = re.search(rf"\b(?:i\s+(?:would\s+)?(?:choose|pick|select|go\s+with|prefer|opt\s+for)|choose|pick|select)\s+(?:program\s+)?({alt})\b", seg, re.I)
        if pm:
            others = {x.upper() for x in re.findall(rf"\bprogram\s+({alt})\b", seg, re.I)} - {pm.group(1).upper()}
            if not others:
                return dict(value=pm.group(1).upper(), valid=True, method="prose", note="")
            return dict(value=None, valid=False, method="prose", note="two labels")
    return dict(value=None, valid=False, method=method, note="no label at start")


# ----------------------------------------------------------------------------- numbers
def parse_number(text: str, mode: str, lo=None, hi=None, allow_zero=True):
    seg, method = final_segment(text, mode)
    if seg is None:
        return dict(value=None, valid=False, method="none", note="no 'Answer:' marker")
    if not seg:
        return dict(value=None, valid=False, method=method, note="empty")
    s = _PREFIX_RE.sub("", seg, count=1)
    s = re.sub(r"^[\$£€]\s*", "", s)
    mr = _RANGE_RE.match(s)
    if mr:
        try:
            a = _to_float(mr.group("num")) * _MULTS.get((mr.group("mult") or "").lower(), 1)
            b = _to_float(mr.group("num2")) * _MULTS.get((mr.group("mult2") or mr.group("mult") or "").lower(), 1)
            mid = (a + b) / 2
        except ValueError:
            mid = None
        return dict(value=None, valid=False, method=method, note=f"range; midpoint={mid}")
    m = _NUM_RE.match(s)
    if not m:
        w = _word_number(s)
        if w is not None:
            return _bounds(w, method, lo, hi, allow_zero, "number word")
        return dict(value=None, valid=False, method=method, note="no number at start")
    try:
        val = _to_float(m.group("num"))
    except ValueError:
        return dict(value=None, valid=False, method=method, note="bad number")
    mult = (m.group("mult") or "").lower()
    if mult == "m" and not re.match(r"m\b(?!i|e|y)", s[m.end("num"):].strip().lower() + " ", re.I):
        mult = ""
    val *= _MULTS.get(mult, 1)
    rest = s[m.end():]
    note = ""
    if re.match(r"\s*(?:-|–|—|to)\s*\d", rest):
        return dict(value=None, valid=False, method=method, note="range")
    if re.search(r"\d", re.sub(r"\([^)]*\)", "", rest)):
        note = "extra_numbers"
    return _bounds(val, method, lo, hi, allow_zero, note)


_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _word_number(s: str):
    m = re.match(r"([a-z]+)\b", s.strip().lower())
    return float(_WORDS[m.group(1)]) if m and m.group(1) in _WORDS else None


def _bounds(val, method, lo, hi, allow_zero, note):
    if val < 0 or (val == 0 and not allow_zero):
        return dict(value=None, valid=False, method=method, note="non-positive")
    if lo is not None and val < lo:
        return dict(value=None, valid=False, method=method, note=f"below {lo}")
    if hi is not None and val > hi:
        return dict(value=None, valid=False, method=method, note=f"above {hi}")
    if note == "" and val != int(val) and lo is not None:
        note = "non-integer"
    return dict(value=float(val), valid=True, method=method, note=note)


def parse_response(response_type: str, text: str, mode: str, labels=None):
    if response_type == "choice":
        return parse_choice(text, labels, mode)
    if response_type == "rating":
        return parse_number(text, mode, lo=1, hi=9)
    return parse_number(text, mode, allow_zero=True)
