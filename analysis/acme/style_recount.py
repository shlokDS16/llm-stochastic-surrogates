"""Recount of the novelty/knowledge-claim formula and abstract digits (CRP-S09 style guide).

Resolves the L1 (4 of 10) versus L3 (1 of 10) disagreement with ONE stated regex.
Run: python analysis/acme/style_recount.py   (reads research/relaunch/acme-style/texts/A*.md and paper/acme/*.tex)
Text is whitespace-normalised and curly apostrophes are folded before matching.
"""
import re, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# R_NARROW: the knowledge-claim formula itself.
R_NARROW = re.compile(r"\bto (?:the best of )?(?:our|the authors') knowledge\b", re.I)
# R_BROAD: R_NARROW plus other novelty/absence formulas.
R_BROAD = re.compile(
    R_NARROW.pattern
    + r"|\bas far as (?:we|the authors) (?:are aware|know|could (?:find|tell))\b"
    + r"|\b(?:we|the authors) (?:are not aware|found no|could find no)\b"
    + r"|\bin the literature we could access\b"
    + r"|\bno (?:previous|prior|existing) (?:study|work|review|survey)\b"
    + r"|\bthe first (?:review|study|survey|attempt)\b",
    re.I)

def norm(t):
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", t)

def tex_body(path):
    t = open(path, encoding="utf-8").read()
    t = re.sub("(?<!" + re.escape(chr(92)) + ")%.*", "", t)
    return norm(t)

rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "research/relaunch/acme-style/texts/A*.md"))):
    t = norm(open(f, encoding="utf-8").read())
    m = re.search(r"## Abstract (.*?) ## ", t)
    ab = m.group(1) if m else ""
    rows.append((os.path.basename(f)[:-3], len(t.split()), len(R_NARROW.findall(t)),
                 len(R_BROAD.findall(t)), len(re.findall(r"\d", ab))))
print("id   words narrow broad abstract_digit_chars")
for r in rows:
    print("%-4s %6d %6d %5d %6d" % r)
print("exemplars with narrow >=1: %d of %d" % (sum(r[2] > 0 for r in rows), len(rows)))
print("exemplars with broad  >=1: %d of %d" % (sum(r[3] > 0 for r in rows), len(rows)))
print("exemplar abstracts with no digit: %d of %d" % (sum(r[4] == 0 for r in rows), len(rows)))
print("--- ours (paper/acme/*.tex, comments removed) ---")
for f in sorted(glob.glob(os.path.join(ROOT, "paper/acme/*.tex"))):
    t = tex_body(f)
    n, b = len(R_NARROW.findall(t)), len(R_BROAD.findall(t))
    if n or b:
        print("%-32s narrow=%d broad=%d" % (os.path.basename(f), n, b))
