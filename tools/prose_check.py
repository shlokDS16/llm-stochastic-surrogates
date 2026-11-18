#!/usr/bin/env python
"""prose_check.py: a free, local substitute for Grammarly Premium on LaTeX manuscripts.

Pipeline
  1. LaTeX -> plain text. The .tex file is cut into chunks at blank lines (never inside a
     begin/end pair); each chunk keeps its first source line number. Project macros
     (paper/common/macros.tex, autonumbers.tex) are expanded, citations become "[1]" (\\citep)
     or "Smith et al." (\\citet), cross-references become "1", display and non-trivial inline
     math become "x", headings become one-sentence paragraphs, figure/table/equation
     environments are skipped (captions are kept). All chunks go through ONE pandoc call
     (`pandoc -f latex -t plain --wrap=none`), separated by marker paragraphs.
  2. Three checkers run on the plain text: LanguageTool (language_tool_python, local server,
     en-GB, picky level), Harper (harper-cli, british), Vale (proselint, write-good, Microsoft,
     and the custom ACME style built from the research-humanizer catalogues).
  3. Flags are mapped back to source lines. METHOD: the chunk of the flag is known exactly
     (start line); inside the chunk, the flagged sentence and then the flagged text are searched
     in the alphanumeric-only, lower-cased text of each source line. Result is a line number
     plus a confidence tag: span (flagged text found), sentence (sentence found), chunk (only the
     chunk start line is known). Approximate by design; column is not reported.
  4. Protection: no suggestion is shown that changes digits, citation markers or defined terms;
     spelling flags on defined terms, acronyms, CamelCase words and tokens with digits are dropped;
     flags that fall wholly inside a placeholder are dropped.
  5. Overlapping flags from different checkers are merged (the higher severity is kept, the
     others are listed under "also").
  6. Output: reports/prose/<name>.md and .json.

Usage (project venv):
  .venv/Scripts/python.exe tools/prose_check.py paper/common/01-introduction.tex
  .venv/Scripts/python.exe tools/prose_check.py paper/common --only grammar,punctuation
"""
from __future__ import annotations

import argparse
import bisect
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "tools" / "bin"
VALE_EXE = BIN / "vale" / "vale.exe"
HARPER_EXE = BIN / "harper" / "harper-cli.exe"
LT_DIR = next(iter(sorted((BIN / "languagetool").glob("LanguageTool-*"))), None)
VALE_INI = ROOT / "tools" / "vale" / ".vale.ini"
TERMS_FILE = ROOT / "tools" / "prose_terms.txt"
AI_EXEMPT_FILE = ROOT / "tools" / "prose_ai_exempt.txt"
MACRO_FILES = [ROOT / "paper" / "common" / "macros.tex", ROOT / "paper" / "common" / "autonumbers.tex"]
OUT_DIR = ROOT / "reports" / "prose"
PANDOC_FALLBACK = Path(r"C:\Users\Shlok\AppData\Local\Pandoc\pandoc.exe")
DEFAULT_EXCLUDE = {"macros.tex", "autonumbers.tex", "figures.tex"}

CATEGORIES = ["grammar", "punctuation", "spelling", "style", "clarity", "AI-pattern"]
SEV_NAME = {3: "high", 2: "medium", 1: "low"}
SEV_NUM = {"high": 3, "medium": 2, "low": 1}
CHECKER_ORDER = {"languagetool": 0, "harper": 1, "vale": 2}

# --------------------------------------------------------------------------- rule -> category

# LanguageTool category id -> (category, severity)
LT_CATEGORY = {
    "TYPOS": ("spelling", 3),
    "GRAMMAR": ("grammar", 3),
    "CONFUSED_WORDS": ("grammar", 3),
    "SEMANTICS": ("grammar", 3),
    "AGREEMENT": ("grammar", 3),
    "COMPOUNDING": ("spelling", 2),
    "PUNCTUATION": ("punctuation", 2),
    "CASING": ("grammar", 2),
    "TYPOGRAPHY": ("punctuation", 1),
    "COLLOCATIONS": ("grammar", 2),
    "NONSTANDARD_PHRASES": ("style", 1),
    "REDUNDANCY": ("clarity", 1),
    "PLAIN_ENGLISH": ("clarity", 1),
    "STYLE": ("style", 1),
    "REPETITIONS_STYLE": ("style", 1),
    "WIKIPEDIA": ("style", 1),
    "MISC": ("style", 1),
    "BRITISH_ENGLISH": ("spelling", 2),
    "AMERICAN_ENGLISH": ("spelling", 2),
}
LT_ENABLED_CATEGORIES = {
    "STYLE", "PLAIN_ENGLISH", "REDUNDANCY", "COLLOCATIONS", "CONFUSED_WORDS", "TYPOGRAPHY",
    "PUNCTUATION", "GRAMMAR", "TYPOS", "CASING", "SEMANTICS", "MISC", "NONSTANDARD_PHRASES",
    "REPETITIONS_STYLE", "COMPOUNDING", "BRITISH_ENGLISH",
}
# Rules that are noise on plain text converted from LaTeX (extend after reading the benchmark).
LT_DISABLED_RULES = {"WHITESPACE_RULE", "COMMA_PARENTHESIS_WHITESPACE", "EN_UNPAIRED_BRACKETS",
                     "SERIAL_COMMA_ON", "OXFORD_SPELLING_Z_NOT_S", "REP_PASSIVE_VOICE", "EN_REPEATEDWORDS_SEVERAL",
                     "PROBLEM_SOLVE_HYPHEN", "NOT_THE_SAME", "NOT_ACCEPT", "OBTAIN"}
# Prefixes dropped after the call: house-style conventions this manuscript does not follow (British -ise,
# no serial comma) and thesaurus-style suggestions that were wrong in the benchmark.
LT_DROP_PREFIXES = ("OXFORD_SPELLING", "SERIAL_COMMA_ON", "EN_REPEATEDWORDS_", "REP_PASSIVE")

# Harper rules that were wrong on academic prose in the benchmark (reports/prose/BENCHMARK.md)
HARPER_IGNORE = ["OxfordComma", "DisjointPrefixes", "SplitWords", "NoFrenchSpaces", "EllipsisLength", "CompoundNouns",
                 "AnA", "MassNouns", "ThatThan", "NounVerbConfusion", "MissingPreposition", "CriteriaPhenomena",
                 "NumericRangeEnDash"]

# Harper lint kind -> (category, severity)
HARPER_KIND = {
    "Spelling": ("spelling", 3), "Typo": ("spelling", 3), "BoundaryError": ("spelling", 2),
    "Grammar": ("grammar", 3), "Agreement": ("grammar", 3), "Eggcorn": ("grammar", 2),
    "Malapropism": ("grammar", 2), "WordChoice": ("grammar", 2), "Capitalization": ("grammar", 2),
    "Repetition": ("grammar", 2), "Punctuation": ("punctuation", 2), "Formatting": ("punctuation", 1),
    "Readability": ("clarity", 1), "Redundancy": ("clarity", 1), "Style": ("style", 1),
    "Enhancement": ("style", 1), "Usage": ("style", 1), "Nonstandard": ("style", 1),
    "Miscellaneous": ("style", 1), "Regionalism": ("style", 1),
}

# Vale: rule -> category. ACME.* is explicit; other styles by prefix with a few overrides.
VALE_ACME = {
    "AIVocab": "AI-pattern", "AIVocabSoft": "AI-pattern", "AIPhrases": "AI-pattern",
    "VagueAttribution": "AI-pattern", "TrailingParticiple": "AI-pattern", "HedgeStack": "AI-pattern",
    "Booster": "AI-pattern", "NegativeParallel": "AI-pattern", "ConnectiveStack": "AI-pattern",
    "EmDash": "AI-pattern", "Copula": "AI-pattern", "Attractor": "AI-pattern", "ChatResidue": "AI-pattern",
    "Wordy": "clarity", "Redundant": "clarity", "Intensifier": "clarity", "EmptyOpener": "clarity",
    "LongSentence": "clarity", "Grammar": "grammar",
}
VALE_OVERRIDE = {
    "Microsoft.Wordiness": "clarity", "Microsoft.Adverbs": "clarity", "Microsoft.Hyphens": "punctuation",
    "Microsoft.Dashes": "punctuation", "Microsoft.Ellipses": "punctuation", "Microsoft.OxfordComma": "punctuation",
    "Microsoft.Semicolon": "punctuation", "Microsoft.SentenceLength": "clarity", "Microsoft.Spacing": "punctuation",
    "Microsoft.RangeFormat": "punctuation", "Microsoft.Ranges": "punctuation", "Microsoft.Plurals": "grammar",
    "Microsoft.Negative": "style", "Microsoft.Contractions": "style",
    "proselint.Typography": "punctuation", "proselint.DateCase": "punctuation",
    "proselint.Spelling": "spelling", "proselint.Hyperbole": "style", "proselint.Very": "clarity",
    "write-good.Illusions": "grammar", "write-good.ThereIs": "clarity", "write-good.Weasel": "clarity",
    "write-good.Passive": "style", "write-good.TooWordy": "clarity", "write-good.Cliches": "style",
    "write-good.So": "style", "write-good.Adverbs": "clarity",
}
VALE_LEVEL = {"error": 3, "warning": 2, "suggestion": 1}

# --------------------------------------------------------------------------- small utilities


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def free_ram_gb() -> float:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPhys / 1024 ** 3


def nz(s: str) -> str:
    """Alphanumeric-only, lower-cased form used to match plain text against source lines."""
    return re.sub(r"[^0-9a-z]+", "", s.lower())


def strip_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*$", "", line)


def read_braced(s: str, i: int) -> tuple[str, int]:
    """s[i] must be '{'. Return (content, index after the closing brace)."""
    depth = 0
    j = i
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], n


def load_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            out.append(ln)
    return out


# --------------------------------------------------------------------------- macros


def parse_macros(paths: list[Path]) -> dict[str, tuple[int, str]]:
    macros: dict[str, tuple[int, str]] = {}
    for p in paths:
        if not p.exists():
            continue
        txt = "\n".join(strip_comment(ln) for ln in p.read_text(encoding="utf8").splitlines())
        for m in re.finditer(r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\s*(?:\[(\d)\])?\s*\{", txt):
            body, _ = read_braced(txt, m.end() - 1)
            if re.search(r"\\(input|resizebox|includegraphics|tabledir)", body):
                continue
            macros[m.group(1)] = (int(m.group(2) or 0), body)
    return macros


def clean_value(v: str) -> str:
    v = v.replace("{,}", ",").replace("\\%", "%").replace("\\,", " ").replace("\\ ", " ")
    return v


def expand_macros(text: str, macros: dict[str, tuple[int, str]]) -> str:
    for _ in range(3):
        out = []
        i = 0
        changed = False
        for m in re.finditer(r"\\([A-Za-z]+)(?![A-Za-z])", text):
            if m.start() < i or m.group(1) not in macros:
                continue
            n, body = macros[m.group(1)]
            out.append(text[i:m.start()])
            j = m.end()
            if n == 0:
                mm = re.match(r"\s*\{\}", text[j:])
                if mm:
                    j += mm.end()
                out.append(clean_value(body))
            elif n == 1:
                k = j
                while k < len(text) and text[k] == " ":
                    k += 1
                if k < len(text) and text[k] == "{":
                    arg, j = read_braced(text, k)
                    out.append(clean_value(body).replace("#1", arg))
                else:
                    out.append(text[m.start():j])
            else:
                out.append(text[m.start():j])
            i = j
            changed = True
        out.append(text[i:])
        text = "".join(out)
        if not changed:
            break
    return text


# --------------------------------------------------------------------------- LaTeX -> plain

SKIP_ENVS = {"figure", "figure*", "table", "table*", "tabular", "tabularx", "longtable", "equation",
             "equation*", "align", "align*", "gather", "gather*", "multline", "multline*", "eqnarray",
             "eqnarray*", "lstlisting", "verbatim", "tikzpicture", "algorithm", "algorithmic",
             "thebibliography", "sidewaystable", "sidewaysfigure"}
DROP_LINE = re.compile(r"^\s*(?:\}%?\s*$|\\(newcommand|renewcommand|providecommand|def|usepackage|input|include|"
                       r"bibliographystyle|bibliography|graphicspath|documentclass|setlength|"
                       r"begin\{document\}|end\{document\}|maketitle|label|clearpage|newpage)\b)")
CITE_RE = re.compile(r"\\(cite[a-zA-Z]*|parencite|textcite|autocite|footcite)\*?\s*(?:\[[^\]]*\]\s*){0,2}\{[^}]*\}")
REF_RE = re.compile(r"\\(?:[cC]ref|ref|autoref|eqref|pageref|nameref|vref)\*?\{[^}]*\}")
TEXTUAL_CITES = ("citet", "citeauthor", "textcite", "citealt", "citeyearpar")


@dataclass
class Chunk:
    idx: int
    first_line: int
    last_line: int
    lines: list[tuple[int, str]]  # (lineno, comment-stripped source)
    kind: str = "para"            # para | caption
    plain: str = ""
    keys: list[tuple[int, str]] = field(default_factory=list)  # (lineno, nz text)


def chunk_tex(src_lines: list[str]) -> list[Chunk]:
    chunks: list[Chunk] = []
    cur: list[tuple[int, str]] = []
    stack: list[str] = []
    skip_depth = 0
    cap_buf: list[tuple[int, str]] = []

    def flush() -> None:
        nonlocal cur
        if cur:
            chunks.append(Chunk(len(chunks), cur[0][0], cur[-1][0], cur))
        cur = []

    for no, raw in enumerate(src_lines, start=1):
        line = strip_comment(raw)
        for m in re.finditer(r"\\(begin|end)\{([^}]*)\}", line):
            kind, name = m.group(1), m.group(2)
            if kind == "begin":
                stack.append(name)
                if name in SKIP_ENVS:
                    skip_depth += 1
            elif stack:
                if name in stack:
                    while stack:
                        top = stack.pop()
                        if top in SKIP_ENVS:
                            skip_depth -= 1
                        if top == name:
                            break
        if skip_depth > 0 or any(re.search(r"\\(begin|end)\{%s\}" % re.escape(e), line) for e in SKIP_ENVS):
            # keep captions inside skipped environments
            if "\\caption" in line or cap_buf:
                cap_buf.append((no, line))
                joined = " ".join(t for _, t in cap_buf)
                mm = re.search(r"\\caption\*?(?:\[[^\]]*\])?\s*\{", joined)
                if mm:
                    content, end = read_braced(joined, mm.end() - 1)
                    if end <= len(joined) and joined[mm.end() - 1:].count("{") <= joined[mm.end() - 1:].count("}"):
                        flush()
                        chunks.append(Chunk(len(chunks), cap_buf[0][0], cap_buf[-1][0],
                                            [(n_, content if k == 0 else "") for k, (n_, _) in enumerate(cap_buf)],
                                            kind="caption"))
                        cap_buf = []
                if len(cap_buf) > 12:
                    cap_buf = []
            continue
        if DROP_LINE.match(line):
            continue
        if line.strip() == "" and not stack:
            flush()
            continue
        if line.strip() == "":
            continue
        cur.append((no, line))
    flush()
    return chunks


def simple_math(inner: str) -> str:
    inner = inner.strip()
    if re.fullmatch(r"[\d\s.,+\-−%\[\]()<>=±]+", inner):
        return inner
    return "x"


CODE_TOKENS: set[str] = set()  # words found in texttt, verb and path commands: identifiers, not prose
CODE_RE = re.compile(r"\\(?:texttt|path|code|verb\*?|lstinline)\s*(?:\{([^{}]*)\}|([|!+])(.*?)\2)")


def prep_text(text: str, macros: dict[str, tuple[int, str]]) -> str:
    t = expand_macros(text, macros)
    for m in CODE_RE.finditer(t):
        for w in re.findall(r"[A-Za-z0-9]+", m.group(1) or m.group(3) or ""):
            CODE_TOKENS.add(w.lower())
    t = re.sub(r"\$\$.*?\$\$", " x ", t, flags=re.S)
    t = re.sub(r"\\\[.*?\\\]", " x ", t, flags=re.S)
    t = re.sub(r"\\\(.*?\\\)", "x", t, flags=re.S)
    t = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: simple_math(m.group(1)), t, flags=re.S)

    def cite(m: re.Match) -> str:
        return "Smith et al." if m.group(1) in TEXTUAL_CITES else "[1]"

    t = CITE_RE.sub(cite, t)
    t = re.sub(r"Smith et al\.\s*\.", "Smith et al.", t)
    t = REF_RE.sub("1", t)
    t = re.sub(r"\\url\{[^}]*\}", "URL", t)
    t = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\textcolor\{[^}]*\}\{([^}]*)\}", r"\1", t)
    # footnotes -> parenthetical
    while True:
        m = re.search(r"\\footnote\s*\{", t)
        if not m:
            break
        content, end = read_braced(t, m.end() - 1)
        t = t[:m.start()] + " (" + content + ")" + t[end:]
    # headings -> one-sentence paragraphs
    while True:
        m = re.search(r"\\(?:section|subsection|subsubsection|paragraph|subparagraph|chapter)\*?\s*(?:\[[^\]]*\])?\s*\{", t)
        if not m:
            break
        content, end = read_braced(t, m.end() - 1)
        content = content.strip()
        if content and content[-1] not in ".?!:":
            content += "."
        t = t[:m.start()] + "\n\n" + content + "\n\n" + t[end:]
    return t


def line_key(line: str, macros: dict[str, tuple[int, str]]) -> str:
    t = prep_text(line, macros)
    t = re.sub(r"\\[A-Za-z]+\*?", " ", t)
    t = t.replace("~", " ")
    return nz(t)


def find_pandoc() -> str:
    p = shutil.which("pandoc")
    if p:
        return p
    if PANDOC_FALLBACK.exists():
        return str(PANDOC_FALLBACK)
    raise SystemExit("pandoc not found")


MARK_RE = re.compile(r"^MKR(\d{5})MKR$", re.M)


def tex_to_plain(path: Path, macros: dict[str, tuple[int, str]]) -> tuple[str, list[dict]]:
    """Return (plain text, segments). Segment: {start, end, chunk}."""
    src_lines = path.read_text(encoding="utf8", errors="replace").splitlines()
    chunks = chunk_tex(src_lines)
    parts = []
    for ch in chunks:
        body = "\n".join(t for _, t in ch.lines)
        ch.keys = [(n, line_key(t, macros)) for n, t in ch.lines if t.strip()]
        prepped = prep_text(body, macros).strip()
        if not re.search(r"[A-Za-z]{2}", re.sub(r"\\[A-Za-z]+", "", prepped)):
            ch.plain = ""
            continue
        parts.append(f"MKR{ch.idx:05d}MKR\n\n{prepped}")
    combined = "\n\n".join(parts)
    cmd = [find_pandoc(), "-f", "latex", "-t", "plain", "--wrap=none", "--eol=lf"]
    res = subprocess.run(cmd, input=combined.encode("utf8"), capture_output=True)
    if res.returncode != 0:
        # one chunk has unbalanced LaTeX: convert chunk by chunk and skip the ones pandoc rejects
        log(f"warning: pandoc rejected the combined input of {path.name}; converting chunk by chunk")
        pieces = []
        for part in parts:
            r1 = subprocess.run(cmd, input=part.encode("utf8"), capture_output=True)
            if r1.returncode == 0:
                pieces.append(r1.stdout)
            else:
                log("warning: chunk skipped (pandoc error): " + part.split("\n", 2)[0])
        res.stdout = b"\n\n".join(pieces)
    out = res.stdout.decode("utf8").replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
    marks = list(MARK_RE.finditer(out))
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(out)
        chunks[int(m.group(1))].plain = out[m.end():end].strip()
    text_parts, segments, pos = [], [], 0
    for ch in chunks:
        if not ch.plain:
            continue
        start = pos
        text_parts.append(ch.plain)
        pos += len(ch.plain)
        segments.append({"start": start, "end": pos, "chunk": ch})
        text_parts.append("\n\n")
        pos += 2
    return "".join(text_parts), segments


# --------------------------------------------------------------------------- flags


@dataclass
class Flag:
    start: int
    end: int
    checker: str
    rule: str
    category: str
    severity: int
    message: str
    suggestions: list[str]
    text: str = ""
    also: list[str] = field(default_factory=list)
    line: int = 0
    line_method: str = ""
    context: str = ""
    note: str = ""


def lt_flags(text: str, segments: list[dict], heap: str, min_free: float) -> tuple[list[Flag], str]:
    free = free_ram_gb()
    if free < min_free:
        return [], f"skipped: free RAM {free:.1f} GB < {min_free:.1f} GB required to start the LanguageTool JVM"
    if LT_DIR is None:
        return [], "skipped: LanguageTool not found under tools/bin/languagetool"
    os.environ["LTP_JAR_DIR_PATH"] = str(LT_DIR)
    os.environ["JAVA_TOOL_OPTIONS"] = f"-Xmx{heap}"
    import language_tool_python as ltp  # noqa: WPS433

    flags: list[Flag] = []
    t0 = time.time()
    tool = ltp.LanguageTool("en-GB")
    try:
        tool.picky = True
        tool.enabled_categories = set(LT_ENABLED_CATEGORIES)
        tool.disabled_rules = set(LT_DISABLED_RULES)
        # batches of whole segments, <= 12k characters, offsets shifted back
        batch_start, batch_end = None, None
        batches: list[tuple[int, int]] = []
        for seg in segments:
            if batch_start is None:
                batch_start, batch_end = seg["start"], seg["end"]
            elif seg["end"] - batch_start <= 12000:
                batch_end = seg["end"]
            else:
                batches.append((batch_start, batch_end))
                batch_start, batch_end = seg["start"], seg["end"]
        if batch_start is not None:
            batches.append((batch_start, batch_end))
        for bs, be in batches:
            for m in tool.check(text[bs:be]):
                cat_id = getattr(m, "category", "") or ""
                cat, sev = LT_CATEGORY.get(cat_id, ("style", 1))
                rid = m.rule_id
                if rid.startswith(LT_DROP_PREFIXES):
                    continue
                if rid.startswith(("MORFOLOGIK", "HUNSPELL", "GB_SPELLING")):
                    cat, sev = "spelling", 3
                s = bs + m.offset
                e = s + m.error_length
                flags.append(Flag(s, e, "languagetool", rid, cat, sev, m.message or "",
                                  list(m.replacements[:3]), text[s:e]))
    finally:
        tool.close()
    return flags, f"ok: {len(flags)} raw flags in {time.time() - t0:.0f} s (LanguageTool {LT_DIR.name.split('-', 1)[-1]}, en-GB, picky, -Xmx{heap})"


def harper_flags(text: str, tmp: Path) -> tuple[list[Flag], str]:
    if not HARPER_EXE.exists():
        return [], "skipped: harper-cli not found"
    f = tmp / "h.txt"
    with open(f, "w", encoding="utf8", newline="\n") as fh:
        fh.write(text)
    udict = tmp / "harper_dict.txt"
    udict.write_text("\n".join(load_terms(TERMS_FILE)) + "\n", encoding="utf8")
    fdir = tmp / "harper_files"
    fdir.mkdir(exist_ok=True)
    t0 = time.time()
    res = subprocess.run([str(HARPER_EXE), "lint", "--format", "json", "--quiet", "-d", "british",
                          "--ignore", ",".join(HARPER_IGNORE), "-u", str(udict), "-f", str(fdir), str(f)], capture_output=True, text=True,
                         encoding="utf8")
    try:
        data = json.loads(res.stdout[res.stdout.index("["):])
    except Exception:
        return [], "error: harper output unreadable: " + (res.stderr or res.stdout)[-300:]
    flags: list[Flag] = []
    for doc in data:
        for lint in doc.get("lints", []):
            s, e = lint["span"]["char_start"], lint["span"]["char_end"]
            if text[s:e] != lint.get("matched_text", text[s:e]):
                idx = text.find(lint["matched_text"], max(0, s - 40))
                if idx >= 0:
                    s, e = idx, idx + len(lint["matched_text"])
            cat, sev = HARPER_KIND.get(lint["kind"], ("style", 1))
            sugg = [re.sub(r"^(Replace with|Insert|Remove):?\s*", "", x).strip("“”\"` ") for x in lint.get("suggestions", [])[:3]]
            flags.append(Flag(s, e, "harper", lint["rule"], cat, sev, lint["message"], sugg, text[s:e]))
    return flags, f"ok: {len(flags)} raw flags in {time.time() - t0:.0f} s (harper-cli 3.0.0, british)"


def vale_flags(text: str, tmp: Path) -> tuple[list[Flag], str]:
    if not VALE_EXE.exists():
        return [], "skipped: vale not found"
    vocab = VALE_INI.parent / "styles" / "config" / "vocabularies" / "ACME" / "accept.txt"
    vocab.parent.mkdir(parents=True, exist_ok=True)
    vocab.write_text(chr(10).join(load_terms(TERMS_FILE)) + chr(10), encoding="utf8")
    f = tmp / "v.txt"
    with open(f, "w", encoding="utf8", newline="\n") as fh:
        fh.write(text)
    t0 = time.time()
    res = subprocess.run([str(VALE_EXE), "--config", str(VALE_INI), "--output=JSON", "--no-exit", str(f)],
                         capture_output=True, text=True, encoding="utf8")
    try:
        data = json.loads(res.stdout)
    except Exception:
        return [], "error: vale output unreadable: " + (res.stderr or res.stdout)[-300:]
    line_off = [0]
    for ln in text.split("\n"):
        line_off.append(line_off[-1] + len(ln) + 1)
    flags: list[Flag] = []
    for _, alerts in data.items():
        for a in alerts:
            check, match = a["Check"], a.get("Match", "")
            ln = a["Line"]
            base = line_off[ln - 1] if 0 < ln <= len(line_off) else 0
            s = base + a["Span"][0] - 1
            if text[s:s + len(match)].lower() != match.lower():
                seg_end = line_off[ln] if ln < len(line_off) else len(text)
                idx = text.lower().find(match.lower(), base, seg_end)
                if idx < 0:
                    idx = text.lower().find(match.lower(), max(0, s - 200))
                if idx >= 0:
                    s = idx
            lead = len(match) - len(match.lstrip())
            s += lead
            e = s + len(match.strip())
            style, _, name = check.partition(".")
            if style == "ACME":
                cat = VALE_ACME.get(name, "style")
            else:
                cat = VALE_OVERRIDE.get(check, "style")
            sev = VALE_LEVEL.get(a.get("Severity", "suggestion"), 1)
            sugg = []
            act = a.get("Action") or {}
            if act.get("Name") == "replace" and act.get("Params"):
                sugg = [p for p in act["Params"] if isinstance(p, str)][:3]
            flags.append(Flag(s, e, "vale", check, cat, sev, a["Message"], sugg, text[s:e]))
    return flags, f"ok: {len(flags)} raw flags in {time.time() - t0:.0f} s (vale 3.26.0)"


# --------------------------------------------------------------------------- post-processing

NUM_RE = re.compile(r"\d[\d,.]*")
CITE_TOKEN_RE = re.compile(r"\[\d+\]|Smith et al\.")


def is_defined_term_token(tok: str, terms_lc: set[str]) -> str | None:
    if tok.lower() in terms_lc:
        return "defined term"
    if "-" in tok:
        for part in tok.split("-"):
            if part and (part.lower() in terms_lc or part.lower() in CODE_TOKENS or part.isupper() or any(c.isdigit() for c in part)):
                return "hyphenated compound containing a defined term"
    if any(ch.isdigit() for ch in tok):
        return "token with digits"
    if len(tok) >= 2 and tok.isupper():
        return "acronym"
    if re.search(r"[a-z][A-Z]", tok) or re.match(r"^[A-Z][a-z]+[A-Z]", tok):
        return "CamelCase name"
    if tok in {"x", "URL", "et", "al"} or len(tok) == 1:
        return "placeholder or single symbol"
    if tok.lower() in CODE_TOKENS:
        return "identifier in texttt or code"
    return None


def protect(flags: list[Flag], text: str, terms: list[str], ai_exempt: list[str]) -> tuple[list[Flag], Counter]:
    terms_lc = {t.lower() for t in terms}
    exempt_lc = {t.lower() for t in ai_exempt}
    terms_cs = [t for t in terms if len(t) > 1]
    kept: list[Flag] = []
    dropped: Counter = Counter()
    placeholder_spans = [(m.start(), m.end()) for m in CITE_TOKEN_RE.finditer(text)]
    for f in flags:
        span = text[f.start:f.end]
        # wholly inside a placeholder
        if any(ps <= f.start and f.end <= pe for ps, pe in placeholder_spans):
            dropped["inside citation placeholder"] += 1
            continue
        if f.checker == "vale" and f.rule in ("ACME.AIVocab", "ACME.AIVocabSoft") and span.strip().lower() in exempt_lc:
            dropped["AI vocabulary used as a technical term (tools/prose_ai_exempt.txt)"] += 1
            continue
        if f.category == "spelling":
            toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", span)
            reason = None
            if len(toks) == 1:
                reason = is_defined_term_token(toks[0], terms_lc)
            if span.strip().lower() in terms_lc:
                reason = "defined term"
            if reason:
                dropped[f"spelling: {reason}"] += 1
                continue
        # suggestion protection
        overlaps_ph = any(f.start < pe and ps < f.end for ps, pe in placeholder_spans)
        safe = []
        withheld = False
        for s in f.suggestions:
            if Counter(NUM_RE.findall(s)) != Counter(NUM_RE.findall(span)):
                withheld = True
                continue
            if Counter(CITE_TOKEN_RE.findall(s)) != Counter(CITE_TOKEN_RE.findall(span)):
                withheld = True
                continue
            if any(t in span and t not in s for t in terms_cs):
                withheld = True
                continue
            safe.append(s)
        if overlaps_ph and f.suggestions:
            safe, withheld = [], True
        if withheld:
            f.note = "suggestion withheld: would change a number, citation marker or defined term"
        f.suggestions = safe
        kept.append(f)
    return kept, dropped


def overlap_ratio(a: Flag, b: Flag) -> float:
    ov = min(a.end, b.end) - max(a.start, b.start)
    if ov <= 0:
        return 1.0 if (a.start == b.start and (a.end == a.start or b.end == b.start)) else 0.0
    return ov / max(1, min(a.end - a.start, b.end - b.start))


FAMILY = {"style": "sc", "clarity": "sc"}


def merge_flags(flags: list[Flag]) -> list[Flag]:
    flags = sorted(flags, key=lambda f: (f.start, -(f.end - f.start)))
    kept: list[Flag] = []
    for f in flags:
        target = None
        for k in reversed(kept):
            if k.end <= f.start and f.start - k.end > 400:
                break
            same_cat = k.category == f.category or (FAMILY.get(k.category) and FAMILY.get(k.category) == FAMILY.get(f.category))
            if same_cat and overlap_ratio(k, f) >= 0.5:
                target = k
                break
        if target is None:
            kept.append(f)
            continue
        better = (f.severity, -CHECKER_ORDER[f.checker]) > (target.severity, -CHECKER_ORDER[target.checker])
        if better:
            f.also = target.also + [f"{target.checker}:{target.rule}"]
            for s in target.suggestions:
                if s not in f.suggestions and len(f.suggestions) < 3:
                    f.suggestions.append(s)
            kept[kept.index(target)] = f
        else:
            target.also.append(f"{f.checker}:{f.rule}")
            for s in f.suggestions:
                if s not in target.suggestions and len(target.suggestions) < 3:
                    target.suggestions.append(s)
    return kept


def sentence_bounds(text: str, s: int, e: int, lo: int, hi: int) -> tuple[int, int]:
    a = max([text.rfind(x, lo, s) + len(x) for x in (". ", "? ", "! ", ": ", "\n") if text.rfind(x, lo, s) >= 0] or [lo])
    ends = [text.find(x, e, hi) for x in (". ", "? ", "! ", "\n")]
    ends = [x + 1 for x in ends if x >= 0]
    b = min(ends) if ends else hi
    return a, b


def locate(flags: list[Flag], text: str, segments: list[dict]) -> None:
    starts = [s["start"] for s in segments]
    for f in flags:
        i = bisect.bisect_right(starts, f.start) - 1
        if i < 0:
            continue
        seg = segments[i]
        ch: Chunk = seg["chunk"]
        keys = [(n, k) for n, k in ch.keys if k]
        joined = "".join(k for _, k in keys)
        bounds, pos = [], 0
        for n, k in keys:
            bounds.append((pos, pos + len(k), n))
            pos += len(k)

        def line_at(p: int) -> int:
            for a, b, n in bounds:
                if a <= p < b:
                    return n
            return ch.first_line

        a, b = sentence_bounds(text, f.start, f.end, seg["start"], seg["end"])
        f.context = text[a:b].strip()
        sent = nz(text[a:b])
        span = nz(text[f.start:f.end])
        f.line, f.line_method = ch.first_line, "chunk"
        sp = joined.find(sent[:40]) if len(sent) >= 12 else -1
        if sp >= 0:
            f.line, f.line_method = line_at(sp), "sentence"
            if len(span) >= 3:
                q = joined.find(span, sp)
                if q >= 0 and q < sp + len(sent) + 5:
                    f.line, f.line_method = line_at(q), "span"
        elif len(span) >= 6:
            q = joined.find(span)
            if q >= 0:
                f.line, f.line_method = line_at(q), "span"


# --------------------------------------------------------------------------- reports


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def passage(f: Flag, width: int = 70) -> str:
    ctx, span = f.context, f.text
    if span and span in ctx:
        i = ctx.index(span)
        pre = ctx[max(0, i - width):i]
        post = ctx[i + len(span):i + len(span) + width]
        return ("..." if i > width else "") + pre + "**" + span + "**" + post + ("..." if len(ctx) > i + len(span) + width else "")
    return ctx[:2 * width]


def summarise(flags: list[Flag]) -> dict:
    by_checker = Counter(f.checker for f in flags)
    by_cat = Counter(f.category for f in flags)
    by_sev = Counter(SEV_NAME[f.severity] for f in flags)
    matrix = {c: Counter(f.category for f in flags if f.checker == c) for c in CHECKER_ORDER}
    return {"total": len(flags), "by_checker": dict(by_checker), "by_category": dict(by_cat),
            "by_severity": dict(by_sev), "checker_x_category": {c: dict(v) for c, v in matrix.items()}}


def write_reports(name: str, src: Path, flags: list[Flag], status: dict, dropped: Counter,
                  only: list[str] | None, out_dir: Path, raw_counts: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    flags = sorted(flags, key=lambda f: (-f.severity, f.line, f.start))
    summ = summarise(flags)
    rel = os.path.relpath(src, ROOT).replace("\\", "/")
    payload = {"file": rel, "generated": time.strftime("%Y-%m-%d %H:%M:%S"), "filter_only": only,
               "line_mapping": "chunk-exact, sentence/span search in alphanumeric-only source lines (approximate)",
               "checkers": status, "raw_flags_by_checker": raw_counts,
               "suppressed_by_protection": dict(dropped), "summary": summ,
               "flags": [{"n": i + 1, "line": f.line, "line_method": f.line_method,
                          "severity": SEV_NAME[f.severity], "checker": f.checker, "rule": f.rule,
                          "category": f.category, "text": f.text, "message": f.message,
                          "suggestions": f.suggestions, "also": f.also, "note": f.note,
                          "sentence": f.context} for i, f in enumerate(flags)]}
    (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf8")

    md = [f"# Prose check: {rel}", "",
          f"Generated {payload['generated']}. Filter: {', '.join(only) if only else 'none'}. "
          f"Line numbers: {payload['line_mapping']}.", "", "## Checkers", ""]
    for c, s in status.items():
        md.append(f"- {c}: {s}")
    md += ["", "## Summary", "", f"Flags after protection, merging and filter: **{summ['total']}**. "
           f"Severity: " + ", ".join(f"{k} {summ['by_severity'].get(k, 0)}" for k in ("high", "medium", "low")) + ".", ""]
    cats = [c for c in CATEGORIES if summ["by_category"].get(c)]
    md.append("| checker | " + " | ".join(cats) + " | total |")
    md.append("|---|" + "---|" * (len(cats) + 1))
    for c in CHECKER_ORDER:
        row = summ["checker_x_category"].get(c, {})
        md.append(f"| {c} | " + " | ".join(str(row.get(k, 0)) for k in cats) + f" | {summ['by_checker'].get(c, 0)} |")
    md.append("| all (after merge) | " + " | ".join(str(summ["by_category"].get(k, 0)) for k in cats) + f" | {summ['total']} |")
    if dropped:
        md += ["", "Suppressed by protection (not shown): " + "; ".join(f"{k} {v}" for k, v in dropped.items()) + "."]
    md += ["", "## Flagged passages (sorted by severity, then source line)", "",
           "| # | line | sev | checker | rule | category | passage | message | suggestion |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i, f in enumerate(flags, 1):
        sugg = "; ".join(f.suggestions) if f.suggestions else ("(withheld)" if f.note else "")
        also = f" (also {', '.join(f.also)})" if f.also else ""
        md.append(f"| {i} | {f.line}{'~' if f.line_method == 'chunk' else ''} | {SEV_NAME[f.severity]} | {f.checker} | "
                  f"{esc(f.rule)}{esc(also)} | {f.category} | {esc(passage(f))} | {esc(f.message)} | {esc(sugg)} |")
    path = out_dir / f"{name}.md"
    path.write_text("\n".join(md) + "\n", encoding="utf8")
    return path


# --------------------------------------------------------------------------- driver


def collect_inputs(p: Path, recursive: bool, exclude: set[str]) -> list[Path]:
    if p.is_file():
        return [p]
    it = p.rglob("*.tex") if recursive else p.glob("*.tex")
    return sorted(x for x in it if x.name not in exclude and "archive" not in x.parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help=".tex file or directory of .tex files")
    ap.add_argument("--only", help="comma list of categories: " + ",".join(CATEGORIES))
    ap.add_argument("--checkers", default="lt,harper,vale", help="subset of lt,harper,vale")
    ap.add_argument("--min-severity", choices=["low", "medium", "high"], default="low")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--exclude", default=",".join(sorted(DEFAULT_EXCLUDE)), help="file names skipped in a directory run")
    ap.add_argument("--min-free-gb", type=float, default=6.0, help="start LanguageTool only if this much RAM is free")
    ap.add_argument("--lt-heap", default="1g", help="LanguageTool JVM heap cap")
    ap.add_argument("--terms", default=str(TERMS_FILE), help="defined-terms file, one per line")
    ap.add_argument("--save-plain", action="store_true", help="write <name>.plain.txt next to the report")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    only = [c.strip() for c in args.only.split(",")] if args.only else None
    if only:
        bad = [c for c in only if c not in CATEGORIES]
        if bad:
            raise SystemExit(f"unknown category {bad}; choose from {CATEGORIES}")
    want = {c.strip() for c in args.checkers.split(",")}
    inputs = collect_inputs(Path(args.input), args.recursive, {x for x in args.exclude.split(",") if x})
    if not inputs:
        raise SystemExit("no .tex files found")
    terms = load_terms(Path(args.terms))
    ai_exempt = load_terms(AI_EXEMPT_FILE)
    macros = parse_macros(MACRO_FILES)
    out_dir = Path(args.out_dir)
    index_rows = []

    for src in inputs:
        log(f"== {src}")
        text, segments = tex_to_plain(src, macros)
        name = src.stem
        if args.save_plain:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{name}.plain.txt").write_text(text, encoding="utf8")
        status, all_flags, raw_counts = {}, [], {}
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            if "lt" in want:
                fl, st = lt_flags(text, segments, args.lt_heap, args.min_free_gb)
                status["languagetool"], raw_counts["languagetool"] = st, len(fl)
                all_flags += fl
            if "harper" in want:
                fl, st = harper_flags(text, tmp)
                status["harper"], raw_counts["harper"] = st, len(fl)
                all_flags += fl
            if "vale" in want:
                fl, st = vale_flags(text, tmp)
                status["vale"], raw_counts["vale"] = st, len(fl)
                all_flags += fl
        flags, dropped = protect(all_flags, text, terms, ai_exempt)
        flags = merge_flags(flags)
        locate(flags, text, segments)
        if only:
            flags = [f for f in flags if f.category in only]
        flags = [f for f in flags if f.severity >= SEV_NUM[args.min_severity]]
        path = write_reports(name, src, flags, status, dropped, only, out_dir, raw_counts)
        s = summarise(flags)
        index_rows.append((name, s))
        print(f"{src.name}: {s['total']} flags -> {os.path.relpath(path, ROOT)}")
    if len(inputs) > 1:
        lines = ["# Prose check: directory summary", "", "| file | total | high | medium | low | " + " | ".join(CATEGORIES) + " |",
                 "|---|---|---|---|---|" + "---|" * len(CATEGORIES)]
        for name, s in index_rows:
            lines.append(f"| [{name}]({name}.md) | {s['total']} | " + " | ".join(str(s['by_severity'].get(k, 0)) for k in ("high", "medium", "low"))
                         + " | " + " | ".join(str(s['by_category'].get(c, 0)) for c in CATEGORIES) + " |")
        (out_dir / "_summary.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
