#!/usr/bin/env python3
"""Build a v1.1 candidate register from the staged corrections. Publishes nothing.

Writes to audit/v1.1-candidate/ so data/ranchos-register.{csv,json} stay
byte-identical to the Zenodo v1.0 deposit until Aodhan decides to cut v1.1.
Nothing here reaches the live site.

What it applies:
  1. Field corrections from audit/proposed-corrections-consolidated.json, but
     ONLY where the grader supplied an unambiguous replacement value. A
     correction whose text is an explanation rather than a value is reported as
     needing a human, not guessed at.
  2. Supreme Court citations from audit/proposed-scotus-citations.json, into the
     blank scotus_cite column.
  3. A docket_relation column from audit/proposed-docket-relation.json.
  4. grantor_office and grantor_office_verbatim columns from
     audit/grantor-office.json, for the grants whose granting officer was NOT a
     governor. Those corrections used to be deferred wholesale: the register had
     nowhere to say "an alcalde made this grant", so naming the alcalde in the
     governor column would have asserted he was governor. With the office
     recorded the name can be corrected without the false claim.

What it deliberately does NOT do:
  * It does not delete or suppress the four byte-identical duplicate rows. They
    are marked docket_relation=duplicate and left in place. Whether the register
    holds 672 rows or 668 is an editorial ruling about the sources, not a
    mechanical de-duplication, and three of the four need a case file to settle.
  * It does not touch outcome values resolved only at the weaker hoffman-table
    evidence tier.

Usage: python3 scripts/build_v11_candidate.py
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "audit" / "v1.1-candidate"

# A correction is applied only if its text yields a clean value. These patterns
# are deliberately strict: a wrong automated "correction" is worse than a
# deferred one, because it looks authoritative.
VALUE = [
    re.compile(r"^\s*([A-Z][\w'áéíóúñÁÉÍÓÚÑ.\- ]{2,60}?)\s*(?:,|\.|$| per | according)"),
    re.compile(r"^\s*(1[78]\d\d)\b"),
]


# Graders write "<value>, per the grant decree of ... 'quoted Spanish'". The value
# is the leading segment; the rest is the citation that makes it trustworthy.
# An earlier version length-checked the WHOLE string before extracting, so every
# well-cited correction was rejected for being long, which deferred 104 perfectly
# usable grantee corrections. Extract first, then judge the extracted value.
# "\.\s" as a boundary truncates "Juan B. Alvarado" to "Juan B", so a single
# initial followed by a stop does not end the value.
# Do NOT break on "(": graders write the Spanish form inline, as in
# "Charles William (Carlos Guillermo) Flugge", and breaking there truncates the
# surname off. Capture through to a real terminator, then strip parentheticals.
# Graders also separate value from citation with a dash, as in
# "Francisco Lopez and Jose Arellanes - concession decree" and
# "Rejected - D.C. decree 19 Feb 1862". Both hyphen and em dash terminate.
LEAD = re.compile(r"^\s*([^,;]{2,80}?)\s*(?:,|;|\s[-\u2013\u2014]\s|\bper\b"
                  r"|(?<![A-Z])\.\s|$)")
# A captured verb means the regex swallowed a clause, not a name:
# "Nicolas Gutierrez granted El Molino" is a sentence, not a value.
VERBY = re.compile(r"\b(granted|took|held|issued|signed|petitioned|bought|died|"
                   r"was|were|is|are|had|made|acted)\b", re.I)
PROSE = re.compile(r"\b(should|appears|probably|unclear|cannot|needs|structural|"
                   r"split|cannot be|cf\.|NOT )\b", re.I)
# A correction naming an office rather than a person is a CATEGORY correction:
# it says the grantor was not a governor at all. Squeezing the name into the
# governor column alone would assert he WAS governor, so these are handled
# separately, through audit/grantor-office.json, which carries the office too.
# Anything that file does not cover is still deferred here rather than guessed.
OFFICE = re.compile(r"\b(alcalde|prefect|vocal|junta|acting|interino|ayuntamiento|"
                    r"commandant|delegated|in exercise of|ex-officio|military)\b", re.I)


def clean_value(text, field):
    if not text:
        return None
    t = text.strip()
    if field == "year":
        m = re.match(r"^\s*(1[78]\d\d)\b", t)
        return m.group(1) if m else None
    if field == "governor" and OFFICE.search(t):
        return None
    m = LEAD.match(t)
    if not m:
        return None
    v = m.group(1)
    # An unbalanced "(" means the capture ended inside a gloss, e.g.
    # "William Dickey (Sp" or "Jose Joaquin de la Torre (grant of June 22".
    # Cut back to before it rather than keeping the fragment.
    if v.count("(") != v.count(")"):
        v = v.split("(")[0]
    v = re.sub(r"\s*\([^)]*\)\s*", " ", v)                    # drop inline glosses
    v = re.sub(r"\s{2,}", " ", v).strip(" .,'\"")
    if not (2 < len(v) <= 60) or PROSE.search(v) or VERBY.search(v):
        return None
    if not re.match(r"^[A-Z0-9]", v):
        return None
    # a personal name needs a surname; a lone forename or initial is a truncation
    if field in ("governor", "grantee", "patent_to") and len(v.split()) < 2:
        return None
    return v


def main():
    rows = list(csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8")))
    hdr = list(rows[0].keys())
    idx = {r["id"]: r for r in rows}

    corr = json.load(open(REPO / "audit" / "proposed-corrections-consolidated.json",
                          encoding="utf-8"))["corrections"]
    rel = json.load(open(REPO / "audit" / "proposed-docket-relation.json",
                         encoding="utf-8"))["relation"]
    scotus = json.load(open(REPO / "audit" / "proposed-scotus-citations.json",
                            encoding="utf-8"))["records"]
    office_path = REPO / "audit" / "grantor-office.json"
    office = ({o["id"]: o for o in
               json.load(open(office_path, encoding="utf-8"))["records"]}
              if office_path.exists() else {})

    tally = Counter()
    applied, deferred = [], []
    for c in corr:
        r = idx.get(c["id"])
        if not r:
            tally["record not in register"] += 1
            continue
        f = c["field"]
        if f not in r:
            tally["field not exported"] += 1
            continue
        if f == "governor" and c["id"] in office:
            continue          # handled below, with its office
        v = clean_value(c.get("correction"), f)
        if not v:
            tally["deferred: correction is prose, not a value"] += 1
            deferred.append({**c, "reason": "no unambiguous replacement value"})
            continue
        if (r[f] or "").strip() == v:
            tally["already correct"] += 1
            continue
        applied.append({"id": c["id"], "field": f, "from": r[f], "to": v,
                        "evidence": (c.get("evidence") or "")[:220]})
        r[f] = v
        tally["applied"] += 1

    # The staged citations were taken as printed in Hoffman and only ever checked
    # structurally. scripts/verify_scotus_cites.py has now read them against the
    # official reports: two carry a WRONG PAGE NUMBER in the printed table, and
    # both are fixed by the claimant Hoffman's own entry names (Bolsa de Tomales
    # 22 How. 87 to 89, United States v. Galbraith; Nemshas 24 How. 151 to 131,
    # United States v. Chana). Prefer the verified citation where one exists.
    ver_path = REPO / "audit" / "scotus-verification.json"
    verified = ({v["id"]: v for v in
                 json.load(open(ver_path, encoding="utf-8"))["records"]}
                if ver_path.exists() else {})
    for s in scotus:
        r = idx.get(s["id"])
        if r is None or (r.get("scotus_cite") or "").strip():
            continue
        v = verified.get(s["id"], {})
        pc = v.get("proposed_correction")
        if pc:
            r["scotus_cite"] = pc["cite"]
            applied.append({"id": s["id"], "field": "scotus_cite",
                            "from": "", "to": pc["cite"],
                            "evidence": pc["why"][:220]})
            tally["scotus citation added, page corrected against the reports"] += 1
        else:
            r["scotus_cite"] = s["hoffman_scotus_cite"]
            tally["scotus citation added"] += 1

    # The granting officer and his office. An EMPTY grantor_office is not a claim
    # that the office was checked; it is the register's standing assumption that
    # the grant was gubernatorial, which holds for the great majority and has not
    # been separately verified row by row.
    for col in ("grantor_office", "grantor_office_verbatim"):
        if col not in hdr:
            hdr.append(col)
    for r in rows:
        r.setdefault("grantor_office", "")
        r.setdefault("grantor_office_verbatim", "")
    for rid, o in office.items():
        r = idx.get(rid)
        if r is None:
            tally["office record not in register"] += 1
            continue
        was = r["governor"]
        r["governor"] = o["grantor_name"]
        r["grantor_office"] = o["office"]
        r["grantor_office_verbatim"] = o["office_verbatim"]
        applied.append({"id": rid, "field": "governor+grantor_office",
                        "from": was, "to": f'{o["grantor_name"]} ({o["office"]})',
                        "evidence": (o.get("evidence") or "")[:220]})
        tally["applied"] += 1
        tally["grantor office recorded"] += 1
        # Some grantor corrections drag a dependent field with them. Micheltorena
        # was not governor in 1834 and Jose Castro was not a Spanish governor in
        # 1820, so changing the name alone would leave the row contradicting
        # itself. Those rows carry an explicit also_changes block with its reason;
        # a correction that needed one and did not have it stayed deferred.
        for f2, v2 in (o.get("also_changes") or {}).items():
            if f2 not in r:
                tally["dependent field not exported"] += 1
                continue
            applied.append({"id": rid, "field": f2, "from": r[f2], "to": v2,
                            "evidence": "dependent on the grantor correction: "
                                        + (o.get("also_changes_why") or "")[:180]})
            r[f2] = v2
            tally["applied"] += 1
            tally["dependent field change"] += 1

    if "docket_relation" not in hdr:
        hdr.append("docket_relation")
    for r in rows:
        r["docket_relation"] = rel.get(r["id"], "sole")

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "ranchos-register.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (OUT / "ranchos-register.json").write_text(json.dumps(
        {"title": "Ranchos of California: A Register of the Land Grants of Alta California",
         "version": "1.1-candidate", "license": "https://creativecommons.org/licenses/by/4.0/",
         "note": ("CANDIDATE, not published. Corrections from the accuracy audit and the "
                  "case-file census applied; Supreme Court citations from Hoffman added; "
                  "docket_relation added. The four byte-identical duplicate rows are MARKED, "
                  "not removed: whether the register holds 672 rows or 668 is an editorial "
                  "ruling, not a mechanical de-duplication."),
         "count": len(rows), "records": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "CHANGES.json").write_text(json.dumps(
        {"applied": applied, "deferred_for_a_human": deferred,
         "tally": dict(tally.most_common())}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("v1.1 CANDIDATE (published files untouched)\n")
    for k, v in tally.most_common():
        print(f"  {v:4d}  {k}")
    print(f"\n  rows {len(rows)} (unchanged; 4 duplicates marked, not removed)")
    print(f"  docket_relation: {dict(Counter(r['docket_relation'] for r in rows).most_common())}")
    offs = Counter(r["grantor_office"] for r in rows if r["grantor_office"])
    print(f"  grantor_office:  {dict(offs.most_common())} "
          f"({sum(offs.values())} of {len(rows)}; the rest are recorded as gubernatorial)")
    print(f"\nwrote {OUT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
