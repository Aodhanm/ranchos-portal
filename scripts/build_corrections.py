#!/usr/bin/env python3
"""Consolidate every audit ERR into one proposed-corrections file for v1.1.

Reads the blind-100 verdicts and every census chunk, collects each field graded
ERR together with its register value, the graders' correction text, and the
evidence citation, then writes audit/proposed-corrections-consolidated.json.

This STAGES corrections; it changes no data. data/ranchos-register.* stays
byte-identical to the Zenodo v1.0 deposit until Aodhan cuts v1.1.

Each entry is cross-marked:
  in_v11_staged  - already in audit/proposed-corrections-v1.1.json (the blind-100 30)
  in_errata      - already publicly disclosed in data/errata.json
so the delta needing new errata entries is visible at a glance.

Safe to re-run at any point in the census; it rebuilds from scratch each time.
"""
import csv
import json
import glob
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIELDS = ["name", "year", "governor", "grantee", "land_case", "outcome",
          "patent_to", "patent_date", "glo_patent_no"]


def load_blind():
    d = json.load(open(REPO / "audit" / "verdicts-2026-09-01.json"))
    return d["records"] if isinstance(d, dict) else d


def main():
    register = {r["id"]: r for r in
                csv.DictReader(open(REPO / "data" / "ranchos-register.csv", encoding="utf-8"))}
    v11 = {(c["id"], c["field"]) for c in
           json.load(open(REPO / "audit" / "proposed-corrections-v1.1.json"))["corrections"]}
    # errata uses display names for fields ("grant year"); normalize crudely
    FIELD_ALIAS = {"grant year": "year", "granting governor": "governor",
                   "land case": "land_case", "original grantee": "grantee",
                   "adjudication outcome": "outcome"}
    errata = set()
    for e in json.load(open(REPO / "data" / "errata.json"))["entries"]:
        f = e.get("field", "")
        errata.add((e["id"], FIELD_ALIAS.get(f, f)))

    sources = [("blind-100", load_blind())]
    for f in sorted(glob.glob(str(REPO / "audit" / "census-partial-2026-09-02" / "chunk*.json"))):
        sources.append((Path(f).name, json.load(open(f))))

    out, seen = [], set()
    dupes = 0
    for src, records in sources:
        for r in records:
            rid = r.get("id")
            verdicts = r.get("verdicts") or {}
            corr = r.get("corrections") or {}
            for field in FIELDS:
                v = verdicts.get(field)
                if not isinstance(v, dict) or v.get("grade") != "ERR":
                    continue
                key = (rid, field)
                if key in seen:
                    dupes += 1
                    continue
                seen.add(key)
                reg = register.get(rid) or {}
                out.append({
                    "id": rid,
                    "field": field,
                    "register_value": reg.get(field, ""),
                    "correction": corr.get(field),
                    "evidence": v.get("evidence"),
                    "audit_source": src,
                    "in_v11_staged": key in v11,
                    "in_errata": key in errata,
                })
    out.sort(key=lambda e: (e["field"], e["id"]))

    by_field = Counter(e["field"] for e in out)
    n_new = sum(1 for e in out if not e["in_v11_staged"])
    missing_corr = [f'{e["id"]}/{e["field"]}' for e in out if not e["correction"]]

    doc = {
        "note": ("CONSOLIDATED proposed corrections from the blind-100 audit + the "
                 "Phase B census - NOT applied; data/ranchos-register.* stays "
                 "byte-identical to Zenodo v1.0 until Aodhan cuts v1.1. Census is "
                 "still in progress; re-run scripts/build_corrections.py to refresh."),
        "census_records_graded": sum(len(recs) for src, recs in sources if src != "blind-100"),
        "count": len(out),
        "new_beyond_v11_staged": n_new,
        "by_field": dict(by_field.most_common()),
        "entries_missing_correction_text": missing_corr,
        "corrections": out,
    }
    dest = REPO / "audit" / "proposed-corrections-consolidated.json"
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} corrections ({n_new} beyond the staged 30; {dupes} cross-source dupes skipped)")
    print("by field:", dict(by_field.most_common()))
    if missing_corr:
        print(f"⚠ {len(missing_corr)} ERR verdicts carry no correction text:", missing_corr[:6])
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
