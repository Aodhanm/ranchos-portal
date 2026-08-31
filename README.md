# ranchos-portal

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22185500.svg)](https://doi.org/10.5281/zenodo.22185500)

The register is published as a citable dataset: **DOI [10.5281/zenodo.22185500](https://doi.org/10.5281/zenodo.22185500)** (concept DOI, always resolves to the newest version). Citation metadata in `CITATION.cff`; reuse terms in `LICENSE.md` (CC BY 4.0). The Zenodo deposit carries `data/ranchos-register.csv` and `data/ranchos-register.json` with a field dictionary. The map boundaries are ECAI/UCSD data and are not part of the deposit.

Serves **https://ranchos.archivesofcalifornia.com** (GitHub Pages, custom domain via the `CNAME` file).

A self-contained research portal for the Spanish & Mexican land grants: an interactive
map, a full register, dynasties, cattle brands, and a diseños (land-grant map) gallery.

## How images are hosted

The heavy diseño imagery (~666MB) is **not** stored in this repo. It is served from the
maps site, `https://maps.archivesofcalifornia.com/gallery/…`, and every `thumb`/`img`
URL in the data is an **absolute https** link to that host. Keep it that way.

- `data/ranchos-experimental.json` — the map data; each rancho's `disenos[]` have absolute `thumb`/`img` URLs.
- `gallery/disenos-data.json` — the gallery data (same rule).
- The map is `maps/ranchos-portal-embed.html` (an iframe, same origin) using `assets/js/map-engine-experimental.js`.
- The diseños gallery is rendered **natively in the page** (not an iframe) by `assets/js/disenos.js`.

## Known bug, fixed 2026-08-26 (do not reintroduce)

The diseño image URLs were once malformed as **`../https://maps…`** — a stray `../` left
over from the old relative paths when they were rewritten to absolute URLs. This made
every map-popup thumbnail and the click-to-enlarge a dead link (broken-image icons).
Fix: the URLs must be plain `https://maps.archivesofcalifornia.com/gallery/…` with no
leading `../`.

Two related gotchas:
- The map runs in a throttled iframe, so **do not lazy-load** popup thumbnails; load them eagerly.
- Do **not** lazy-load the gallery thumbnails inside an iframe either — that is why the
  gallery is rendered natively in the page.

## Before every deploy

Run the link guard. It fails loudly if any diseño URL is malformed, relative, or dead:

```
bash verify-links.sh
```
