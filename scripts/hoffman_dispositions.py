#!/usr/bin/env python3
"""Recompute Hoffman's 1862 confirmed/rejected split from the FINAL disposition.

Sources §6 publishes "813 claims (545 confirmed/patented, 239 rejected, ~29
other)" and attributes it to data/hoffman-claims.json, a file absent from this
repo (audit/hoffman-split-note-2026-09-03.md). The screening parser in
hoffman_crosscheck.py cannot check it: its rule is "rejected only if 'rejected'
appears and 'confirmed' does not", which miscounts every claim whose fortunes
changed on appeal, and there are many in both directions.

This reads each entry's disposition events IN TEXT ORDER and takes the LAST one,
which is what Hoffman's own table records: the posture as of 1862.

Two traps the crude rule falls into, both handled here:
  * "appeal dismissed" does NOT dismiss the claim, it FINALIZES the decree below
    it. Reading it as a dismissal turns confirmed claims into "other".
  * "rejected by the Commission, confirmed by the District Court" is a confirmed
    claim, and the reverse is a rejected one. Order is the whole answer.

Usage: python3 scripts/hoffman_dispositions.py /path/to/GR_1919_djvu.txt
       (Internet Archive item GR_1919, file GR_1919_djvu.txt)
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hoffman_crosscheck import parse_appendix

# Ordered so the longest / most specific alternatives win at the same position.
# The djvu OCR mangles "confirmed" often enough to matter (confinned, conflrmed,
# couflrmed). Missing one silently demotes a confirmed claim to "unclear".
CONFIRMED_OCR = r"con[fft][il1r]?[rn]?[mn][eo]d"

EVENT = re.compile(
    # "affirmed" is NOT a disposition. It upholds whatever precedes it, so an
    # affirmed REJECTION is still a rejection. Counting it as a confirmation
    # inflated the confirmed total and wrongly contradicted the register on
    # ND 394 (Punta de Lobos) and ND 209 (Potrero), where the Supreme Court
    # affirmed rejections. Skipped, exactly like "appeal dismissed".
    r"(?P<affirms_prior>(?:judgment|decree|decrees)?\s*affirmed)"
    r"|(?P<appeal_dismissed>appeals?\s+(?:was\s+|were\s+)?dismissed)"
    r"|(?P<confirmed>" + CONFIRMED_OCR + r")"
    r"|(?P<rejected>rejected)"
    r"|(?P<reversed>reversed)"
    r"|(?P<discontinued>discontinued|withdrawn)"
    r"|(?P<dismissed>dismissed)",
    re.I)


# parse_appendix only starts a new chunk on a full "comm, court, district"
# marker, so an entry printed without one bleeds into its predecessor's chunk.
# Last-match would then read the NEIGHBOUR's disposition. Cut at the next
# claimant line: a number, comma, capitalised word, after sentence punctuation.
# The boundary is the entry-opening signature itself: commission no, court no,
# district. It must tolerate djvu noise, which splits and re-spaces the numerals
# ("71, 10 N. D.", "25 1 73, 1 82, N. D."). An earlier version required
# number-comma-Capital and so missed both, letting the NEXT claim's disposition
# be read as this one's. That misread ND 201 and ND 411 as confirmed when both
# were rejected.
NEXT_ENTRY = re.compile(
    # digits (which the OCR may split with spaces: "1 73" for 173), comma,
    # digits, optional comma, then the district letter and D.
    r"(?<=[.;])\s*[\d][\d ]{0,6},[\d ]{0,7},?\s*[NS8]\s*[\.,]?\s*[DI)]"
    r"|(?<=[.;])\s*\d{1,3},\s+[A-Z][a-z]")


def trim_to_own_entry(text):
    m = NEXT_ENTRY.search(text, 60)
    return text[:m.start()] if m else text


def final_disposition(text):
    """Last substantive disposition event in the entry, or None."""
    text = trim_to_own_entry(text)
    last = None
    for m in EVENT.finditer(text):
        kind = m.lastgroup
        if kind in ("appeal_dismissed", "affirms_prior"):
            continue          # upholds whatever precedes it; not a disposition
        last = kind
    return last


def classify(entry):
    d = final_disposition(entry["raw"])
    if d == "confirmed":
        return "confirmed"
    if d == "rejected":
        return "rejected"
    if d in ("discontinued", "dismissed"):
        return "other"
    if d == "reversed":
        return "other"        # "reversed and remanded": unresolved as of 1862
    return "unclear"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    entries = parse_appendix(Path(sys.argv[1]).read_text(errors="replace"))
    tally = Counter(classify(e) for e in entries)
    patented = sum(1 for e in entries if re.search(r"patented", e["raw"], re.I))

    print(f"parsed {len(entries)} appendix entries "
          f"({100*len(entries)/813:.0f}% of Hoffman's 813)\n")
    for k in ("confirmed", "rejected", "other", "unclear"):
        print(f"  {k:10} {tally[k]:4d}   {100*tally[k]/len(entries):5.1f}%")
    print(f"  {'patented':10} {patented:4d}   (subset of confirmed)")

    print("\nvs the figures published in Sources section 6 (545 / 239 / ~29 of 813):")
    scale = 813 / len(entries)
    print(f"  scaled to 813: confirmed {tally['confirmed']*scale:.0f}, "
          f"rejected {tally['rejected']*scale:.0f}, other "
          f"{(tally['other']+tally['unclear'])*scale:.0f}")

    # How badly does the screening rule differ? This is the number that matters
    # for judging whether the old parse could ever have produced 239.
    crude = Counter()
    for e in entries:
        low = e["raw"].lower()
        if "rejected" in low and "confirmed" not in low:
            crude["rejected"] += 1
        elif "confirmed" in low:
            crude["confirmed"] += 1
        else:
            crude["other"] += 1
    print(f"\nscreening rule for comparison: confirmed {crude['confirmed']}, "
          f"rejected {crude['rejected']}, other {crude['other']}")
    flipped = sum(1 for e in entries
                  if (classify(e) == "rejected") !=
                     ("rejected" in e["raw"].lower() and "confirmed" not in e["raw"].lower()))
    print(f"entries the two rules disagree on: {flipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
