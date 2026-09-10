# Hoffman printed 74 errata to his own table. Nothing downstream applies them.

Date: 2026-09-09.

## What was found

The 1862 appendix ends with two pages of errata keyed to claim numbers (appendix
pp. [145]-146, leaves n606-n607 of IA item `GR_1919`). They are not cosmetic:
28 touch the granting governor or the official who made the grant, 23 correct
grant years, 3 change acreages, and 2 collapse one claim into another.

No dataset downstream of the OCR applies them, including our own
`audit/hoffman-crosscheck-2026-09-01.json`, which is the file that ordered the
entire census queue and defined the "flagged" stratum in
`census-stratification-2026-09-03.md`.

## Why that matters, concretely

If the printed table is wrong and the register is right, the cross-check raises a
flag against the register that **Hoffman himself already withdrew**. Three such
flags exist:

| record | Hoffman no. | printed | erratum | register |
|---|---|---|---|---|
| rancho-canada-carpenteria | 650 | 1845 | **1835** | 1835 |
| rancho-calleguas | 430 | 1847 | **1837** | 1837 |
| rancho-guadalasca | 31 | 1846 | **1836** | 1836 |

In every case the register was right, the printed table was wrong, and Hoffman
corrected it two pages later.

## The triangulation, which is the real result

These three are confirmed by three independent routes that never saw each other:

1. **Census agents reading the case files.** On Cañada de la Carpentería an agent
   reported "decree, translation, judicial possession and the District Court
   opinion all read 1835; Hoffman's 1845 is wrong." On Calleguas: "grant decree
   and its sworn translation both read 10 May 1837; Hoffman's 1847 is a typo."
   Both were graded OK against the register before anyone had read the errata.
2. **Hoffman's own errata**, recovered here.
3. **Chronology.** Guadalasca's printed entry has Mariano Chico granting in 1846.
   Chico was governor in 1836, not 1846, so 1836 is right on grounds independent
   of both other routes.

Three methods, three agreements. That is also a strong check on the census
graders: they got these right from the manuscripts with no knowledge of the
errata.

## Effect on the audit

Small but real, and it moves in the direction of the register being cleaner:

- substantively flagged rows: **160 to 157**
- stratification weight of the flagged stratum: **23.8% to 23.4%**

Two further errata change a flag's content without withdrawing it
(rancho-san-antonio-rodeo-aguas, printed 1831 corrected to 1834 against the
register's 1838; rancho-monte-diablo, printed 1844 corrected to 1834 against
1836). Those disagreements stand but are about different years than we recorded.

## What should happen

`hoffman_crosscheck.py` should apply `audit/hoffman-errata.json` before
generating flags, and the stratification note should be recomputed on the
corrected weight. Neither is done here: the cross-check is the input to a census
that is 80% complete, and silently re-generating it mid-pass would make the
graded and ungraded halves incomparable. This is a v1.1-era change, to be made
once the census closes.

## Caveat

The errata were recovered from the same OCR as the table, so they carry the same
risk. 74 entries were parsed; the source pages report 76 corrections plus two to
the Index to Claimants. The shortfall is unexamined. The parse should be checked
against the page images before the errata are applied to anything published.

## Reproduce

    python3 scripts/hoffman_errata.py /tmp/hoffman/GR_1919_djvu.txt
