#!/usr/bin/env python3
"""
Fix stale claims in the outreach copy.

Two defects, both of which would have shipped:

  1. Model count frozen at 81 while the dataset is now 89. A link that says
     "81 models" on a page showing 89 is a self-inflicted credibility hit.

  2. "Anthropic cut Luna-tier pricing 80%" — GPT-5.6 Luna is an OpenAI model.
     Anthropic ships no "Luna" tier at all; the sentence bled over from the
     GPT-5.6 Sol sentence right before it.

Idempotent: running twice changes nothing the second time.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

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

# Current model count, read from the shipping JSON so this can never drift again.
data = ROOT / "site" / "data" / "model-prices.json"
CURRENT = len(__import__("json").loads(data.read_text(encoding="utf-8"))["models"])

# (pattern, replacement, label)
FIXES = [
    (
        re.compile(r"\b(?:70|81|84)\s+(models|model)\b", re.I),
        rf"{CURRENT} \1",
        "stale model count",
    ),
    (
        re.compile(r"\b(?:70|81|84)\s*个模型"),
        f"{CURRENT}个模型",
        "stale model count (zh)",
    ),
    (
        re.compile(r"Anthropic cut Luna-tier pricing 80%"),
        "OpenAI cut GPT-5.6 Luna pricing 80%",
        "wrong vendor on the Luna cut",
    ),
]

print(f"current model count in site/data: {CURRENT}\n")
total = 0
for path in TARGETS:
    if not path.exists():
        print(f"  skip    {path.name} (not found)")
        continue
    original = path.read_text(encoding="utf-8")
    text = original
    hits = []
    for rx, repl, label in FIXES:
        text, n = rx.subn(repl, text)
        if n:
            hits.append(f"{label} x{n}")
    if text == original:
        print(f"  clean   {path.name}")
        continue
    path.write_text(text, encoding="utf-8")
    total += sum(1 for _ in hits)
    print(f"  fixed   {path.name:<32} {', '.join(hits)}")

print(f"\nfiles changed: {total}")

# ---- sweep for anything the regexes above would have missed
print("\nresidual scan (should print nothing):")
BAD = re.compile(r"\b(?:70|81|84)\s+models?\b|个模型|Anthropic cut Luna", re.I)
clean = True
for path in TARGETS:
    if not path.exists():
        continue
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if BAD.search(line):
            print(f"  {path.name}:{i}  {line.strip()[:90]}")
            clean = False
if clean:
    print("  nothing left")