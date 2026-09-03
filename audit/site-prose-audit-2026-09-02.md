# Ranchos portal — site prose/claims audit findings

Date: 2026-09-02. Read-only pass over `/Users/aodhan/ranchos-portal`. Every numeric
claim below was checked against `data/ranchos-register.csv` (672 rows), the
`data/ranchos-register.json` (`count: 672`), the in-app `DATA` blob embedded in
`index.html`, and the completed audit (`audit/FINDINGS-2026-09-01.md`,
`audit/README.md`): 100/100 verified, overall field error 5.3%, grantee 16.7%.

Key structural fact that drives findings 1–4: the generated HTML pages and the
interactive map are built by `build_pages.py::load()`, whose "single source of
truth" is the `DATA` object embedded in `index.html`. That `DATA` has **673
records** (`counts.total: 673`, `mapped: 535`, `unmapped: 138`, `counties: 40`).
The **downloadable dataset** (`data/ranchos-register.csv` + `.json`, and the audit
universe) has **672 records**. The one extra record is **`u-100` "Topanga Malibu"**,
which is flagged `"duplicate_of": "Topanga Malibu Sequit (SD 147)"` and
`"suppress_register": true` — it is deliberately hidden from the register table
(build_pages line 415) and excluded from the export, yet still counted in
`counts.total`. So 672 is the correct, self-consistent number; every "673" counts a
suppressed duplicate.

---

## Findings

### 1. "673 records / 673 grants" — WRONG (should be 672)
- **register/index.html** (summ): *"Every grant and claim we hold: **673** records
  across 40 counties, of which **535** have a mapped boundary and their own page."*
- **register/index.html** (meta description): *"The full register of **673** Spanish
  and Mexican land grants and claims of Alta California…"*
- **index.html** (og:description + JSON-LD Dataset description): *"…1769 to 1846:
  **673** grants and claims across 40 counties, 535 with mapped boundaries…"*
- **All 535 per-rancho pages `r/*.html`** (hardcoded footer link, build_pages line
  400): *"Back to the full register of **673** grants and claims."* (confirmed in
  535 files)
- **sources/index.html §6** table: *"Register rows | **673** | Rows in
  register-data.json: 535 mapped + 138 unmapped"* and drift paragraph *"the
  register's **673** rows supersede the index's 662."*
- **Verified value:** 672. `data/ranchos-register.csv` = 672 data rows;
  `ranchos-register.json` `count` field = 672; the 673rd (`u-100`) is a
  `suppress_register` duplicate of Topanga Malibu Sequit (SD 147) that the site
  itself hides from the table and the download.
- **Severity: WRONG** (and it inflates the headline of a dataset paper with an
  acknowledged duplicate). Appears on the register page, the homepage social/
  structured-data card, and 535 rancho pages.

### 2. "The remaining 138 are claims… / 535 mapped + 138 unmapped" — WRONG (should be 137)
- **register/index.html** (summ): *"The remaining **138** are claims recorded in the
  United States land case files for which no surveyed boundary survives."*
- **sources/index.html §6**: *"535 mapped + **138** unmapped."*
- **Verified value:** 137. In the exported register, mapped `yes` = 535, so unmapped
  = 672 − 535 = **137**. The 138 again counts the suppressed duplicate `u-100`
  (which is unmapped). Same off-by-one as finding 1.
- **Severity: WRONG.**

### 3. "for 532 of them, the United States patent" — WRONG (should be 531)
- **register/index.html** (meta description): *"…adjudication outcome and, for **532**
  of them, the United States patent with its patentee, date and patented acreage."*
- **Verified value:** 531. `build_pages.py` computes this live as records with a
  patent date; in the exported CSV, `patent_date` is non-empty on **531** rows
  (the `DATA` blob shows 532 only because `u-100` carries a patent date). No other
  patent column yields 532 either (patent_to = 497, patent_acres = 483,
  glo_patent_no = 550). Off by one, same duplicate.
- **Severity: WRONG (minor magnitude).**

### 4. Sources page contradicts itself on the register total — INTERNAL CONTRADICTION
- **sources/index.html** says **672** in two places: §"What this is" (*"The register
  holds **672** grants"*) and §10 (*"A blind sample of 100 of the **672** records"*).
- The **same page** says **673** in §6 (table row + drift paragraph). A reader sees
  both 672 and 673 for "the register" on one page.
- **Verified value:** 672. The §6 "673/138" strings are the wrong ones.
- **Severity: MISLEADING / internal contradiction.**

### 5. Sources §10 audit status — STALE (contradicted by the finished audit)
- **sources/index.html §10**: *"**Status: sample committed, verification in progress,
  0 of 100 checked.** The rate will be published here per field and overall…a partial
  audit will be reported as partial."*
- Also §"What this is": *"…and **is being verified** field by field against the case
  files. The rate **will be published** here whatever it turns out to be. Section 10
  gives the current status."*
- **Verified fact:** the audit is **complete**. `audit/README.md` and
  `audit/FINDINGS-2026-09-01.md`: 100 of 100 checked (2026-09-02); 49/100 clean,
  25/100 carry ≥1 error; overall field error **5.3%** (30/568); per field name 0.0%,
  land_case 0.0%, outcome 1.1%, governor 4.2%, year 9.6%, **grantee 16.7%**.
- The live prose says 0 checked and speaks in the future tense; the numbers already
  exist in the repo. This is the single most conspicuous stale claim for a data-paper
  submission. (Source of the stale text: the `SOURCES_HTML` const inside
  `index.html`, which `build_pages.py` copies verbatim into `sources/index.html`.)
- **Severity: STALE (high priority).**

### 6. Errata page "no corrections / checking only just begun" — STALE
- **errata/index.html**: *"**No corrections recorded yet.** This page went up with the
  accuracy audit, on 1 September 2026, and will fill as the audit and readers turn
  things up. An empty register this early means the checking **has only just begun**,
  not that the register is clean."*
- **Verified fact:** the checking is finished, not "only just begun," and the audit
  found **30 field errors** across 25 records (grantee especially: 16 errors,
  including one rejected claim shown as Confirmed, `u-23` Orchard of San Juan Bautista
  SD 385). The register is measurably **not** clean.
- Nuance: `data/errata.json` is legitimately still empty because the audit's
  corrections are *staged, not yet published* (`audit/proposed-corrections-v1.1.json`,
  `audit/proposed-errata-2026-09-01.json`). So an empty errata table is defensible;
  the **sentence** "the checking has only just begun" is what is false.
- **Severity: STALE.**

### 7. `data/ranchos-experimental.json` abstract + legend — STALE (self-acknowledged)
- **abstract**: *"…this map shows the **510** grants with a reconstructed surveyed
  boundary…"*; **legend_note**: *"**510 of 813** claims mapped with a boundary."*
- Current mapped = **535** (of which 530 carry a polygon per sources §1). Sources §6
  explicitly says the "510 still printed in the map's abstract and legend note are
  stale text from earlier builds; the legend line…should be refreshed to 535."
- The interactive app (`index.html`) renders its own embedded `DATA.legend`, not this
  abstract, so 510 may not be visible in the live UI — but it is a **published,
  downloadable data file** carrying a wrong headline that the site's own Sources page
  flags. Refresh or remove.
- **Severity: STALE (moderate — published file, self-flagged).**

### 8. Hoffman rejected-count: "246" vs "239" — INTERNAL CONTRADICTION
- **ranchos-experimental.json** abstract: *"about 545 confirmed or patented, some
  **246** rejected."*
- **sources/index.html §2 and §6**: *"545 claims as confirmed or patented and **239**
  as rejected, plus roughly 29 in other postures"* / *"545 confirmed/patented, **239**
  rejected, ~29 other."*
- The sources figures reconcile to 813 (545 + 239 + 29 = 813); 545 + 246 does not.
  So **239** is the internally consistent value and the abstract's **246** is the
  outlier. Could not independently confirm the true Hoffman split: the referenced
  `data/hoffman-claims.json` (813 rows) is **not present** in the current repo, so
  this is flagged as a contradiction between two published surfaces, resolved in favor
  of 239 on arithmetic grounds.
- **Severity: MISLEADING / internal contradiction.**

### 9. "across 40 counties" — MISLEADING (minor)
- **register/index.html** (meta + summ) and **index.html** description: *"across **40**
  counties."*
- **Verified value:** the register has 40 distinct non-blank `county` values, but one
  of them is the literal string **"various"** (not a county), and **157** records have
  a blank county. So "40 counties" is the raw distinct-value count; the number of real
  named counties is **39**. Borderline; state as "40 county values" or drop "various."
- **Severity: MISLEADING (minor).**

### 10. Dynasty / "granted to X" attribution inherits the 16.7% grantee error — CAVEAT
- The 27 dynasty pages (`dynasties/*.html`, from the `GEN` blob) attribute ranchos to
  families largely through the `grantee` field, e.g. Peralta: *"The Peraltas held
  Rancho San Antonio, the 44,800-acre grant…"* No single dynasty statement was found
  false, but the audit measured `grantee` at **16.7%** error, the dominant class being
  the U.S.-era land-case **claimant** recorded in place of the original Mexican
  **grantee** (purchasers and heirs: Soulajule, Nicasio, Quito, Las Posas, Cuyama,
  etc.). Any "granted to <person>" or family-membership line therefore carries that
  inherited risk. Sources §"What this is" already warns patentees are not inferred
  from grantees, but does not warn that dynasty attribution runs *through* grantee.
- **Severity: OK-verified-notable / methodological caveat**, not a specific number to
  fix.

---

## Verified-correct (checked, no change needed)
- **672** in CSV, JSON `count`, and the audit universe — mutually consistent.
- **Mapped 535 = 511 rancho-class + 13 ex-mission + 7 pueblo + 4 presidio** (sources
  §6) — verified exactly against the register.
- **date_range 1769–1846** (map) = CSV year min/max exactly; scope "Spanish
  1769–1821 / Mexican 1822–1846" is standard and correct.
- **Era legend date ranges** all historically correct: Echeandía 1825–1831, Figueroa
  1833–1835, interim (Gutiérrez·Chico·Castro) 1835–1836, Alvarado 1836–1842,
  Micheltorena 1842–1845, Pío Pico 1845–1846, Spanish "to 1821."
- **"38 surviving cattle brands"** (brands page summ) = 38 rendered brand cards.
- **"27 landholding families"** (dynasties index) = 27 `GEN` families = 27 dynasty
  pages.
- **"813 claims filed before the Land Commission"** — standard, uncontested figure.
- Alvarado is correctly the largest granting era (210 of 672 register rows; 192 of
  535 mapped), consistent with the map coloring emphasis.

---

## Strongest 5 to fix before the JOHD submission
1. **Kill the 673 → 672 overcount everywhere.** It appears on the register page
   (summ + meta), the homepage og/JSON-LD card, and **all 535 rancho-page footers**
   (hardcoded in `build_pages.py` line 400), and it makes the Sources page contradict
   itself (672 vs 673). Root cause: `DATA.counts.total` counts the `suppress_register`
   duplicate `u-100`; exclude it so counts match the published dataset and the audit.
2. **Update Sources §10** — replace "verification in progress, 0 of 100 checked" with
   the completed result (100/100; overall 5.3%; grantee 16.7%, year 9.6%, governor
   4.2%, outcome 1.1%, name/land_case 0.0%). This is the most damaging stale line for
   a data paper; the numbers are already in `audit/`.
3. **Fix the Errata sentence** "the checking has only just begun, not that the
   register is clean" — the checking is done and found 30 errors (incl. a rejected
   claim shown Confirmed). Empty errata *table* is OK if corrections are still staged;
   the sentence is not.
4. **Fix "138 unmapped" → 137 and "532 patents" → 531** (same duplicate off-by-one).
5. **Refresh or delete the stale `ranchos-experimental.json` abstract/legend** ("510",
   "246 rejected") — the site's own Sources page already says 510 should be 535, and
   246 contradicts the page's own 239.
