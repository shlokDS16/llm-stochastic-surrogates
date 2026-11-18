"""List every place the manuscript mentions generative-AI use, with section, PDF page and exact sentence.

    python tools/ai_use_locations.py [--pdf research/review/sn-build.pdf] [--out research/review/ai-use-locations.md]

Sources of sentences: every line of paper/common/*.tex tagged "% AIU-n" (canonical or restated), and the "Use of generative
AI" entry in backmatter.tex. Pages: each sentence's first eight words, after LaTeX is stripped, are searched in the per-page
text of the built PDF (pdftotext; hyphenation and line breaks joined). A sentence whose words cannot be matched is listed
with page "?" so that nothing is dropped silently.
"""
import argparse
import sys
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BS = chr(92)
SEC = re.compile(re.escape(BS) + r"(sub)*section\*?\{([^}]*)\}")
BRAND = re.compile(r"\b(Claude|Codex|OLMo|Qwen|Haiku|Sonnet|Opus|Exa|Anthropic|OpenAI|gpt-6)\b")
ROLE = re.compile(r"\b(primary (coder|coding)|second (coder|coding)|classifiers? [ABC]|protocol critic|disagreement classifier|paraphrase writer|"
                  r"truncation reviewer|reference checker|search agent|abstract coder|drafting assistant|language-model|model (coder|rater)s?|generative AI|"
                  r"language models? (acting|screened|coded|classif))")
EXEMPT = re.compile(r"\b(Gemini|Llama|Mistral|GPT|families|family|Granite|grids?|cells?)\b")
WORKWORD = re.compile(r"\b(coder|coded|coding|rater|classif|agent|screen|drafted|debate|critic|judged|audit)", re.I)
TAG = re.compile(r"%\s*AIU-(\d+)(\s*\(restated\))?")


def macro_values():
    vals = {}
    pat = re.compile(re.escape(BS + "newcommand{" + BS) + r"([A-Za-z]+)\}\{([^}]*)\}")
    for f in ["paper/common/autonumbers.tex", "paper/common/macros.tex"]:
        for line in open(ROOT / f, encoding="utf-8"):
            m = pat.match(line)
            if m:
                vals[m.group(1)] = m.group(2).replace("{,}", ",")
    return vals


def plain(tex, vals):
    t = re.split(r"(?<!" + re.escape(BS) + r")%", tex, maxsplit=1)[0]
    t = re.sub(re.escape(BS) + r"cite[pt]?\{[^}]*\}", "#", t)
    t = re.sub(re.escape(BS) + r"ref\{[^}]*\}", "#", t)
    t = re.sub(re.escape(BS) + r"RQ\{(\d)\}", r"RQ\1", t)
    t = re.sub(re.escape(BS) + r"([A-Za-z]+)\{\}", lambda m: vals.get(m.group(1), ""), t)
    t = re.sub(re.escape(BS) + r"[A-Za-z]+\*?(\[[^]]*\])?\{([^}]*)\}", r"\2", t)
    t = re.sub(re.escape(BS) + r"[A-Za-z]+", "", t)
    t = t.replace("~", " ").replace("{", "").replace("}", "").replace("``", '"').replace("''", '"').replace("$", "")
    return re.sub(r"\s+", " ", t).strip()


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="research/review/sn-build.pdf")
    ap.add_argument("--out", default="research/review/ai-use-locations.md")
    a = ap.parse_args()
    vals = macro_values()
    sys.path.insert(0, str(ROOT / "tools" / "docx_build"))
    from texexpand import Expander, strip_comments
    ex = Expander()
    for nm in ["macros", "autonumbers", "abstract", "figures", "01-introduction", "02-background", "03-review-method", "04-results-review",
               "05-audit", "06-pilot", "07-discussion", "08-challenges", "09-limitations", "10-conclusion", "backmatter"]:
        ex.load(strip_comments((ROOT / "paper/common" / f"{nm}.tex").read_text(encoding="utf-8")))

    def expand_line(line):
        code = re.split(r"(?<!" + re.escape(BS) + r")%", line, maxsplit=1)[0]
        try:
            out = ex.expand(code).replace("{,}", ",")
            m = re.search(re.escape(BS) + r"caption\{", out)
            if m and BS + "begin{figure}" in out:  # a figure macro: the caption is the sentence
                from texexpand import read_group
                out = read_group(out, m.end() - 1)[0]
            return out
        except Exception:
            return code
    n_pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", a.pdf], capture_output=True, text=True, cwd=ROOT).stdout).group(1))
    pages = []
    for p in range(1, n_pages + 1):
        t = subprocess.run(["pdftotext", "-enc", "UTF-8", "-f", str(p), "-l", str(p), a.pdf, "-"], capture_output=True, text=True,
                           encoding="utf-8", cwd=ROOT).stdout
        pages.append(norm(re.sub(r"-\s*\n\s*", "", t)))
    rows = []
    last = 0
    order = ["abstract.tex"] + [f"{i:02d}" for i in range(1, 11)] + ["backmatter.tex", "figures.tex"]
    files = sorted((ROOT / "paper/common").glob("*.tex"), key=lambda f: next((i for i, k in enumerate(order) if f.name.startswith(k)), 99))
    for f in files:
        if f.name in ("autonumbers.tex", "macros.tex"):
            continue
        sec = ""
        in_ai = False
        in38 = False
        for i, line in enumerate(open(f, encoding="utf-8"), 1):
            m = SEC.search(line)
            if m:
                sec = plain(m.group(2), vals)
                in38 = "sec:method-ai" in line
            if f.name == "backmatter.tex":
                if "bmhead{Use of generative AI}" in line:
                    in_ai = True
                    sec = "Declarations: Use of generative AI"
                    continue
                if in_ai and line.lstrip().startswith(BS + "bmhead"):
                    in_ai = False
            tag = TAG.search(line)
            stripped = line.lstrip()
            if stripped.startswith(("%", BS + "providecommand", BS + "newcommand", BS + "renewcommand", BS + "todo", BS + "pending")):
                continue
            if "&" in line and not stripped.startswith((BS + "caption", BS + "newcommand")):
                continue  # table rows: coder column labels and studied model families are data, not statements about AI use
            text = plain(expand_line(line), vals)
            if not text:
                continue
            zone = "3.8" if in38 else ("Declarations" if in_ai else "elsewhere")
            for sent in ([text] if tag else re.split(r"(?<=[.])\s+(?=[A-Z])", text)):
                brand = bool(BRAND.search(sent))
                role = bool(ROLE.search(sent))
                if zone == "elsewhere" and not tag:
                    if brand and EXEMPT.search(sent):
                        brand = False
                    if brand and not WORKWORD.search(sent):
                        brand = False
                    if not (brand or role):
                        continue
                elif zone != "elsewhere" and not tag and not (in_ai or in38):
                    continue
                if zone == "elsewhere":
                    kind = "brand" if brand else "role"
                else:
                    kind = zone
                # match on the longest stretch without a citation or cross-reference (typeset differently), in document order
                chunk = max(sent.split("#"), key=lambda c: len(c.split()))
                words = norm(" ".join(chunk.split()[:8]))
                hit = next((k for k in range(last, len(pages)) if words and words in pages[k]), None)
                if hit is None:  # sentence split across a page break: match from the second word
                    words2 = norm(" ".join(chunk.split()[1:9]))
                    hit = next((k for k in range(last, len(pages)) if words2 and words2 in pages[k]), None)
                if hit is None:
                    hit = next((k for k, pt in enumerate(pages) if words and words in pt), None)
                pg = "?" if hit is None else str(hit + 1)
                if hit is not None:
                    last = hit
                sent = re.sub(r"\s*#\s*", " [ref] ", sent).replace(" [ref] .", " [ref].").strip()
                rows.append(dict(sec=sec or f.name, page=pg, kind=kind, tagged=bool(tag),
                                 aiu=(f"AIU-{tag.group(1)}" + (" (restated)" if tag.group(2) else "")) if tag else ("Declarations" if in_ai else "role label" if kind == "role" else "name"),
                                 src=f"{f.name}:{i}", text=sent))
    cnt = {k: sum(r["kind"] == k for r in rows) for k in ("3.8", "Declarations", "brand", "role")}
    md = ["# Where the manuscript mentions generative-AI use", "",
          f"Built PDF: `{a.pdf}` ({n_pages} pages). Generated by `tools/ai_use_locations.py`; rerun after every rebuild. "
          "Page \"?\" means the sentence was not found in the PDF text and must be checked by hand.", "",
          "Role labels are defined once in Methods 3.8 (classifier A, B, C; primary coder; second coder; protocol critic; disagreement classifier; "
          "paraphrase writer; truncation reviewer; reference checker; search agent; analysis and drafting assistant).", "",
          "| Where | Sentences |", "|---|---|",
          f"| Methods 3.8 (single record, brand names allowed) | {cnt['3.8']} |",
          f"| Declarations (brand names allowed) | {cnt['Declarations']} |",
          f"| Elsewhere, naming a brand (Claude, Codex, OLMo, Qwen, Exa, ...) | {cnt['brand']} |",
          f"| Elsewhere, role labels or generic AI wording only | {cnt['role']} |", ""]
    heads = {"3.8": "## Methods 3.8 and Declarations (the record of AI use)", "brand": "## Elsewhere: sentences that name a model or tool by brand",
             "role": "## Elsewhere: sentences that use role labels or generic wording only"}
    for kind in ("3.8", "brand", "role"):
        sel = [r for r in rows if (r["kind"] in ("3.8", "Declarations") if kind == "3.8" else r["kind"] == kind)]
        md += [heads[kind], "", "| # | Section | Page | Tag | Exact sentence (as typeset) | Source line |", "|---|---|---|---|---|---|"]
        for k, r in enumerate(sel, 1):
            md.append(f"| {k} | {r['sec']} | {r['page']} | {r['aiu']} | {r['text'].replace('|', '/')} | {r['src']} |")
        md.append("")
    md += [f"Total: {len(rows)} sentences in {len({r['sec'] for r in rows})} places; not found in the PDF: {sum(r['page'] == '?' for r in rows)}."]
    (ROOT / a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("3.8:", cnt["3.8"], "declarations:", cnt["Declarations"], "brand elsewhere:", cnt["brand"], "role elsewhere:", cnt["role"])
    print("\n".join(md[-1:]))


if __name__ == "__main__":
    main()
