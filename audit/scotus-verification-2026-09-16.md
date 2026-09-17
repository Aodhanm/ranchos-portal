# The 29 Supreme Court citations, checked against the reports for the first time

Date: 2026-09-16. The citations staged for v1.1 were taken as printed in
Hoffman's 1862 table and had passed only a structural check: all fell in Howard
17 to 24, the right range for an 1862 imprint. Nobody had opened the reports,
because CourtListener answers scripted clients with a bot challenge.

**The Caselaw Access Project's static bulk host does not.** `static.case.law`
serves per-volume `CasesMetadata.json` over plain anonymous HTTP, with no
account, no challenge and no rate limiting. Each record carries both the
nominative citation ("23 How. 273") and the official one ("64 U.S. 273"), which
is exactly the pair a register needs. Howard volumes 1 to 24 are U.S. Reports 42
to 65, so *n* Howard = (41 + *n*) U.S.

## Result

| | count |
|---|---|
| **confirmed**: the page carries a case naming Hoffman's own claimant | **25** |
| correct page and volume, but captioned under other parties | 2 |
| **wrong page number in Hoffman's printed table** | **2** |

**27 of the 29 stand. Two do not, and both are fixed by the claimant that
Hoffman's own entry names.**

| record | Hoffman prints | the reports have | corrected to |
|---|---|---|---|
| u-28 Bolsa de Tomales | 22 Howard 87, which is *Hodge v. Williams* | *United States v. James D. Galbraith* at 22 How. 89, and Hoffman's entry names "James D. Galbraith, claimant for Bolsa de Tomales" | **22 How. 89** |
| u-108 Nemshas | 24 Howard 151, where no case begins | *United States v. Chana* at 24 How. 131, and Hoffman's entry names "Charles Chana, claimant for Nemshas" | **24 How. 131** |

Both are applied in the v1.1 candidate, which now records 27 citations as printed
and 2 corrected against the reports.

## The two captioned under other parties are not errors

- **Rancho Los Putos**, 18 How. 556, is *The United States, Appellants, v. Juan
  Manuel Vaca and Juan Felipe Pena*. Hoffman's claimant is Chiles, a later
  purchaser; the Court styled the appeal under the original grantees. Right
  citation, different caption.
- **Valle de San Jose**, 20 How. 261, names "Antonio Sunot" where Hoffman has
  Sunol. Same man, and the citation is correct.

## Three traps, all of which produced a wrong answer before being fixed

1. **Two cases can share a first page.** 18 How. 539 is both *Hudgins v. Kemp*, a
   one-page order, and *de Arguello v. United States*, running 539 to 553.
   Taking the first match reported Rancho Pulgas as a bad citation when Hoffman
   was right. This is the same `cands[0]` bug found in the Hoffman docket join on
   the same day, in a different script, written by the same hand.
2. **A volume can report several appeals under one head.** 20 How. 261 is four:
   De Pacheco, Hensley, Bidwell and "Antonio Sunot et al.". Three register rows
   citing it is correct, not a copied citation, and the party has to be sought in
   the full case name rather than the abbreviation. The script now flags a shared
   citation rather than treating it as a fault.
3. **A fuzzy name match must not be fuzzy on short names.** Allowing two edits let
   "Chana" match "Canal", which made the Nemshas correction ambiguous and dropped
   it silently. The edit-distance path now requires seven characters; shorter
   names match on a folded prefix only.

## What this does not establish

That the case is about the right rancho. The register names a rancho and the
reports name the parties, so the check is claimant-to-party. Where it succeeds it
is strong: *United States v. Osio* for Angel Island, *Fremont v. United States*
for Las Mariposas, *United States v. Vallejo* for Yulupa, *United States v.
Teschmaker* for Lup Yomi, *United States v. Gomez* for Panoche Grande. But it is
a name match, not a reading of the opinion.

## Reproduce

    python3 scripts/verify_scotus_cites.py
