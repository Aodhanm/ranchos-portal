# Phase B census method (durable copy)

Copied from the session scratchpad on 2026-09-03 because that directory is garbage collected. This is the method the census agents follow.

---

# Ranchos register audit — per-record verification against the Bancroft land case files

You are grading a rancho land-grant register's claimed values against the PRIMARY source: the digitized Bancroft land case file PDF for each record. Accuracy is the entire point of this audit. Never infer, never guess; every grade must cite the PDF page it rests on.

Scratchpad root: `/private/tmp/claude-501/-Users-aodhan/cdabb158-80b3-425b-aca5-c0d859fed5b0/scratchpad`
(call it $S below). Your input file is `$S/phaseB/chunkNN.json` and your output file is `$S/verdicts-B/chunkNN.json`, where NN is the agent number given in your prompt. Work in your own subdirectory `$S/work-NN/` for downloads.

## Per record in your input file

1. **Derive the PDF URL.** From `claimed.land_case` like `ND 060`: lowercase, strip the space, keep leading zeros → `nd060`. The file lives at `<scan_record_url>/files/cubanc_lcf_nd060.pdf`. Check with `curl -sIL -o /dev/null -w "%{http_code}"` first. If it 404s, fetch the `scan_record_url` HTML and extract the real filename (`grep -o 'files/cubanc_lcf_[^"]*\.pdf'`) — and note the discrepancy, because the filename encodes the docket the Bancroft actually assigned.
2. **Download.** Prefer the repo helper, which resolves the docket, downloads with RESUME, and cuts out just the pages you need:

   ```
   python3 ~/ranchos-portal/scripts/fetch_case_pages.py "ND 060" --pages 1-30 --discard-full
   ```

   It prints the excerpt path on stdout; pass that path to the Read tool. `--discard-full` deletes the full PDF as soon as the excerpt is written, which is mandatory here because disk is shared. Add `--record-url` if the docket does not resolve, or `--info` to get the page count first.
   This replaces the old `curl -sL -m 300`, which **cannot finish the large dockets**: digicoll gives about 1.8MB/s, so a 486MB pueblo file needs roughly 4.5 minutes and the 300s cap kills it every time. Verified 2026-09-03 on ND 060 (43.8MB, 49 pages, 16s) and ND 419 Pueblo Lands of San Jose (486.5MB, 585 pages, 4m20s).
   Plain `curl -sL` into `$S/work-NN/` is still fine for a small file. Either way, **delete the PDF as soon as you finish its record.**
3. **Read the pages** with the Read tool (`pages` parameter, max 20 per call). Typical structure: page 1 is a red case label (case no., district, rancho name, claimant); an early leaf states the total page count (e.g. `LAND CASE 60 ND pgs. 41`); then the printed *Transcript of the Proceedings*: petition, expediente translation (the grant decree with date, granting governor, and original grantee), and commission/court decrees. Roughly half the images are blank versos — that is normal, keep going. Read pages 1–12 first; if the grant decree has not appeared, read 13–28. Cap the hunt at ~30 pages read; beyond that, grade what you have and mark the rest UV with a note saying where the missing piece likely sits.
4. **Grade each field** — `name`, `year`, `governor`, `grantee`, `land_case`, `outcome`:
   - **OK** register agrees with the source · **ERR** register wrong (state the correct reading verbatim, with the page) · **PART** right entity, imprecise form · **UV** not determinable from the pages read · **NA** register blank by design.
   - `year`/`governor`/`grantee`: grade against the GRANT itself (the concession decree or its sworn translation in the expediente), not against witness testimony. If they disagree with the register, quote the decree's own words.
   - `land_case`: register docket vs the red label and the PDF filename.
   - `outcome`: grade only as far as the file shows (decrees of confirmation, rejection, appeal). If the register says "Patented" and the file shows confirmation but no patent, grade PART with note "confirmation verified; patent not in file (Phase C checks GLO)". The Land Commission's first decision is NOT final — District Court and Supreme Court decrees supersede it.
   - `patent_to`, `patent_date`, `glo_patent_no`: leave null (a later phase checks GLO records) unless a patent copy physically appears in the file — then grade it and cite the page.
5. **`hoffman_1862` in your input** is a cross-check from Ogden Hoffman's 1862 printed table — a secondary source, not authority. If Hoffman and the case file agree against the register, say so in the note. The case file governs every grade.
6. If an image is illegible at PDF resolution, grade UV and say so. Re-read a page rather than half-trust it. A wrong OK is the worst possible output of this audit; an honest UV is fine.

## Output

Write a JSON array to `$S/verdicts-B/chunkNN.json`, one object per record:

```json
[{"id": "rancho-arroyo-alameda",
  "pdf_url_used": "…/files/cubanc_lcf_nd060.pdf",
  "pdf_pages_stated": 41,
  "pages_read": [1, 12, "13-20"],
  "verdicts": {
    "name":      {"grade": "OK",  "evidence": "p1 red label: 'ARROYO de ALAMEDA GRANT'"},
    "year":      {"grade": "OK",  "evidence": "p9 grant decree translation: '…1842…'"},
    "governor":  {"grade": "…",   "evidence": "…"},
    "grantee":   {"grade": "…",   "evidence": "…"},
    "land_case": {"grade": "…",   "evidence": "…"},
    "outcome":   {"grade": "…",   "evidence": "…"},
    "patent_to": null, "patent_date": null, "glo_patent_no": null},
  "corrections": {"year": "1843 per grant decree p9: '…'"},
  "notes": "anything a re-reader needs"}]
```

Every `evidence` string names at least one PDF page. Your final text reply must be only a short summary (records completed, ERR/PART/UV counts, anything odd) — the JSON file is the deliverable.

## Phase B additions

- Some records have `"scan_record_url": null` (presidio/pueblo claims and unmatched grants). For these, first try a digicoll search: `curl -sL "https://digicoll.lib.berkeley.edu/search?p=<url-encoded rancho name>+land+case"` and look for a Land Case Files record link (`/record/NNNNNN`). If a matching case file is found, note the found URL and proceed normally. If not, grade every field UV with note "no digitized case file located" — do NOT guess.
- Records whose `hoffman_flags` list substantive disagreements (year/governor/grantee/outcome) are the priority: read far enough to settle each flagged field decisively, quoting the decree.

## Execution rule (mandatory)

Work strictly synchronously, one record at a time: `curl -sL -m 300` blocks until the download completes — that is the correct behavior. Do NOT use run_in_background, Monitors, watchers, or paced/queued downloaders; they end your turn with nothing graded. If your output file already contains graded records, skip those ids and continue with the rest. Delete every PDF immediately after grading its record.
