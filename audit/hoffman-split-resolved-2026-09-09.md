# The 545 / 239 / ~29 split cannot be reproduced. Here is what can.

Date: 2026-09-09. This closes the question left open in
`hoffman-split-note-2026-09-03.md`, which could only say the figure was
unverifiable because the file Sources section 6 cites for it,
`data/hoffman-claims.json`, is not in the repo.

It is now verifiable, and the answer is that the published split is not
reproducible from Hoffman's printed appendix under any consistent reading.

## Method

`scripts/hoffman_dispositions.py` reads each entry of the "Table of Land Claims"
(Internet Archive item `GR_1919`) and takes its **last disposition event in text
order**, which is what the table records: the posture as of 1862. Two traps that
defeat a naive reading, both handled and both verified against hand-checked
entries:

- **"appeal dismissed" does not dismiss the claim.** It finalizes the decree
  below it. Counting it as a dismissal turns confirmed claims into "other".
- **Order is the whole answer.** "Rejected by the Commission, confirmed by the
  District Court" is a confirmed claim (ND 35, ND 37, SD 31); the reverse is a
  rejected one (ND 11, Yerba Buena Island). The screening rule in
  `hoffman_crosscheck.py` reads only presence, not order, and so gets these
  backwards. The two rules disagree on 25 entries.

Two defects in this script's own first cut were found by hand-checking a sample
and fixed before any number below was trusted:
- The djvu OCR prints "confinned" for "confirmed" often enough to matter, which
  silently demoted confirmed claims to "unclear" (ND 77 was the case that showed it).
- `parse_appendix` opens a new chunk only on a full "commission, court, district"
  marker, so an entry printed without one bleeds into its predecessor and
  last-match could read the **neighbour's** disposition (ND 44 showed it). Chunks
  are now truncated at the next claimant line.

Coverage: 766 of Hoffman's 813 entries parse, 94%. Figures are given raw and
scaled to 813; the scaling assumes the unparsed 47 behave like the rest, which is
an assumption, not a measurement.

## Result

| final disposition, 1862 | raw (of 766) | scaled to 813 |
|---|---|---|
| confirmed | 572 (74.7%) | 607 |
| rejected | 157 (20.5%) | 167 |
| other (discontinued, dismissed, reversed-and-remanded) | 35 | 39 |
| unclear | 2 | 2 |
| *of the confirmed, marked patented by 1862* | *87* | *92* |

## Why the published 239 is not any of these

The obvious explanation would be that 239 counts the Land Commission's **first**
decision rather than the final one. It does not. Both bracketing readings were
computed, and the published figure falls between them, matching neither:

| reading | scaled to 813 | vs published 239 |
|---|---|---|
| rejected by the Commission (first decision) | 282 | +43 |
| "rejected" appearing anywhere in the entry | 299 | +60 |
| **rejected as final disposition** | **167** | **-72** |

The same bracketing holds for the confirmed count: first-decision 505, final 607,
published 545 sits between them. A figure that lands between two consistent
readings on both sides is not a stricter or looser version of either. It comes
from a different dataset, a mixed rule, or an error, and with
`data/hoffman-claims.json` absent there is no way to tell which.

## What this means historically, which is the part worth getting right

Under the defensible reading, **about four in five claims were ultimately
confirmed** (74.7% confirmed against 20.5% rejected as of 1862, before the
appeals still pending were resolved). The published 545/239 implies 29.4%
rejected. The difference is not cosmetic: it is the difference between a
commission that mostly upheld Mexican title slowly and expensively, and one that
struck down nearly a third of it. The first is what the record shows and what the
land-grant historiography describes; the second overstates dispossession by
decree at the expense of dispossession by cost, delay, and forced sale.

This is also exactly the caveat the site already makes elsewhere: Sources warns
that "the Land Commission's first decision is NOT final", and the audit's own
grading rule says District Court and Supreme Court decrees supersede it. The
239 does not honour that warning.

## Recommendation for the JOHD submission

Preferred: replace the parenthetical with the reproducible figures and name the
method, for example "of the 813 claims Hoffman tabulates, about 75 percent stood
confirmed as of 1862 and about 20 percent rejected, counting each claim's final
recorded disposition rather than the Commission's first decision". Ship
`scripts/hoffman_dispositions.py` as the provenance.

Acceptable: drop the breakdown and cite only the uncontested 813.

Not acceptable: leave 545/239/~29 standing on a page whose argument is that this
project publishes measured, reproducible numbers. It is the one figure on the
Sources page that cannot be checked against anything the project ships.

Aodhan's call. No site text has been changed.

## Reproduce

    curl -sL -o /tmp/GR_1919_djvu.txt https://archive.org/download/GR_1919/GR_1919_djvu.txt
    python3 scripts/hoffman_dispositions.py /tmp/GR_1919_djvu.txt
