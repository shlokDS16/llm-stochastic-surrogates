"""Count the full-text eligibility decisions referred to the first author (protocol section 6: every disagreement between
the two coders and every borderline exclusion). Reads the coder outputs frozen in runs/rq234-final/input-snapshot.

    python analysis/fulltext/referral_count.py [--run runs/rq234-final] [--out runs/referrals-final]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/rq234-final")
    ap.add_argument("--out", default="runs/referrals-final")
    a = ap.parse_args()
    snap = ROOT / a.run / "input-snapshot"
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    ids = sorted(p.stem for p in (snap / "claude").glob("*.json"))
    rows = []
    for i in ids:
        c = json.loads((snap / "claude" / f"{i}.json").read_text(encoding="utf-8"))["eligibility"]
        x_path = snap / "codex" / f"{i}.json"
        x = json.loads(x_path.read_text(encoding="utf-8"))["eligibility"] if x_path.exists() else {}
        dc, dx = str(c.get("decision", "")).upper(), str(x.get("decision", "")).upper()
        disagree = bool(dx) and dc != dx
        border_excl = (dc == "NO" and bool(c.get("borderline"))) or (dx == "NO" and bool(x.get("borderline")))
        border_any = bool(c.get("borderline")) or bool(x.get("borderline"))
        rows.append(dict(id=i, claude=dc, codex=dx, disagree=disagree, borderline_exclusion=border_excl, borderline_any=border_any,
                         referred=disagree or border_excl))
    n = len(rows)
    s = dict(records=n, disagreements=sum(r["disagree"] for r in rows), borderline_exclusions=sum(r["borderline_exclusion"] for r in rows),
             referred=sum(r["referred"] for r in rows), borderline_flag_any=sum(r["borderline_any"] for r in rows),
             unclear_either=sum(r["claude"] == "UNCLEAR" or r["codex"] == "UNCLEAR" for r in rows))
    (out / "referrals.json").write_text(json.dumps(dict(summary=s, rows=rows), indent=1), encoding="utf-8")
    print(json.dumps(s))


if __name__ == "__main__":
    main()
