"""Fetch the body text of open-access (CC BY) Springer articles for private style analysis.

Usage: python analysis/acme/fetch_springer_oa.py <id>=<doi> [<id>=<doi> ...]
Writes research/relaunch/acme-style/texts/<id>.md (git-ignored) and prints a metadata line per article.
Only articles whose page declares Open Access are saved. References, figures and tables are dropped;
display equations become [EQ], inline math [m]. Citation markers stay (needed for density metrics).
"""
import json, re, subprocess, sys, tempfile, time
from pathlib import Path
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parents[2] / "research/relaunch/acme-style/texts"
SKIP = {"References", "Acknowledgements", "Author information", "Ethics declarations", "Additional information",
        "Rights and permissions", "About this article", "Inline Recommendations", "Data Availability",
        "Funding", "Declarations", "Code Availability", "Availability of data and material", "Abbreviations"}
JAR = str(Path(tempfile.gettempdir()) / "springer_cj.txt")

def get(url):
    # plain urllib is served a bot-check page; curl with a browser UA and a cookie jar gets the article
    r = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "-b", JAR, "-c", JAR, "--max-time", "90", url],
                       capture_output=True)
    return r.stdout.decode("utf8", "replace")

def clean(el):
    for t in el.select("math, .mathjax-tex, .MathJax, script, style, sup.c-article-supplement"):
        t.replace_with(" [m] ")
    txt = el.get_text(" ", strip=True)
    txt = re.sub(r"\s+([,.;:)\]])", r"\1", txt)
    txt = re.sub(r"([(\[])\s+", r"\1", txt)
    return re.sub(r"\s+", " ", txt)

def walk(sec, out, level):
    for ch in sec.children:
        if getattr(ch, "name", None) is None:
            continue
        cls = " ".join(ch.get("class", []))
        if ch.name in ("h2", "h3", "h4", "h5"):
            out.append("#" * int(ch.name[1]) + " " + clean(ch))
        elif ch.name == "p":
            out.append(clean(ch))
        elif ch.name in ("ul", "ol"):
            for i, li in enumerate(ch.find_all("li", recursive=False), 1):
                out.append(("- " if ch.name == "ul" else f"{i}. ") + clean(li))
        elif "equation" in cls:
            out.append("[EQ]")
        elif ch.name in ("figure", "table") or "table" in cls or "figure" in cls:
            continue
        elif ch.name in ("section", "div"):
            walk(ch, out, level)

def main(args):
    OUT.mkdir(parents=True, exist_ok=True)
    for a in args:
        id_, doi = a.split("=")
        try:
            h = get("https://link.springer.com/article/" + doi)
        except Exception as e:
            print(id_, doi, "FETCH-FAIL", e); continue
        oa = '"Open Access":"Y"' in h
        lic = re.search(r"licensed under a (Creative Commons [^<]{0,60}?License)", h)
        s = BeautifulSoup(h, "html.parser")
        title = (s.find("meta", {"name": "citation_title"}) or {}).get("content", "")
        date = (s.find("meta", {"name": "citation_publication_date"}) or {}).get("content", "")
        b = s.select_one("div.c-article-body")
        out = []
        if b and oa:
            for sec in b.find_all("section", attrs={"data-title": True}, recursive=True):
                if sec.find_parent("section", attrs={"data-title": True}):
                    continue
                if sec["data-title"] in SKIP:
                    continue
                walk(sec, out, 2)
            body = "\n\n".join(x for x in out if x)
            (OUT / f"{id_}.md").write_text(body, encoding="utf8")
        print(json.dumps({"id": id_, "doi": doi, "oa": oa, "license": lic.group(1) if lic else None, "title": title,
                          "date": date, "words": len(" ".join(out).split())}))
        time.sleep(3)

main(sys.argv[1:])
