# The census pass is an adverse sample. Do not pool it with the blind 100.

Date: 2026-09-03. Written the moment the Phase B census crossed 92 graded records,
because the aggregate that falls out of those 92 is alarming and wrong, and the
next person to run the resume command will compute it too.

## The trap

Pooling every graded census record and reporting the result gives:

| field | census so far (n=92) | published blind 100 |
|---|---|---|
| name | 1.1% | 0.0% |
| year | 20.9% | 9.6% |
| governor | 14.1% | 4.2% |
| grantee | **42.4%** | 16.7% |
| land_case | 0.0% | 0.0% |
| outcome | 0.0% | 1.1% |
| **overall field error** | **13.1%** | **5.3%** |

Read naively that says the register is two and a half times worse than published
and that grantee is wrong in more than four records in ten. It says no such thing.

## Why

The Phase B queue was deliberately built **Hoffman-flagged first**. Verified:

- Chunks 01 through 11 contain 132 records and **every one of them carries a
  Hoffman disagreement flag**. Chunks 43 through 48 carry none at all.
- Of the 92 records graded so far, **92 are substantively Hoffman-flagged**
  (a disagreement on year, governor, grantee, or outcome). Not 91. All of them.
- Register-wide, only **160 of 672 rows (23.8%)** are substantively flagged.

So the census has so far read nothing but the stratum the 1862 printed table
already said was suspect. Its error rate is the error rate of that stratum, and
it will keep looking catastrophic until the queue reaches chunk 43 and abruptly
looks pristine. Neither number describes the register.

## The control

The blind 100 was drawn at random, so it can be split the same way after the
fact. Its flagged subset is a like-for-like comparison, graded by different
agents at a different time with no knowledge of this question:

| field | blind 100, flagged (n=27) | census, flagged (n=92) | blind 100, unflagged (n=73) |
|---|---|---|---|
| year | 29.6% | 20.9% | 1.5% |
| governor | 14.8% | 14.1% | 0.0% |
| grantee | 40.7% | 42.4% | 7.2% |
| **overall** | **14.2%** | **13.1%** | **1.7%** |

Two independent passes over the flagged stratum agree: 14.2% against 13.1%
overall, 40.7% against 42.4% on grantee. The census graders are not stricter
than the blind-sample graders. The population they were handed is worse.

## What this is actually evidence of

**A Hoffman disagreement predicts a register error, hard.** Within the blind 100,
which is the only unbiased sample available, a substantively flagged row has an
overall field error of 14.2% against 1.7% for an unflagged row, and a grantee
error of 40.7% against 7.2%. That is roughly an eightfold difference on the
overall rate and close to sixfold on grantee. The 1862 table is a cheap, powerful
screen, and building the census queue around it was the right call. It just makes
the running total unreadable as a headline.

## Re-estimating the register, correctly

Weighting the two strata by their true share of the 672 rows (23.8% flagged,
76.2% unflagged):

| field | published (blind 100) | stratified, blind strata | stratified, census flagged + blind unflagged |
|---|---|---|---|
| name | 0.0% | 0.0% | 0.3% |
| year | 9.6% | 8.2% | 6.1% |
| governor | 4.2% | 3.5% | 3.4% |
| grantee | 16.7% | 15.2% | 15.6% |
| land_case | 0.0% | 0.0% | 0.0% |
| outcome | 1.1% | 1.2% | 1.2% |
| **overall** | **5.3%** | **4.7%** | **4.4%** |

Every stratified estimate lands at or below the published figure. The reason is
mundane: the blind draw happened to pull 27 flagged rows where the population
rate implies about 24, so the published rate is very slightly pessimistic.

**Consequence for the JOHD submission: the published 5.3% and grantee 16.7% stand,
and are if anything conservative.** They are the defensible numbers because they
come from a pre-registered, hash-committed random sample. Do not restate them from
census data.

## Rules for whoever resumes the census

1. **Never report a pooled census rate as the register's accuracy.** Report it as
   the flagged-stratum rate, with n, and say the queue is ordered worst-first.
2. The census is worth finishing for **corrections**, not for a headline. Every
   ERR it turns up is a real correction for the errata register and for v1.1.
3. The rate only becomes comparable again once the unflagged chunks (roughly 43
   onward) are done. At that point compute the two strata separately and weight
   them, rather than averaging the pile.
4. The blind 100 remains the published measurement. It is not superseded by a
   larger non-random sample, no matter how much larger it gets.

## Reproduce

    python3 - <<'PY'
    import json, glob, collections
    FIELDS=['name','year','governor','grantee','land_case','outcome']
    SUB={'year','governor','grantee','outcome'}
    hc={r['id']: r for r in json.load(open('audit/hoffman-crosscheck-2026-09-01.json'))['records']}
    subflag=lambda i: any(f.split(':')[0] in SUB for f in ((hc.get(i) or {}).get('flags') or []))
    bv=json.load(open('audit/verdicts-2026-09-01.json'))
    blind=bv if isinstance(bv,list) else (bv.get('records') or bv.get('verdicts') or list(bv.values()))
    census=[r for f in sorted(glob.glob('audit/census-partial-2026-09-02/chunk*.json'))
            for r in json.load(open(f))]
    print(sum(subflag(r['id']) for r in census), 'of', len(census), 'census records are flagged')
    print(sum(subflag(i) for i in hc), 'of', len(hc), 'register rows are flagged')
    PY
