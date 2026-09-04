# RESTART HERE — ranchos register audit (updated 2026-09-03)

## TL;DR — the site fix is DONE and LIVE
The blind 100-record audit is complete, and the whole site-correction pass is now
**published and verified live** on ranchos.archivesofcalifornia.com. Working tree is
clean. What remains is the census pass (optional, more coverage) and two decisions
that are Aodhan's.

## DONE + LIVE (committed & pushed, verified on the domain)
- **Blind 100-record audit complete.** Overall field error **5.3%** (30/568); by field:
  name 0, land_case 0, outcome 1.1%, governor 4.2%, year 9.6%, **grantee 16.7%**.
  49/100 exact, 25/100 with ≥1 error. One outcome error (u-23, rejected shown Confirmed).
  Evidence: `audit/verdicts-2026-09-01.json` (every grade cites its PDF page),
  `audit/FINDINGS-2026-09-01.md`.
- **673→672 overcount fixed site-wide** (root cause: suppressed duplicate u-100 counted in
  DATA.counts.total). 672 / 137 unmapped / 531 patents now correct on the register page,
  homepage og+JSON-LD, Sources §6, and all 535 rancho-page footers. Commit `6b900b0`.
- **Errata register populated + live**: 30 corrections, each with the land case file that
  settled it (`data/errata.json`). "30 corrections recorded" confirmed live.
- **Sources §10 refreshed** from "0 of 100 checked" to the completed 5.3% result. Live.
- **Frozen dataset preserved**: `data/ranchos-register.{csv,json}` byte-identical to Zenodo
  v1.0 (concept DOI 10.5281/zenodo.22185500); generated-date drift reverted each build.
- Hoffman 1862 cross-check of all 672 (`audit/hoffman-crosscheck-2026-09-01.json`).
- Site-prose audit (`audit/site-prose-audit-2026-09-02.md`).

## OPTIONAL NEXT WORK (Claude can just do)
1. **Census pass (Phase B)** — verify the other ~570 records against their case files, same
   method as the blind 100. **40 done** (`audit/census-partial-2026-09-02/` + scratchpad
   `verdicts-B/`). Inputs: scratchpad `phaseB/chunk01-48.json` (Hoffman-flagged first),
   `phaseB/INSTRUCTIONS.md`. ⚠ THROTTLE to ~4-6 agents (10+ tripped session limits twice);
   big pueblo/litigated PDFs (200-486MB) stall the watchdog and need pypdf page-range
   splitting (no qpdf/gs on this machine). Same claimant-as-grantee pattern keeps recurring.
2. **Lower-sev site cleanups still open** (from `audit/site-prose-audit-2026-09-02.md`):
   `data/ranchos-experimental.json` abstract/legend "510"→535 and "246 rejected"→239
   (match "510 of 813" / "510 grants" / "246 rejected" only — 246 appears elsewhere);
   "40 counties" counts the literal value "various" (39 real named counties).

## AODHAN'S CALLS (staged, do NOT do without his OK)
1. **Register v1.1**: apply the 30 data corrections (`audit/proposed-corrections-v1.1.json`)
   to the register data + cut a new Zenodo deposit. (Errata already discloses them publicly;
   v1.1 is the formal fold-in.)
2. **JOHD number**: the vault dissemination draft cites a *different* audit (200 records,
   19 July 2026, grantee 2.5%); THIS audit is 100 records, grantee 16.7%. Decide the
   canonical cited figure before submission. (This is the strongest single point of the JOHD
   review, so it matters which number is quoted.)

## RESUME COMMANDS
- Census status: `python3 -c "import json,glob;print(sum(len(json.load(open(f))) for f in glob.glob('audit/census-partial-2026-09-02/chunk*.json')),'graded')"`
- Rebuild after any edit: `python3 build_pages.py && git checkout data/ranchos-register.json && bash verify-links.sh`
- Verify live: `curl -s https://ranchos.archivesofcalifornia.com/register/ | grep -o "we hold: <b>[0-9]*"`
