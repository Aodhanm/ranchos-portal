#!/usr/bin/env python3
"""Audit the register's name column and its docket collisions, offline.

Written 2026-09-09 while digicoll is behind a bot challenge, to make the point
that a useful pass over the register does not always need the case files. Every
check here runs against data/ranchos-register.csv alone.

Motivation: a census agent noticed that in a stretch where every substantive
field (year, governor, grantee) verified clean against the Spanish concessions,
the defects it did find were all in the NAME string. The name column had never
had a pass of its own.

Reports:
  * malformed name strings (garbled heads, descriptions used as names, stray
    punctuation, unbalanced brackets)
  * rows that share a land case docket, classified, since these are not all the
    same thing and the register has no field that tells them apart
  * rows byte-identical to another row apart from their id, which is the u-100
    duplicate class that caused the 673-vs-672 error
  * acreage double counted across collided dockets

Changes nothing. See audit/duplicate-rows-2026-09-09.md for the findings.
"""
import csv
import collections
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPORT_IGNORE = {"id", "portal_url"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def docket(r):
    lc = (r.get("land_case") or "").strip().upper().replace(".", " ")
    m = re.match(r"^(ND|SD)\s*0*(\d+)$", lc)
    return f"{m.group(1)} {int(m.group(2)):03d}" if m else None


def acres(r):
    try:
        return float((r.get("patent_acres") or "0").replace(",", ""))
    except ValueError:
        return 0.0


def main():
    rows = list(csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8")))
    print(f"{len(rows)} rows\n")

    bad = collections.defaultdict(list)
    for r in rows:
        n = (r["name"] or "").strip()
        if not n:
            bad["empty name"].append(r["id"]); continue
        if re.match(r"^[A-Za-z]{1,2}\s+(Of|De|Del|La|El|Los|Las)\b", n):
            bad["garbled head"].append(f"{r['id']}: {n!r}")
        if re.search(r"\b\d+\s*(by|x)\s*\d+\b|varas|square leagues?|feet", n, re.I):
            bad["description used as name"].append(f"{r['id']}: {n!r}")
        if "  " in n or re.search(r"[,;:]\s*$|\s(de|del|la|los)$", n, re.I):
            bad["malformed"].append(f"{r['id']}: {n!r}")
        if n.count("(") != n.count(")"):
            bad["unbalanced brackets"].append(f"{r['id']}: {n!r}")
    for k, v in bad.items():
        print(f"--- {k}: {len(v)} ---")
        for x in v[:10]:
            print("   ", x)
    print()

    by = collections.defaultdict(list)
    for r in rows:
        d = docket(r)
        if d:
            by[d].append(r)
    dups = {k: v for k, v in sorted(by.items()) if len(v) > 1}
    print(f"--- dockets claimed by more than one row: {len(dups)}, "
          f"covering {sum(len(v) for v in dups.values())} rows ---")

    identical = []
    for d, v in dups.items():
        same_name = len({norm(x["name"]) for x in v}) == 1
        print(f"\n  {d}  ({'same name' if same_name else 'different names'})")
        for x in v:
            print(f"     {x['id']:34} {x['name'][:36]:36} yr={x['year']:5} "
                  f"acres={x['patent_acres'] or '-'}")
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                a, b = v[i], v[j]
                if all((a[k] or "") == (b[k] or "") for k in a if k not in EXPORT_IGNORE):
                    identical.append((a["id"], b["id"], d))

    print(f"\n--- BYTE-IDENTICAL row pairs (the u-100 duplicate class): {len(identical)} ---")
    for a, b, d in identical:
        print(f"    {d}: {a}  ==  {b}")

    extra = sum(sum(acres(x) for x in v[1:]) for v in dups.values())
    tot = sum(acres(r) for r in rows)
    print(f"\ntotal patent_acres {tot:,.0f}; repeated across collided dockets "
          f"{extra:,.0f} ({100*extra/tot:.1f}%) -- double counted by any naive sum")
    return 0


if __name__ == "__main__":
    sys.exit(main())
