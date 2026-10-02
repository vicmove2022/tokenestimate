#!/usr/bin/env python3
"""
Sync the model count in the outreach copy with the shipping dataset.

Three earlier versions of this file caused real damage, all from the same root
cause: matching an arbitrary integer next to the word "models".

  1. hardcoded (70|81|84) -- could never advance past 84, so a file sitting at 89
     was reported as "clean" when it was simply out of date.
  2. a vendor guard written as `group(2).startswith("vendor")`, which is never
     true because group(2) is " vendors" with a leading space. "23 vendors" became
     "92 vendors" in seven places.
  3. no range guard, so "every 2-3 models a week" became "every 2-92 models", and
     a historical aside about "11 models" was rewritten to "92 models".

What it does now:

  * only replaces numbers in [MIN, MAX], a window a dataset size actually occupies
  * never matches `vendors`
  * negative lookbehind so a number inside a range ("2-3") is skipped
  * prints every substitution, so a wrong edit is visible before it ships

The vendor count is left alone entirely: it is a different fact and this script
has no business inferring it.

Idempotent. Safe to re-run after any pricing patch.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from vendors import slug_of

# A model count for this project is always in this window. Anything outside it is
# a different kind of number (a cadence, a historical incident, an id).
MIN, MAX = 70, 250

TARGETS = [
    ROOT / "投放文案" / "01-HN.md",
    ROOT / "投放文案" / "02-Reddit-LocalLLaMA.md",
    ROOT / "投放文案" / "03-HuggingFace.md",
    ROOT / "投放文案" / "05-Newsletter-pitch.txt",
    ROOT / "投放文案" / "06-GitHub-awesome-PR.md",
    ROOT / "外链投放包.md",
    ROOT / "automation" / "post-outreach.js",
    ROOT / "automation" / "hf-card.md",
    ROOT / "repo" / "README.md",
]

data = json.loads((ROOT / "site" / "data" / "model-prices.json").read_text(encoding="utf-8"))
CURRENT = len(data["models"])
# Count vendor slugs, not `provider` values. `provider` is not a vendor: it also
# carries API product lines and used to carry a hosting region, so counting it
# reported 22 vendors for a site that publishes 23 pages.
VENDORS = len({slug_of(m["vendor"]) for m in data["models"]})

# (?<![\d\u2013\u2014-]) keeps "2-3" and "gpt-4" style prefixes out of the match.
RX_EN = re.compile(r"(?<![\d\u2013\u2014-])(\d+)(\s+models?\b)(?!\s*(?:of|from|added|were|is)\b)", re.I)
RX_ZH = re.compile(r"(?<![\d\u2013\u2014-])(\d+)(\s*个模型)")

audit = []


def in_window(n):
    return MIN <= n <= MAX


def sub_en(m):
    n = int(m.group(1))
    if n == CURRENT or not in_window(n):
        return m.group(0)
    audit.append(f"{m.group(0)!r} -> {CURRENT}{m.group(2)}")
    return f"{CURRENT}{m.group(2)}"


def sub_zh(m):
    n = int(m.group(1))
    if n == CURRENT or not in_window(n):
        return m.group(0)
    audit.append(f"{m.group(0)!r} -> {CURRENT}{m.group(2)}")
    return f"{CURRENT}{m.group(2)}"


print(f"dataset: {CURRENT} models, {VENDORS} vendors")
print(f"replaceable numbers: {MIN}-{MAX} (vendor counts are never touched)\n")

changed = 0
for path in TARGETS:
    if not path.exists():
        print(f"  skip     {path.name} (not found)")
        continue
    original = path.read_text(encoding="utf-8")
    text = RX_ZH.sub(sub_zh, RX_EN.sub(sub_en, original))
    if text == original:
        print(f"  ok       {path.name}")
        continue
    path.write_text(text, encoding="utf-8")
    changed += 1
    print(f"  updated  {path.name}")

if audit:
    print(f"\n{len(audit)} substitution(s):")
    for a in audit:
        print(f"  {a}")
else:
    print("\nno substitutions needed")

# ---- report anything still inconsistent, without guessing what it should be
print("\nresidual check:")
problems = 0
for path in TARGETS:
    if not path.exists():
        continue
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for rx, tag in ((RX_EN, "models"), (RX_ZH, "个模型")):
            for m in rx.finditer(line):
                if int(m.group(1)) != CURRENT and in_window(int(m.group(1))):
                    print(f"  {path.name}:{i}  {m.group(0)!r} != {CURRENT}")
                    problems += 1
print("  none" if not problems else f"  {problems} to look at")
print(f"\nfiles written: {changed}")