# Three more exact duplicate rows, and a docket-collision class the register does not model

Date: 2026-09-09. Found by a name-column sweep run entirely against local data,
while digicoll is behind a bot challenge and no case files can be read.

## The headline

`u-100` "Topanga Malibu" was found in the 09-01 audit to be a duplicate row
counted in `DATA.counts.total`, and suppressing it is what turned 673 into 672.
It is not the only one. **Three further pairs are byte-identical across every
exported field except `id`:**

| docket | rows | status |
|---|---|---|
| ND 308 | `rancho-canada-hambre-bolsas` / `-1` | identical, neither suppressed |
| ND 319 | `rancho-new-helvetia` / `-1` | identical, neither suppressed |
| SD 337 | `rancho-unnamed-3` / `rancho-unnamed-4` | identical, neither suppressed |

The app carries exactly **one** `suppress_register` flag in `DATA` (u-100), so
these three are live on the register page, in the CSV, in the JSON, and in the
Zenodo v1.0 deposit. If they are duplicates in the same sense u-100 was, the
published total is **669, not 672**, and the same off-by-one logic that produced
the 673 error is still producing a three-count error.

They are NOT being fixed here. `data/ranchos-register.*` stays byte-identical to
the deposit until v1.1, and whether New Helvetia's second row is a duplicate or a
genuine second claim on the same docket is a question about the source, not the
data file. It needs the case file, which is currently unreachable.

## The wider class: 12 dockets are claimed by more than one row

28 of 672 rows share a docket with at least one other row. They are not all the
same kind of thing, and the register has no field that distinguishes them:

1. **Exact duplicates** (the three above). Almost certainly rows to suppress.
2. **Pueblo double entry** (SD 242, SD 382, SD 386, SD 390). Each pueblo appears
   once as `pueblo-*` and once as `u-*`, same patentee and same acreage, but with
   different years: Santa Barbara 1834 against 1782, San Diego 1834 against 1769.
   One row is dating the Mexican-era grant and the other the Spanish founding.
   Both are defensible facts about the same claim, but as two rows they double
   the pueblo in every count.
3. **Multi-claimant splits** (ND 392 Nicasio, five rows; SD 337 Potreros, three).
   One grant generating several claims is a real historical pattern and the
   Sources page already says so. The problem is that every share carries the
   **same** `patent_acres`, so the parcel is counted once per claimant.
4. **Same docket, different name** (SD 388: "Laguna" against "Canada de los Pinos
   or College Rancho", identical patentee and acreage). One of those names is
   probably wrong, or one row is a duplicate wearing a second name.
5. **Probable genuine parcels** (SD 032 Sespe No. 1 and No. 2) which nonetheless
   share an identical 8,880.81 acres, which is worth a look.

## Why it matters beyond tidiness

**Summing `patent_acres` over the register double counts 173,606 acres, 2.2% of
the 7,806,505 acre total.** Nothing on the site sums that column today, so
nothing published is currently wrong because of it. But it is a downloadable
CC BY dataset with a DOI, and total-acreage-by-era or by-county is the most
obvious thing a reuser will compute. They will get a number 2.2% too high with no
way to know.

The cheapest honest fix, and it does not require touching a single value: add a
column that marks a row's relationship to its docket (`primary`, `duplicate`,
`share_of_grant`, `alternate_dating`). Reusers can then aggregate correctly and
the three exact duplicates stop being invisible.

## Recommended for v1.1

1. Resolve the three exact duplicates against their case files when access
   returns, then suppress them the way u-100 was, and restate the total.
2. Add the docket-relationship column.
3. Decide the pueblo double-entry question once, as policy, rather than per row.

All three are Aodhan's calls. Nothing has been changed.

## Reproduce

    python3 scripts/audit_name_column.py
