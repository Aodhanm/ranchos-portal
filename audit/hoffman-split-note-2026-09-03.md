# Note: the "545 confirmed / 239 rejected / ~29 other" Hoffman split is NOT verified

Date: 2026-09-03. Raised while closing site-prose finding 8 (the
`ranchos-experimental.json` abstract said "246 rejected" where Sources §2 and §6
say "239").

## What was done
The abstract was aligned to **239** so the two published surfaces stop
contradicting each other, and its stale "510 grants" was corrected to **535**
(verified: `data/ranchos-experimental.json` carries 535 features, and the
register CSV has `mapped=yes` on exactly 535 of 672 rows).

## What is still unverified, and matters for the JOHD submission
1. **The cited source file is not in the repo.** Sources §6 attributes
   "813 (545 confirmed/patented, 239 rejected, ~29 other)" to
   `data/hoffman-claims.json`, marked "Hoffman 1862 (verified in file)".
   `data/` holds only `errata.json`, `ranchos-experimental.json`, and the two
   register exports. The 813-row file the page cites is absent, so the split
   cannot be reproduced from anything published.
2. **An independent re-parse does not reproduce it.** Hoffman's printed appendix
   (IA item `GR_1919`, `GR_1919_djvu.txt`) was re-parsed on 2026-09-03 with the
   repo's own `scripts/hoffman_crosscheck.py::parse_appendix`. It yields **766**
   entries (not 813), tallying 601 confirmed / 162 rejected / 2 dismissed /
   1 unclear, with 88 marked patented.
3. **That tally is itself unreliable and does not refute 239.** The parser's
   disposition rule is `rejected` only when "rejected" appears and "confirmed"
   does not, so every claim rejected on appeal after a Commission confirmation
   (and vice versa) is counted "confirmed". The rule is a screening heuristic,
   as the script's own docstring says. It biases hard toward "confirmed" and
   explains most of the gap from 239.

## Consequence
239 is the *internally consistent* figure (545 + 239 + 29 = 813) and is now the
only one published, but it rests on a file the repo does not ship and a tally
nothing here can reproduce. Before the JOHD submission, either restore
`data/hoffman-claims.json` and recompute the split with a disposition rule that
reads the *final* decree rather than any occurrence of the word, or drop the
parenthetical breakdown and cite only the uncontested 813.

Not a claim to fix silently. Aodhan's call.
