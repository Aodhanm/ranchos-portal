#!/usr/bin/env python3
"""Apply Hoffman's own printed errata to the cross-check and re-derive the flags.

Hoffman's 1862 appendix ends with two pages of errata keyed to claim numbers
(audit/hoffman-errata-2026-09-09.md). Nothing downstream applied them, including
audit/hoffman-crosscheck-2026-09-01.json, which ordered the census queue and
defined the "flagged" stratum in the stratification analysis.

The consequence is specific: where the printed table is wrong and the register is
right, the cross-check raises a flag against the register that Hoffman himself
already withdrew. Three such flags exist (canada-carpenteria, calleguas,
guadalasca), all confirmed independently by census agents reading the case files
and, at Guadalasca, by chronology alone.

This writes a v2 cross-check rather than overwriting the original. The original
is cited by name in published findings, and rewriting a file that other documents
quote would silently invalidate them.

Usage: python3 scripts/apply_hoffman_errata.py
Writes audit/hoffman-crosscheck-v2-errata-applied.json
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SUBSTANTIVE = {"year", "governor", "grantee", "outcome"}

YEAR_SWAP = [
    re.compile(r"[Ii]nstead of\s*[“\"]?\s*(1[78]\d\d)[^,]*,\s*insert\s*[“\"]?\s*(1[78]\d\d)"),
    re.compile(r"[Ii]nsert\s+(1[78]\d\d)\s+in\s+the\s+place\s+of\s*[“\"]?\s*(1[78]\d\d)"),
]
GOV_SWAP = [
    re.compile(r"[Ff]or\s+([A-Z][\w.\s]{3,30}?),?\s*read\s*[“\"]?\s*([A-Z][\w.\s]{3,30}?)[”\".,]"),
    re.compile(r"[Ii]nstead of\s+([A-Z][\w.\s]{3,30}?),?\s*insert\s*[“\"]?\s*([A-Z][\w.\s]{3,30}?)[”\".,]"),
]


def corrected_year(body):
    for i, rx in enumerate(YEAR_SWAP):
        m = rx.search(body)
        if m:
            # pattern 0 is "instead of PRINTED, insert CORRECT"; pattern 1 reverses it
            return int(m.group(2) if i == 0 else m.group(1))
    return None


def corrected_governor(body):
    for rx in GOV_SWAP:
        m = rx.search(body)
        if m:
            new = m.group(2).strip(" .,“”")
            if re.search(r"Alvarado|Micheltorena|Figueroa|Pico|Gutierrez|Chico|Castro|"
                         r"Echeandia|Sola|Arguello|Victoria", new):
                return new
    return None


def overlap(a, b):
    """Loose name agreement, OCR-tolerant, matching the original cross-check's spirit."""
    t = lambda s: {w for w in re.sub(r"[^a-z ]", " ", (s or "").lower()).split() if len(w) > 2}
    x, y = t(a), t(b)
    if not x or not y:
        return 0.0
    return len(x & y) / min(len(x), len(y))


def main():
    hc = json.load(open(REPO / "audit" / "hoffman-crosscheck-2026-09-01.json", encoding="utf-8"))
    errata = {int(k): v for k, v in
              json.load(open(REPO / "audit" / "hoffman-errata.json", encoding="utf-8"))["errata"].items()}

    applied, withdrawn, changed = Counter(), [], []
    for rec in hc["records"]:
        h = rec.get("hoffman")
        if not h:
            continue
        e = errata.get(h.get("commission_no"))
        if not e:
            continue
        before = dict(h)
        y = corrected_year(e)
        g = corrected_governor(e)
        if y and h.get("year") != y:
            h["year"] = y
            applied["year corrected"] += 1
        if g and h.get("governor") and overlap(g, h["governor"]) < 0.5:
            h["governor"] = g
            applied["governor corrected"] += 1
        if before == h:
            continue
        h["erratum_applied"] = e[:180]

        # re-derive the substantive flags for this record against the corrected entry
        old_flags = [f for f in (rec.get("flags") or []) if f.split(":")[0] in SUBSTANTIVE]
        kept = [f for f in (rec.get("flags") or []) if f.split(":")[0] not in SUBSTANTIVE]
        new_flags = []
        for f in old_flags:
            kind = f.split(":")[0]
            if kind == "year" and y:
                m = re.search(r"register\s+(\d{4})", f)
                if m and int(m.group(1)) == y:
                    withdrawn.append((rec["id"], f, "Hoffman's own erratum agrees with the register"))
                    continue
                new_flags.append(f"year: register {m.group(1) if m else '?'} vs hoffman {y} (per erratum)")
                changed.append((rec["id"], f))
                continue
            if kind == "governor" and g:
                m = re.search(r"register '([^']*)'", f)
                if m and overlap(m.group(1), g) >= 0.5:
                    withdrawn.append((rec["id"], f, "erratum's governor matches the register"))
                    continue
                new_flags.append(f"governor: register '{m.group(1) if m else '?'}' vs hoffman '{g}' (per erratum)")
                changed.append((rec["id"], f))
                continue
            new_flags.append(f)
        rec["flags"] = kept + new_flags

    flagged = sum(1 for r in hc["records"]
                  if any(f.split(":")[0] in SUBSTANTIVE for f in (r.get("flags") or [])))
    hc["run"] = "2026-09-16 (v2: Hoffman's printed errata applied)"
    hc["errata_note"] = ("Hoffman's own errata, appendix pp. [145]-146, applied to the entries "
                         "before flags were re-derived. The 2026-09-01 file is retained unchanged "
                         "because published findings cite it by name.")
    hc["errata_effect"] = {"entries_corrected": dict(applied),
                           "flags_withdrawn": len(withdrawn),
                           "flags_restated": len(changed),
                           "substantively_flagged_rows": flagged}

    dest = REPO / "audit" / "hoffman-crosscheck-v2-errata-applied.json"
    dest.write_text(json.dumps(hc, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"errata matched to register rows: {sum(applied.values())} field corrections")
    for k, v in applied.most_common():
        print(f"   {k:22} {v}")
    print(f"\nflags WITHDRAWN (Hoffman himself agrees with the register): {len(withdrawn)}")
    for i, f, why in withdrawn:
        print(f"   {i[:34]:34} {f[:58]}")
        print(f"       -> {why}")
    print(f"\nflags RESTATED against the corrected value: {len(changed)}")
    for i, f in changed:
        print(f"   {i[:34]:34} {f[:64]}")
    print(f"\nsubstantively flagged rows: {len(hc['records'])} total -> {flagged} flagged")
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
