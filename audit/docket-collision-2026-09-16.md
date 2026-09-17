# Hoffman's table is not unique on the district court number, and the join assumed it was

Date: 2026-09-16. Found while assembling the work-list for the 115 unread
records, by asking why exactly one of them disagreed with Hoffman.

## The bug

`scripts/resolve_unread_from_hoffman.py` joined each register row to Hoffman's
appendix on the district court number, then took `cands[0]`. Six district court
numbers in the printed table carry **two** entries each. Where that happened the
join took whichever the parser had reached first.

| docket | Hoffman commission no. | claim |
|---|---|---|
| S.D. 270 | 531 | Los Gatos or Santa Rita, Monterey county, confirmed |
| S.D. 270 | 598 | Canada de los Pinacates, Los Angeles county, rejected |
| N.D. 166 | 89 | Carmel, Morehead claimant, confirmed on appeal |
| N.D. 166 | 705 | 50 varas square in Mission Dolores, de Haro heirs |

Twelve entries across the table sit on a collided number. Two of them fall in
the 115 unread rows.

## What it cost

`u-114 Canada de los Pinacates` was matched to the Santa Rita entry and reported
as Hoffman "Confirmed" against a register "Rejected". That was the **only**
register-versus-Hoffman disagreement in the whole 115, and it was an artefact of
the join. Hoffman's actual Pinacates entry, commission 598, reads:

> 598, 270, S. D. Maria Antonia Cruz, claimant for Canada de los Pinacates, one-
> fourth square league, in Los Angeles county, granted November 20th, 1835, by
> Jos6 Castro to Jose Cruz and Jose Maria Cruz; claim filed February 17th, 1853,
> rejected by the Commission January 23d, 1855, and appeal dismissed for failure
> of prosecution February 11th, 1856.

Rejected, and the appeal dismissed, which is what the register says.

`u-49 Carmel` was matched correctly, but by luck rather than by rule.

## The fix

The join now breaks a tie on the rancho name, comparing distinctive tokens after
dropping the generic ones (rancho, canada, de, los, san, santa). If exactly one
candidate scores highest and the score is above zero it is taken; a tie or a zero
score is recorded as `ambiguous docket` with the candidate list and **no outcome
is asserted**. Guessing on a collided docket is how the artefact was produced in
the first place.

## Result after the fix

| | before | after |
|---|---|---|
| agrees with the register | 100 | **101** |
| DISAGREES | 1 | **0** |
| Hoffman confirmed | 50 | 49 |
| Hoffman rejected | 51 | 52 |
| ambiguous docket | (not detected) | 0 |

**Across all 115 records with no case-file reading, Hoffman's 1862 table now
disagrees with the register on nothing.** 101 of the 115 are comparable; the
other 14 are 11 entries whose disposition chain does not end in a plain
confirmation or rejection and 3 with no entry in the table at all.

That is a corroboration, not a verification. It remains evidence tier
`hoffman-table`, which is weaker than reading the decree, and the two sources are
not fully independent: some register rows were themselves built from Hoffman.

## Caveat on the collision count

Six collisions is what the entry-head regex finds in the djvu OCR of a printed
table. An OCR digit error would create a false collision or hide a real one, so
six is a working figure, not a census. The two that matter here were both read
back against the printed page text and are real.

## Reproduce

    python3 scripts/resolve_unread_from_hoffman.py /tmp/GR_1919_djvu.txt
