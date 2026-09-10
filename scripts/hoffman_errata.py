#!/usr/bin/env python3
"""Extract Hoffman's own printed ERRATA and test them against our register flags.

Hoffman's 1862 appendix ends with two pages of errata keyed to claim numbers
(appendix pp. [145]-146, leaves n606-n607 of IA item GR_1919). They are not
cosmetic: they swap granting governors, correct grant years, and collapse claims
into one another. Nothing downstream of the OCR applies them, including our own
audit/hoffman-crosscheck-2026-09-01.json, which is what ordered the whole census
queue and defined the flagged stratum.

That matters in a specific way. If the printed table is wrong about a grant year
and our register is right, the cross-check raises a flag against the register
that Hoffman himself already withdrew. Such a record would be pulled into the
adverse stratum and graded as a priority for no reason, and the flag would be
counted as a Hoffman disagreement in the stratification.

Usage: python3 scripts/hoffman_errata.py /path/to/GR_1919_djvu.txt
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
YEAR = re.compile(r"\b(1[78]\d\d)\b")
GOVERNORS = ("Alvarado", "Micheltorena", "Figueroa", "Pico", "Gutierrez", "Chico",
             "Castro", "Echeandia", "Sola", "Argue", "Vallejo", "Estrada")


def extract(text):
    """Pull the trailing errata block and split it into 'No. N. body' entries."""
    tail = text[-40000:]
    m = re.search(r"ERRATA[^\n]*\n", tail)
    if not m:
        raise SystemExit("errata block not found in the OCR text")
    block = tail[m.start():]
    out = {}
    for em in re.finditer(r"No\.?\s*(\d{1,3})\s*\.\s*(.+?)(?=\s*No\.?\s*\d{1,3}\s*\.|\Z)",
                          block, re.S):
        n = int(em.group(1))
        body = re.sub(r"\s+", " ", em.group(2)).strip()
        if body and n not in out:
            out[n] = body
    return out


def classify(body):
    kinds = []
    low = body.lower()
    if re.search(r"same title as in no|this claim is part of|see no|included in no", low):
        kinds.append("collapses_into_another_claim")
    if YEAR.search(body) and re.search(r"instead of|in the place of|insert|read", low):
        kinds.append("year")
    if any(g.lower() in low for g in GOVERNORS):
        kinds.append("governor_or_official")
    if re.search(r"^for .+?, read", low):
        kinds.append("spelling")
    if re.search(r"containing [\d,]+\.?\d* acres", low):
        kinds.append("acreage")
    return kinds or ["other"]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    text = Path(sys.argv[1]).read_text(errors="replace")
    errata = extract(text)
    kinds = Counter(k for b in errata.values() for k in classify(b))

    print(f"{len(errata)} errata entries recovered, keyed to claim numbers "
          f"{min(errata)}-{max(errata)}\n")
    for k, v in kinds.most_common():
        print(f"  {k:32} {v}")

    # Which of OUR register flags sit on a claim Hoffman himself corrected?
    hc = json.load(open(REPO / "audit" / "hoffman-crosscheck-2026-09-01.json",
                        encoding="utf-8"))["records"]
    SUB = {"year", "governor", "grantee", "outcome"}
    hits = []
    for r in hc:
        h = r.get("hoffman") or {}
        cn = h.get("commission_no")
        if cn in errata:
            flags = [f for f in (r.get("flags") or []) if f.split(":")[0] in SUB]
            if flags:
                hits.append({"id": r["id"], "commission_no": cn,
                             "erratum": errata[cn], "kinds": classify(errata[cn]),
                             "our_flags": flags})

    print(f"\n--- register rows whose Hoffman entry carries an erratum AND which we "
          f"flagged: {len(hits)} ---")
    for h in hits:
        print(f"\n  {h['id']}  (Hoffman no. {h['commission_no']}, {'/'.join(h['kinds'])})")
        print(f"    erratum : {h['erratum'][:150]}")
        for f in h["our_flags"]:
            print(f"    our flag: {f[:130]}")

    dest = REPO / "audit" / "hoffman-errata.json"
    dest.write_text(json.dumps(
        {"note": ("Hoffman's own printed errata, appendix pp. [145]-146 of the 1862 "
                  "printing (IA GR_1919 leaves n606-n607). NOT applied to any dataset; "
                  "recorded so the cross-check can be re-derived with them."),
         "count": len(errata), "by_kind": dict(kinds.most_common()),
         "errata": {str(k): v for k, v in sorted(errata.items())},
         "flagged_rows_touched_by_an_erratum": hits},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
