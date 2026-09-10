#!/usr/bin/env python3
"""Stage a docket_relation classification for every register row. Applies nothing.

28 rows share a land case docket with another row, in classes the register has no
field to distinguish (audit/duplicate-rows-2026-09-09.md). Because every share of
a split grant repeats the SAME patent_acres, any naive sum of that column double
counts 173,606 acres, 2.2% of the total. The fix touches no existing value: one
new column saying what a row IS relative to its docket.

Proposed vocabulary:
  sole            the only row on its docket (the overwhelming majority)
  primary         first row of a multi-row docket, carries the parcel's acreage
  duplicate       byte-identical to another row apart from id (the u-100 class)
  share_of_grant  a distinct claimant's share of one grant; acreage repeats the
                  parcel total and must NOT be summed
  alternate_dating same claim entered twice under different dates, e.g. a pueblo
                  dated to its Spanish founding in one row and its Mexican
                  confirmation in the other
  unresolved      collides on a docket but the class cannot be decided without
                  the case file

Only `duplicate` is decided mechanically here (byte-identity is checkable).
Everything else on a collided docket is proposed, never asserted: distinguishing
a genuine share from a duplicate wearing a second name requires the case file.

Writes audit/proposed-docket-relation.json. Aodhan's call whether v1.1 adopts it.
"""
import csv
import collections
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IGNORE = {"id", "portal_url"}
PUEBLO_HINT = re.compile(r"\b(pueblo|city lands|mission)\b", re.I)


def docket(r):
    lc = (r.get("land_case") or "").strip().upper().replace(".", " ")
    m = re.match(r"^(ND|SD)\s*0*(\d+)$", lc)
    return f"{m.group(1)} {int(m.group(2)):03d}" if m else None


def identical(a, b):
    return all((a[k] or "") == (b[k] or "") for k in a if k not in IGNORE)


def main():
    rows = list(csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8")))
    by = collections.defaultdict(list)
    for r in rows:
        d = docket(r)
        if d:
            by[d].append(r)

    out, notes = {}, {}
    for r in rows:
        d = docket(r)
        if d is None or len(by[d]) == 1:
            out[r["id"]] = "sole"
            if d is None:
                notes[r["id"]] = "no parseable docket in the register"
            continue

        group = by[d]
        dup_of = next((o["id"] for o in group
                       if o["id"] != r["id"] and identical(r, o)), None)
        if dup_of:
            # deterministic: the later id in sort order is the duplicate
            ids = sorted(o["id"] for o in group if identical(r, o) or o["id"] == r["id"])
            out[r["id"]] = "duplicate" if r["id"] != ids[0] else "primary"
            notes[r["id"]] = f"byte-identical to {dup_of} apart from id"
            continue

        years = {o["year"] for o in group}
        if PUEBLO_HINT.search(r["name"] or "") and len(years) > 1:
            out[r["id"]] = "alternate_dating"
            notes[r["id"]] = (f"docket {d} carries {len(group)} rows with years {sorted(years)}; "
                              "pueblo/mission claim probably entered under both its Spanish "
                              "founding and its Mexican confirmation. PROPOSED, needs the case file.")
            continue

        acr = {(o["patent_acres"] or "") for o in group}
        if len(acr) == 1 and list(acr)[0]:
            out[r["id"]] = "share_of_grant"
            notes[r["id"]] = (f"docket {d} has {len(group)} rows all carrying patent_acres "
                              f"{list(acr)[0]}; acreage is the parcel total, not this row's. "
                              "PROPOSED, needs the case file to confirm these are real shares.")
            continue

        out[r["id"]] = "unresolved"
        notes[r["id"]] = f"docket {d} collision, class undecidable from the register alone"

    tally = collections.Counter(out.values())
    collided = sum(len(v) for v in by.values() if len(v) > 1)

    doc = {
        "note": ("PROPOSED docket_relation column, nothing applied. "
                 "data/ranchos-register.* stays byte-identical to Zenodo v1.0. "
                 "Only 'duplicate' is decided mechanically (byte-identity); every other "
                 "class on a collided docket is a proposal needing the case file."),
        "generated_from": "data/ranchos-register.csv",
        "rows": len(rows),
        "rows_sharing_a_docket": collided,
        "tally": dict(tally.most_common()),
        "acres_double_counted_if_summed": 173606,
        "relation": out,
        "notes": {k: v for k, v in notes.items()},
    }
    dest = REPO / "audit" / "proposed-docket-relation.json"
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"{len(rows)} rows; {collided} share a docket")
    for k, v in tally.most_common():
        print(f"  {k:17} {v}")
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
