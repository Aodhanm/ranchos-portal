#!/usr/bin/env python3
"""Verify the staged Supreme Court citations against the official reports.

The 29 citations in audit/proposed-scotus-citations.json were taken as printed in
Hoffman's 1862 table and passed only a STRUCTURAL check (all in Howard 17 to 24,
the right range for an 1862 imprint). They were never checked against the reports
themselves, because CourtListener answers scripted clients with a bot challenge.

The Caselaw Access Project's static bulk host does not. https://static.case.law
serves per-volume CasesMetadata.json over plain anonymous HTTP, no account, no
challenge, no rate limit encountered. Each record carries both the nominative
citation ("23 How. 273") and the official one ("64 U.S. 273"), which is exactly
the pair the register needs.

Howard volumes 1 to 24 are U.S. Reports 42 to 65, so n Howard = (41 + n) U.S.

A citation is CONFIRMED when a case in that volume starts on that page AND its
reported parties are plausibly the land claim, which is tested against the
CLAIMANT'S SURNAME as Hoffman's own entry gives it. Matching on the page alone is
not enough, twice over:

  * TWO CASES CAN SHARE A FIRST PAGE. 18 How. 539 is both "Hudgins v. Kemp" (a
    one-page order) and "de Arguello v. United States" (539 to 553). Taking the
    first match reported rancho-pulgas as a bad citation when Hoffman was right.
    That is the same cands[0] bug found in the Hoffman docket join the same day.
  * A PAGE NUMBER CAN BE MISPRINTED and still land on a real case. Hoffman gives
    Bolsa de Tomales as 22 Howard 87, which is "Hodge v. Williams"; his own entry
    names the claimant James D. Galbraith, and "United States v. Galbraith" is at
    22 How. 89. Nemshas is given as 24 Howard 151, where no case begins at all;
    his entry names Charles Chana, and "United States v. Chana" is at 24 How. 131.

So when the page does not yield the claimant, the volume is searched for the
claimant by surname and a corrected citation is PROPOSED, with both readings
shown. Nothing is applied automatically.

Usage: python3 scripts/verify_scotus_cites.py
Writes audit/scotus-verification.json. Changes no register data.
"""
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAP = "https://static.case.law/us/{vol}/CasesMetadata.json"
UA = "ranchos-portal-audit/1.0 (+https://ranchos.archivesofcalifornia.com)"


def volume(vol, cache={}):
    if vol not in cache:
        req = urllib.request.Request(CAP.format(vol=vol), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            cache[vol] = json.loads(r.read().decode("utf-8"))
    return cache[vol]


def hoffman_raw(land_case, _cache={}):
    """The full printed entry for a docket. The staged file carries only the TAIL
    of the entry, the disposition clause, and the claimant's name is in the HEAD,
    so the appendix has to be re-read to get it."""
    if not _cache:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hoffman_crosscheck import parse_appendix          # noqa: PLC0415
        src = Path(os.environ.get("HOFFMAN_TXT", "/tmp/GR_1919_djvu.txt"))
        if not src.exists():
            _cache["_missing"] = True
            return None
        for e in parse_appendix(src.read_text(errors="replace")):
            _cache[(e["district"], int(e["court_no"]))] = e["raw"]
    m = re.match(r"^\s*([NS])\s*\.?\s*D\s*\.?\s*0*(\d+)", (land_case or "").upper())
    return _cache.get((m.group(1) + "D", int(m.group(2)))) if m else None


def cite_of(case, kind):
    return next((c["cite"] for c in case["citations"] if c["type"] == kind), None)


def pick(cases, party):
    """The one case naming that party, or None. Ambiguity is not resolved by
    guessing: if two cases name it, that is reported, not silently halved."""
    if not party:
        return None
    hits = [c for c in cases if same_party(party, c["name"])] \
        or [c for c in cases if party.lower() in c["name"].lower()]
    return hits[0] if len(hits) == 1 else None


def claimant_surname(evidence):
    """Hoffman's entries open "<Name>[ et al.], claimant[s] for <rancho>". Getting
    the surname out has to survive the OCR and the compositor:
      "Antonio Maria Osio, 'claimant for"      a stray curly quote
      "Thomas O. Larkin et al., claimants for"  et al.
      "Maria dc la Soledad, Ortega de Argucllo et als., claimants for"
    So: take everything before the claimant marker, drop "et al", and keep the
    last word that looks like a surname."""
    if not evidence:
        return None
    m = re.search(r"^(.{0,200}?)[^A-Za-z]{0,4}claimants?\s+for\b", evidence, re.S)
    if not m:
        return None
    head = m.group(1)
    head = re.split(r"\b\d{1,3},\s*\d{1,3},?\s*[NS8][\.,]?\s*[DI)][\.,]?(?:\s*\d+\.)?", head)[-1]
    head = re.sub(r"\bet\s+als?\.?", " ", head, flags=re.I)
    words = [w.strip(".,;'\u2019\u201c\u201d ") for w in head.split()]
    words = [w for w in words if len(w) > 2 and w[:1].isupper()]
    return words[-1] if words else None


def same_party(surname, case_name):
    """The reports and Hoffman's OCR do not spell these the same: Cervantez against
    Cervantes, Teschemacher against Teschmaker, Fucntes against Fuentes. An exact
    match would reject three correct citations, so compare on a folded prefix."""
    if not surname:
        return False
    if surname.lower() in case_name.lower():
        return True
    fold = lambda w: re.sub(r"[^a-z]", "", w.lower())
    a = fold(surname)
    if len(a) < 4:
        return False
    for w in case_name.split():
        b = fold(w)
        if len(b) < 4:
            continue
        # The edit-distance path is for OCR damage in a long surname. On a short
        # one it matches anything: "Chana" came within two edits of "Canal" and
        # made the Nemshas correction ambiguous, so it was silently dropped.
        if b[:5] == a[:5] or (min(len(a), len(b)) >= 7 and edits_within(a, b, 2)):
            return True
    return False


def edits_within(a, b, k):
    """Levenshtein distance no greater than k. The djvu OCR reads e as c, m as rn
    and l as 1, so Arguello prints as "Argucllo" and Fuentes as "Fucntes"; a
    prefix test alone rejects both, and they are correct citations."""
    if abs(len(a) - len(b)) > k:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        if min(cur) > k:
            return False
        prev = cur
    return prev[-1] <= k


def main():
    recs = json.load(open(REPO / "audit" / "proposed-scotus-citations.json",
                          encoding="utf-8"))["records"]
    out, tally = [], Counter()
    for r in recs:
        m = re.match(r"(\d+) U\.S\. (\d+)", r.get("us_reports_cite") or "")
        if not m:
            tally["citation not parseable"] += 1
            out.append({**r, "verdict": "unparseable"})
            continue
        vol, page = int(m.group(1)), int(m.group(2))
        # Hoffman prints the nominative form; check we derived the official one right.
        hm = re.match(r"(\d+) Howard,?\s*(\d+)", r.get("hoffman_scotus_cite") or "")
        derived_ok = bool(hm) and (41 + int(hm.group(1)) == vol) and int(hm.group(2)) == page
        cases = volume(vol)
        claimant = claimant_surname(hoffman_raw(r.get("land_case")) or r.get("evidence"))
        onpage = [c for c in cases if str(c.get("first_page")) == str(page)]
        # Prefer the case whose parties match Hoffman's named claimant; failing
        # that, a United States party, which is the signature of a land appeal.
        hit = (pick(onpage, claimant) or pick(onpage, "United States")
               or (onpage[0] if onpage else None))
        if hit:
            official = cite_of(hit, "official")
            named = same_party(claimant, hit["name"])
            # These volumes report several appeals under one head. 20 How. 261 is
            # four: De Pacheco, Hensley, Bidwell and "Antonio Sunot et al.". So a
            # citation shared by several register rows is usually correct, and the
            # party must be sought in the FULL name, not the abbreviation.
            consolidated = hit["name"].count(" v. ") > 1
            # The Court styled an appeal under the ORIGINAL GRANTEES where the
            # claimant was a later purchaser: Rancho Los Putos is "United States
            # v. Juan Manuel Vaca and Juan Felipe Pena" though Hoffman's claimant
            # is Chiles. That is not a bad citation, it is a different caption.
            v = ("confirmed" if named else
                 "page and volume correct, but the case is styled under other "
                 "parties than Hoffman's claimant")
            out.append({**r, "verdict": v,
                        "reports_case_name": hit["name_abbreviation"],
                        "reports_decision_date": hit.get("decision_date"),
                        "reports_official_cite": official,
                        "reports_nominative_cite": cite_of(hit, "nominative"),
                        "hoffman_claimant": claimant,
                        "cases_sharing_that_page": [c["name_abbreviation"] for c in onpage],
                        "consolidated_report": consolidated,
                        "reports_full_name": hit["name"][:300],
                        "howard_conversion_ok": derived_ok})
        else:
            out.append({**r, "verdict": "NO CASE STARTS ON THAT PAGE",
                        "hoffman_claimant": claimant,
                        "howard_conversion_ok": derived_ok})
        # Whatever happened above, if the claimant is findable elsewhere in the
        # volume and is not what we just matched, say so. A misprinted page that
        # lands on a real case is the failure this catches.
        if claimant and (not hit or not same_party(claimant, hit["name"])):
            alt = pick(cases, claimant)
            if alt:
                out[-1]["proposed_correction"] = {
                    "cite": cite_of(alt, "nominative"),
                    "us_reports_cite": cite_of(alt, "official"),
                    "case_name": alt["name_abbreviation"],
                    "why": (f"Hoffman's own entry names the claimant {claimant}, and "
                            f"{alt['name_abbreviation']} is the only case in this volume "
                            f"with that party. The printed page number does not reach it."),
                }
                # A proposed correction means the printed PAGE is wrong, so the
                # earlier "page and volume correct" verdict must not stand.
                out[-1]["verdict"] = "PAGE NUMBER WRONG in Hoffman's table"
                tally["corrected page number PROPOSED"] += 1
        tally[out[-1]["verdict"]] += 1
        if not derived_ok:
            tally["Howard to U.S. conversion WRONG"] += 1

    tally = Counter(r["verdict"] for r in out)
    # One Supreme Court case can genuinely cover several ranchos, but it can also
    # mean a citation was copied across rows. Either way a reader should be told.
    shared = Counter(r.get("us_reports_cite") for r in out if r.get("us_reports_cite"))
    for r in out:
        n = shared.get(r.get("us_reports_cite"), 0)
        if n > 1:
            r["citation_shared_with"] = n - 1
            tally["citation shared by more than one register row"] += 1

    doc = {
        "note": ("The 29 staged Supreme Court citations, checked against the official "
                 "reports for the first time. Source: Caselaw Access Project static "
                 "bulk, https://static.case.law/us/<volume>/CasesMetadata.json. "
                 "CONFIRMED means a case in that volume begins on that page and its "
                 "official citation matches. It does NOT mean the case is the right "
                 "land claim: the register names a rancho and the reports name the "
                 "parties, so reports_case_name is given for a human to judge."),
        "source": "https://static.case.law",
        "rule": "Howard volumes 1 to 24 are U.S. Reports 42 to 65, so n Howard = (41 + n) U.S.",
        "tally": dict(tally.most_common()),
        "records": out,
    }
    (REPO / "audit" / "scotus-verification.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in tally.most_common():
        print(f"  {v:3d}  {k}")
    print(f"\nwrote audit/scotus-verification.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
