# The last 115, and everything else still open

Date: 2026-09-16. Written because the census stalled at 557 of 672 when Berkeley
put its scans behind a bot challenge, and the question was what, if anything,
could still be done.

**The short answer changed today. 99 of the 115 can be read after all, free, from
the Internet Archive.** The rest of this plan says how, what it is worth, and
what is left over.

---

## 1. Where the register actually stands

| | count | evidence tier |
|---|---|---|
| read against the original manuscript case file | **557** of 672 (83%) | `case-file` |
| resolved from Hoffman's 1862 printed table only | 115 | `hoffman-table` |
| of those 115, corroborating the register | **101 of 101** comparable rows | zero disagreements |
| of those 115, not resolvable from Hoffman | 14 | 11 inconclusive chains, 3 no entry |

The one apparent disagreement was ours, not the register's: the join took the
first Hoffman entry on a colliding docket number and matched Cañada de los
Pinacates to the Los Gatos or Santa Rita entry. Fixed 2026-09-16
(`audit/docket-collision-2026-09-16.md`).

**Accuracy, recomputed today across all 557 read records** and now reproducible
with `python3 scripts/census_strata.py`:

| stratum | n | overall field error | grantee |
|---|---|---|---|
| Hoffman-flagged | 157 | 13.8% | 45.9% |
| unflagged | 400 | 2.8% | 10.3% |
| **re-weighted to the register (23.4% flagged)** | | **5.39%** | **18.60%** |
| published blind 100, the unbiased estimator | 100 | 5.28% | 16.67% |

The census now independently corroborates the published figure rather than
threatening it. That is worth saying in the data paper: the blind sample said
5.28%, and reading five and a half times as many records says 5.39%.

⚠ The grading rule is `ERR` only. `PART`, a garbled but correct-entity value, is
partial credit and is **not** an error. Nothing in the repository recorded that
until today, and recomputing with `PART` counted as an error roughly doubles
every rate and reproduces none of the published numbers. `scripts/census_strata.py`
now pins the rule against the blind 100, which it reproduces to the decimal.

---

## 2. The last 115: the route that works

### What was found

The Wayback Machine crawled digicoll's case-file PDFs in 2024, **before** the AWS
WAF went up. They replay freely: no account, no card, no login, no challenge, and
nothing about Berkeley's control is touched or defeated. It is a different public
source, not a way around the first one.

Verified three ways before being written down here:

1. A probe agent found and measured it.
2. An independent agent instructed to refute it could not, and re-derived the
   counts from scratch.
3. **Directly, by hand**: `cubanc_lcf_nd369.pdf` replays as 15,420,945 bytes, a
   valid 17-page PDF, and page 1 is the case cover reading `CASE NO. 369 /
   NORTHERN DISTRICT / TOWN OF SUTTER GRANT / JOHN A. SUTTER / CLAIMANT`. That is
   register row `u-128`, "Town of Sutter", ND 369, exactly.

### Coverage

| | records |
|---|---|
| **archived, readable at `case-file` tier** | **99** of 115 |
| not archived at all | 16 |

12.2 GB in total, median 59 MB per case, one case (ND 420, New Almaden) split
across eight archived parts. Per-record detail:
`audit/unread-115/wayback-coverage.json`.

⚠ **Two are archived under a docket the register does not carry.** The Bancroft
finding aid records 17 cases transferred between districts, and two of the 115
are filed under the transferred number: ND 18 as **SD 78**, ND 191 as **SD 179**.
A third, ND 278, transferred to SD 393, which is not archived either. The finding
aid itself is served without a challenge at
`https://cinco-prd.s3.amazonaws.com/media/ead/mlandcases_cubanc.xml`.
⚠ SD 78 is catalogued as "San Felipe, an augmentation", claimant Francisco P.
Pacheco, which does **not** match the register's "San Miguelito de Trinidad".
Read it before grading; do not assume the transfer makes them the same claim.

### The tooling

    python3 scripts/wayback_case_files.py --census        # refresh the index
    python3 scripts/wayback_case_files.py "ND 369"        # fetch one docket
    python3 scripts/wayback_case_files.py "ND 369" --pages 1-20

Two traps are handled, both of which fail silently:

- **Truncated captures.** The replay serves partial bytes with a 200 and a `%PDF`
  header. Completeness is checked on the `%%EOF` trailer, never on the status
  code. This is the same shape of failure as the WAF's HTTP 202. `nd102` is
  partial and the tool says so rather than letting it be graded as a full read.
- **The `id_` modifier is required.** Without it the Wayback Machine injects its
  banner and the bytes are not a valid PDF.

Throttle it. A burst of about a hundred requests drew connection refusals, so the
fetcher retries with resume; a polite pace is roughly one case at a time.

### What reading them is actually worth

Projecting the unflagged stratum's measured rates onto the 112 unflagged and 3
flagged records among the 115:

| field | expected corrections |
|---|---|
| grantee | ~12 |
| year | ~4 |
| governor | ~2 |
| name | ~1 |
| land_case | ~1 |
| **outcome** | **~1** |
| total | **~20** of roughly 690 field values |

So: reading all 115 should yield about twenty corrections, mostly grantee, and
should change **about one adjudication outcome**. That is consistent with Hoffman
agreeing on 101 of 101, and it is the honest case both for and against doing the
work. It will not move the headline numbers. It will finish the sentence "every
record in this register has been checked against its case file", which is the
claim the data paper wants to make and cannot make today.

### Suggested order

1. **The 14 that Hoffman cannot resolve** (11 inconclusive chains, 3 with no
   entry). These are the only records where no source currently gives an
   adjudication. Highest value per file read.
2. **The 3 Hoffman-flagged records** among the 115, which sit in the 13.8%
   stratum rather than the 2.8% one.
3. **The remaining 80**, in docket order.
4. Re-run `scripts/census_strata.py` and `scripts/sync_census_verdicts.py` after
   each batch. Record every null result: a record read and found correct is a
   finding, and if it is not written down the queue re-issues it forever.

---

## 3. The 16 with no archived capture

| docket | record | Hoffman says |
|---|---|---|
| N.D. 23 | Jimeno Rancho | Confirmed |
| ND 121 | Bolsa de Tomales | Confirmed |
| ND 229 | Rincon de la Ballena | Rejected |
| ND 272 | Nueva Flandria | Rejected |
| ND 278 | Panoche Grande | inconclusive |
| ND 299 | Yerba Buena Island (Goat Island) | Rejected |
| ND 302 | Nemshas | inconclusive |
| N.D. 394 | Punta de Lobos | Rejected |
| ND 412 | Orchard of Santa Clara | Rejected |
| N.D. 423 | Pueblo of Sonoma | Confirmed |
| SD 38 | addition to San Miguelito | Confirmed |
| S.D. 57 | Cañada de San Miguelito and Cañada del Diablo | Confirmed |
| S.D. 109 | Guadalupe Llanito de los Correos | Confirmed |
| SD 229 | Cajon de los Negros | Rejected |
| SD 285 | Tres Ojos de Agua | Confirmed |
| ND/SD 425 | the California Missions and land | no entry |

Options, in order of cost:

**a. Print, free.** 10 of the 16 are Northern District, and Hoffman's *Reports*
prints full opinions for many Northern District cases in its main body, not just
the appendix table. That is a printed district-court opinion, a weaker tier than
the manuscript but stronger than the table, and the volume is already on disk
(IA item `GR_1919`). Worth trying first; costs nothing.

**b. Aeon, about $20 to $100 a case.** Bancroft's published fee schedule
(`guides.lib.berkeley.edu/bancroftdupeperm/feeschedule`, last updated 30 June
2026) lists Research Quality PDFs at $20 for 1 to 25 consecutive pages, $40 for
26 to 51, rising to $100+ above 100 pages, and a whole microfilm reel at $45. A
free online account takes minutes and needs no Berkeley affiliation, and no email
to an archivist is required. **Two cautions.** A 115-case order is untested at
that scale and would likely be refused or quoted as a project. And re-publication
permission is a separate question: there is no $0 non-profit rate for an
individual, contrary to a first reading of the terms, so treat re-publication
cost as unknown until asked.

**c. Wait.** The 18 are archived in the Bancroft's own digital collection and the
WAF may be reconfigured. Re-test with a single plain request every few months;
`scripts/wayback_case_files.py --census` will also pick up any new crawl.

**d. In person.** The Bancroft reading room holds the film (BANC MSS C-A 300
FILM, 200 reels, index in Microfilm Binder 42). Free, but it is a trip to
Berkeley. The Huntington's duplicate set is not a substitute: 26 of its 72 reels,
including every Northern District reel, are marked too fragile to circulate.

**Recommendation: (a), then leave the residue at `hoffman-table` tier and say so.**
Sixteen records at a disclosed weaker tier, in a register that states its tiers,
is an honest publication. Spending several hundred dollars to upgrade sixteen
rows whose expected yield is under four corrections is not a good use of money
before the data paper is out.

### Routes tested and found dead or not worth it

- **Calisphere and other UC hosts.** Not a mirror of the case files.
- **FamilySearch.** Carries NARA microfilm publications, not the Bancroft case
  files. Its catalogue is behind a sign-in shell.
- **NARA and the GLO.** `catalog.archives.gov` and `glorecords.blm.gov` are
  wide open, no challenge, free. But NARA's relevant series is
  *Confirmed* Private Land Claims Papers and GLO patents exist only where a
  patent issued, so both are structurally blind to rejected claims, which are 52
  of the 115. Useful for the patent layer, not for adjudication.
- **CourtListener and loc.gov.** Both behind Cloudflare challenges. The Caselaw
  Access Project static bulk host answers plain requests and is the way to verify
  the 29 staged Supreme Court citations.

---

## 4. Everything else still open

### Claude can do these

| item | state |
|---|---|
| **Read the 99** | unblocked as of today; tooling written and tested |
| **Hoffman main body for the 10 ND records** with no capture | not started, free, on disk |
| ~~Verify the 29 staged SCOTUS citations~~ | DONE. 27 stand; 2 carry a wrong page number in Hoffman's printed table and are corrected in the candidate. `audit/scotus-verification-2026-09-16.md` |
| **The 5 unexplained GLO acreage differences** | flagged, not resolved; three are under two acres and are as likely OCR as real. Needs the page images, not the OCR |
| ~~The 43 Hoffman entries still unparsed~~ | DONE. 785 of 813 recovered (97%). The remaining 28 are diagnosed, not merely unreached: see `audit/hoffman-parse-recovery-2026-09-16.md` |

### These need Aodhan

| decision | why it is his |
|---|---|
| **Cut v1.1** | Needs his Zenodo login. The candidate is built and sitting in `audit/v1.1-candidate/`: 171 corrections applied, 29 Supreme Court citations, `docket_relation`, and the new `grantor_office` and `grantor_office_verbatim` columns |
| **672 rows or 668** | Four pairs are byte-identical across every field except `id`. Whether they are duplicates in the same sense `u-100` was is an editorial ruling about the sources, not a mechanical de-duplication, and three of the four need a case file to settle. Summing `patent_acres` over the register double counts 173,606 acres, 2.2%, until this is decided |
| **The 3 grantor corrections still deferred** | `rancho-monte-cabestros` (the case file says Villavicencio, prefect ad interim; Hoffman says Alvarado, and the docket is certainly right), `rancho-cienegas` (Hoffman names both de la Guerra and Micheltorena, and Bancroft cannot explain the pairing), `rancho-potrero-rincon-san-pedro-reglado` (three officers, two tracts, two years). Each is a real source conflict, not a gap |
| **Gates 1958** | JSTOR-gated. He has institutional access; Claude does not |
| **The JOHD submission** | His call on timing |

---

## 5. What must not change

`data/ranchos-register.csv` and `data/ranchos-register.json` stay byte-identical
to the Zenodo v1.0 deposit, md5 `758bb1f6cd168e941925dbdbf6704bb7`, until Aodhan
cuts v1.1. Every correction in this session went to `audit/v1.1-candidate/`.

Never contact `digicoll.lib.berkeley.edu`, `oac.cdlib.org`, `courtlistener.com`
or `loc.gov` expecting a scripted client to be served, and never attempt to
defeat a bot challenge, a paywall or a login. The Internet Archive route exists
precisely because it does not require any of that.

## Reproduce

    python3 scripts/census_strata.py
    python3 scripts/wayback_case_files.py --census
    python3 scripts/resolve_unread_from_hoffman.py /tmp/GR_1919_djvu.txt
