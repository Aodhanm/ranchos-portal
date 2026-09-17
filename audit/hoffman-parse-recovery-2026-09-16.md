# Getting Hoffman's table from 766 entries to 785

Date: 2026-09-16. Hoffman's appendix prints 813 claims. The parser was reading
766 of them, and nothing recorded which 47 were missing or why. Two fixes later
it reads 785, or 97 per cent, and the 28 that remain are diagnosed rather than
merely unreached.

## Why entries went missing

Every one of them fails the same way: **the OCR damages the entry HEAD, so the
parser never sees that an entry begins, and the whole entry is swallowed into the
one before it.** Four kinds of damage, all confirmed against the page text:

| damage | example | entries |
|---|---|---|
| specks read as punctuation at the start of the line | `••172, 353, S. D.` (Las Cienegas) | 4 |
| the running page header lands inside the head | `APPENDIX. 25 1 73, 1 82, N. D.` | several |
| the digits of a number split apart | `1 29` for 129, `7 44` for 744 | several |
| the district letter garbled | `X. D.`, `ST. D.`, `S$D`, `NjD`, `Sv D.`, and `71, 10 N. D.` dropping the comma | 8 |

Las Cienegas is the one that had already cost something: it was reported as
having no entry in Hoffman at all, and that report was used as a reason to defer
a correction. It has one, and it names a second grantor the register does not.

## Why the recovery is additive, not a better regex

Rewriting the entry-head regex to catch these was tried first. It found 773
distinct commission numbers, up from 767, **but lost eight it had previously
found.** A pass that trades eight known-good entries for six new ones is the
worse trade, and the loss would have been silent.

So the main pass is untouched, and a second pass hunts only for commission
numbers the first one missed, keeps a candidate only if the text that follows
reads like an entry, and splices it in by position so it still gets cut at the
next entry. Verified: **0 entries lost, 15 gained.**

## What moved

| | before | after |
|---|---|---|
| appendix entries parsed | 766 | **785** (97% of 813) |
| Hoffman confirmed / rejected / other | 566 / 169 / 31 | **579 / 172 / 28** |
| register rows matched to an entry | 616 | **631** |
| register rows with an unmatched docket | 42 | **27** |
| the 115 unread: agreement with the register | 101 of 101 | **101 of 101**, unchanged |

Sources section 6 carries the new figures.

## The 28 still missing

139, 153, 158, 173, 259, 269, 372, 379, 501, 568, 613, 640, 648, 653, 662, 676,
682, 693, 695, 743, 748, 750, 755, 756, 757, 764, 765, 770, 778, 787, 812.

Spot checks put most of them in the running-header and split-digit classes, sitting
inside the preceding entry's chunk. They are recoverable, and the next pass should
normalise the page headers out of the text before parsing rather than pattern-match
around them. That was not done here because normalising changes every chunk
boundary in the file and would need the whole table re-verified.

## One thing this does NOT change, deliberately

`audit/hoffman-crosscheck-v2-errata-applied.json` still rests on the frozen
2026-09-01 parse, and must. That parse is what ordered the census queue, so
re-deriving the strata from a better parse would silently change which records
count as flagged and break comparability with every record already graded. The
new parse would move the flag count from 251 to 243. None of that reaches the
accuracy figures until the census is finished.

## A hazard fixed at the same time

`hoffman_crosscheck.py` wrote its output straight over
`audit/hoffman-crosscheck-2026-09-01.json`, the dated file published findings cite
by name, so re-running it after a parser change silently rewrote the cited
evidence. Re-runs now write `audit/hoffman-crosscheck-latest.json`; replacing the
cited file takes `--overwrite`.

## Reproduce

    python3 scripts/hoffman_dispositions.py /tmp/GR_1919_djvu.txt
    python3 scripts/hoffman_crosscheck.py /tmp/GR_1919_djvu.txt
