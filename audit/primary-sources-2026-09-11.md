# Two official primary sources for California land claim outcomes, both verified

Date: 2026-09-11. Found in answer to Aodhan's question of whether the aggregate
outcome figures could rest on primary rather than secondary sources. They can.
Both are federal, free, outside Berkeley, and unaffected by the digicoll bot
challenge. Both were checked directly, not taken on report.

## 1. The government's own cumulative tally (1881)

**Thomas Donaldson, *The Public Domain: Its History, with Statistics*
(Washington: GPO, 1884), p. 1114.** H. Misc. Doc. No. 45, pt. 4, 47th Cong.,
2d Sess., Serial 2158. The figures come from a statement by Luther Harrison,
principal clerk of the GLO's Private Land Claims Division, dated 30 November 1881.

Transcribed verbatim from the text:

> CLAIMS IN CALIFORNIA PRESENTED TO BOARD OF LAND COMMISSIONERS (ACT MARCH 3,
> 1851, AND SUPPLEMENTAL LEGISLATION).
> Number of claims 813
> Mission claims under No. 609 (24) 23
> Total 836
> Claims rejected by Board and courts, or both 212
> Claims finally confirmed (estimated) 624
> Claims surveyed and reported 596
> Confirmed claims not yet reported 28
> Confirmed claims docketed but not disposed of 25
> Total in California to be disposed of 53
> In the settlement of these claims we dispose, on an average, of seventeen a year.

Arithmetic is internally consistent: 813+23=836, 212+624=836, 596+28=624,
28+25=53.

Two things make this the best aggregate source available:
- It is the **General Land Office counting its own work**, nineteen years after
  Hoffman, by which time most appeals had closed.
- Note the word **"(estimated)"**. The government itself would not give an exact
  final confirmed count. That is worth quoting: it is the strongest possible
  evidence that a single clean number does not exist, which is precisely why the
  published secondary figures disagree with one another.

⚠ The base is **836, not 813**: it adds 23 mission claims filed under No. 609.
Do not compare 624/212 against an 813-base figure without saying so.

## 2. The government's own PER-CLAIM status list (1881)

**"H H., List of private land claims in California under Spanish and Mexican
authorities", in the Annual Report of the Commissioner of the General Land
Office for the fiscal year ending June 30, 1881**, within the Report of the
Surveyor General of California, H.R. Exec. Doc. No. 1, 47th Cong., 1st Sess.,
Serial 2017, table at pp. 533-549.

Columns: Land commission number | number on map of public surveys | name |
**confirmee** | **condition** | location | area by county | total area.
Arranged alphabetically, Acalanes to Zayanta.

Verified present: 448 rows carry a `Patented <month day, year>` condition, and
others read "Not surveyed" or "Before Commissioner General Land Office". Sample
rows read directly include Nuestra Señora del Refugio, A. M. Ortega et al.,
"Patented July 28, 1866", Santa Barbara, 26,529 acres.

**This is the independent cross-check the register has never had.** It supplies,
from the government's own records, four fields we currently carry on other
authority: `patent_to` (their "confirmee"), `patent_date`, `patent_acres`, and
county. It is to the patent layer what Hoffman's table is to the grant layer.

## Where this leaves the outcome figures

| source | basis | confirmed | rejected | other |
|---|---|---|---|---|
| Hittell III:695 (1898) | Commission first decision | 514 | 280 | 19 |
| Hittell's own appellate correction, same page | final | ~594 | ~200 | 19 |
| Morrow 1923 p.14 | final | 604 | 190 | 19 |
| our parse of Hoffman's 1862 table | final as of 1862 | 607 | 167 | 39 |
| **GLO / Donaldson 1884 p.1114** | **final as of 1881, base 836** | **624** | **212** |, |

Our 1862 figure and the GLO's 1881 figure differ in the direction and roughly the
magnitude you would expect from nineteen more years of appeals closing. That
coherence is itself a check on the parse.

## Recommended next step

Build a `glo_1881_crosscheck.py` on the model of `hoffman_crosscheck.py`, matching
Table H H to the register by rancho name and Land Commission number, and flagging
disagreements in patentee, patent date and acreage. Caveat: the djvu OCR of a
wide ruled table is poor (column bleed is visible in the sample above), so the
table should be read from page images rather than the OCR text for any value
that ends up published.

## Reproduce

    curl -sL -o /tmp/donaldson.txt https://archive.org/download/publicdomainitsh00dona/publicdomainitsh00dona_djvu.txt
    grep -A12 'CLAIMS IN CALIFORNIA PRESENTED' /tmp/donaldson.txt
    curl -sL -o /tmp/glo1881.txt https://archive.org/download/annualreportofco00unse_45/annualreportofco00unse_45_djvu.txt

⚠ OCR trap, hit twice now: Donaldson's OCR breaks "Claims" into "Clai ms", and
Hittell spells his numbers out in words. A numeric or exact-phrase grep returns
zero for passages that are plainly there. Search loosely before concluding a
figure is absent.
