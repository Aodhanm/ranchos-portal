# The crossover: what the unflagged stratum actually looks like

Date: 2026-09-09, at 313 of 572 census records graded. This is the update to
`census-stratification-2026-09-03.md` that its own "rules for whoever resumes"
asked for, and it is written now because the census has just passed the point
where it stops being an adverse sample.

## The census is no longer worst-first

**All 133 substantively Hoffman-flagged records in the Phase B universe are now
graded**, plus 180 unflagged ones. Every record from here to the end of the
census is unflagged. The pooled census rate, which was meaningless while the
queue was working through the flagged head, is becoming meaningful, and it will
keep falling as the unflagged tail lands.

## The four cells

| stratum | overall field error | grantee | n records |
|---|---|---|---|
| census flagged | 13.4% | 45.9% | 133 |
| blind-100 flagged (control) | 14.2% | 40.7% | 27 |
| **census unflagged** | **3.4%** | **11.5%** | **180** |
| blind-100 unflagged (control) | 1.7% | 7.2% | 73 |

The flagged cells agree closely, as they did at n=92. That was the check that
the census graders were not stricter than the blind-sample graders, and it still
holds.

**The unflagged cells do not agree as well.** The census finds roughly double the
error the blind-100's unflagged subsample did, on both the pooled rate and on
grantee.

## Is that difference real? Not at conventional significance, not yet.

Two-proportion z tests, census unflagged against blind-100 unflagged:

| comparison | census | blind | z | p |
|---|---|---|---|---|
| all fields pooled | 35/1025 = 3.4% | 7/406 = 1.7% | +1.71 | 0.088 |
| grantee | 20/174 = 11.5% | 5/69 = 7.2% | +0.98 | 0.326 |
| year | 6/173 = 3.5% | 1/67 = 1.5% | +0.82 | 0.415 |

None reaches p < 0.05. The blind-100's unflagged subsample is only 73 records,
so it was never going to pin this down. The Wilson intervals overlap heavily:
census unflagged grantee 11.5% [7.6, 17.1], blind unflagged grantee 7.2%
[3.1, 15.9].

**So this is a drift to watch, not a finding to publish.** It is recorded now
because the direction has been consistent since the crossover began and the
census sample is already 2.5 times the size of the control.

## What it would mean if it holds

Re-weighting with the census's own two strata (23.8% flagged):

| | overall | grantee |
|---|---|---|
| stratified from census alone | 5.78% | 19.68% |
| published, blind 100 | 5.28% | 16.67% |

The published grantee figure carries a 95% Wilson interval of [10.5, 25.4] at
n=96, so 19.7% sits comfortably inside it and **nothing published is
contradicted**. But the point estimate has moved up, not down. At n=92 the
stratified estimate was 15.6% and read as mildly conservative; at n=313 it reads
as mildly optimistic. That reversal is the thing to keep an eye on.

## The caveat that stops this being a better estimate than the blind 100

**The census unflagged records are not a random sample of unflagged records.**
The rebuilt work-list sorts flagged-first and then by id, so the 180 unflagged
records graded so far are the alphabetically-first 180 of roughly 439. Alphabetical
order is not obviously correlated with accuracy, but it is not random either, and
if the register was compiled in batches whose quality differed, id order could
track that. Until the census finishes, the blind 100 remains the only unbiased
estimator of the register and stays the published number.

## What to do at the end of the census

1. Recompute the four cells on the complete data. With every unflagged record
   graded, the unflagged cell stops being a sample and becomes a census: the
   stratified figure then beats the blind 100 on precision and should replace it.
2. Re-run the z tests. If the unflagged divergence survives at full n, the
   published grantee rate understates and v1.1 should say so plainly.
3. If it does not survive, say that too. A drift that washed out is worth one
   sentence in the data paper, because it is evidence the blind sample was sound.

## Reproduce

    python3 - <<'PY'
    import json, glob, collections
    FIELDS=['name','year','governor','grantee','land_case','outcome']
    SUB={'year','governor','grantee','outcome'}
    hc={r['id']:r for r in json.load(open('audit/hoffman-crosscheck-2026-09-01.json'))['records']}
    sub=lambda i: any(f.split(':')[0] in SUB for f in ((hc.get(i) or {}).get('flags') or []))
    census=[r for f in sorted(glob.glob('audit/census-*/chunk*.json')) for r in json.load(open(f))]
    print(sum(sub(r['id']) for r in census), 'flagged of', len(census), 'graded')
    PY

---

# Addendum, 2026-09-16: Hoffman's errata applied, conclusions unchanged

`scripts/apply_hoffman_errata.py` applies Hoffman's own printed errata to the
cross-check and re-derives the flags, writing
`audit/hoffman-crosscheck-v2-errata-applied.json`. The 2026-09-01 file is left
unchanged because published findings cite it by name.

**Effect on the flagging.** 6 field corrections matched register rows (5 year,
1 governor). Three flags are withdrawn because Hoffman's own erratum agrees with
the register: canada-carpenteria (1845 to 1835), calleguas (1847 to 1837),
guadalasca (1846 to 1836). Two are restated against the corrected value rather
than withdrawn (san-antonio-rodeo-aguas, monte-diablo). Substantively flagged
rows fall from 160 to 157, and the stratum weight from 23.8% to 23.4%.

**Effect on the estimates: negligible.**

| stratum | overall before | after | grantee before | after | n |
|---|---|---|---|---|---|
| census flagged | 13.4% | 13.7% | 45.9% | 46.9% | 133 → 130 |
| blind-100 flagged | 14.2% | 14.2% | 40.7% | 40.7% | 27 |
| census unflagged | 3.2% | 3.1% | 11.3% | 11.2% | 324 → 327 |
| blind-100 unflagged | 1.7% | 1.7% | 7.2% | 7.2% | 73 |

| stratified estimate | before | after | published |
|---|---|---|---|
| overall | 4.49% | 4.51% | 5.28% |
| grantee | 16.44% | 16.52% | 16.67% |

**Nothing in the 09-03 or 09-09 findings needs revising.** The flagged and
unflagged strata still differ by roughly fourfold on the overall rate and
sixfold on grantee; the census flagged cell still agrees with the random
control; and the stratified grantee estimate, 16.52%, remains inside the
published figure's interval and is now within 0.15 points of it.

The three withdrawn flags moved from the flagged stratum to the unflagged one,
which is why the flagged cell ticks up slightly: they were the three cases where
Hoffman was wrong and the register was right, so removing them takes three clean
records out of the flagged group.

**Why this was worth doing anyway.** The point was never the decimal. It was that
the cross-check was raising three accusations against the register that the
source itself had already retracted, and a reader checking those three would have
found the register correct and the audit wrong.
