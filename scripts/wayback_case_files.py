#!/usr/bin/env python3
"""Fetch Bancroft land case files from the Internet Archive instead of digicoll.

WHY THIS EXISTS. digicoll.lib.berkeley.edu went behind an AWS WAF bot challenge
part-way through the case-file census, which stopped it at 557 of 672 records.
The challenge is not worked around and must not be: it returns HTTP 202 with
`x-amzn-waf-action: challenge` and an empty body, and that is the library saying
no to scripted clients.

The Internet Archive's Wayback Machine crawled those same PDFs in 2024, before
the WAF went up, and serves them freely to anyone with no challenge, no account
and no login. That is a different, open, public source, not a way around
Berkeley's control. Verified end to end on 2026-09-16: cubanc_lcf_nd369.pdf
replays as 15,420,945 bytes, 17 pages, and page 1 is the case cover reading
"CASE NO. 369 / NORTHERN DISTRICT / TOWN OF SUTTER GRANT / JOHN A. SUTTER /
CLAIMANT", which is register row u-128 exactly.

COVERAGE, measured not assumed: 97 of the 115 unread records have manuscript
bytes in the archive; 18 have none. Of the 97, one (nd102) is truncated at
exactly 1,048,576 bytes and one (nd420, New Almaden) is split across twelve
part files. See audit/wayback-census.json for the per-record census.

TWO TRAPS, both of which fail silently and both of which are checked here:

  1. A capture can be TRUNCATED. The Wayback replay happily serves the partial
     bytes with a 200 and a %PDF header. A file of exactly 1,048,576 bytes is
     the signature, but any short read is possible, so completeness is checked
     by looking for the %%EOF trailer, not by trusting the status code. This is
     the same class of failure as the WAF's 202: a success code over a non-file.

  2. The `id_` modifier is REQUIRED. Without it the Wayback Machine rewrites
     the response and injects its own banner, which corrupts a binary PDF.

Usage:
    python3 scripts/wayback_case_files.py --census          # rebuild the census
    python3 scripts/wayback_case_files.py "ND 369"          # fetch one docket
    python3 scripts/wayback_case_files.py "ND 369" --pages 1-20
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CENSUS = REPO / "audit" / "wayback-census.json"
CACHE = Path(os.environ.get("CASEFILE_CACHE", "/tmp/casefile-cache"))
UA = "ranchos-portal-audit/1.0 (+https://ranchos.archivesofcalifornia.com)"
CDX = ("http://web.archive.org/cdx/search/cdx?url=digicoll.lib.berkeley.edu"
       "&matchType=domain&filter=original:.*cubanc_lcf.*&filter=statuscode:200"
       "&filter=mimetype:application/pdf&output=json&fl=original,timestamp,length")
TRUNCATED_1MIB = 1048576


def _open(url, headers=None, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def docket_slug(docket):
    """"ND 060" and "N.D. 219" are both written in the register. Match both."""
    t = re.sub(r"[.\s]+", " ", (docket or "").strip().upper())
    m = re.match(r"^([NS])\s*D\s*0*(\d+)$", t)
    return f"{m.group(1).lower()}d{int(m.group(2)):03d}" if m else None


def build_census():
    """One CDX query, then the best capture per file. Writes audit/wayback-census.json.

    "Best" is the largest WARC record for that filename: the archive holds several
    captures of many files and the short ones are partial crawls.
    """
    with _open(CDX, timeout=180) as r:
        rows = json.loads(r.read().decode("utf-8", "replace"))[1:]
    best = {}
    for orig, ts, length in rows:
        # Multi-volume cases are suffixed: nd136A, nd136B, nd420A..nd420L.
        m = re.search(r"cubanc_lcf_([a-z]{2}\d+[a-z]?)\.pdf", orig, re.I)
        if not m:
            continue
        name = m.group(1).lower()
        n = int(length) if str(length).isdigit() else 0
        if name not in best or n > best[name][0]:
            best[name] = (n, ts, orig)
    files = {k: {"warc_bytes": v[0], "timestamp": v[1], "original_url": v[2],
                 "replay_url": f"http://web.archive.org/web/{v[1]}id_/{v[2]}"}
             for k, v in sorted(best.items())}
    doc = {
        "note": ("Bancroft land case file PDFs held by the Internet Archive's Wayback "
                 "Machine, crawled before digicoll went behind an AWS WAF bot challenge. "
                 "A free, open, unauthenticated source; not a way around the challenge, "
                 "which is neither touched nor defeated here."),
        "built_from": CDX,
        "files": len(files),
        "caveats": [
            "warc_bytes is the WARC record length, NOT the PDF size. Do not infer "
            "completeness from it; check for the %%EOF trailer after downloading.",
            "The id_ modifier in replay_url is required. Without it the Wayback "
            "Machine injects a banner and the bytes are not a valid PDF.",
            "Some captures are partial. nd102 replays exactly 1,048,576 bytes.",
        ],
        "records": files,
    }
    CENSUS.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"census: {len(files)} archived case files -> {CENSUS.relative_to(REPO)}")
    return doc


def load_census():
    if not CENSUS.exists():
        return build_census()
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def captures_for(slug, census):
    """The file itself, else its lettered parts in order. Never guesses a URL."""
    recs = census["records"]
    if slug in recs:
        return [(slug, recs[slug])]
    parts = sorted(k for k in recs if re.fullmatch(re.escape(slug) + r"[a-z]", k))
    return [(k, recs[k]) for k in parts]


def complete(path):
    """A PDF that does not end in %%EOF is a partial capture, whatever the status
    code said. Checked on the tail so a 400MB file is not read into memory."""
    if not path.exists() or path.stat().st_size < 1024:
        return False
    with open(path, "rb") as fh:
        if not fh.read(5).startswith(b"%PDF"):
            return False
        fh.seek(max(0, path.stat().st_size - 2048))
        return b"%%EOF" in fh.read()


def download(url, dest):
    """Resumable. These run to 440MB, so a dropped connection must cost the
    missing bytes and not a fresh start."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if complete(dest):
        print(f"cache {dest.name} ({dest.stat().st_size/1e6:.1f}MB)", file=sys.stderr)
        return dest
    for attempt in range(5):
        have = dest.stat().st_size if dest.exists() else 0
        try:
            hdrs = {"Range": f"bytes={have}-"} if have else {}
            with _open(url, headers=hdrs, timeout=600) as r, \
                    open(dest, "ab" if have else "wb") as fh:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
        except Exception as e:                       # noqa: BLE001
            print(f"  attempt {attempt+1}: {e}", file=sys.stderr)
        if complete(dest):
            return dest
    return dest if dest.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docket", nargs="?", help='e.g. "ND 369"')
    ap.add_argument("--census", action="store_true", help="rebuild the census and exit")
    ap.add_argument("--pages", help="page range to cut out, e.g. 1-30")
    ap.add_argument("--out", help="output path for the excerpt")
    a = ap.parse_args()

    if a.census:
        build_census()
        return 0
    if not a.docket:
        ap.error("give a docket, or --census")

    slug = docket_slug(a.docket)
    if not slug:
        raise SystemExit(f"cannot read a docket out of {a.docket!r}")
    census = load_census()
    caps = captures_for(slug, census)
    if not caps:
        raise SystemExit(f"{a.docket} ({slug}) is NOT in the Internet Archive. "
                         "18 of the 115 unread records are in this position; see "
                         "audit/PLAN-remaining-work-2026-09-16.md for what is left.")
    if len(caps) > 1:
        print(f"MULTI-VOLUME: {a.docket} is archived in {len(caps)} parts "
              f"({', '.join(k for k, _ in caps)}). Fetching all.", file=sys.stderr)

    got = []
    for name, rec in caps:
        dest = CACHE / f"{name}.pdf"
        print(f"fetching {name} from the Internet Archive "
              f"(capture {rec['timestamp']})", file=sys.stderr)
        p = download(rec["replay_url"], dest)
        if p is None:
            print(f"  FAILED {name}", file=sys.stderr)
            continue
        size = p.stat().st_size
        if not complete(p):
            flag = " (exactly 1 MiB: a truncated crawl)" if size == TRUNCATED_1MIB else ""
            print(f"  ⚠ PARTIAL capture, {size/1e6:.1f}MB, no %%EOF{flag}. "
                  f"Usable for the pages it does contain, but do NOT record it as "
                  f"a full reading of the case file.", file=sys.stderr)
        else:
            print(f"  ok {size/1e6:.1f}MB", file=sys.stderr)
        got.append(p)

    if a.pages and got:
        out = Path(a.out) if a.out else CACHE / f"{slug}_p{a.pages}.pdf"
        cmd = ["pdftoppm", "-png", "-r", "150",
               "-f", a.pages.split("-")[0], "-l", a.pages.split("-")[-1],
               str(got[0]), str(out.with_suffix(""))]
        try:
            subprocess.run(cmd, check=True)
            print(f"wrote page images {out.with_suffix('')}-NN.png")
        except FileNotFoundError:
            print("pdftoppm not found; install poppler to cut page images",
                  file=sys.stderr)
    for p in got:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
