#!/usr/bin/env python3
"""Draw the blind accuracy sample for the ranchos register.

Deterministic: same CSV + same seed always yields the same 100 records, so the
sample can be reproduced by anyone and cannot have been chosen after the answers
were known. The drawn file and its sha256 were committed before any record was
checked. See audit/README.md.
"""
import csv, json, hashlib, random, sys
from collections import Counter, defaultdict

SEED = "ranchos-register-audit-2026-09-01"
N = 100
SRC = "data/ranchos-register.csv"
OUT = "audit/sample-2026-09-01.json"
FIELDS = ("year", "governor", "grantee", "land_case", "outcome",
          "patent_to", "patent_date", "glo_patent_no")


def draw():
    rows = list(csv.DictReader(open(SRC)))
    rnd = random.Random(SEED)
    by_era = defaultdict(list)
    for r in rows:
        by_era[r["era"]].append(r)
    for k in by_era:
        by_era[k].sort(key=lambda r: r["id"])

    quota = {e: max(1, round(N * len(rs) / len(rows))) for e, rs in by_era.items()}
    while sum(quota.values()) != N:
        diff = N - sum(quota.values())
        era = max(quota, key=lambda e: len(by_era[e]))
        quota[era] += 1 if diff > 0 else -1

    sample = []
    for era in sorted(by_era):
        picks = rnd.sample(by_era[era], min(quota[era], len(by_era[era])))
        for r in sorted(picks, key=lambda x: x["id"]):
            sample.append({
                "id": r["id"], "name": r["name"], "era": era, "mapped": r["mapped"],
                "claimed": {k: r[k] for k in FIELDS + ("patent_acres",)},
                "evidence": {"bancroft_scan_url": r["bancroft_scan_url"]},
                "verdicts": {k: None for k in FIELDS},
                "notes": None, "checked_on": None,
            })

    payload = {
        "sample_of": SRC, "population": len(rows), "n": len(sample), "seed": SEED,
        "method": ("proportional stratified random sample by granting era; deterministic sort "
                   "then random.sample with the fixed public seed above; reproducible by "
                   "re-running scripts/build_audit_sample.py"),
        "drawn": "2026-09-01", "committed_before_checking": True, "records": sample,
    }
    return json.dumps(payload, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    blob = draw()
    digest = hashlib.sha256(blob.encode()).hexdigest()
    if "--verify" in sys.argv:
        live = open(OUT, encoding="utf-8").read()
        # compare the drawn ids only: verdicts get filled in as checking proceeds
        a = [r["id"] for r in json.loads(blob)["records"]]
        b = [r["id"] for r in json.loads(live)["records"]]
        print("ids match:", a == b, "| n =", len(b), "| fresh-draw sha256 =", digest)
    else:
        open(OUT, "w", encoding="utf-8").write(blob)
        print("wrote", OUT, "sha256 =", digest)
        print("strata:", dict(Counter(r["era"] for r in json.loads(blob)["records"])))
