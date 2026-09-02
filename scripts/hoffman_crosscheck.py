#!/usr/bin/env python3
"""Cross-check the ranchos register against Hoffman's 1862 appendix.

Source: Ogden Hoffman, *Reports of Land Cases Determined in the United States
District Court for the Northern District of California* (San Francisco, 1862),
appendix "Table of Land Claims" — every claim presented to the Land Commission
under the Act of March 3, 1851, with docket numbers, grant date, granting
governor, original grantee, disposition, and acreage.

Text: Internet Archive item GR_1919, file GR_1919_djvu.txt.
Usage: python3 scripts/hoffman_crosscheck.py /path/to/hoffman.txt

Output: audit/hoffman-crosscheck-2026-09-01.json — one row per register record
with per-field agree/disagree/absent flags and the raw Hoffman entry text for
any disagreement, so the per-record case-file reads can target them. This is a
screening pass over an 1862 printed source, not a verdict: the land case file
itself remains the authority for every grade.
"""
import csv, json, re, sys, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def normalize(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()


def edit1(a, b):
    """Levenshtein distance capped at 3 (enough to absorb djvu OCR confusion)."""
    if abs(len(a) - len(b)) > 3:
        return 4
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > 3:
            return 4
        prev = cur
    return prev[-1]


def name_overlap(a, b):
    """Token overlap ratio between two personal/place names, OCR-tolerant."""
    ta, tb = set(normalize(a)), set(normalize(b))
    stop = {"de", "la", "del", "los", "las", "y", "el", "don", "dona", "jose",
            "maria", "juan", "et", "als", "al"}
    ta, tb = ta - stop, tb - stop
    if not ta or not tb:
        return 0.0
    hits = 0
    for x in ta:
        for y in tb:
            tol = 1 if len(x) >= 3 else 0
            if x == y or (len(x) > 3 and len(y) > 3 and (x in y or y in x)) \
                    or (tol and edit1(x, y) <= (2 if len(x) >= 7 else 1)):
                hits += 1
                break
    return min(1.0, hits / max(min(len(ta), len(tb)), 1))


def parse_appendix(text):
    start = text.find("TABLE  OF  LAND  CLAIMS")
    if start < 0:
        sys.exit("appendix header not found")
    body = text[start:]
    # Entries open with: commission_no, court_no, N. D./S. D. [, jimeno_no].
    entry_re = re.compile(
        r"^\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([NS8])[\.,]?\s*[DI)][\.,]?", re.M)
    marks = list(entry_re.finditer(body))
    entries = []
    for i, m in enumerate(marks):
        chunk = body[m.start(): marks[i + 1].start() if i + 1 < len(marks) else m.start() + 2500]
        chunk = re.sub(r"[¬-]\s*\n\s*", "", chunk)          # printer's hyphen at line break
        chunk = re.sub(r"\s*\n\s*", " ", chunk)
        chunk = re.sub(r"APPENDIX\.?", " ", chunk)
        chunk = re.sub(r"\s{2,}", " ", chunk).strip()
        district = "ND" if m.group(3) == "N" else "SD"
        e = {"commission_no": int(m.group(1)), "court_no": int(m.group(2)),
             "district": district, "raw": chunk[:900]}
        cm = re.search(r"claimants?\s+for\s+(.+?)\s*,", chunk)
        e["rancho"] = cm.group(1) if cm else None
        ym = re.search(r"granted[^;]*?1?8\s?(\d{2})", chunk)
        gm = re.search(
            r"granted\s+(?:in\s+)?[A-Za-z]*\.?\s*\d*[a-z]*\s*,?\s*(1\s?8\s?\d\s?\d)\s*,?\s*"
            r"(?:by\s+(.+?)\s+)?to\s+(.+?)\s*[;,]", chunk)
        if gm:
            e["year"] = int(re.sub(r"\s", "", gm.group(1)))
            e["governor"] = (gm.group(2) or "").strip() or None
            e["grantee"] = gm.group(3).strip()
        else:
            e["year"] = int("18" + re.sub(r"\s", "", ym.group(1))) if ym else None
            e["governor"] = e["grantee"] = None
        low = chunk.lower()
        e["patented_1862"] = "patented" in low
        if "rejected" in low and "confirmed" not in low:
            e["disposition_1862"] = "rejected"
        elif "confirmed" in low:
            e["disposition_1862"] = "confirmed"
        elif "dismissed" in low or "discontinued" in low:
            e["disposition_1862"] = "dismissed"
        else:
            e["disposition_1862"] = "unclear"
        entries.append(e)
    return entries


def main():
    text = Path(sys.argv[1]).read_text(errors="replace")
    entries = parse_appendix(text)
    by_docket = {}
    for e in entries:
        by_docket.setdefault((e["district"], e["court_no"]), []).append(e)

    rows = list(csv.DictReader(open(REPO / "data" / "ranchos-register.csv")))
    out, tallies = [], {"matched": 0, "no_docket_match": 0, "no_land_case": 0}
    for r in rows:
        rec = {"id": r["id"], "name": r["name"], "flags": [], "hoffman": None}
        lc = (r.get("land_case") or "").strip()
        dm = re.match(r"^(ND|SD)\s*0*(\d+)$", lc.replace(".", "").upper())
        if not dm:
            tallies["no_land_case"] += 1
            rec["flags"].append("no-parseable-docket-in-register")
            out.append(rec)
            continue
        cands = by_docket.get((dm.group(1), int(dm.group(2))), [])
        # A court number can repeat across the table's OCR noise; pick by name.
        best = max(cands, key=lambda e: name_overlap(e.get("rancho") or "", r["name"]),
                   default=None)
        if not best or (len(cands) > 1 and name_overlap(best.get("rancho") or "", r["name"]) < 0.34):
            tallies["no_docket_match"] += 1
            rec["flags"].append("docket-not-found-in-hoffman")
            out.append(rec)
            continue
        tallies["matched"] += 1
        rec["hoffman"] = {k: best[k] for k in
                          ("commission_no", "court_no", "district", "rancho", "year",
                           "governor", "grantee", "disposition_1862", "patented_1862")}
        if name_overlap(best.get("rancho") or "", r["name"]) < 0.34:
            rec["flags"].append("name-mismatch")
        if best["year"] and r["year"] and abs(best["year"] - int(r["year"][:4])) > 0:
            rec["flags"].append(f"year: register {r['year']} vs hoffman {best['year']}")
        if best["governor"] and r["governor"] and \
                name_overlap(best["governor"], r["governor"]) == 0:
            rec["flags"].append(f"governor: register {r['governor']!r} vs hoffman {best['governor']!r}")
        if best["grantee"] and r["grantee"] and name_overlap(best["grantee"], r["grantee"]) < 0.34:
            rec["flags"].append(f"grantee: register {r['grantee']!r} vs hoffman {best['grantee']!r}")
        reg_out = (r.get("outcome") or "").lower()
        if best["disposition_1862"] == "rejected" and "reject" not in reg_out:
            # Post-1862 reversals exist; flag for the case-file read, don't judge.
            rec["flags"].append(f"outcome: register {r['outcome']!r} vs hoffman-1862 'rejected'")
        if rec["flags"]:
            rec["hoffman_raw"] = best["raw"]
        out.append(rec)

    flagged = [r for r in out if r["flags"]]
    result = {"source": "IA GR_1919 (Hoffman 1862 appendix)", "run": "2026-09-01",
              "register_rows": len(rows), "appendix_entries": len(entries),
              "tallies": tallies, "flagged_count": len(flagged), "records": out}
    dest = REPO / "audit" / "hoffman-crosscheck-2026-09-01.json"
    dest.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"appendix entries parsed: {len(entries)}")
    print(f"register matched: {tallies['matched']}  unmatched-docket: {tallies['no_docket_match']}  "
          f"no-docket: {tallies['no_land_case']}")
    print(f"flagged records: {len(flagged)} -> {dest}")
    for r in flagged[:25]:
        print(" ", r["id"], "|", "; ".join(r["flags"])[:160])


if __name__ == "__main__":
    main()
