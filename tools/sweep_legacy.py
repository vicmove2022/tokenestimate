#!/usr/bin/env python3
"""
Sweep legacy pages for stale model counts and stale verification dates.

apply_patch.py + build.py regenerate the /models and /providers trees, but the
twelve hand-written pages (api.html, embed.html, the seven original calculator
articles, the two blog posts) still quote the old model count and the old
lastVerified date. Those are factual errors on indexed URLs, so they get fixed
here rather than left to rot.

Prints every substitution it makes. Idempotent.

Usage:  python sweep_legacy.py [--dry]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
DATA = SITE / "data" / "model-prices.json"

DRY = "--dry" in sys.argv

# Generated trees are already correct; never touch them.
GENERATED = re.compile(r"(^|[\\/])(models|providers)[\\/]")

# (pattern, replacement) — ordered, longest first so "70+ models" wins over "70 models".
# Counts are replaced with the exact figure rather than an "n+" form, so the
# number on the page always equals len(models).
COUNT_RULES = [
    (r"\b\d+\+ Models\b", "{n} Models"),
    (r"\b\d+\+ models\b", "{n} models"),
    (r"\b\d+\+ AI models\b", "{n} AI models"),
    (r"\b\d+ AI models\b", "{n} AI models"),
    (r"\b\d+\+ LLMs\b", "{n} LLMs"),
    (r"\b\d+ LLMs\b", "{n} LLMs"),
    (r"\b\d+ models\b", "{n} models"),
    (r"\b\d+-model\b", "{n}-model"),
    (r"\b\d+-model pricing\b", "{n}-model pricing"),
    (r"\b\d+ provider groups\b", "{p} provider groups"),
    (r"\b\d+ providers\b", "{p} providers"),
]

# Dates, keyed on the old value so we only ever move forward.
DATE_RULES = [
    (r"last verified 2026-09-30", "last verified {d}"),
    (r"Last verified 2026-09-30", "Last verified {d}"),
    (r"verified 2026-09-30", "verified {d}"),
    (r"2026-09-30", "{d}"),
    (r"updated Aug 2026", "updated {mon} 2026"),
]


def vendor_count(models):
    """Mirror build.py: the 'US & EU' bucket is split into real vendors."""
    override = {"grok-4.1": "xAI", "llama-4": "Meta", "mistral-large": "Mistral AI", "amazon-nova-pro": "Amazon"}
    slugs = set()
    for m in models:
        v = override.get(m["id"], m["provider"])
        slugs.add(re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-"))
    return len(slugs)


def month_name(iso):
    return [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ][int(iso.split("-")[1]) - 1]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    n = len(data["models"])
    d = data["_meta"]["lastVerified"]
    mon = month_name(d)

    p = vendor_count(data["models"])
    fmt = {"n": n, "d": d, "mon": mon, "p": p}

    targets = [
        p
        for p in sorted(SITE.rglob("*.html"))
        if not GENERATED.search(str(p.relative_to(SITE)))
    ]

    total = 0
    for p in targets:
        rel = p.relative_to(SITE).as_posix()
        if rel == "index.html":
            continue  # handled by sync_homepage.py
        text = original = p.read_text(encoding="utf-8")
        hits = []
        for pat, rep in COUNT_RULES + DATE_RULES:
            text, k = re.subn(pat, rep.format(**fmt), text)
            if k:
                hits.append(f"{k}x {pat}")
        if text != original:
            total += len(hits)
            print(f"\n{rel}")
            for h in hits:
                print(f"    {h}")
            if not DRY:
                p.write_text(text, encoding="utf-8")

    print(f"\n{'would change' if DRY else 'changed'}: {total} substitution group(s) across {len(targets)} legacy page(s)")
    if DRY:
        print("re-run without --dry to apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



