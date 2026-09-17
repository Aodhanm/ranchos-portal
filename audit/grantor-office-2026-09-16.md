# Not every grant was made by a governor: a grantor_office column

Date: 2026-09-16. Answers the question the v1.1 build kept deferring: 17 staged
corrections said the register had named the wrong man in the `governor` column,
and the right man was not a governor at all. There was nowhere to put that, so
writing his name into a column called `governor` would have replaced one false
claim with another. Fourteen of the seventeen are now applied.

## The column

Two new columns in the v1.1 candidate, appended so nothing shifts for a v1.0
consumer:

- **`grantor_office`**, the office under which the named person made the grant.
- **`grantor_office_verbatim`**, the office as the case file itself states it,
  in the original language where the source is Spanish.

**An empty `grantor_office` is not a claim.** It is the register's standing
assumption that the grant was gubernatorial, which holds for the great majority
and has not been verified row by row. A value of `governor` means the office was
checked and the grantor was in fact the governor. That distinction is the point
of the column: it separates "checked" from "assumed".

## The vocabulary

| term | what it covers |
|---|---|
| governor | The chief executive holding the office in his own right, verified for this grant. |
| acting governor | The executive held ad interim. |
| prefect | Head of a district under the decree of 27 February 1839, granting on delegated authority. |
| acting prefect | Prefecto interino, in the titular prefect's absence. |
| alcalde | The elected municipal magistrate of a pueblo, granting pueblo land. |
| military commandant | A presidial or district commandant granting under the governor's authority. |

Two of the six, `acting prefect` and `military commandant`, are defined but
currently unused, because the two records that would carry them are among the
three still deferred.

## The one ruling that mattered: Jimeno is one office, not two

Ten of the seventeen name Manuel Jimeno Casarin, whom the case files style two
ways, `1er vocal propietario de la Excma Junta Departamental en ejercicio del
Gobierno` and `gobernador interino`. Whether those are one office or two decides
whether the register needs one controlled term or two.

They are one, and the decisive evidence is inside the case files. In
`rancho-san-jacinto-viejo` the two stylings are conjoined in a single phrase: the
Spanish act of judicial possession says `Exmo Sr Gobernador Interino del
Departamento Dn Manuel Jimeno`, and the Board's opinion on the same grant says
`Manuel Jimeno Vocal of the Departmental Assembly and acting Governor of
California`. In `rancho-tulucay` and `rancho-zanjones` the titulo uses the vocal
recital and the court, describing that same instrument, says `Governor ad
interim`. In `rancho-estero-americano` the petition styles him flatly `Governor
of California` with no recital at all. One document cannot use two names for one
act if they are two offices.

Bancroft says it outright, Hist. Cal. iv, note to 1841: **"It was as 1st vocal of
the dip. that Jimeno became acting gov."**

So: one term, `acting governor`. The same term also covers a jefatura politica
held ad interim by a different route, as Nicolas Gutierrez held it in 1836 as
ranking military officer. The route differs; the office does not.

## Method: three sources, and an instruction to refute

Each of the seventeen went to an independent verifier holding the case-file
quotations and the full local text of Bancroft's *History of California*, under
instruction to try to **refute** the correction rather than confirm it. None was
refuted. Every one was then checked a third time against Hoffman's printed
appendix, which the verifiers did not have.

Hoffman independently prints the corrected grantor for `rancho-brea`
("Jose Antonio Carrillo"), `rancho-canada-pala` ("Jose Castro") and every one of
the Jimeno records. That is a third source agreeing with the manuscript against
the register.

## What changed, and the dependent fields

Fourteen applied: 10 `acting governor`, 1 `alcalde`, 1 `prefect`, 1 `governor`,
1 compound `governor; acting governor`.

Four field changes ride along, because correcting the grantor alone would have
left the row contradicting itself:

| record | dependent change | why |
|---|---|---|
| rancho-petaluma | year 1834 to 1843, era figueroa to micheltorena | Micheltorena was not governor in 1834. Hoffman and the case file both date the operative grant to October 1843. |
| rancho-pulgas | year 1820 to 1835, era spanish to interim | The register carried 1820 and "spanish" on the strength of the phrase "a Spanish governor", which this correction retires. Hoffman dates the grant 1835; Castro's acting governorship ran September 1835 to January 1836. |

**The era rule**, stated so it is not reinvented: `era` labels the administration
in which the grant was made, not the individual who signed. The ten Jimeno rows
keep era `alvarado`, because Jimeno held the executive ad interim inside
Alvarado's governorship, and `rancho-brea` keeps `echeandia` although an alcalde
made the grant. era moves only when a corrected year moves the grant into a
different administration.

A correction that needed a dependent change and could not carry one stayed
deferred. That is what stopped `rancho-cienegas`.

## The three still deferred, and why

- **rancho-monte-cabestros.** The titulo in the expediente is signed by Jose
  Maria Villavicencio as Prefecto interino on 30 July 1840; Hoffman's entry for
  the same docket names Juan B. Alvarado. Grantee, date and acreage all match to
  the acre, so this is a real disagreement between two primary sources, not a
  misassigned docket. The question behind it, whether a prefect's titulo is the
  operative grant or a provisional act perfected by the governor, is a legal one.
- **rancho-cienegas.** See below; the recovered Hoffman entry names Micheltorena
  as well as de la Guerra, so the register's value is half of a pairing rather
  than plainly wrong.
- **rancho-potrero-rincon-san-pedro-reglado.** Three officers across three
  sources, two tracts and two years.

## A parser bug found on the way, which matters beyond this

Hoffman's appendix was being parsed at 766 entries. The entry-head regex anchored
on the start of a line, and the djvu OCR sometimes prefixes an entry with specks
it reads as punctuation. **Four entries were being lost silently**: `,118, 81,
S. D.` (Canada Larga o Verde), `-247, 334, N. D.` (part of Soulajule), `••172,
353, S. D.` (Las Cienegas) and `"%93, 344, N. D.` (Jose Castro et al.).

Las Cienegas had been reported as having no Hoffman entry at all, and that report
was used as a reason to defer. It has one, and it reads:

> 172, 353, S. D. Januario Abila, claimant for Las Cienegas, 1 square league, in
> Los Angeles county, granted in 1823, by Jose de la Guerra y Noriega and Manuel
> Micheltorena to Francisco Abila; claim filed October 4th, 1852, confirmed by
> the Commission June 26th, 1855, and appeal dismissed June 8th, 1857;
> containing 4,439.05 acres.

The fix takes the parse to **770 entries, 95% of Hoffman's 813**, and moves the
disposition count from 566 confirmed / 169 rejected / 31 other to **568 / 171 /
28**. Section 6 of the live Sources page quotes the old figures and needs the new
ones.

A second hazard, fixed at the same time: `hoffman_crosscheck.py` wrote its output
straight over `audit/hoffman-crosscheck-2026-09-01.json`, the dated file that
published findings cite by name, so a re-run after the parser change silently
rewrote it. Re-runs now write `audit/hoffman-crosscheck-latest.json`; replacing
the cited file takes `--overwrite`.

## Nothing is published

`data/ranchos-register.csv` and `.json` remain byte-identical to the Zenodo v1.0
deposit, md5 `758bb1f6cd168e941925dbdbf6704bb7`. All of this lands in
`audit/v1.1-candidate/`, which now carries 171 applied corrections, 29 Supreme
Court citations, `docket_relation`, and the two new columns.

## Reproduce

    python3 scripts/build_v11_candidate.py
    python3 scripts/hoffman_dispositions.py /tmp/GR_1919_djvu.txt
