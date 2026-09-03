# RESTART HERE — ranchos register audit (2026-09-02)

Session paused mid-flight. This is the exact state and how to resume.

## TL;DR
The **blind 100-record audit is COMPLETE and safely committed+pushed**. Overall
field error rate **5.3%** (30/568); grantee **16.7%** (dominant class: US-era
land-case claimant recorded instead of the original Mexican grantee); one outcome
error (u-23 shown Confirmed, actually rejected). Site fixes are **half-applied in
the working tree but NOT rebuilt and NOT pushed** — the live site is unchanged.

## COMMITTED + PUSHED (safe on GitHub, github.com/Aodhanm ranchos repo)
- `7038bcf` Hoffman 1862 cross-check of all 672 records (`audit/hoffman-crosscheck-2026-09-01.json`)
- `41a2b86` audit checkpoint 54/100
- `bcb2a16` audit COMPLETE 100/100 — `audit/verdicts-2026-09-01.json` (every grade cites its PDF page),
  `audit/FINDINGS-2026-09-01.md`, `audit/README.md` (status updated),
  `audit/proposed-errata-2026-09-01.json` (30 entries STAGED), `audit/proposed-corrections-v1.1.json` (30 STAGED)
- site-prose audit commit — `audit/site-prose-audit-2026-09-02.md`

## UNCOMMITTED working-tree edits — IN FLIGHT, live site UNCHANGED (run `git diff` to see)
All are the "make the counts correct + refresh stale audit prose" pass. Root cause of
the count bugs: `DATA.counts.total` counted the suppressed duplicate `u-100` (Topanga
Malibu, dup of SD 147). Verified-correct values: total **672**, unmapped **137**,
patents **531** (NOT 673/138/532).
- `index.html`: DATA.counts total 673→672 and unmapped 138→137 (DONE);
  Sources §10 status block rewritten from "0 of 100 checked" to the completed results (DONE)
- `build_pages.py`: rancho-page footer "673"→`{D["counts"]["total"]}` (DONE);
  `npat` now excludes `suppress_register` →531 (DONE); module docstring 673→672 (DONE);
  errata "How corrections are found" tense fixed to past/complete (DONE)
- `data/errata.json`: **NOT populated yet** (entries[] still empty). The generator was
  interrupted. Re-run it (script below) to fill the errata table from the 30 verified errors.

## TO FINISH THE SITE FIX (in order)
1. Populate errata: regenerate `data/errata.json` — schema the builder expects is
   `{id,name,field,was,now,source,date}` (see build_pages.py lines 528-537). Source data =
   `audit/verdicts-2026-09-01.json` ERR grades + register `was` values. (Generator script was
   ready; it maps each ERR to a concise corrected `now`.)
2. `python3 build_pages.py` then `bash verify-links.sh`.
3. ⚠ REVERT the `generated` date drift in `data/ranchos-register.{csv,json}` after building —
   build_pages rewrites it and it MUST stay byte-identical to the Zenodo v1.0 deposit
   (concept DOI 10.5281/zenodo.22185500). `git checkout data/ranchos-register.csv data/ranchos-register.json`
   if the only change is the generated date.
4. Also fix (lower sev, self-flagged): `data/ranchos-experimental.json` abstract/legend
   "510"→535 and "246 rejected"→239 (unique-string edits; 246 appears elsewhere so match
   "246 rejected" / "510 of 813" / "510 grants" only).
5. Commit + push. Verify LIVE on ranchos.archivesofcalifornia.com (hard-refresh): register
   page + a rancho page footer + Sources §10 + errata table all show 672 and the real rates.

## CENSUS PASS (Phase B — the "more than 100, all records" ask)
- **40 of ~570 graded**, all agents now dead (session/classifier/watchdog on big PDFs).
- Verdicts: scratchpad `verdicts-B/chunk01-08.json` (also being copied to `audit/census-partial-2026-09-02/`).
- Inputs: scratchpad `phaseB/chunk01-48.json` (48 chunks of 12, Hoffman-flagged first). INSTRUCTIONS: `phaseB/INSTRUCTIONS.md`.
- Same pattern recurring: claimant-as-grantee (ND 023 Jimeno Rancho name+grantee wrong; James Enright/Garcia; etc.).
- To resume: relaunch agents on chunks with <12 graded, THROTTLE to ~4-6 at once (10+ tripped
  session limits twice; big pueblo/litigated PDFs 200-486MB stall the watchdog — they need
  pypdf page-range splitting, no qpdf/gs on this machine).

## STILL PENDING — AODHAN'S CALLS (do not do without his OK)
1. Cut register **v1.1** applying the 30 data corrections (staged `audit/proposed-corrections-v1.1.json`)
   + new Zenodo deposit. (Errata publishing the corrections = the interim method; v1.1 = the formal fold-in.)
2. **JOHD number reconciliation**: the vault dissemination draft cites a *different* audit
   (200 records, 19 July 2026, grantee 2.5%); THIS audit is 100 records with grantee 16.7%.
   Decide which is the canonical cited figure before submission.

## KEY NUMBERS (from audit/FINDINGS-2026-09-01.md)
n=100. 49 exact / 25 with >=1 error. Per field err%: name 0, land_case 0, outcome 1.1,
governor 4.2, year 9.6, grantee 16.7. Patent date + GLO number = UV (no clean public-domain
source; BLM API route was REJECTED on a credential-exploit policy call — do not revive it).

## RESUME SNIPPET (regenerate errata.json)
```
cd ~/ranchos-portal && python3 - <<'PY'
import json, csv
d=json.load(open("audit/verdicts-2026-09-01.json")); reg={r['id']:r for r in csv.DictReader(open('data/ranchos-register.csv'))}
LBL={'year':'grant year','governor':'granting governor','grantee':'grantee','name':'name','outcome':'adjudication outcome','land_case':'land case'}
def concise(t):
    t=t.strip()
    for s in [' per ',', per',' (',' — ','; ']:
        i=t.find(s)
        if 0<i<90: t=t[:i]; break
    return t.strip(' ,.;:')[:120]
E=[]
for r in d["records"]:
    for f in ['name','year','governor','grantee','land_case','outcome']:
        v=r["verdicts"].get(f)
        if v and v.get("grade")=="ERR":
            E.append({"id":r["id"],"name":r.get("name") or r["id"],"field":LBL[f],
                "was":reg.get(r["id"],{}).get(f,"") or "(blank)",
                "now":concise((r.get("corrections") or {}).get(f) or v.get("evidence","")),
                "source":f"Bancroft land case file {reg.get(r['id'],{}).get('land_case','')}".strip(),
                "date":"2026-09-02"})
json.dump({"title":"Errata","policy":json.load(open('data/errata.json'))['policy'],"updated":"2026-09-02","entries":E},
          open("data/errata.json","w"),indent=1,ensure_ascii=False)
print(len(E),"entries")
PY
```
