#!/usr/bin/env python3
"""Fetch a Bancroft land case file PDF and cut a readable page range out of it.

Why this exists: the census pass stalls on the big dockets. The pueblo and
heavily litigated case files run 200-486MB, this machine has neither qpdf nor
ghostscript, and the standing `curl -sL -m 300` in the audit instructions times
out on anything over roughly 300MB at the throughput digicoll gives us
(~1.8MB/s measured 2026-09-03, so 486MB needs about 4.5 minutes). The download
dies at the 300s mark, the agent retries, and the record never gets graded.

What this does instead: resolves the docket to its real PDF, downloads it ONCE
with resume (so a dropped connection costs only the missing bytes, not a
restart), caches it, and writes out just the pages asked for. The excerpt is
what you hand to the Read tool.

Usage:
    python3 scripts/fetch_case_pages.py "ND 060" --pages 1-12
    python3 scripts/fetch_case_pages.py "ND 419" --pages 1-30 --discard-full
    python3 scripts/fetch_case_pages.py "SD 147" --info
    python3 scripts/fetch_case_pages.py --record-url https://digicoll.lib.berkeley.edu/record/266100 --pages 1-20

Docket resolution order: --pdf-url, --record-url, the bancroft_scan_url column
of data/ranchos-register.csv, then a digicoll search. The PDF filename is
derived from the docket ("ND 060" -> cubanc_lcf_nd060.pdf) and, if that 404s,
read off the record page; the tool prints a NOTE when the two disagree, because
the real filename encodes the docket the Bancroft actually assigned and that
discrepancy is itself audit evidence.

NOT worth retrying (tested 2026-09-03, both negative):
  * HTTP Range requests do not help. pypdf reads the whole stream regardless of
    how few pages you want, so a range-backed file object fetched 100% of both a
    43.8MB and a 486.5MB docket. The bytes are unavoidable.
  * digicoll serves no IIIF manifest and no per-page images for these items. The
    record page lists exactly one artifact, the whole PDF. There is no page-level
    endpoint to fetch instead.

Exit codes: 0 ok, 2 could not resolve, 3 fetch/parse failed.
"""
import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UA = "ranchos-portal-audit/1.0 (+https://ranchos.archivesofcalifornia.com)"
DIGICOLL = "https://digicoll.lib.berkeley.edu"
CACHE = Path(os.environ.get("CASEFILE_CACHE", "/tmp/casefile-cache"))


def _open(url, headers=None, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def docket_slug(docket):
    m = re.match(r"^\s*(ND|SD)\s*\.?\s*0*(\d+)\s*$", (docket or "").replace(".", " ").upper())
    return f"{m.group(1).lower()}{int(m.group(2)):03d}" if m else None


def record_url_for(docket):
    """bancroft_scan_url from the register, else a digicoll search."""
    slug = docket_slug(docket)
    csv_path = REPO / "data" / "ranchos-register.csv"
    if slug and csv_path.exists():
        for r in csv.DictReader(open(csv_path, encoding="utf-8")):
            if docket_slug(r.get("land_case") or "") == slug and r.get("bancroft_scan_url"):
                return r["bancroft_scan_url"].rstrip("/")
    q = urllib.parse.quote_plus(f"{docket} land case")
    try:
        with _open(f"{DIGICOLL}/search?p={q}", timeout=60) as r:
            html = r.read().decode("utf-8", "replace")
        m = re.search(r"/record/(\d+)", html)
        if m:
            return f"{DIGICOLL}/record/{m.group(1)}"
    except Exception:
        pass
    return None


def head_size(url):
    """Size of the remote file, or None if the URL does not serve a PDF.

    ⚠ digicoll answers a WRONG filename with HTTP 200 and an HTML error page,
    not a 404 (verified 2026-09-04 on the two-volume cases ND 136 and ND 199:
    cubanc_lcf_nd136.pdf is 200 text/html, the real files are nd136A/nd136B).
    So a status check is worthless; require the %PDF magic bytes.
    """
    try:
        with _open(url, headers={"Range": "bytes=0-7"}, timeout=60) as r:
            if not r.read(5).startswith(b"%PDF"):
                return None
            cr = r.headers.get("Content-Range")
            if cr:
                return int(cr.rsplit("/", 1)[1])
            cl = r.headers.get("Content-Length")
            return int(cl) if cl else None
    except Exception:
        return None


def pdf_url_for(record_url, docket):
    """Derived filename first; fall back to whatever the record page actually lists."""
    slug = docket_slug(docket) if docket else None
    if slug:
        cand = f"{record_url}/files/cubanc_lcf_{slug}.pdf"
        if head_size(cand):
            return cand, None
    try:
        with _open(record_url, timeout=60) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as e:
        raise SystemExit(f"could not read record page {record_url}: {e}")
    names = list(dict.fromkeys(re.findall(r"files/(cubanc_lcf_[^\"'>?]+\.pdf)", html)))
    if not names:
        raise SystemExit(f"no cubanc_lcf PDF listed on {record_url}")
    pick = names[0]
    notes = []
    if len(names) > 1:
        notes.append(f"MULTI-VOLUME case: record lists {', '.join(names)}; using "
                     f"{pick}. The decree may sit in a later volume; re-run with "
                     f"--pdf-url for the others.")
    if slug and f"cubanc_lcf_{slug}.pdf" != pick:
        notes.append(f"docket mismatch: register says {docket!r} (expected "
                     f"cubanc_lcf_{slug}.pdf) but the Bancroft file is {pick}")
    return f"{record_url}/files/{pick}", ("; ".join(notes) or None)


def download(url, dest, expect=None, tries=4):
    """Resumable download. Returns dest, or raises. Resume is the whole point:
    a drop on a 486MB file must cost the missing bytes, not a fresh start."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and expect and dest.stat().st_size == expect:
        print(f"cache {dest} ({expect/1e6:.1f}MB, complete)", file=sys.stderr)
        return dest
    if not shutil.which("curl"):
        raise SystemExit("curl not found")
    for attempt in range(1, tries + 1):
        have = dest.stat().st_size if dest.exists() else 0
        if expect and have == expect:
            break
        print(f"get   attempt {attempt}/{tries}, have {have/1e6:.1f}MB"
              + (f" of {expect/1e6:.1f}MB" if expect else ""), file=sys.stderr, flush=True)
        cmd = ["curl", "-sL", "-C", "-", "--fail-with-body", "--retry", "2",
               "--connect-timeout", "30", "--speed-time", "60", "--speed-limit", "1024",
               "-A", UA, "-o", str(dest), url]
        rc = subprocess.run(cmd).returncode
        have = dest.stat().st_size if dest.exists() else 0
        if rc == 0 and (not expect or have == expect):
            break
        if rc == 33:            # server refused the resume; start clean once
            dest.unlink(missing_ok=True)
    have = dest.stat().st_size if dest.exists() else 0
    if not have or (expect and have != expect):
        raise SystemExit(f"download incomplete: {have} bytes"
                         + (f" of {expect}" if expect else ""))
    with open(dest, "rb") as fh:
        if not fh.read(5).startswith(b"%PDF"):
            dest.unlink(missing_ok=True)
            raise SystemExit("server sent HTML instead of a PDF (digicoll answers a "
                             "wrong filename with 200 + an error page); URL is wrong")
    print(f"got   {have/1e6:.1f}MB -> {dest}", file=sys.stderr)
    return dest


def parse_pages(spec, npages):
    """'1-30' or '1,3,9-12' -> sorted 0-based indices, clamped to the document."""
    want = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            want.update(range(int(a), int(b) + 1))
        else:
            want.add(int(part))
    return sorted(i - 1 for i in want if 1 <= i <= npages)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docket", nargs="?", help='land case docket, e.g. "ND 060"')
    ap.add_argument("--record-url", help="digicoll record URL (skips docket lookup)")
    ap.add_argument("--pdf-url", help="direct PDF URL (skips all resolution)")
    ap.add_argument("--pages", default="1-30", help='page spec, e.g. "1-30" or "1,3,9-12"')
    ap.add_argument("--out", help="output PDF path (default alongside the cache)")
    ap.add_argument("--info", action="store_true",
                    help="report size and page count only, write nothing")
    ap.add_argument("--discard-full", action="store_true",
                    help="delete the cached full PDF after extracting (disk is shared)")
    a = ap.parse_args()

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        raise SystemExit("pypdf is required: python3 -m pip install pypdf")

    note = None
    if a.pdf_url:
        pdf_url = a.pdf_url
    else:
        rec = a.record_url.rstrip("/") if a.record_url else None
        if not rec:
            if not a.docket:
                ap.error("give a docket, --record-url, or --pdf-url")
            rec = record_url_for(a.docket)
        if not rec:
            print(f"could not resolve a digicoll record for {a.docket!r}", file=sys.stderr)
            return 2
        pdf_url, note = pdf_url_for(rec, a.docket)

    if note:
        print(f"NOTE  {note}", file=sys.stderr)
    print(f"pdf   {pdf_url}", file=sys.stderr)

    size = head_size(pdf_url)
    if size:
        print(f"size  {size/1e6:.1f}MB remote", file=sys.stderr)
    name = pdf_url.rsplit("/", 1)[-1]
    full = CACHE / name
    try:
        download(pdf_url, full, expect=size)
    except SystemExit as e:
        print(f"{e}", file=sys.stderr)
        return 3

    try:
        reader = PdfReader(str(full))
        npages = len(reader.pages)
    except Exception as e:
        print(f"parse failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    print(f"pages {npages} in document", file=sys.stderr)

    if a.info:
        print(full)
        return 0

    idxs = parse_pages(a.pages, npages)
    if not idxs:
        print(f"page spec {a.pages!r} selects nothing of {npages} pages", file=sys.stderr)
        return 3
    out = Path(a.out) if a.out else CACHE / f"{name[:-4]}-p{re.sub(r'[^0-9]+', '_', a.pages)}.pdf"
    try:
        writer = PdfWriter()
        for i in idxs:
            writer.add_page(reader.pages[i])
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as fh:
            writer.write(fh)
    except Exception as e:
        print(f"extract failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 3

    if a.discard_full:
        full.unlink(missing_ok=True)
        print("clean cached full PDF deleted", file=sys.stderr)

    print(f"wrote {len(idxs)} pages -> {out} ({out.stat().st_size/1e6:.1f}MB)", file=sys.stderr)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
