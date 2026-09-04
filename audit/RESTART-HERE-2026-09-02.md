# RESTART HERE, ranchos register audit (updated 2026-09-03)

## TL;DR
The site-correction pass is finished and live. The Phase B census is running and
is the only substantial work left. Two things on this page are new and matter
more than the progress numbers: **the census head is an adverse sample and must
not be reported as the register's accuracy**, and **the JOHD "which audit number"
question was a false alarm and is closed.**

## The one thing not to get wrong

`audit/census-stratification-2026-09-03.md`. Read it before you quote any census
figure. In short: the Phase B queue is ordered **Hoffman-flagged first**, chunks
01 to 11 are 100% flagged records and chunks 43 to 48 are 0% flagged, so the
running census total is the error rate of the stratum the 1862 printed table
already called suspect, not of the register. Pooled it currently reads 13.1%
overall and 42.4% on grantee against the published 5.3% and 16.7%, and that
comparison is meaningless.

The control: splitting the random blind 100 the same way gives its flagged subset
14.2% overall and 40.7% grantee (n=27) against the census flagged records' 13.5%
and 47.2% (n=127, recomputed 2026-09-04 at 141 graded). Two independent passes
agree. Re-weighting both strata to their true share of the register (23.8%
flagged) puts the register-wide estimate at roughly 4.5% overall and about 16.8%
grantee, in line with the published numbers.

**The published blind-100 figures stand. Do not
restate them from census data.** Finish the census for the corrections it yields.

## DONE + LIVE (verified on the domain, not from local files)
- **Blind 100-record audit complete.** Overall field error **5.3%** (30/568); by
  field: name 0, land_case 0, outcome 1.1%, governor 4.2%, year 9.6%, **grantee
  16.7%**. 49/100 exact, 25/100 with at least one error. One outcome error (u-23,
  a rejected claim shown Confirmed). Evidence `audit/verdicts-2026-09-01.json`
  (every grade cites its PDF page) and `audit/FINDINGS-2026-09-01.md`.
- **673 to 672 overcount fixed site-wide** (root cause: the suppressed duplicate
  u-100 was counted in DATA.counts.total). Commit `6b900b0`.
- **Errata register populated + live**: 30 corrections, each with the land case
  file that settled it (`data/errata.json`).
- **Sources §10 refreshed** from "0 of 100 checked" to the completed result.
- **Lower-severity prose pass DONE 2026-09-03** (commit `825a8dd`, verified live):
  `ranchos-experimental.json` abstract and legend "510" to **535** and "246
  rejected" to **239**; "40 counties" to **39** on the register page, the homepage
  og:description and the JSON-LD Dataset description (40 distinct county values,
  but one is the literal string "various", so 39 are real named counties); the
  build log now counts published rows (672) instead of including u-100.
- **Frozen dataset preserved**: `data/ranchos-register.{csv,json}` byte-identical
  to Zenodo v1.0 (concept DOI 10.5281/zenodo.22185500).
- Hoffman 1862 cross-check of all 672 (`audit/hoffman-crosscheck-2026-09-01.json`).
- Site-prose audit (`audit/site-prose-audit-2026-09-02.md`), now fully worked off.

## OPEN WORK (Claude can just do)

**1. Finish the census (Phase B).** Verify the remaining records against their
case files, same method as the blind 100.
- Progress: `python3 -c "import json,glob;print(sum(len(json.load(open(f))) for f in glob.glob('audit/census-partial-2026-09-02/chunk*.json')),'of 572 graded')"`
- Inputs: scratchpad `phaseB/chunk01-48.json` + `phaseB/INSTRUCTIONS.md`.
- ⚠ **THROTTLE to 4-6 concurrent agents.** 10+ tripped session limits twice. On
  this 8-core machine the Workflow tool's own cap is 6, which is correct; a
  pipeline over chunks self-throttles.
- ⚠ **Verdicts live in a session scratchpad that gets garbage collected.** Run
  `python3 scripts/sync_census_verdicts.py` to pull them into the repo. It
  refuses to shrink a chunk, so it is safe to run while agents are still writing.
- The claimant-as-grantee pattern is the dominant error class and keeps recurring.

**2. Big case files no longer need to stall.** `scripts/fetch_case_pages.py`
resolves a docket to its Bancroft PDF, downloads it **with resume**, and cuts out
a page range. Use it instead of `curl -sL -m 300` on anything large:

    python3 scripts/fetch_case_pages.py "ND 419" --pages 1-30 --discard-full

⚠ NEW 09-04: a WRONG filename gets HTTP 200 + an HTML error page from digicoll,
not a 404 (two-volume cases ND 136 = nd136A/B, ND 199 = nd199A/B). The helper now
requires %PDF magic bytes and prints a MULTI-VOLUME note; never hand-roll curl
checks against the status code.

Verified end to end on ND 060 (43.8MB, 49 pages, 16s) and ND 419 Pueblo Lands of
San Jose (486.5MB, 585 pages, 4m20s), both producing legible excerpts.
**Do not retry these two ideas, both tested and dead:** HTTP Range requests save
nothing (pypdf reads the whole stream regardless, and fetched 100% of both files),
and digicoll serves no IIIF manifest and no per-page images for these items.

## AODHAN'S CALLS (staged, do NOT do without his OK)

**1. Register v1.1.** Apply the 30 data corrections
(`audit/proposed-corrections-v1.1.json`) to the register data and cut a new Zenodo
deposit. The errata register already discloses them publicly; v1.1 is the formal
fold-in.

**2. ~~JOHD number~~ CLOSED 2026-09-03, this was a false alarm.** The earlier
restart note said the vault dissemination draft cited a competing ranchos audit
(200 records, 19 July 2026, "grantee 2.5%") and that the canonical figure had to
be chosen. It does not. That 200-record audit is the **C-A archives database**
audit (concept DOI 10.5281/zenodo.21327098), a different dataset with different
fields, graded on dates 6.5 / persons 2.5 / substance 5.5 / page-pins 1.0, 73%
exact. It has no grantee field at all; "grantee 2.5%" was a misreading of
"persons 2.5". The two numbers do not compete and nothing needs deciding.
The stale line in the vault (`06 Main Notes/Research Projects/ca-archives/
dissemination-drafts-2026-07-22.md`, polish item 1, which still said "verification
0 of 100, the submission waits on this number") has been updated with the finished
result and a warning against the same conflation.

**3. NEW: the Hoffman 545 / 239 / ~29 split is not verifiable.** See
`audit/hoffman-split-note-2026-09-03.md`. Sources §6 attributes it to
`data/hoffman-claims.json`, marked "Hoffman 1862 (verified in file)", and **that
file is not in the repo**. An independent re-parse of Hoffman's appendix (IA item
GR_1919) with the repo's own parser yields 766 entries and 601/162, and that
parser's disposition rule is a screening heuristic that miscounts appeals, so it
neither confirms nor refutes 239. The abstract was aligned to 239 to stop two
published surfaces contradicting each other, but before the JOHD submission
either restore `hoffman-claims.json` and recompute the split from the final
decree, or drop the parenthetical breakdown and cite only the uncontested 813.

## RESUME COMMANDS
- Census status: `python3 -c "import json,glob;print(sum(len(json.load(open(f))) for f in glob.glob('audit/census-partial-2026-09-02/chunk*.json')),'of 572 graded')"`
- Pull verdicts out of the scratchpad: `python3 scripts/sync_census_verdicts.py`
- Rebuild after any edit: `python3 build_pages.py && git checkout data/ranchos-register.json && bash verify-links.sh`
- Verify live: `curl -s https://ranchos.archivesofcalifornia.com/register/ | grep -o "we hold: <b>[0-9]*"`
