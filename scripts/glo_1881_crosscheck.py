#!/usr/bin/env python3
"""Cross-check register patent data against the GLO's own 1881 per-claim table.

Source: "H H.-List of private land claims in California under Spanish and Mexican
authorities", in the Report of the Surveyor General of California, printed in the
Annual Report of the Commissioner of the General Land Office for FY1881
(H.R. Exec. Doc. No. 1, 47th Cong., 1st Sess., Serial 2017), table at pp. 533-549.
IA item annualreportofco00unse_45.

This is the government's own statement of what it had patented, and it is an
INDEPENDENT authority for fields the register currently carries from other
sources: patent date and patent acreage.

⚠ METHOD NOTE, and the reason this script does not match on rancho name. The djvu
OCR of a wide ruled table destroys the name column: "Mission Santa Barbara" comes
out as "Massionisantal barbara", and column bleed mixes neighbouring cells. Name
matching against this text would be guesswork. The patent DATE and the
comma-grouped ACREAGE survive OCR intact in all 448 patented rows, and a
(date, acreage) pair is distinctive enough to match on by itself. So the join key
is the date, and the acreage is the thing tested.

⚠ Anything that ends up PUBLISHED from this table should be read off the page
images, not this OCR. This script is a screening pass, exactly like
hoffman_crosscheck.py, not a verdict.

Usage: python3 scripts/glo_1881_crosscheck.py /path/to/annualreportofco00unse_45_djvu.txt
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROW = re.compile(r"Patented\s+([A-Z][a-z]{2,9})\.?\s+(\d{1,2}),?\s*(18\d\d)")
ACRES = re.compile(r"(\d{1,3}(?:,\s?\d{3})+|\d{2,6})\.\s?(\d{2})\s*$")
MONTH = {m: i for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split(), 1)}
# The register writes months in abbreviated forms with stops.
REG_MONTH = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
             "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12, "apl": 4, "sept": 9}


def glo_rows(path):
    out = []
    for line in Path(path).read_text(errors="replace").split("\n"):
        m = ROW.search(line)
        if not m:
            continue
        mon = MONTH.get(m.group(1).capitalize())
        if not mon:
            continue
        a = ACRES.search(line.rstrip(" .|"))
        acres = None
        if a:
            try:
                acres = float(a.group(1).replace(",", "").replace(" ", "") + "." + a.group(2))
            except ValueError:
                acres = None
        out.append({"date": (int(m.group(3)), mon, int(m.group(2))),
                    "acres": acres, "raw": re.sub(r"\s+", " ", line)[:200]})
    return out


def reg_date(s):
    m = re.match(r"\s*([A-Za-z]{3,5})\.?\s+(\d{1,2}),?\s*(18\d\d)", s or "")
    if not m:
        return None
    mon = REG_MONTH.get(m.group(1)[:4].lower()) or REG_MONTH.get(m.group(1)[:3].lower())
    return (int(m.group(3)), mon, int(m.group(2))) if mon else None


def one_digit_apart(a, b):
    """True if two acreages differ in exactly one digit position.

    That is the signature of an OCR misread, and it is the right test: a crude
    "is the difference round" rule calls 5,000 and 70,000 OCR but misses 600 and
    200, which are equally single-digit substitutions (27,654 vs 27,054).
    """
    x, y = f"{a:.2f}", f"{b:.2f}"
    if len(x) != len(y):
        return False
    return sum(1 for i, j in zip(x, y) if i != j) == 1


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    glo = glo_rows(sys.argv[1])
    by_date = defaultdict(list)
    for g in glo:
        by_date[g["date"]].append(g)

    rows = list(csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8")))

    # A GLO row claimed by more than one register row is an ambiguous match, not
    # evidence about either. Two register rows sharing a patent date will both
    # bind to the single GLO row carrying it, and the acreage comparison is then
    # meaningless: canon-santa-ana and san-jose-buenos-ayres both matched the one
    # GLO row for 25 July 1866 and produced a spurious 8,891-acre "disagreement".
    claimants = Counter()
    for r in rows:
        d = reg_date(r.get("patent_date"))
        if d and len(by_date.get(d, [])) == 1:
            claimants[d] += 1
    tally = Counter()
    findings = []
    for r in rows:
        d = reg_date(r.get("patent_date"))
        if not d:
            tally["register has no parseable patent date"] += 1
            continue
        cands = by_date.get(d)
        if not cands:
            tally["date not in the GLO 1881 table"] += 1
            continue
        try:
            ra = float((r.get("patent_acres") or "").replace(",", "")) if r.get("patent_acres") else None
        except ValueError:
            ra = None
        # unique date match is the only case where acreage can be tested safely
        if len(cands) == 1 and claimants[d] > 1:
            tally["ambiguous: several register rows share this patent date"] += 1
        elif len(cands) == 1 and ra is not None and cands[0]["acres"] is not None:
            diff = abs(cands[0]["acres"] - ra)
            if diff < 0.02:
                tally["date + acreage both agree"] += 1
            else:
                cause = ("single-digit OCR misread" if one_digit_apart(ra, cands[0]["acres"])
                         else "unexplained")
                tally[f"date agrees, acreage differs ({cause})"] += 1
                findings.append({"id": r["id"], "name": r["name"],
                                 "patent_date": r["patent_date"],
                                 "register_acres": ra, "glo_acres": cands[0]["acres"],
                                 "difference": round(diff, 2), "likely_cause": cause,
                                 "glo_row": cands[0]["raw"]})
        elif len(cands) > 1:
            tally["date matches but is shared by several claims"] += 1
        else:
            tally["date agrees, acreage not comparable"] += 1

    print(f"GLO 1881 table: {len(glo)} patented rows parsed, "
          f"{sum(1 for g in glo if g['acres'] is not None)} with an acreage\n")
    for k, v in tally.most_common():
        print(f"  {v:4d}  {k}")

    if findings:
        print(f"\n--- acreage disagreements ({len(findings)}) ---")
        for f in findings[:12]:
            print(f"  {f['id'][:34]:34} {f['patent_date']:18} "
                  f"register {f['register_acres']:>12,.2f} vs GLO {f['glo_acres']:>12,.2f}"
                  f"  (diff {f['difference']:,})")

    dest = REPO / "audit" / "glo-1881-crosscheck.json"
    dest.write_text(json.dumps(
        {"note": ("Screening cross-check of register patent data against the GLO's own "
                  "1881 per-claim table. Matched on patent DATE because the djvu OCR "
                  "destroys the name column. A screening pass, not a verdict: anything "
                  "published from this table must be read off the page images."),
         "source": ("Report of the Surveyor General of California, table H H, in the "
                    "Annual Report of the Commissioner of the General Land Office FY1881, "
                    "H.R. Exec. Doc. No. 1, 47th Cong., 1st Sess., Serial 2017, pp. 533-549."),
         "glo_rows_parsed": len(glo), "tally": dict(tally.most_common()),
         "acreage_disagreements": findings},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
