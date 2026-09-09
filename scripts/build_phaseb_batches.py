#!/usr/bin/env python3
"""Rebuild the Phase B census work-list from the repo's own durable data.

The original phaseB/chunk*.json batches lived only in a session scratchpad and
were pruned on 2026-09-08 with 378 of 572 records still ungraded. Nothing was
lost that cannot be regenerated: every field in those batches derives from
data/ranchos-register.csv and audit/hoffman-crosscheck-2026-09-01.json. This
script is that regeneration, kept in the repo so the work-list can never be the
thing that goes missing again.

Ordering reproduces the original rule: records whose Hoffman cross-check shows a
SUBSTANTIVE disagreement (year, governor, grantee, outcome) come first, because a
Hoffman flag predicts a register error roughly eightfold (see
audit/census-stratification-2026-09-03.md). Within each stratum, id order.

By default it emits only the records not yet graded, into a fresh directory, so
resuming cannot collide with verdict files written against the old batches.

Usage:
    python3 scripts/build_phaseb_batches.py --out /path/to/scratchpad/phaseB2
    python3 scripts/build_phaseb_batches.py --all --out /tmp/full   # full 572
    python3 scripts/build_phaseb_batches.py --validate              # self-check only
"""
import argparse
import csv
import json
import glob
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SUBSTANTIVE = {"year", "governor", "grantee", "outcome"}
DEFAULT_CHUNK = 12

# One record from the original batches, captured before they were pruned.
# The rebuild must reproduce it byte-for-byte or the reconstruction is wrong.
GOLDEN = {
    "id": "rancho-san-miguel-1", "name": "San Miguel", "era": "alvarado",
    "claimed": {"year": "1841", "governor": "Alvarado", "grantee": "P. Apis",
                "land_case": "SD 065", "outcome": "Confirmed",
                "patent_to": "Raimundo Olivas and Felipe Lorenzana",
                "patent_date": "Mar. 21, 1873", "glo_patent_no": "394",
                "patent_acres": "4,693.91"},
    "scan_record_url": "https://digicoll.lib.berkeley.edu/record/266100",
    "hoffman_1862": {"commission_no": 472, "court_no": 65, "district": "SD",
                     "rancho": "San Miguel", "year": 1841,
                     "governor": "Juan B. Alvarado", "grantee": "E. Olivas et al.",
                     "disposition_1862": "confirmed", "patented_1862": False},
    "hoffman_flags": ["grantee: register 'P. Apis' vs hoffman 'E. Olivas et al.'"],
}


def build_all():
    hc = {r["id"]: r for r in json.load(
        open(REPO / "audit" / "hoffman-crosscheck-2026-09-01.json", encoding="utf-8"))["records"]}
    blind = json.load(open(REPO / "audit" / "verdicts-2026-09-01.json", encoding="utf-8"))
    blind_ids = {r["id"] for r in (blind["records"] if isinstance(blind, dict) else blind)}

    recs = []
    for r in csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8")):
        if r["id"] in blind_ids:          # the blind 100 is a separate, published pass
            continue
        h = hc.get(r["id"]) or {}
        flags = [f for f in (h.get("flags") or []) if f.split(":")[0] in SUBSTANTIVE]
        recs.append({
            "id": r["id"], "name": r["name"], "era": r["era"],
            "claimed": {k: r[k] for k in
                        ("year", "governor", "grantee", "land_case", "outcome",
                         "patent_to", "patent_date", "glo_patent_no", "patent_acres")},
            "scan_record_url": r["bancroft_scan_url"] or None,
            "hoffman_1862": h.get("hoffman"),
            "hoffman_flags": flags,
        })
    recs.sort(key=lambda x: (not x["hoffman_flags"], x["id"]))
    return recs


def graded_ids():
    got = set()
    for f in glob.glob(str(REPO / "audit" / "census-*" / "chunk*.json")):
        for r in json.load(open(f, encoding="utf-8")):
            got.add(r["id"])
    return got


def validate(recs):
    hit = next((r for r in recs if r["id"] == GOLDEN["id"]), None)
    if hit is None:
        return "golden record not produced at all"
    if hit != GOLDEN:
        diffs = [k for k in GOLDEN if hit.get(k) != GOLDEN[k]]
        return f"golden record mismatch on {diffs}\n  got: {json.dumps(hit, ensure_ascii=False)}"
    if len(recs) != 572:
        return f"expected 572 non-blind records, produced {len(recs)}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="directory to write chunkNN.json into")
    ap.add_argument("--all", action="store_true",
                    help="emit all 572 records, not just the ungraded ones")
    ap.add_argument("--validate", action="store_true", help="self-check and exit")
    ap.add_argument("--size", type=int, default=DEFAULT_CHUNK,
                    help="records per chunk (default 12). Smaller chunks complete "
                         "and report before a session limit can kill the agent, so "
                         "its findings survive; verdicts survive either way.")
    a = ap.parse_args()

    recs = build_all()
    err = validate(recs)
    if err:
        print(f"VALIDATION FAILED: {err}", file=sys.stderr)
        return 3
    print(f"validated: 572 records, golden record reproduces exactly")
    print(f"  {sum(1 for r in recs if r['hoffman_flags'])} substantively Hoffman-flagged (they sort first)")
    if a.validate:
        return 0
    if not a.out:
        ap.error("--out is required unless --validate")

    if not a.all:
        got = graded_ids()
        before = len(recs)
        recs = [r for r in recs if r["id"] not in got]
        print(f"  {before - len(recs)} already graded, {len(recs)} remain")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(0, len(recs), a.size):
        n += 1
        (out / f"chunk{n:02d}.json").write_text(
            json.dumps(recs[i:i + a.size], indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {n} chunk file(s) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
