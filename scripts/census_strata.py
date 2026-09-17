#!/usr/bin/env python3
"""Stratified accuracy figures for the register, from every record read so far.

Why this exists: the crossover and stratification notes computed their four cells
ad hoc, and nothing in the repository recorded the grading rule. Recomputing them
from scratch on 2026-09-16 with PART counted as an error reproduced NONE of the
published numbers, and the discrepancy looked like a real regression until the
rule was reverse-engineered from the blind 100.

THE RULE, pinned against the published blind-100 result (30 of 568 = 5.28%,
grantee 16.67%, year 9.6%, governor 4.2%, outcome 1.1%), which it reproduces to
the decimal:

    an error is grade ERR only.
    PART is NOT an error. A truncated or garbled but correct-entity value is
      partial credit, and counting it as an error roughly doubles every rate.
    UV (not visible in the pages read) and NA (field not applicable) leave the
      denominator, they do not count as correct.

Strata are the SUBSTANTIVE Hoffman flags, i.e. a real disagreement on year,
governor or outcome. The three bookkeeping flags (name-mismatch,
docket-not-found-in-hoffman, no-parseable-docket-in-register) are excluded; they
mark a join problem, not a claim that the register is wrong, and including them
moves the flagged share from 23.4% to 37.1% and the weights with it.

Usage: python3 scripts/census_strata.py [--json]
"""
import collections
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIELDS = ["name", "year", "governor", "grantee", "land_case", "outcome"]
BOOKKEEPING = {"name-mismatch", "docket-not-found-in-hoffman",
               "no-parseable-docket-in-register"}
ERROR, NOT_GRADED = {"ERR"}, {"UV", "NA"}


def flagged_ids():
    cc = json.load(open(REPO / "audit" / "hoffman-crosscheck-v2-errata-applied.json",
                        encoding="utf-8"))
    return {r["id"] for r in cc["records"]
            if [f for f in (r.get("flags") or [])
                if isinstance(f, str) and f not in BOOKKEEPING]}


def graded_records():
    seen = {}
    for f in glob.glob(str(REPO / "audit" / "census-*" / "chunk*.json")):
        for r in json.load(open(f, encoding="utf-8")):
            seen.setdefault(r["id"], r)
    b = json.load(open(REPO / "audit" / "verdicts-2026-09-01.json", encoding="utf-8"))
    for r in (b["records"].values() if isinstance(b["records"], dict) else b["records"]):
        seen.setdefault(r["id"], r)
    return seen


def main():
    flagged = flagged_ids()
    recs = graded_records()
    total_rows = len(json.load(open(REPO / "data" / "ranchos-register.json",
                                    encoding="utf-8"))["records"])
    w = len(flagged) / total_rows

    cells = collections.defaultdict(collections.Counter)
    n = collections.Counter()
    for rid, r in recs.items():
        st = "flagged" if rid in flagged else "unflagged"
        n[st] += 1
        for f, v in (r.get("verdicts") or {}).items():
            if isinstance(v, dict):
                cells[(st, f)][(v.get("grade") or "").upper()] += 1

    def rate(st, f):
        c = cells[(st, f)]
        den = sum(v for k, v in c.items() if k not in NOT_GRADED)
        return sum(v for k, v in c.items() if k in ERROR), den

    out = {"records_read": len(recs), "register_rows": total_rows,
           "substantively_flagged": len(flagged), "flagged_share": round(w, 4),
           "rule": "error = grade ERR; PART is partial credit, not an error; "
                   "UV and NA leave the denominator",
           "strata": {}, "register_wide_reweighted": {}}
    for st in ("flagged", "unflagged"):
        tb = tt = 0
        out["strata"][st] = {"n_records": n[st], "fields": {}}
        for f in FIELDS:
            bad, den = rate(st, f)
            tb, tt = tb + bad, tt + den
            out["strata"][st]["fields"][f] = {"errors": bad, "graded": den,
                                              "rate": round(100 * bad / den, 2) if den else None}
        out["strata"][st]["overall"] = {"errors": tb, "graded": tt,
                                        "rate": round(100 * tb / tt, 2) if tt else None}
    for f in FIELDS + ["overall"]:
        get = (lambda st: rate(st, f)) if f != "overall" else (
            lambda st: (out["strata"][st]["overall"]["errors"],
                        out["strata"][st]["overall"]["graded"]))
        bf, df = get("flagged")
        bu, du = get("unflagged")
        out["register_wide_reweighted"][f] = round(
            100 * (w * bf / df + (1 - w) * bu / du), 2) if df and du else None

    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
        return 0
    print(f"{out['records_read']} of {total_rows} records read against a case file "
          f"({100*out['records_read']/total_rows:.0f}%)")
    print(f"error = ERR only; PART is partial credit; UV and NA leave the denominator")
    print(f"strata = substantive Hoffman flags, {len(flagged)}/{total_rows} = {100*w:.1f}%\n")
    for st in ("flagged", "unflagged"):
        s = out["strata"][st]
        print(f"  {st} (n={s['n_records']}):")
        for f in FIELDS:
            d = s["fields"][f]
            print(f"      {f:11s} {d['errors']:3d}/{d['graded']:4d} = {d['rate']:5.1f}%")
        d = s["overall"]
        print(f"      {'OVERALL':11s} {d['errors']:3d}/{d['graded']:4d} = {d['rate']:5.1f}%\n")
    print("  register-wide, re-weighted from these two strata:")
    for f in FIELDS + ["overall"]:
        print(f"      {f:11s} {out['register_wide_reweighted'][f]:5.2f}%")
    print("\n  published blind 100 (the unbiased estimator): overall 5.28%, "
          "grantee 16.67%, year 9.6%, governor 4.2%, outcome 1.1%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
