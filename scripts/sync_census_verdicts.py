#!/usr/bin/env python3
"""Copy Phase B census verdicts out of the session scratchpad into the repo.

The verdicts are written to a per-session scratchpad that can be garbage
collected; the repo copy under audit/census-partial-2026-09-02/ is the durable
one. Refuses to shrink a chunk: a repo file is replaced only when the scratchpad
holds a superset of its ids, so a half-written or truncated in-flight file can
never overwrite good graded work.

Usage: python3 scripts/sync_census_verdicts.py [scratchpad_verdicts_dir]
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEST = REPO / "audit" / "census-partial-2026-09-02"
DEFAULT_SRC = Path("/private/tmp/claude-501/-Users-aodhan/"
                   "cdabb158-80b3-425b-aca5-c0d859fed5b0/scratchpad/verdicts-B")


def ids(path):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None                      # unparseable => in flight, skip
    if not isinstance(d, list):
        return None
    return {r.get("id") for r in d if isinstance(r, dict) and r.get("id")}


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.is_dir():
        raise SystemExit(f"no such scratchpad dir: {src}")
    DEST.mkdir(parents=True, exist_ok=True)
    copied = skipped = held = 0
    total = 0
    for s in sorted(src.glob("chunk*.json")):
        new = ids(s)
        if new is None:
            print(f"skip  {s.name}: unparseable (agent mid-write)")
            skipped += 1
            continue
        d = DEST / s.name
        old = ids(d) if d.exists() else set()
        if old and not old <= new:
            print(f"HOLD  {s.name}: repo has {len(old - new)} id(s) the scratchpad lacks, "
                  f"not overwriting")
            held += 1
            total += len(old)
            continue
        if old == new and d.exists():
            total += len(new)
            continue
        shutil.copy2(s, d)
        print(f"copy  {s.name}: {len(old)} -> {len(new)} graded")
        copied += 1
        total += len(new)
    print(f"\n{copied} chunk(s) updated, {skipped} in flight, {held} held back; "
          f"{total} records graded in the repo copy")
    return 1 if held else 0


if __name__ == "__main__":
    sys.exit(main())
