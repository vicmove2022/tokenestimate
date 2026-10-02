#!/usr/bin/env python3
"""
Wire the new /models/ and /providers/ trees into the existing homepage,
and refresh robots.txt + llms.txt.

The homepage is the highest-authority URL on the site. New pages that are
only reachable from sitemap.xml get discovered slowly and inherit little
internal link equity. Linking them from the homepage is the cheapest
distribution move available.

Idempotent: safe to re-run.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
INDEX = SITE / "index.html"
ROBOTS = SITE / "robots.txt"
LLMS = SITE / "llms.txt"

NAV_ANCHOR = '<a href="#faq">FAQ</a>'
NAV_NEW = (
    '<a href="/models/">All models</a>\n'
    '        <a href="/providers/">Providers</a>\n'
    '        <a href="#faq">FAQ</a>'
)

# Inserted right before the Guides section closes out the calculators grid.
TAIL_ANCHOR = """          <a class="card" href="qwen-token-counter.html">
            <h3><span class="emoji">Q</span>Qwen calculator</h3>
            <p>Qwen Max / Plus / Turbo counts and list prices.</p>
          </a>
        </div>
      </div>
    </section>"""

TAIL_NEW = """          <a class="card" href="qwen-token-counter.html">
            <h3><span class="emoji">Q</span>Qwen calculator</h3>
            <p>Qwen Max / Plus / Turbo counts and list prices.</p>
          </a>
          <a class="card" href="/models/">
            <h3><span class="emoji">&#9634;</span>Every model</h3>
            <p>All 70 models &#8212; a dedicated calculator preselected to each one.</p>
          </a>
          <a class="card" href="/providers/">
            <h3><span class="emoji">&#9635;</span>By provider</h3>
            <p>List pricing for 23 vendors side by side, with rates per 1M tokens.</p>
          </a>
        </div>
        <p style="margin-top:14px">
          Looking for a specific model? <a href="/models/">Browse all 70 model calculators</a> or
          <a href="/providers/">compare every provider's pricing</a>. Each page opens with that model
          already selected.
        </p>
      </div>
    </section>"""

# Below the start CTA, before the footer.
START_ANCHOR = '<p><a href="#tool">Try the calculator</a></p>'
START_NEW = (
    '<p><a href="#tool">Try the calculator</a></p>\n'
    '        <p style="margin-top:10px">'
    'Jump straight to a model: <a href="/models/gpt-5/">GPT-5</a> · '
    '<a href="/models/claude-opus-5-5/">Claude Opus</a> · '
    '<a href="/models/gemini-3-1-pro/">Gemini 3.1 Pro</a> · '
    '<a href="/models/deepseek-v4-pro/">DeepSeek V4</a> · '
    '<a href="/models/qwen3-max/">Qwen3</a> · '
    '<a href="/models/grok-4-1/">Grok</a> · '
    '<a href="/models/llama-4/">Llama 4</a></p>'
)

ROBOTS_FULL = """User-agent: *
Allow: /
Disallow: /*?
Disallow: /index.html

Sitemap: https://tokenestimate.com/sitemap.xml

# AI crawlers are explicitly welcome - all content is public and server-rendered.
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: DuckAssistBot
Allow: /

User-agent: AppleBot
Allow: /
"""


def patch(path, pairs, label):
    if not path.exists():
        print(f"  skip  {label}: {path.name} not found")
        return 0
    t = path.read_text(encoding="utf-8")
    n = 0
    for anchor, new in pairs:
        if new in t:
            continue
        if anchor not in t:
            print(f"  WARN  {label}: anchor not found -> {anchor[:60]!r}")
            continue
        t = t.replace(anchor, new, 1)
        n += 1
    if n:
        path.write_text(t, encoding="utf-8")
    print(f"  {label}: {n} patch(es) applied")
    return n


def main():
    print("patching:")
    write_robots()
    patch(INDEX, [(NAV_ANCHOR, NAV_NEW), (TAIL_ANCHOR, TAIL_NEW), (START_ANCHOR, START_NEW)], "index.html")

    # llms.txt: point at the full-text version and the new hubs.
    if LLMS.exists():
        t = LLMS.read_text(encoding="utf-8")
        add = []
        if "/models/" not in t:
            add.append("- [Every model calculator](https://tokenestimate.com/models/)")
        if "/providers/" not in t:
            add.append("- [Pricing by provider](https://tokenestimate.com/providers/)")
        if "llms-full.txt" not in t:
            add.append("")
            add.append("Full-text version of this data: https://tokenestimate.com/llms-full.txt")
            add.append("Machine-readable pricing: https://tokenestimate.com/data/model-prices.json")
        if add:
            lines = t.splitlines()
            i = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
            lines[i:i] = add
            LLMS.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            print(f"  llms.txt: appended {len(add)} line(s)")

    idx = INDEX.read_text(encoding="utf-8")
    print()
    print("homepage internal links now pointing at new trees:")
    for m in sorted(set(re.findall(r'href="(/models/[^"]*|/providers/[^"]*)"', idx))):
        print(f"  {m}")




def write_robots():
    """Overwrite robots.txt wholesale.

    A write, not patch(). The earlier version passed an empty anchor to patch(),
    and str.replace("", new, 1) INSERTS at position 0 instead of replacing,
    which silently duplicated the entire file on every run. That shipped once.
    """
    ROBOTS.parent.mkdir(parents=True, exist_ok=True)
    ROBOTS.write_text(ROBOTS_FULL, encoding="utf-8")
    text = ROBOTS.read_text(encoding="utf-8")
    wildcards = len(re.findall(r"(?m)^User-agent: \*", text))
    assert wildcards == 1, "robots.txt has %d wildcard groups, expected 1" % wildcards
    assert text.count("Sitemap:") == 1, "expected exactly one Sitemap line"
    assert "\ufffd" not in text, "robots.txt contains a replacement character"
    print("  robots.txt: %d bytes, single wildcard group, one Sitemap line, no mojibake"
          % len(text.encode("utf-8")))


if __name__ == "__main__":
    main()