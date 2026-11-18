"""Parsers for Arm S of the new items, written before any model output on these items was seen (2026-11-06).
Ratings reuse the pilot parser unchanged (1 to 9). Yes/No: F0 - the first word after the pilot's skipped prefix (markdown, quotes,
'Answer:') must be yes or no (case-insensitive); F1 - the last 'Answer:' marker is used, as in the pilot. Anything else is invalid.
"""
from __future__ import annotations

import re

import parsers as P   # analysis/pilot/parsers.py

_YN = re.compile(r"^(yes|no)\b", re.I)


def parse_yesno(text, mode):
    seg, method = P.final_segment(text, mode)
    if seg is None:
        return dict(value=None, valid=False, method="none", note="no 'Answer:' marker")
    s = P._strip(seg)
    s = P._PREFIX_RE.sub("", s, count=1)
    m = _YN.match(s)
    if not m:
        return dict(value=None, valid=False, method=method, note="no yes/no at start")
    return dict(value=m.group(1).capitalize(), valid=True, method=method, note="")


def parse(rtype, text, mode):
    if rtype == "yesno":
        return parse_yesno(text, mode)
    return P.parse_response("rating", text, mode)
