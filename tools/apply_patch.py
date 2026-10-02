#!/usr/bin/env python3
"""
Apply a dated pricing patch to model-prices.json.

Design rules:
  - Never mutate the baseline. Writes a new versioned file.
  - Corrections must land on an id that already exists, else they are refused
    (a typo in a correction would silently create a bogus model).
  - Additions must not collide with an existing id.
  - Every applied change is recorded in _meta.revisions so the JSON is
    self-documenting for anyone who downloads it.
  - Fields the patch does not mention are left exactly as they were.

Usage:  python apply_patch.py pricing-patch-2026-10-02.json
"""

import json
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
# Patches are cumulative: apply the next one on top of the current shipping file.
# Reading the pristine baseline every time would make a second patch silently
# drop everything the first one added, which is exactly what happened once.
SHIPPING = ROOT / "site" / "data" / "model-prices.json"
PRISTINE = ROOT / "_baseline" / "data" / "model-prices.json"
if len(sys.argv) > 2:
    DATA = Path(sys.argv[2])
elif SHIPPING.exists():
    DATA = SHIPPING
else:
    DATA = PRISTINE
OUT = ROOT / "site" / "data" / "model-prices.json"


def main():
    if len(sys.argv) < 2:
        print("usage: python apply_patch.py <patch.json>")
        return 1

    patch = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["_patch"]
    data = json.loads(DATA.read_text(encoding="utf-8"))

    by_id = {m["id"]: m for m in data["models"]}
    meta = data["_meta"]
    prev_verified = meta.get("lastVerified")

    print(f"patch     : {sys.argv[1]}")
    print(f"patch date: {patch['date']}")
    print(f"was       : lastVerified {prev_verified}, {len(data['models'])} models\n")

    # ---------------- corrections
    applied_c = skipped_c = 0
    print("corrections")
    for c in patch.get("corrections", []):
        mid, field = c["id"], c["field"]
        if mid not in by_id:
            print(f"  REFUSED {mid}: no such model (typo in patch?)")
            skipped_c += 1
            continue
        have = by_id[mid].get(field)
        if have != c["from"]:
            print(f"  REFUSED {mid}.{field}: expected {c['from']!r}, found {have!r}")
            skipped_c += 1
            continue
        by_id[mid][field] = c["to"]
        print(f"  ok  {mid}.{field}: {c['from']} -> {c['to']}")
        applied_c += 1

    # ---------------- additions
    applied_a = skipped_a = 0
    print("\nadditions")
    for a in patch.get("additions", []):
        mid = a["id"]
        if mid in by_id:
            print(f"  SKIP    {mid}: already present, not overwriting")
            skipped_a += 1
            continue
        row = {
            "id": mid,
            "label": a["label"],
            "provider": a["provider"],
            "tokenizer": a["tokenizer"],
            "contextWindow": a["contextWindow"],
            "priceInputPer1M": a["priceInputPer1M"],
            "priceOutputPer1M": a["priceOutputPer1M"],
        }
        for optional in ("priceCachedInputPer1M", "maxOutputTokens", "note"):
            if optional in a:
                row[optional] = a[optional]
        by_id[mid] = row
        data["models"].append(row)
        cached = f"  cached ${a['priceCachedInputPer1M']}" if "priceCachedInputPer1M" in a else ""
        print(f"  ok  {a['label']:<22} ${a['priceInputPer1M']}/{a['priceOutputPer1M']}{cached}")
        applied_a += 1

    # ---------------- meta
    meta["lastVerified"] = patch["date"]
    meta["previousLastVerified"] = prev_verified
    meta["revisionNote"] = (
        f"Updated {patch['date']}: {applied_a} models added, {applied_c} field corrections. "
        f"Per-model sources are listed in the repository's pricing-patch files. "
        f"Cite this date, not the old one."
    )
    revisions = meta.setdefault("revisions", [])
    revisions.append(
        {
            "date": patch["date"],
            "added": applied_a,
            "corrected": applied_c,
            "patchFile": Path(sys.argv[1]).name,
        }
    )
    # meta.count if present
    if "count" in meta:
        meta["count"] = len(data["models"])

    # ---------------- write
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.copy2(OUT, ROOT / "_baseline" / "data" / "model-prices.prev.json")
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---------------- report
    print(f"\n{'=' * 58}")
    print(f"corrections applied : {applied_c}   refused/skipped: {skipped_c}")
    print(f"models added        : {applied_a}   skipped: {skipped_a}")
    print(f"total models        : {len(data['models'])}  (was {len(data['models']) - applied_a})")
    print(f"lastVerified        : {prev_verified} -> {patch['date']}")
    print(f"written             : {OUT}")

    flagged = patch.get("flagged_not_changed", [])
    if flagged:
        print(f"\nneeds your verification ({len(flagged)}):")
        for f in flagged:
            print(f"  - {f['id']}: {f['status']}")

    print("\nnext:  python build.py  &&  python wire_homepage.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
