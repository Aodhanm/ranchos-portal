# RESTART HERE, ranchos register audit (updated 2026-09-16)

## TL;DR

**The census is unblocked.** Berkeley's bot challenge stopped it at 557 of 672
records, and the answer turned out to be the Internet Archive, which holds the
same Bancroft case-file PDFs from a 2024 crawl and serves them freely. 97 of the
remaining 115 can be read. Tooling is written and proven.

Two things here matter more than the progress numbers:

1. **The census now corroborates the published accuracy figure** rather than
   threatening it. Re-weighted across all 557 records read it gives 5.39% overall
   against the blind 100's published 5.28%. Reproduce with
   `python3 scripts/census_strata.py`.
2. **The grading rule is `ERR` only.** `PART` is partial credit, not an error.
   Nothing recorded this until 2026-09-16, and recomputing with `PART` counted as
   an error doubles every rate and reproduces none of the published numbers.

## The plan

`audit/PLAN-remaining-work-2026-09-16.md`. Read it before starting anything. It
covers the 97 readable records, the 18 that are not archived, every access route
tested and found dead, and what needs Aodhan.

## The one thing not to get wrong

Access controls are never worked around. `digicoll.lib.berkeley.edu` returns
**HTTP 202** with `x-amzn-waf-action: challenge` and an empty body; 202 is a
SUCCESS code, so a status check passes and only a `%PDF` magic-byte check catches
it. Re-tested 2026-09-16, still live. The Internet Archive route is a different
public source, not a way around that one, and the HARD STOP section of
`audit/census-INSTRUCTIONS.md` still stands in full.

## DONE + LIVE (verified on the domain, not from local files)

- **Blind 100-record audit complete.** Overall field error **5.3%** (30/568);
  name 0, land_case 0, outcome 1.1%, governor 4.2%, year 9.6%, **grantee 16.7%**.
  Evidence `audit/verdicts-2026-09-01.json`, `audit/FINDINGS-2026-09-01.md`.
- **Case-file census at 557 of 672 (83%)**, all strata computed and reproducible.
- **Hoffman 1862 corroborates the register on all 115 unread records**: 101 of
  101 comparable rows agree, zero disagreements. The one apparent disagreement
  was our own join bug (`audit/docket-collision-2026-09-16.md`).
- **Errata register live**, 30 corrections each citing the case file that settled
  it (`data/errata.json`).
- **Frozen dataset preserved**: `data/ranchos-register.{csv,json}` byte-identical
  to Zenodo v1.0, md5 `758bb1f6cd168e941925dbdbf6704bb7` (concept DOI
  10.5281/zenodo.22185500).
- **Sources section 6 corrected 2026-09-16** to 568 confirmed / 171 rejected / 28
  other across 770 of Hoffman's 813 entries, and says why the figures moved.

## OPEN WORK (Claude can just do)

**1. Finish the census.** 97 records are reachable.

    python3 scripts/wayback_case_files.py --census     # refresh the index
    python3 scripts/wayback_case_files.py "ND 369"     # fetch one docket

Method: `audit/census-INSTRUCTIONS.md`, which now carries the Internet Archive
route. Work-list: `audit/unread-115/worklist.json`. Coverage:
`audit/unread-115/wayback-coverage.json`.

- Order: the 14 Hoffman cannot resolve first, then the 3 Hoffman-flagged, then
  the rest in docket order.
- ⚠ **THROTTLE.** One case at a time. A burst of about a hundred requests draws
  connection refusals.
- ⚠ **A capture can be truncated** and is served with a 200 and a `%PDF` header,
  the same failure shape as the WAF's 202. The helper checks the `%%EOF` trailer;
  trust that, never the status code.
- ⚠ Verdicts written to a session scratchpad are garbage collected. Run
  `python3 scripts/sync_census_verdicts.py` to pull them into the repo.
- Expected yield across all 115: about 20 field corrections, mostly grantee, and
  about one adjudication outcome. Worth doing to finish the sentence, not to move
  the headline.

**2. Remaining desk work**, all free, none started: Hoffman's main body for the
12 Northern District records with no archived capture; verifying the 29 staged
Supreme Court citations against `static.case.law`; the 5 unexplained GLO acreage
differences; the 43 Hoffman appendix entries still unparsed.

## AODHAN'S CALLS (staged, do NOT do without his OK)

1. **Cut v1.1.** Needs his Zenodo login. `audit/v1.1-candidate/` holds 171
   corrections, 29 Supreme Court citations, `docket_relation`, and the new
   `grantor_office` and `grantor_office_verbatim` columns.
2. **672 rows or 668.** Four pairs are byte-identical across every field except
   `id`. Summing `patent_acres` double counts 173,606 acres until this is ruled
   on. See `audit/duplicate-rows-2026-09-09.md`.
3. **Three grantor corrections where the sources conflict**:
   `rancho-monte-cabestros`, `rancho-cienegas`,
   `rancho-potrero-rincon-san-pedro-reglado`. Detail and evidence in
   `audit/grantor-office.json` under `still_deferred`.
4. **Gates 1958**, JSTOR-gated. **The JOHD submission**, his call on timing.

## Closed

- **The Hoffman 545/239 split**, retired; it matches neither a first-decision nor
  a final count. `audit/hoffman-split-resolved-2026-09-09.md`.
- **The JOHD "which audit number" question**, a false alarm. The competing
  200-record audit is the C-A archives database, a different dataset with no
  grantee field; "grantee 2.5%" was a misreading of "persons 2.5".

## RESUME COMMANDS

- Census status: `python3 scripts/census_strata.py`
- Fetch a case file: `python3 scripts/wayback_case_files.py "ND 369"`
- Pull verdicts out of the scratchpad: `python3 scripts/sync_census_verdicts.py`
- Rebuild the v1.1 candidate: `python3 scripts/build_v11_candidate.py`
- Rebuild the site: `python3 build_pages.py && git checkout data/ranchos-register.json && bash verify-links.sh`
- Verify live: `curl -s https://ranchos.archivesofcalifornia.com/register/ | grep -o "we hold: <b>[0-9]*"`
- Confirm the deposit is untouched: `md5 -q data/ranchos-register.csv` must be
  `758bb1f6cd168e941925dbdbf6704bb7`
