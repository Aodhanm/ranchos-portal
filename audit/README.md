# Blind accuracy audit of the ranchos register

**Sample committed 2026-09-01, before any record was checked.**

```
file    audit/sample-2026-09-01.json
sha256  0f27e66ae19369336f1e5c3ebdaaef8d4838e6832e328791abc5de9afcd5e057
n       100 of 672 records
seed    ranchos-register-audit-2026-09-01
```

## Why this exists

The register is compiled from printed and digitized intermediaries: the Bancroft
land case files, the Online Archive of California finding aid, Cris Perez's 1982
state patent register (OCR'd), Ogden Hoffman's 1862 *Reports of Land Cases*, and the
case summaries of the California Land Grants ArcGIS project. A compilation at that
remove from the manuscripts can only be as accurate as its sources and its own
transcription, and a reader has no way to judge that from the interface. So the
register is audited the way the Archives of California calendar is audited: a
random sample is drawn and frozen, then each record is checked against the
underlying documents, and the resulting error rate is published whatever it says.

## Method

Proportional stratified random sample by granting era, drawn with a fixed public
seed after a deterministic sort, so the draw is reproducible by anyone:

```
python3 scripts/build_audit_sample.py --verify
```

That prints the ids of a fresh draw and confirms they match the committed file.
The sample was written, hashed, and pushed to the public repository before a
single record was verified. Strata: alvarado 31, micheltorena 26, pico 18,
figueroa 9, interim 6, spanish 4, mission 2, echeandia 1, presidio 1, pueblo 1,
unattributed 1.

## What is checked

Eight fields per record, each graded independently against a source that is
recorded with the verdict:

| Field | Checked against |
|---|---|
| `year` | the grant date in the land case file |
| `governor` | the granting authority named in the case file |
| `grantee` | the grantee named in the case file |
| `land_case` | the docket number in the Bancroft or OAC finding aid |
| `outcome` | the final disposition, not the Land Commission's first decision |
| `patent_to` | the patentee, only where a source states it verbatim |
| `patent_date` | the date the patent issued |
| `glo_patent_no` | the General Land Office patent number |

## Grades

- **OK** the register agrees with the source.
- **ERR** the register is wrong. The correction goes into the errata and into the data.
- **PART** partially right: right entity, imprecise form (an abbreviated name, a date given only by year).
- **UV** unverifiable from the available sources. Recorded as such, never silently counted as correct.
- **NA** the field is deliberately blank, for instance a patentee that no source names.

A blank field is not an error. The register's rule is that an unsourced value is
omitted rather than inferred, so `NA` counts as compliance with that rule, and the
audit reports the blank rate separately from the error rate.

## Reporting

On completion the rate is published per field and overall, on the portal's Sources
page and in the next versioned Zenodo release, together with every correction found.
A partial audit is reported as partial, with the number checked so far.

## Status

Sample drawn and committed 2026-09-01. Verification not yet begun: 0 of 100 checked.
