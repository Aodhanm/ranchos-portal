#!/usr/bin/env python3
"""Resolve the outcome of the still-unread register rows from Hoffman's 1862 table.

Berkeley's digicoll is behind a bot challenge we are not going to work around, so
115 of the 672 register rows have no case-file reading. Hoffman's appendix gives
each of them a full disposition chain (Commission decision and date, District
Court decision and date, Supreme Court citation, acreage, patent status), printed
by the judge who presided over the Northern District cases.

That is WEAKER evidence than a case file and is labelled as such. Reading the
decree is tier "case-file"; this is tier "hoffman-table". The register should
never present the two as equivalent, but a documented weaker reading beats an
unexamined row, and it lets all 672 be reported with the evidence stated.

Outcome is decided by the LAST disposition in the entry, the same rule as
scripts/hoffman_dispositions.py, because the Commission's first decision was
routinely reversed on appeal.

Usage: python3 scripts/resolve_unread_from_hoffman.py /path/to/GR_1919_djvu.txt
Writes audit/unread-resolved-from-hoffman.json. Changes no register data.
"""
import csv
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hoffman_crosscheck import parse_appendix          # noqa: E402
from hoffman_dispositions import classify, trim_to_own_entry  # noqa: E402

STAGE = re.compile(
    r"(?P<who>Commission|District Court|Supreme Court)[^.;]{0,80}?"
    r"(?P<when>(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2}[a-z]{0,2},?\s+18\d\d)", re.I)


def graded_ids():
    got = set()
    for f in glob.glob(str(REPO / "audit" / "census-*" / "chunk*.json")):
        for r in json.load(open(f, encoding="utf-8")):
            got.add(r["id"])
    b = json.load(open(REPO / "audit" / "verdicts-2026-09-01.json", encoding="utf-8"))
    for r in (b["records"] if isinstance(b, dict) else b):
        got.add(r["id"])
    return got


def docket(s):
    """The register writes the same docket both ways, "ND 060" and "N.D. 219".
    Matching only the first form silently dropped 37 rows as "no Hoffman entry"."""
    t = re.sub(r"[.\s]+", " ", (s or "").strip().upper())
    m = re.match(r"^([NS])\s*D\s*0*(\d+)$", t)
    return (m.group(1) + "D", int(m.group(2))) if m else None


def norm_name(s):
    """Fold to comparable tokens: Hoffman's OCR mangles accents and long s."""
    s = re.sub(r"[^a-z ]+", " ", (s or "").lower())
    drop = {"rancho", "canada", "de", "del", "la", "las", "los", "el", "y", "or",
            "san", "santa", "the", "of", "in"}
    return {w for w in s.split() if w and w not in drop}


def pick_by_name(reg_name, cands):
    """The candidate whose rancho name shares the most distinctive tokens with the
    register's, but only if exactly one candidate scores highest and scores > 0.
    A tie or a blank score is a null result, and a null result is a finding."""
    scored = [(len(norm_name(reg_name) & norm_name(c.get("rancho"))), c) for c in cands]
    best = max(s for s, _ in scored)
    if best == 0:
        return None
    top = [c for s, c in scored if s == best]
    return top[0] if len(top) == 1 else None


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    entries = parse_appendix(Path(sys.argv[1]).read_text(errors="replace"))
    # Hoffman's headnote: "The first number is that of the Commission; the second
    # is the number of the District Court." The register's ND/SD number is the
    # DISTRICT COURT number, so key on court_no. Verified against ND 060
    # (Commission 82, court 60) and SD 147 (Commission 483, court 147).
    by = {}
    for e in entries:
        by.setdefault((e["district"], e["court_no"]), []).append(e)

    done = graded_ids()
    rows = [r for r in csv.DictReader(open(REPO / "data" / "ranchos-register.csv",
                                           encoding="utf-8")) if r["id"] not in done]

    out, tally, agree = [], Counter(), Counter()
    for r in rows:
        d = docket(r["land_case"])
        cands = by.get(d, []) if d else []
        if not cands:
            out.append({"id": r["id"], "land_case": r["land_case"],
                        "register_outcome": r["outcome"],
                        "hoffman_outcome": None, "evidence_tier": "none",
                        "note": "no Hoffman entry found for this docket"})
            tally["no entry"] += 1
            continue
        # ⚠ Hoffman's table is NOT unique on the district court number. Six numbers
        # carry two entries each (SD 270 is both Los Gatos or Santa Rita, comm.
        # 531, and Canada de los Pinacates, comm. 598; ND 166 is both Carmel,
        # comm. 89, and a 50-vara Mission Dolores lot, comm. 705). Taking cands[0]
        # silently matched "Canada de los Pinacates" to the Santa Rita entry and
        # produced the single register-vs-Hoffman "disagreement" in the 09-11 run.
        # Break the tie on the rancho name, and refuse to guess if it will not break.
        e, ambiguous = cands[0], False
        if len(cands) > 1:
            e = pick_by_name(r.get("name"), cands)
            if e is None:
                out.append({"id": r["id"], "name": r.get("name"),
                            "land_case": r["land_case"],
                            "register_outcome": r["outcome"],
                            "hoffman_outcome": None, "evidence_tier": "none",
                            "candidates": [c["commission_no"] for c in cands],
                            "note": ("docket number carries more than one Hoffman "
                                     "entry and the rancho name does not break the tie")})
                tally["ambiguous docket"] += 1
                continue
            ambiguous = True
        body = trim_to_own_entry(e["raw"])
        stages = [f"{m.group('who')} {m.group('when')}" for m in STAGE.finditer(body)]
        final = classify(e)
        patented = bool(re.search(r"patented", body, re.I))
        reg = (r["outcome"] or "").strip().lower()
        mapped = {"confirmed": "Confirmed", "rejected": "Rejected"}.get(final)
        if mapped and reg:
            agree["agrees" if reg.startswith(mapped.lower())
                  or (reg == "patented" and mapped == "Confirmed") else "DISAGREES"] += 1
        tally[final] += 1
        out.append({
            "id": r["id"], "name": r["name"], "land_case": r["land_case"],
            "commission_docket": e["commission_no"], "district_court_no": e["court_no"],
            "register_outcome": r["outcome"],
            "hoffman_outcome": mapped or final,
            "hoffman_patented_by_1862": patented,
            "disposition_chain": stages,
            "evidence_tier": "hoffman-table",
            "evidence": body[:420],
            **({"docket_collision_resolved_by_name":
                [c["commission_no"] for c in cands]} if ambiguous else {}),
        })

    doc = {
        "note": ("Provisional outcomes for register rows with NO case-file reading, "
                 "derived from Hoffman 1862 Appendix. Evidence tier 'hoffman-table' is "
                 "WEAKER than the 'case-file' tier used for the 557 read records and "
                 "must not be presented as equivalent. Changes no register data."),
        "source": ("Ogden Hoffman, Reports of Land Cases ... Northern District of "
                   "California (San Francisco: Numa Hubert, 1862), Appendix, "
                   "'Table of Land Claims', pp. 1-109. IA item GR_1919."),
        "unread_rows": len(rows),
        "by_hoffman_outcome": dict(tally.most_common()),
        "vs_register": dict(agree),
        "records": out,
    }
    dest = REPO / "audit" / "unread-resolved-from-hoffman.json"
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"{len(rows)} rows with no case-file reading")
    for k, v in tally.most_common():
        print(f"   {k:12} {v}")
    print(f"\nagainst the register's stated outcome: {dict(agree)}")
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
