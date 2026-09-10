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

## CORROBORATED 2026-09-09: the final-disposition reading matches the literature

Independent source work found the figures our two readings should match, and they do:

| basis | published source | our parse |
|---|---|---|
| Commission first decision | Hittell, *History of California* III:695 (1898): 514 / 280 / 19 | 505 / 282 |
| **final disposition** | **Morrow (1923) p.14: 604 confirmed, 190 rejected, 19 withdrawn** | **607 / 167 / 39** |

Morrow states the distinction explicitly: "the final result, before the
commission and on appeal to the District Court and Supreme Court, was the
confirmation of 604 cases, the rejection of 190, and 19 were withdrawn."
Our final-disposition confirmed count is within 3 of his. Robinson (1948,
pp. 105-106) reproduces Morrow and labels it "finally confirmed / finally
rejected".

The published 545 / 239 matches neither basis and no located source gives it.

⚠ **Do not cite Gates for 604.** The strings 604, 607, 545 and 239 appear nowhere
in his 1971 article; he cites Hittell's 514/280/19 in a footnote. Attributing 604
to Gates is a mis-citation common online. His 1958 *Huntington Library Quarterly*
essay remains unchecked and is the one place he might give a full breakdown.

⚠ **Bibliographic correction.** The publisher is **Numa Hubert**, not Sumner
Whitney. The title page reads "NUMA HUBERT, PUBLISHER" and the preface is signed
"N. HUBERT". Sumner Whitney is a cataloguing error that has propagated into
HathiTrust and into the Newberry's own IA metadata for the very copy whose title
page says otherwise. Full citation: Ogden Hoffman, *Reports of Land Cases
Determined in the United States District Court for the Northern District of
California, June Term, 1853 to June Term, 1858, Inclusive*, Volume I (San
Francisco: Numa Hubert, 1862). Only volume I was ever issued.

## VERIFIED IN AODHAN'S OWN HOLDINGS, 2026-09-09

Hittell was checked directly against the vault copy
(`07 Files/Raw/papers/hittell-history-of-california-v3_djvu.txt`) rather than
taken on report. The passage sits between the running heads "LAND COMMISSION.
693" and "696 STATE GROWTH", confirming the citation as **III:695**. Verbatim:

> "The number of land claims presented to it, as has been already stated, was
> eight hundred and thirteen, asking for nineteen thousand one hundred and
> forty-eight square miles or upwards of twelve and a quarter million acres; and
> of the claims presented five hundred and fourteen were confirmed, two hundred
> and eighty rejected, and nineteen discontinued."

514 + 280 + 19 = 813 exactly. (The figures are spelled out in words, which is why
a numeric search of the file finds nothing; worth knowing before anyone concludes
the passage is absent.)

**Hittell then gives the appellate correction himself, on the same page**, and
this is the part that settles the whole question:

> "Almost all were appealed to the United States district courts, in which about
> twenty of those which had been confirmed were rejected, and about a hundred of
> those which had been rejected were confirmed. In four hundred and thirty-four
> of the cases of confirmation, the appeals taken by the United States were
> afterwards, about 1857, withdrawn or dismissed by consent and the judgments of
> the land commission accepted as final decrees, upon which patents were
> eventually issued."

Apply his own arithmetic to his own first-decision figures:

| | confirmed | rejected | other |
|---|---|---|---|
| Hittell, Commission first decision (III:695) | 514 | 280 | 19 |
| Hittell's own appellate correction (−20/+100) | **~594** | **~200** | 19 |
| Morrow 1923 p.14, final result | 604 | 190 | 19 |
| our parse, final disposition | 607 | 167 | 39 |
| **the site's published figure** | **545** | **239** | **~29** |

Three independent estimates of the final result cluster at 594, 604 and 607
confirmed. The published 545 sits below all three, and its 239 rejected sits
above all three. It is not a variant reading of either basis.

Hittell also supplies the MECHANISM, which is exactly what our last-disposition
parser measures: appeals moved roughly a hundred claims from rejected to
confirmed and about twenty the other way. A rule that reads only whether the word
"rejected" appears cannot see that movement, which is why the screening parser
in `hoffman_crosscheck.py` produced 162 and why it should not be trusted for
counts.

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
