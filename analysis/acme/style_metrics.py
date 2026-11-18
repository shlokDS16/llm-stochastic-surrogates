"""Style metrics for the ACME style study (CRP-S09, stage 1).

Measures prose features of the exemplar texts (private, git-ignored, research/relaunch/acme-style/texts/*.md)
and of our draft (paper/acme/abstract.tex and 0*.tex, 1*.tex, LaTeX stripped), so the two can be compared.

Usage:
  python analysis/acme/style_metrics.py            # writes runs/acme-style/metrics.csv, metrics_sections.csv
                                                   # and research/relaunch/acme-style/COMPARISON.md
  python analysis/acme/style_metrics.py --selftest

All measures are heuristics on plain text; the passive-voice and hedge counts are regex based and
indicative, not exact. Citation markers are removed before words are counted, so numeric-bracket
exemplars and \\cite-based LaTeX are treated alike. No exemplar text is written to any output.
"""
import csv
import re
import statistics as st
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXTS = ROOT / "research/relaunch/acme-style/texts"
DRAFT = ROOT / "paper/acme"
RUNS = ROOT / "runs/acme-style"
DOCS = ROOT / "research/relaunch/acme-style"
CHECK = Path.home() / ".claude/skills/research-humanizer/scripts/check_text.py"

CITE_NUM = re.compile(r"\[(\d+(?:\s*[,\u2013\u2014-]\s*\d+)*)\]")
OPEN_CITE = re.compile(
    r"^(?:\[\d|[A-Z][A-Za-z'\u2019-]+(?: et al\.?| (?:and|&) [A-Z][A-Za-z'\u2019-]+)?,? [\(\[](?:\d|19|20))")
ABBR = ["et al.", "e.g.", "i.e.", "Fig.", "Figs.", "Eq.", "Eqs.", "Sec.", "Secs.", "Tab.", "vs.", "cf.", "approx.",
        "Dr.", "No.", "Ref.", "Refs.", "resp.", "etc.", "Vol.", "pp.", "ca.", "Prof.", "Ph.D.", "U.S."]
HEDGES = re.compile(
    r"\b(may|might|could|possibly|potentially|perhaps|likely|unlikely|probably|arguably|appears?|seems?|seemingly|"
    r"suggests?|suggested|indicates?|tends?|tended|generally|typically|usually|often|relatively|somewhat|roughly|"
    r"largely|mostly|presumably|apparently|partly|partially)\b", re.I)
PARTICIPLES = ("known made shown given seen found run built held kept taken done chosen drawn written set put read "
               "left led sent spent met paid said told understood become begun hidden broken fed lost bound "
               "split cut hit shut sought thought brought taught caught bought").split()
NOT_PART = set("often open even seven ten then when token tokens children between eleven green screen sudden golden "
               "kitchen indeed need needs speed feed seed proceed exceed succeed hundred thousand".split())
PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being|gets?|got)\s+(?:(?:not|also|then|thus|often|generally|"
                     r"commonly|typically|usually|widely|\w+ly)\s+){0,2}([a-z]+)\b", re.I)
NOMINAL = re.compile(r"^[a-z]{5,}(?:tions?|sions?|ments?|ness|ities|ity|ances?|ences?|isms?)$")
NOMINAL_STOP = set("experiment experiments environment environments instrument instruments department document documents "
                   "government comment comments moment moments element elements segment segments equipment argument arguments "
                   "reference references difference differences preference preferences presence absence evidence science "
                   "sciences audience conference conferences sentence sentences experience experiences silence licence "
                   "commence essence existence intelligence".split())
SYL = re.compile(r"[aeiouy]+")
OPENERS = {
    "this_these": re.compile(r"^(This|These)\b"),
    "the": re.compile(r"^(The)\b"),
    "we_our": re.compile(r"^(We|Our)\b"),
    "in": re.compile(r"^(In)\b"),
    "connective": re.compile(r"^(However|Moreover|Furthermore|Additionally|In addition|Therefore|Thus|Hence|Nevertheless|"
                             r"Consequently|Similarly|Likewise|Finally|Overall|Notably|Importantly)\b"),
    "subordinate": re.compile(r"^(While|Although|Whereas|Because|Since|If|When|As|Given|Despite|Unlike)\b"),
}
SECTION_TYPES = ["abstract", "intro", "background", "method", "body", "results", "discussion", "future", "conclusion"]


# ---------------------------------------------------------------- text preparation
def classify(title):
    t = re.sub(r"^[\d.\s]+", "", title.lower())
    rules = [("abstract", r"abstract"), ("intro", r"introduction"), ("conclusion", r"conclu|summary and|concluding"),
             ("future", r"challenge|future|outlook|perspective|open problem|limitation|recommend|research direction|"
                        r"opportunit|roadmap"),
             ("results", r"results"),
             ("discussion", r"discussion|implication|synthesis"),
             ("method", r"method|protocol|search strategy|literature search|selection process|review design"),
             ("background", r"background|preliminar|related|foundation|notation|definition|problem (statement|setting)|"
                            r"overview|formulation|basics|fundamental"),
             ("results", r"benchmark|numerical|experiment|results|case study|set-?up|assessment|evaluation|application|"
                         r"data and|analysis of results")]
    for name, pat in rules:
        if re.search(pat, t):
            return name
    return "body"


def md_sections(path):
    """Return list of (type, title, [lines]) from an exemplar markdown file (## = section)."""
    secs = []
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("## "):
            if re.match(r"## (Notes?|Supplementary|Electronic Supplementary)", line):
                secs.append(["skip", line[3:], []])
                continue
            secs.append([classify(line[3:]), line[3:], [line]])
        elif secs:
            secs[-1][2].append(line)
    return [(a, b, c) for a, b, c in secs if a != "skip"]


def strip_tex(src):
    """LaTeX to the same line-based plain format as the exemplars (headings, prose, lists, [EQ])."""
    s = re.sub(r"(?<!\\)%.*", "", src)
    for env in ("figure", "figure*", "table", "table*", "tabular", "tikzpicture", "algorithm", "lstlisting", "comment"):
        s = re.sub(r"\\begin\{%s\}.*?\\end\{%s\}" % (re.escape(env), re.escape(env)), "", s, flags=re.S)
    s = re.sub(r"\\begin\{(equation|align|gather|multline|eqnarray)\*?\}.*?\\end\{\1\*?\}", "\n\n[EQ]\n\n", s, flags=re.S)
    s = re.sub(r"\\\[.*?\\\]", "\n\n[EQ]\n\n", s, flags=re.S)
    s = re.sub(r"\$\$.*?\$\$", "\n\n[EQ]\n\n", s, flags=re.S)
    s = re.sub(r"\\(section|subsection|subsubsection)\*?\{((?:[^{}]|\{[^{}]*\})*)\}",
               lambda m: "\n\n@@H%d@@%s\n\n" % ({"section": 2, "subsection": 3, "subsubsection": 4}[m.group(1)], m.group(2)), s)
    s = re.sub(r"\\begin\{(itemize|enumerate)\}", lambda m: "\n\n@@L%s@@" % m.group(1), s)
    s = re.sub(r"\\end\{(itemize|enumerate)\}", "\n\n", s)
    s = re.sub(r"\\item\s*", "\n@@I@@", s)

    def cite(m):
        keys = [k for k in m.group(2).split(",") if k.strip()]
        body = "[" + ", ".join(str(i + 1) for i in range(len(keys))) + "]"
        return ("Xxxx et al. " + body) if m.group(1).startswith("citet") else body
    s = re.sub(r"\\(cite[a-z]*|Cref|cref|autocite|parencite|textcite)\*?(?:\[[^\]]*\])*\{([^}]*)\}",
               lambda m: cite(m) if m.group(1).startswith("cite") else "1", s)
    s = re.sub(r"\\(?:ref|eqref|autoref|pageref)\{[^}]*\}", "1", s)
    s = re.sub(r"\\NUM\{[^}]*\}", "12", s)
    s = re.sub(r"\\(?:TODO|captionTODO|label|footnote|index|vspace|hspace|noindent|centering|clearpage|newpage)\*?(\{(?:[^{}]|\{[^{}]*\})*\})?", "", s)
    s = re.sub(r"\\RQ\{(\d+)\}", r"RQ\1", s)
    s = s.replace("\\ML", "Many Labs 1")
    s = re.sub(r"\$[^$]*\$", " [m] ", s)
    s = re.sub(r"\\\([^)]*\\\)", " [m] ", s)
    for _ in range(3):
        s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)
    s = s.replace("~", " ").replace("``", '"').replace("''", '"').replace("---", " \u2014 ").replace("--", "\u2013")
    s = re.sub(r"[{}]", "", s).replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    lines, level = [], {"enumerate": 0}
    cur_list = None
    for blk in re.split(r"\n\s*\n", s):
        blk = blk.strip()
        if not blk:
            continue
        m = re.match(r"@@H(\d)@@(.*)", blk, flags=re.S)
        if m:
            lines.append(("H" + m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()))
            continue
        if blk.startswith("@@L"):
            cur_list = re.match(r"@@L(\w+)@@", blk).group(1)
            items = [i for i in blk.split("@@I@@")[1:]]
            for n, it in enumerate(items, 1):
                lines.append(("P", ("%d. " % n if cur_list == "enumerate" else "- ") + re.sub(r"\s+", " ", it).strip()))
            continue
        lines.append(("P", re.sub(r"\s+", " ", blk)))
    return lines


def tex_sections(files):
    """Our draft: one section per file, typed by file name; headings tracked for the heading metric."""
    typemap = {"abstract": "abstract", "01": "intro", "02": "background", "03": "method", "04": "body", "05": "body",
               "06": "body", "07": "results", "08": "discussion", "09": "future", "10": "future", "11": "conclusion"}
    out = []
    for f in files:
        key = "abstract" if f.stem == "abstract" else f.stem[:2]
        lines = strip_tex(f.read_text(encoding="utf8"))
        raw = []
        for kind, t in lines:
            raw.append(("#" * int(kind[1]) + " " if kind[0] == "H" else "") + t)
        out.append((typemap[key], f.stem, raw))
    return out


# ---------------------------------------------------------------- measures
def split_sentences(par):
    p = par
    for a in ABBR:
        p = p.replace(a, a.replace(".", "\u2024"))
    p = re.sub(r"\b([A-Z])\.(?=\s)", "\\1\u2024", p)
    parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[A-Z0-9])", p)
    return [x.replace("\u2024", ".").strip() for x in parts if len(x.strip()) > 1]


def n_refs(m):
    total = 0
    for chunk in re.split(r"\s*,\s*", m.group(1)):
        r = re.split(r"\s*[\u2013\u2014-]\s*", chunk)
        if len(r) == 2 and r[0].isdigit() and r[1].isdigit() and 0 < int(r[1]) - int(r[0]) < 40:
            total += int(r[1]) - int(r[0]) + 1
        else:
            total += 1
    return total


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019%.\-/]*", text)


def clean_for_words(s):
    s = CITE_NUM.sub(" ", s)
    s = s.replace("[m]", "X").replace("[EQ]", "")
    return re.sub(r"\s+", " ", s).strip()


def syllables(w):
    w = w.lower()
    n = len(SYL.findall(w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def measure(lines):
    """lines: list of raw lines ('## ' / '### ' headings, '- ', 'n. ' list items, '[EQ]', prose)."""
    heads, pars, listn, listb = [], [], 0, 0
    for ln in lines:
        ln = ln.strip()
        if not ln or ln == "[EQ]":
            continue
        if ln.startswith("#"):
            lvl = len(ln) - len(ln.lstrip("#"))
            t = re.sub(r"^[\d.\s]+", "", ln.lstrip("#").strip())
            if t.lower() != "abstract":
                heads.append((lvl, len(words(t))))
            continue
        if re.match(r"^\d+\.\s", ln):
            listn += 1
        elif ln.startswith("- "):
            listb += 1
        pars.append(ln)
    para_words, sents, cites_total, cite_groups = [], [], 0, 0
    for p in pars:
        cites_total += sum(n_refs(m) for m in CITE_NUM.finditer(p))
        cite_groups += len(CITE_NUM.findall(p))
        ps = split_sentences(p)
        sents.extend(ps)
        para_words.append(len(words(clean_for_words(p))))
    wl = [len(words(clean_for_words(s))) for s in sents]
    wl = [x for x in wl if x > 0]
    allw = [w for s in sents for w in words(clean_for_words(s))]
    n = max(1, len(allw))
    lower = [w.lower().strip(".,;:") for w in allw]
    passive = 0
    for s in sents:
        t = clean_for_words(s)
        for m in PASSIVE.finditer(t):
            w = m.group(1).lower()
            if w in NOT_PART:
                continue
            if (len(w) >= 5 and (w.endswith("ed") or w.endswith("en"))) or w in PARTICIPLES:
                passive += 1
                break
    we = sum(1 for s in sents if re.search(r"\b(We|we|Our|our|ours|us|ourselves)\b", clean_for_words(s)))
    we_n = len(re.findall(r"\b(?:We|we|Our|our|ours|ourselves)\b|\bus\b", " ".join(clean_for_words(s) for s in sents)))
    hedges = len(HEDGES.findall(" ".join(clean_for_words(s) for s in sents)))
    nom = sum(1 for w in lower if NOMINAL.match(w) and w not in NOMINAL_STOP and len(w) >= 8)
    alpha = [w for w in lower if w.isalpha()]
    syl = sum(syllables(w) for w in alpha)
    nsent = max(1, len(wl))
    fre = 206.835 - 1.015 * (len(alpha) / nsent) - 84.6 * (syl / max(1, len(alpha)))
    ops = {k: sum(1 for s in sents if rx.search(s)) / nsent for k, rx in OPENERS.items()}
    open_cite = sum(1 for s in sents if OPEN_CITE.search(s)) / nsent
    text_all = " ".join(clean_for_words(s) for s in sents)
    inline_enum = len(re.findall(r"\((?:i|ii|iii|iv|v|a|b|c|1|2|3)\)", text_all))
    ordinals = sum(1 for s in sents if re.match(r"^(First|Second|Third|Fourth|Fifth|Finally|Lastly)\b", s))
    h2 = [w for lv, w in heads if lv == 2]
    h3 = [w for lv, w in heads if lv >= 3]
    r = {
        "words": n, "sentences": len(wl), "paragraphs": len(para_words),
        "sent_mean": st.mean(wl) if wl else float("nan"), "sent_sd": st.pstdev(wl) if wl else float("nan"),
        "sent_p10": pct(wl, .1), "sent_p50": pct(wl, .5), "sent_p90": pct(wl, .9),
        "sent_over40_share": sum(1 for x in wl if x > 40) / nsent,
        "par_mean_words": st.mean(para_words) if para_words else float("nan"),
        "par_sent_mean": len(wl) / max(1, len(para_words)),
        "passive_share": passive / nsent,
        "we_sentence_share": we / nsent, "we_per_1000": 1000 * we_n / n,
        "hedges_per_1000": 1000 * hedges / n,
        "cites_per_100w": 100 * cites_total / n, "cite_groups_per_100w": 100 * cite_groups / n,
        "open_cite_share": open_cite,
        "open_this_these": ops["this_these"], "open_the": ops["the"], "open_we_our": ops["we_our"], "open_in": ops["in"],
        "open_connective": ops["connective"], "open_subordinate": ops["subordinate"],
        "nominal_per_100w": 100 * nom / n,
        "flesch": fre,
        "semicolon_per_1000": 1000 * text_all.count(";") / n, "colon_per_1000": 1000 * text_all.count(":") / n,
        "paren_per_1000": 1000 * text_all.count("(") / n, "digit_tokens_per_1000": 1000 * sum(1 for w in allw if re.search(r"\d", w)) / n,
        "headings_h2": len(h2), "headings_h3plus": len(h3),
        "words_per_h2": st.mean(h2) if h2 else float("nan"), "words_per_h3plus": st.mean(h3) if h3 else float("nan"),
        "words_per_heading": st.mean(h2 + h3) if (h2 + h3) else float("nan"),
        "numbered_items_per_1000": 1000 * listn / n, "bullet_items_per_1000": 1000 * listb / n,
        "inline_enum_per_1000": 1000 * inline_enum / n, "ordinal_openers_per_1000": 1000 * ordinals / n,
    }
    return r


def check_text_stats(lines, tag):
    """Run the research-humanizer checker on a plain-text copy; return its headline figures."""
    tmp = Path(tempfile.gettempdir()) / f"acme_style_{tag}.md"
    tmp.write_text("\n\n".join(l for l in lines if l.strip() and l.strip() != "[EQ]"), encoding="utf8")
    out = subprocess.run([sys.executable, str(CHECK), str(tmp)], capture_output=True, text=True, encoding="utf8").stdout
    g = lambda pat, i=1, cast=float: cast(re.search(pat, out).group(i)) if re.search(pat, out) else 0.0
    ai = 0
    blk = re.search(r"hits.*?:\n((?:\s+\d+  .*\n)+)", out)
    if blk:
        ai = sum(int(x) for x in re.findall(r"^\s+(\d+)  ", blk.group(1), flags=re.M))
    return {
        "ct_under12_pct": g(r"Under 12 words: (\d+) %"), "ct_over30_pct": g(r"Over 30 words: (\d+) %"),
        "ct_15to25_pct": g(r"In 15 to 25: (\d+) %"), "ct_over45_n": g(r"Sentences over 45 words: (\d+)"),
        "ct_dashes": g(r"dashes.*?: (\d+)"), "ct_ai_vocab_hits": ai,
        "ct_same_opener_runs": g(r"same opener: (\d+)"), "ct_bare_this": g(r"Bare 'This' \+ verb.*?: (\d+)"),
        "ct_trailing_participle": g(r"Trailing participle clauses.*?: (\d+)"),
    }


# ---------------------------------------------------------------- driver
def exemplar_docs():
    docs = {}
    for f in sorted(TEXTS.glob("A*.md")):
        secs = md_sections(f)
        docs[f.stem] = secs
    return docs


def our_doc():
    files = [DRAFT / "abstract.tex"] + sorted(DRAFT.glob("0*.tex")) + sorted(DRAFT.glob("1*.tex"))
    return tex_sections(files)


def fmt(x, d=2):
    return "nan" if x != x else (f"{x:.{d}f}")


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    docs = exemplar_docs()
    docs["OURS"] = our_doc()
    rows, srows = [], []
    for name, secs in docs.items():
        alllines = [l for _, _, ls in secs for l in ls]
        # level-2 heading marker is already in the lines; add the section title when absent (exemplars carry it)
        r = measure(alllines)
        r.update(check_text_stats(alllines, name))
        r["doc"] = name
        rows.append(r)
        by = {}
        for typ, title, ls in secs:
            by.setdefault(typ, []).extend(ls)
        for typ, ls in by.items():
            sr = measure(ls)
            sr["doc"], sr["section_type"] = name, typ
            srows.append(sr)
    cols = ["doc"] + [k for k in rows[0] if k != "doc"]
    with open(RUNS / "metrics.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    scols = ["doc", "section_type"] + [k for k in srows[0] if k not in ("doc", "section_type")]
    with open(RUNS / "metrics_sections.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=scols)
        w.writeheader()
        for r in srows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    write_comparison(rows, srows)
    print("wrote", RUNS / "metrics.csv", RUNS / "metrics_sections.csv", DOCS / "COMPARISON.md")


def write_comparison(rows, srows):
    ex = [r for r in rows if r["doc"] != "OURS"]
    ours = next(r for r in rows if r["doc"] == "OURS")
    keys = [k for k in ex[0] if k != "doc"]
    L = ["# Exemplar medians against our draft (CRP-S09 style, stage 1)", "",
         f"Exemplars: {len(ex)} ACME open-access articles (see CORPUS.md). Ours: paper/acme abstract and sections 1-11, LaTeX stripped. "
         "Regex heuristics; `ratio` is ours divided by the exemplar median. Generated by analysis/acme/style_metrics.py.", "",
         "## Whole document", "", "| measure | exemplar median | exemplar min | exemplar max | ours | ratio |", "|---|---|---|---|---|---|"]
    for k in keys:
        v = [r[k] for r in ex if r[k] == r[k]]
        if not v:
            continue
        med = st.median(v)
        ratio = ours[k] / med if med and ours[k] == ours[k] else float("nan")
        L.append(f"| {k} | {fmt(med)} | {fmt(min(v))} | {fmt(max(v))} | {fmt(ours[k])} | {fmt(ratio)} |")
    L += ["", "## By section type", "",
          "Medians over the exemplars that have a section of that type (n shown) against ours. Section types come from heading keywords "
          "for the exemplars and from the file for our draft (04-06 = body, 07 = results/own computation, 09-10 = future).", ""]
    sk = ["sent_mean", "passive_share", "we_per_1000", "hedges_per_1000", "cites_per_100w", "open_this_these", "nominal_per_100w"]
    L.append("| section type | n | words (median) | " + " | ".join(f"{k} ex / ours" for k in sk) + " |")
    L.append("|---|---|---|" + "---|" * len(sk))
    for typ in SECTION_TYPES:
        e = [r for r in srows if r["doc"] != "OURS" and r["section_type"] == typ and r["words"] >= 80]
        o = [r for r in srows if r["doc"] == "OURS" and r["section_type"] == typ]
        if not e or not o:
            continue
        cells = [f"{fmt(st.median(r[k] for r in e))} / {fmt(o[0][k])}" for k in sk]
        L.append(f"| {typ} | {len(e)} | {fmt(st.median(r['words'] for r in e), 0)} / {o[0]['words']} | " + " | ".join(cells) + " |")
    (DOCS / "COMPARISON.md").write_text("\n".join(L) + "\n", encoding="utf8")


def selftest():
    s = split_sentences("We used Fig. 3 and e.g. Eq. 2. It works [1, 2]. The end?")
    assert len(s) == 3, s
    assert n_refs(CITE_NUM.search("see [1, 3-5]")) == 4
    assert classify("2 Scoping Review Methodology") == "method"
    assert classify("Results and Discussion") == "results"
    lines = strip_tex(r"\section{Intro}" + "\n\nWe show $x$ \\cite{a,b}. It was done.\n\n\\begin{itemize}\\item one \\item two\\end{itemize}")
    assert lines[0] == ("H2", "Intro") and lines[1][1].startswith("We show"), lines
    m = measure(["## Intro", "We show X [1, 2]. It was done by hand.", "- one"])
    assert m["sentences"] == 3 and m["we_sentence_share"] > 0 and m["passive_share"] > 0
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
