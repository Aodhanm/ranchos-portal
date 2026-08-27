#!/bin/bash
# Guard against broken diseño/image links in the ranchos portal.
# Run before every deploy:  bash verify-links.sh
# Exits non-zero (and prints what's wrong) if anything looks broken.
set -u
cd "$(dirname "$0")"
fail=0
UA="Mozilla/5.0 Chrome/120 Safari/537.36"

say(){ printf '%s\n' "$*"; }
bad(){ printf 'FAIL: %s\n' "$*"; fail=1; }

# 1) No malformed "../http…" URLs (the 2026-08 bug: a stray ../ before https://).
n=$(grep -rEo '\.\./https?://' index.html data gallery assets 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = "0" ] && say "OK  no ../http malformed URLs" || bad "$n malformed ../http URLs (strip the leading ../)"

# 2) Every thumb/img in the map data + gallery data must be absolute https (they are cross-origin).
for f in data/ranchos-experimental.json gallery/disenos-data.json; do
  [ -f "$f" ] || continue
  rel=$(grep -oE '"(thumb|img)": *"[^"]*"' "$f" | grep -cv '"[^"]*": *"https://' || true)
  [ "$rel" = "0" ] && say "OK  $f: all thumb/img are absolute https" || bad "$f: $rel thumb/img are not absolute https"
done

# 3) Live-load a sample thumbnail and a sample full image (catches renamed/missing files).
for kind in disenos-thumb disenos-img; do
  u=$(grep -oE "https://maps\.archivesofcalifornia\.com/gallery/$kind/[^\"]*" data/ranchos-experimental.json 2>/dev/null | head -1)
  if [ -n "${u:-}" ]; then
    code=$(curl -s -A "$UA" -o /dev/null -w '%{http_code}' "$u")
    [ "$code" = "200" ] && say "OK  $kind sample loads ($code)" || bad "$kind sample $code: $u"
  fi
done

# 4) Core same-origin assets exist locally.
for f in index.html assets/js/disenos.js assets/js/map-engine-experimental.js maps/ranchos-portal-embed.html data/ranchos-experimental.json gallery/disenos-data.json CNAME; do
  [ -f "$f" ] && say "OK  $f present" || bad "$f MISSING"
done

echo
[ "$fail" = "0" ] && { echo "ALL CHECKS PASSED"; exit 0; } || { echo "SOME CHECKS FAILED"; exit 1; }
