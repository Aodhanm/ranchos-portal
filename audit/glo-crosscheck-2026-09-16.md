# The GLO's own 1881 table corroborates 54 register patent acreages

Date: 2026-09-16. An independent check on the register's patent layer, using a
federal source, with Berkeley unreachable throughout.

## Source

"H H.—List of private land claims in California under Spanish and Mexican
authorities", Report of the Surveyor General of California, in the Annual Report
of the Commissioner of the General Land Office for FY1881 (H.R. Exec. Doc. No. 1,
47th Cong., 1st Sess., Serial 2017), pp. 533-549. This is the government stating
what it had patented, per claim, with confirmee, condition, county and acreage.

## Why the match is on date, not name

The djvu OCR destroys the name column of a wide ruled table: "Mission Santa
Barbara" is printed as "Massionisantal barbara", and cells bleed into their
neighbours. Name matching would be guesswork. The patent **date** and the
comma-grouped **acreage** survive intact in all 445 patented rows parsed, and a
date is selective enough to join on. So the date is the key and the acreage is
what gets tested.

## Result

| | count |
|---|---|
| **date and acreage both agree** | **54** |
| acreage differs, single-digit OCR misread | 6 |
| acreage differs, unexplained | 5 |
| ambiguous, several register rows share that patent date | 69 |
| date matches but is shared by several GLO claims | 159 |
| date not in the GLO table | 111 |
| register has no parseable patent date | 150 |

**54 register rows are independently corroborated** on patent date and acreage to
the cent, by the government's own record. That is the finding.

## Two guards that turn noise into a result

Both were added after inspecting what the first run called "disagreements", and
both matter more than the headline:

1. **Single-digit OCR test.** A difference is an OCR misread when the two figures
   differ in exactly one digit position. Six do: 13,322.29 against 18,322.29,
   27,654.36 against 27,054.36, 24,903.42 against 94,903.42. A cruder "is the
   difference round" rule catches the 5,000 and the 70,000 but misses the 600 and
   the 200, which are the same kind of error.
2. **Ambiguity guard.** A GLO row claimed by more than one register row is
   evidence about neither. Two register rows sharing a patent date both bind to
   the single GLO row carrying it: canon-santa-ana and san-jose-buenos-ayres both
   matched the one row for 25 July 1866 and produced a spurious 8,891-acre
   "disagreement". 69 comparisons are withdrawn on this ground.

Without those guards the run reported 17 disagreements. Eleven were artefacts.

## The five that remain unexplained

| record | register | GLO | difference |
|---|---|---|---|
| rancho-canada-guadalupe | 942.93 | 560.00 | 382.93 |
| rancho-merced | 2,363.75 | 2,863.25 | 499.50 |
| rancho-cuca | 2,174.52 | 2,174.25 | 0.27 |
| rancho-san-bernabe | 13,296.38 | 13,294.98 | 1.40 |
| rancho-san-bernardo-2 | 13,345.65 | 13,345.02 | 0.63 |

Three are under two acres and are as likely to be OCR in the decimals as real.
Two are larger; rancho-merced differs in two digit positions, which the one-digit
test will not catch but which is still a plausible misread.

**None of these is asserted as a register error.** They are flagged for a reading
of the page images, which is where any published value from this table must come
from anyway.

## Standing caveat

This is a screening pass over OCR, exactly like `hoffman_crosscheck.py`, not a
verdict. Its value is the 54 corroborations and the method; it is not evidence
against the register.

## Reproduce

    curl -sL -o /tmp/glo1881.txt https://archive.org/download/annualreportofco00unse_45/annualreportofco00unse_45_djvu.txt
    python3 scripts/glo_1881_crosscheck.py /tmp/glo1881.txt
