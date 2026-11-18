"""Build the ACME submission package (Springer Nature, class sn-jnl [iicol], sn-basic.bst).

    python tools/package_acme.py flatten            # step 1: flat source tree in submission/acme/source/
    python tools/package_acme.py build              # step 2: clean build in a fresh copy outside the project, PDFs, report
    python tools/package_acme.py zip                # step 3: zip of the source tree (after hygiene on the figure PDFs)

`flatten` copies the ACME wrapper (paper/journals/acme/main.tex, sn-jnl.cls, sn-basic.bst), the body files and the
bibliography from paper/acme/, the tables paper/acme/tables/tab-*.tex and the figures paper/acme/figures/fig-*.pdf into one
folder with no subfolders (the Springer Nature system forbids subfolders). The three path macros of main.tex become empty.
Comments are removed (internal paths, decision numbers and process notes must not go to the editors); a trailing comment keeps
its bare % so that the spacing of the typeset text does not change. Prose is never touched.

`build` copies source/ to a fresh folder in the system temp directory (no access to the project tree), runs
pdflatex, bibtex, pdflatex, pdflatex there, checks the log (errors, undefined references and citations, overfull boxes), runs a
second, final-mode pass (\\def\\ACMEFINAL{1}) only to list what the authors must still fill, splits the combined PDF into
manuscript.pdf (main text) and ESM_1.pdf (supplement), copies the generated main.bbl back into source/, and writes
submission/acme/build-report.txt. Files in source/ that the build never read are listed (not deleted).
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACME = ROOT / "paper" / "acme"
WRAP = ROOT / "paper" / "journals" / "acme"
OUT = ROOT / "submission" / "acme"
SRC = OUT / "source"

BODY_TEX = [
    "macros.tex", "autonumbers.tex", "abstract.tex", "floats.tex", "notation.tex", "declarations.tex", "supplement.tex",
    "01-introduction.tex", "02-background.tex", "03-review-method.tex", "04-state-of-art-specification.tex",
    "05-state-of-art-validation.tex", "06-uncertainty-audit.tex", "07-benchmark.tex", "08-discussion.tex",
    "09-challenges.tex", "10-limitations.tex", "11-conclusion.tex",
]
PATH_MACROS = [
    ("\\newcommand{\\acmedir}{../../acme/}", "\\newcommand{\\acmedir}{}"),
    ("\\newcommand{\\figdir}{../../acme/figures/}", "\\newcommand{\\figdir}{}"),
    ("\\newcommand{\\tabdir}{../../acme/tables/}", "\\newcommand{\\tabdir}{}"),
]


def strip_tex_comments(text: str) -> str:
    """Drop comment-only lines; cut a trailing comment back to a bare % (keeps the text before it, spaces included)."""
    out = []
    for line in text.split("\n"):
        cut = None
        i = 0
        while i < len(line):
            c = line[i]
            if c == "\\":
                i += 2
                continue
            if c == "%":
                cut = i
                break
            i += 1
        if cut is None:
            out.append(line)
        elif line[:cut].strip() == "":
            continue
        else:
            out.append(line[:cut] + "%")
    return "\n".join(out)


def strip_bib_comments(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("%"))


def flatten(keep_comments: bool = False) -> None:
    if SRC.exists():
        shutil.rmtree(SRC)
    SRC.mkdir(parents=True)
    tex = {}
    main = (WRAP / "main.tex").read_text(encoding="utf-8")
    for old, new in PATH_MACROS:
        assert old in main, old
        main = main.replace(old, new)
    tex["main.tex"] = main
    for n in BODY_TEX:
        tex[n] = (ACME / n).read_text(encoding="utf-8")
    for f in sorted((ACME / "tables").glob("tab-*.tex")):
        assert f.name not in tex, f.name
        tex[f.name] = f.read_text(encoding="utf-8")
    for name, t in tex.items():
        if not keep_comments:
            t = strip_tex_comments(t)
        (SRC / name).write_text(t, encoding="utf-8", newline="\n")
    bib = (ACME / "references-acme.bib").read_text(encoding="utf-8")
    (SRC / "references-acme.bib").write_text(bib if keep_comments else strip_bib_comments(bib), encoding="utf-8", newline="\n")
    for n in ("sn-jnl.cls", "sn-basic.bst"):
        shutil.copyfile(WRAP / n, SRC / n)
    for f in sorted((ACME / "figures").glob("fig-*.pdf")):
        shutil.copyfile(f, SRC / f.name)
    n_tab = len(list(SRC.glob("tab-*.tex")))
    n_fig = len(list(SRC.glob("fig-*.pdf")))
    print(f"flattened: {len(list(SRC.iterdir()))} files in {SRC} ({n_tab} tables, {n_fig} figures)")


def run(cmd, cwd, log):
    with open(log, "wb") as fh:
        p = subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=1500)
    return p.returncode


def read(p: Path) -> str:
    return p.read_bytes().decode("latin-1")


def log_stats(log: str):
    errors = re.findall(r"^! .*$", log, re.M)
    undef_ref = re.findall(r"LaTeX Warning: Reference `([^']*)' on page", log)
    undef_cit = re.findall(r"LaTeX Warning: Citation `([^']*)' on page", log)
    rerun = "Rerun to get cross-references right" in log or "Label(s) may have changed" in log
    over = [float(x) for x in re.findall(r"Overfull \\[hv]box \(([0-9.]+)pt too (?:wide|high)\)", log)]
    pages = re.search(r"\((\d+) pages?, \d+ bytes\)", log)
    last = re.search(r"MAIN-TEXT-LAST-PAGE: (\d+)", log)
    return dict(errors=errors, undef_ref=sorted(set(undef_ref)), undef_cit=sorted(set(undef_cit)), rerun=rerun,
                overfull_total=len(over), overfull_gt5=len([x for x in over if x > 5]),
                pages=int(pages.group(1)) if pages else None, last_main=int(last.group(1)) if last else None)


def build() -> None:
    import fitz  # PyMuPDF
    if not SRC.exists():
        sys.exit("run flatten first")
    work = Path(tempfile.gettempdir()) / "acme-clean-build"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SRC, work, ignore=shutil.ignore_patterns("main.bbl"))
    flags = ["-interaction=nonstopmode", "-recorder", "-synctex=0"]
    rep = []
    steps = [["pdflatex", *flags, "main.tex"], ["bibtex", "main"]]
    for i, cmd in enumerate(steps):
        rc = run(cmd, work, work / f"step{i}-{cmd[0]}.out")
        rep.append(f"step {i} {' '.join(cmd[:1])}: exit code {rc}")
    # the page of the last main-text page (label LastMainPage) settles only after the references are in: repeat until stable
    for k in range(2, 8):
        rc = run(["pdflatex", *flags, "main.tex"], work, work / f"step{k}-pdflatex.out")
        rep.append(f"step {k} pdflatex: exit code {rc}")
        if "Label(s) may have changed" not in read(work / "main.log") and "Rerun to get" not in read(work / "main.log"):
            break
    log = read(work / "main.log")
    st = log_stats(log)
    blg = read(work / "main.blg")
    bib_warn = re.findall(r"^Warning--.*$", blg, re.M)
    bib_err = re.findall(r"^(?:I couldn't|You're|---).*$", blg, re.M)
    fls = read(work / "main.fls")
    used = {Path(l[6:].strip()).name for l in fls.splitlines() if l.startswith("INPUT ")}
    unused = sorted(p.name for p in SRC.iterdir() if p.name not in used and p.name != "main.bbl")

    # final-mode pass in a second copy: only to list what remains for the authors
    fin = Path(tempfile.gettempdir()) / "acme-clean-build-final"
    if fin.exists():
        shutil.rmtree(fin)
    shutil.copytree(work, fin)
    run(["pdflatex", *flags, "-jobname=finalcheck", "\\def\\ACMEFINAL{1}\\input{main.tex}"], fin, fin / "final.out")
    flog = read(fin / "finalcheck.log")
    ferr = re.findall(r"^! .*$", flog, re.M)

    # outputs
    pdf = work / "main.pdf"
    doc = fitz.open(pdf)
    n = len(doc)
    last = st["last_main"] or n
    toc = doc.get_toc(simple=True)
    main_doc = fitz.open()
    main_doc.insert_pdf(doc, from_page=0, to_page=last - 1)
    main_doc.set_toc([t for t in toc if t[2] <= last])
    main_doc.save(OUT / "manuscript.pdf", garbage=4, deflate=True)
    esm_doc = fitz.open()
    if last < n:
        esm_doc.insert_pdf(doc, from_page=last, to_page=n - 1)
        esm_doc.set_toc([[t[0], t[1], t[2] - last] for t in toc if t[2] > last])
        esm_doc.save(OUT / "ESM_1.pdf", garbage=4, deflate=True)
    shutil.copyfile(pdf, OUT / "manuscript-with-supplement.pdf")
    shutil.copyfile(work / "main.bbl", SRC / "main.bbl")

    lines = [
        "ACME package build report (tools/package_acme.py build)",
        f"work folder (fresh copy of source/, outside the project): {work}",
        *rep,
        f"combined PDF pages: {st['pages']} ; main text ends on page {st['last_main']} ; supplement pages: {(st['pages'] or 0) - (st['last_main'] or 0)}",
        f"LaTeX errors (draft mode): {len(st['errors'])} {st['errors'][:5]}",
        f"undefined references: {len(st['undef_ref'])} {st['undef_ref'][:10]}",
        f"undefined citations: {len(st['undef_cit'])} {st['undef_cit'][:10]}",
        f"'rerun' warning left after the last pass: {st['rerun']}",
        f"overfull boxes: {st['overfull_total']} in total, {st['overfull_gt5']} above 5 pt",
        f"BibTeX warnings: {len(bib_warn)} {bib_warn[:5]} ; BibTeX errors: {len(bib_err)} {bib_err[:5]}",
        f"files in source/ never read by the build: {unused}",
        f"FINAL-MODE pass: {len(ferr)} errors; distinct messages:",
    ]
    seen = []
    for e in ferr:
        if e not in seen:
            seen.append(e)
    lines += ["  " + e for e in seen[:60]]
    (OUT / "build-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def make_zip() -> None:
    z = OUT / "acme-source.zip"
    if z.exists():
        z.unlink()
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(SRC.iterdir()):
            zf.write(f, f.name)
    print(f"{z}: {z.stat().st_size} bytes, {len(zipfile.ZipFile(z).namelist())} files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["flatten", "build", "zip"])
    ap.add_argument("--keep-comments", action="store_true")
    a = ap.parse_args()
    {"flatten": lambda: flatten(a.keep_comments), "build": build, "zip": make_zip}[a.step]()
