#!/usr/bin/env python3
"""
TokenCalc SEO page generator.

Reads data/model-prices.json and emits:
  site/models/<slug>/index.html    one page per model (real tool page, calculator embedded & preselected)
  site/providers/<slug>/index.html one comparison page per provider
  site/models/index.html           model hub
  site/providers/index.html        provider hub
  site/sitemap.xml                 every URL, with lastmod from _meta.lastVerified
  site/llms-full.txt               full-text version for AI crawlers
  site/404.html                    real 404 with internal search-links

Re-run this whenever you refresh prices. It is the freshness loop.

Usage:  python build.py
"""

import json
import shutil
import re
import html
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# Prefer the patched, shipping copy. Fall back to the mirrored baseline on a
# clean checkout. This is what makes the freshness loop a one-liner:
#   python apply_patch.py <patch>.json && python build.py
PATCHED = SITE / "data" / "model-prices.json"
BASELINE = ROOT / "_baseline" / "data" / "model-prices.json"
DATA = PATCHED if PATCHED.exists() else BASELINE

SITE_URL = "https://tokenestimate.com"
UMAMI = "8f1fd21d-3670-41e7-adf4-20d24de46fd4"

# Dates are read from _meta.lastVerified so a page can never disagree with the
# data file it was generated from. Set by set_dates() from main().
VERIFIED = ""
VERIFIED_HUMAN = ""
human = ""
total = 0


def _month(name):
    return [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ][int(name) - 1]


def set_dates(iso):
    """Derive both the ISO and human-readable verification dates."""
    global VERIFIED, VERIFIED_HUMAN, human
    VERIFIED = iso
    y, m, d = (int(x) for x in iso.split("-"))
    VERIFIED_HUMAN = f"{d} {_month(m)} {y}"
    human = VERIFIED_HUMAN

# Vendor resolution lives in vendors.py so build.py, apply_patch.py and
# verify.py cannot drift apart. It used to be a private copy here, which meant
# the site and the published dataset could disagree about what a vendor is --
# and they did, because `provider` in the JSON carries product lines and a
# hosting region as well as companies.
from vendors import VENDOR_BY_ID_PREFIX as _PREFIXES, VENDOR_SLUG


def vendor_of(m):
    pid = str(m.get("id", "")).lower()
    for prefix, vendor in _PREFIXES:
        if pid.startswith(prefix):
            return vendor
    provider = m.get("provider", "")
    if provider in ("US & EU", "Other", "", None):
        return "Unattributed"
    return provider

# VENDOR_SLUG is imported from vendors.py above; it used to be duplicated here,
# which is how the site and the dataset ended up disagreeing. VENDOR_DISPLAY
# stays local: it is presentation, not resolution.

VENDOR_DISPLAY = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "xai": "xAI",
    "meta": "Meta",
    "mistral": "Mistral AI",
    "amazon": "Amazon",
    "deepseek": "DeepSeek (深度求索)",
    "qwen": "Alibaba Qwen (阿里通义)",
    "zhipu": "Zhipu GLM (智谱)",
    "moonshot": "Moonshot Kimi (月之暗面)",
    "doubao": "ByteDance Doubao (火山引擎)",
    "baidu": "Baidu ERNIE (百度)",
    "tencent": "Tencent Hunyuan (腾讯)",
    "iflytek": "iFlytek Spark (讯飞星火)",
    "minimax": "MiniMax (稀宇科技)",
    "01ai": "01.AI (零一万物)",
    "stepfun": "StepFun (阶跃星辰)",
    "sensetime": "SenseTime (商汤)",
    "baichuan": "Baichuan (百川智能)",
    "kunlun": "Kunlun (昆仑万维)",
    "xiaomi": "Xiaomi MiMo (小米)",
    "huawei": "Huawei PanGu (华为云)",
}

VENDOR_NOTE = {
    "openai": "OpenAI counts every request with the tiktoken Byte-Pair-Encoding tokenizer, which is why every OpenAI model on TokenCalc returns an exact count rather than an estimate.",
    "anthropic": "Anthropic does not publish a public tokenizer, so TokenCalc estimates Claude counts from character ratios calibrated against Anthropic's published benchmarks.",
    "google": "Google's Gemini tokenizer is not public. TokenCalc estimates Gemini counts and shows them alongside the exact OpenAI counts so you can see the gap.",
    "deepseek": "DeepSeek does not expose its tokenizer. TokenCalc estimates from character ratios calibrated on Chinese and English prompts.",
    "qwen": "Alibaba does not publish Qwen's tokenizer. TokenCalc estimates from character ratios, which run wide on mixed Chinese-English prompts.",
    "zhipu": "Zhipu does not publish GLM's tokenizer. TokenCalc estimates from calibrated character ratios.",
    "moonshot": "Moonshot does not publish Kimi's tokenizer. TokenCalc estimates from calibrated character ratios.",
    "doubao": "Volcano Engine does not publish Doubao's tokenizer. TokenCalc estimates from calibrated character ratios.",
}

# Cheap-in / cheap-out estimates differ by tokenizer family; keep it honest and coarse.
CHARS_PER_TOKEN = {"estimate": 3.6, "tiktoken:o200k_base": 4.0, "tiktoken:cl100k_base": 4.0}


def esc(s):
    return html.escape(str(s), quote=True)


def model_slug(mid):
    return re.sub(r"[^a-z0-9]+", "-", mid.lower()).strip("-")




def vendor_slug(m):
    v = vendor_of(m)
    if v in VENDOR_SLUG:
        return VENDOR_SLUG[v]
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")


def is_exact(m):
    return str(m.get("tokenizer", "")).startswith("tiktoken")


def ctx_tokens(m):
    """Parse '400K' / '1M' / '2M' / '262K' into an int. Returns None if absent."""
    c = str(m.get("contextWindow") or "").strip()
    if not c or c in ("-", "–", "N/A"):
        return None
    mult = {"K": 1_000, "M": 1_000_000}
    mm = re.match(r"^([\d.]+)\s*([KM])$", c, re.I)
    if not mm:
        return None
    return int(float(mm.group(1)) * mult[mm.group(2).upper()])


def money(v):
    if v is None:
        return "—"
    v = float(v)
    if v == 0:
        return "Free"
    if v >= 1:
        return "${:,.2f}".format(v)
    s = "${:,.4f}".format(v)
    return s.rstrip("0").rstrip(".") if s.count(".") == 1 and len(s.split(".")[1]) > 3 else s


def fmt_int(n):
    return "{:,}".format(int(n))


def cjk_note(m):
    """CJK-heavy tokenizers run far denser than English ones."""
    return is_exact(m)


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="keywords" content="{kw}">
  <meta name="author" content="TokenCalc">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">

  <link rel="canonical" href="{url}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="TokenCalc">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE_URL}/og-cover.png">
  <meta property="og:locale" content="en_US">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{SITE_URL}/og-cover.png">

  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="stylesheet" href="/css/style.css">

{schema}
  <style>
    .article {{ max-width: 820px; margin: 24px auto 60px; padding: 0 26px; }}
    .article h1 {{ font-size: 2rem; line-height: 1.25; margin-bottom: 10px; }}
    .article h2 {{ font-size: 1.4rem; margin: 36px 0 12px; }}
    .article h3 {{ font-size: 1.05rem; margin: 22px 0 6px; }}
    .article p, .article li {{ color: var(--text-dim); font-size: .98rem; }}
    .article ul, .article ol {{ margin: 10px 0 14px 22px; }}
    .article li {{ margin-bottom: 6px; }}
    .article table {{ width: 100%; border-collapse: collapse; margin: 16px 0 22px; font-size: .9rem; }}
    .article th, .article td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
    .article th {{ color: var(--text); font-weight: 600; }}
    .article .meta {{ color: var(--text-faint); font-size: .85rem; margin-bottom: 24px; }}
    .tag {{ font-size: .68rem; }}
    code {{ font-family: var(--mono); background: var(--bg-input); border: 1px solid var(--border); border-radius: 6px; padding: 1px 6px; font-size: .88em; }}
    .cta {{ background: var(--bg-soft); border: 1px solid var(--border-soft); border-radius: var(--radius-sm); padding: 18px 22px; margin: 26px 0; }}
    .cta a {{ font-weight: 600; }}
    .breadcrumb {{ font-size: .82rem; color: var(--text-faint); margin-bottom: 16px; }}
    .calc {{ margin: 26px 0 8px; }}
    .calc iframe {{ display: block; width: 100%; height: 660px; border: 1px solid #dfe6f1; border-radius: 16px; background: #fff; }}
    .exact {{ color: #16a34a; font-weight: 600; }}
    .approx {{ color: #b45309; font-weight: 600; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 18px 0 26px; }}
    .stat {{ background: var(--bg-soft); border: 1px solid var(--border-soft); border-radius: var(--radius-sm); padding: 14px 16px; }}
    .stat b {{ display: block; font-size: 1.15rem; color: var(--text); }}
    .stat span {{ font-size: .78rem; color: var(--text-faint); }}
    .note {{ background: var(--bg-soft); border-left: 3px solid var(--accent); border-radius: var(--radius-sm); padding: 13px 16px; margin: 18px 0 22px; font-size: .92rem; color: var(--text-dim); }}
.note b {{ color: var(--text); }}
.links {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 26px; }}
    .links a {{ font-size: .82rem; padding: 5px 11px; border: 1px solid var(--border); border-radius: 999px; text-decoration: none; }}
  </style>
  <script defer src="https://cloud.umami.is/script.js" data-website-id="{UMAMI}"></script>
</head>
<body>
  <div class="bg-grid" aria-hidden="true"></div>
  <header class="site-header">
    <div class="container">
      <a class="brand" href="/index.html" aria-label="AI Token Calculator home">
        <svg viewBox="0 0 24 24" fill="none" stroke="#4f8cff" stroke-width="2" aria-hidden="true">
          <path d="M12 2 4 6v6c0 5 3.4 9.1 8 10 4.6-.9 8-5 8-10V6l-8-4Z"/>
          <path d="m9 12 2 2 4-4" stroke="#22d3ee" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Token<em>Calc</em></span>
      </a>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="/index.html#tool">Calculator</a>
        <a href="/models/">Models</a>
        <a href="/providers/">Providers</a>
        <a href="/api.html">Pricing data</a>
      </nav>
    </div>
  </header>

  <main>
    <div class="container">
      <article class="article">
"""

FOOT = """      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        List prices last verified {human}.<br>
        <a href="/privacy.html">Privacy Policy</a> · <a href="/models/">All models</a> · <a href="/api.html">Pricing JSON</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""


def head_fmt(**kw):
    kw.setdefault("SITE_URL", SITE_URL)
    kw.setdefault("UMAMI", UMAMI)
    return HEAD.format(**kw)


def crumbs_json(path, name):
    trail = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": "Models", "item": SITE_URL + "/models/"},
    ]
    trail.append({"@type": "ListItem", "position": 3, "name": name})
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": trail,
    }


def dump_schema(*blocks):
    out = []
    for b in blocks:
        out.append('  <script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=2) + "\n  </script>")
    return "\n".join(out)


# --------------------------------------------------------------------------- model page


def build_model_page(m, models, vgroups):
    label = m["label"]
    mid = m["id"]
    slug = model_slug(mid)
    url = f"{SITE_URL}/models/{slug}/"
    vslug = vendor_slug(m)
    vdisp = VENDOR_DISPLAY.get(vslug, vendor_of(m))
    exact = is_exact(m)
    tok = m.get("tokenizer", "estimate")
    ct = ctx_tokens(m)
    pin = m.get("priceInputPer1M")
    pout = m.get("priceOutputPer1M")
    free = pin == 0
    cpt = CHARS_PER_TOKEN.get(tok, 3.6)

    if exact:
        title = f"{label} Token Calculator — Count {label} Tokens & API Cost (2026)"
        desc = (
            f"Free {label} token calculator. Count {label} tokens with the official "
            f"{tok.split(':')[1]} tokenizer and see exact API cost at {money(pin)}/1M input "
            f"and {money(pout)}/1M output. Runs in your browser — nothing is uploaded."
        )
        kw = f"{label} token calculator, {label} token counter, count {label} tokens, {label} API cost, {label} pricing, tiktoken {label}"
    else:
        title = f"{label} Token Calculator — {label} Token Count & API Cost (2026)"
        desc = (
            f"Free {label} token calculator for {vdisp}. Estimate {label} token counts and "
            f"API cost at {money(pin)}/1M input and {money(pout)}/1M output. 100% in-browser, "
            f"no upload, no sign-up. Prices verified {human}."
        )
        kw = f"{label} token calculator, {label} token counter, {label} tokens, {label} API pricing, {vdisp} pricing"

    # ---- stat tiles
    tiles = []
    if ct:
        tiles.append((esc(m["contextWindow"] + " tokens"), "context window"))
        tiles.append((fmt_int(ct), "max input tokens"))
        tiles.append((esc(f"~{fmt_int(ct / 1.3)}"), "≈ English words that fit"))
    if pin is not None:
        tiles.append((esc(money(pin)), "per 1M input tokens"))
    if pout is not None:
        tiles.append((esc(money(pout)), "per 1M output tokens"))
    tiles.append(("Exact" if exact else "±5–10%", "count accuracy"))
    tiles_html = "\n".join(
        f'        <div class="stat"><b>{b}</b><span>{s}</span></div>' for b, s in tiles
    )

    # ---- provider comparison table (real sibling data)
    sibs = [x for x in vgroups.get(vslug, []) if x["id"] != mid]
    rows = []
    me = (
        f"<tr><td><strong>{esc(label)}</strong></td>"
        f"<td><span class=\"tag\">{esc(tok.split(':')[-1] if exact else 'estimate')}</span></td>"
        f"<td>{esc(m.get('contextWindow') or '—')}</td>"
        f"<td>{esc(money(pin))}</td><td>{esc(money(pout))}</td></tr>"
    )
    for s in sibs:
        rows.append(
            f"<tr><td><a href=\"/models/{model_slug(s['id'])}/\">{esc(s['label'])}</a></td>"
            f"<td><span class=\"tag\">{'cl100k' if 'cl100k' in s.get('tokenizer','') else ('o200k' if exact else 'estimate')}</span></td>"
            f"<td>{esc(s.get('contextWindow') or '—')}</td>"
            f"<td>{esc(money(s.get('priceInputPer1M')))}</td>"
            f"<td>{esc(money(s.get('priceOutputPer1M')))}</td></tr>"
        )
    sib_table = (
        "        <table>\n"
        "          <thead><tr><th>Model</th><th>Tokenizer</th><th>Context</th>"
        f"<th>Input / 1M</th><th>Output / 1M</th></tr></thead>\n"
        f"          <tbody>\n            {me}\n" + "\n".join("            " + r for r in rows) + "\n          </tbody>\n        </table>\n"
        if rows
        else ""
    )

    # ---- cost scenarios from the real rate
    scen = []
    for n, label2 in ((1_000, "1K"), (10_000, "10K"), (100_000, "100K"), (1_000_000, "1M")):
        ci = None if pin is None else n / 1e6 * pin
        co = None if pout is None else n / 1e6 * pout
        scen.append(
            f"<tr><td>{label2} tokens</td>"
            f"<td>≈ {fmt_int(n / 1.3)} words</td>"
            f"<td>{money(0 if ci is None else round(ci, 6))}</td>"
            f"<td>{money(0 if co is None else round(co, 6))}</td></tr>"
        )
    scen_table = (
        "        <table>\n"
        "          <thead><tr><th>Volume</th><th>Approx. size</th>"
        f"<th>Input cost</th><th>Output cost</th></tr></thead>\n"
        "          <tbody>\n            "
        + "\n            ".join(scen)
        + "\n          </tbody>\n        </table>\n"
    )

    # ---- sibling quick links
    link_html = "\n".join(
        f'        <a href="/models/{model_slug(s["id"])}/">{esc(s["label"])}</a>' for s in sibs[:12]
    )

    # ---- accuracy section, honest per tokenizer
    if exact:
        acc = (
            f"The count on this page is <span class=\"exact\">exact</span>. {esc(label)} is billed by "
            f"OpenAI using the <code>{esc(tok.split(':')[1])}</code> Byte-Pair-Encoding tokenizer, and "
            "TokenCalc runs that same tokenizer in your browser — the count you see is the count you are "
            "charged. There is no rounding and no estimate."
        )
    else:
        acc = (
            f"{esc(vdisp)} does not publish a public tokenizer, so this page reports "
            f"<span class=\"approx\">an estimate</span> — accurate to roughly 5–10% on English text and "
            f"widening on code or mixed Chinese-English prompts. Treat it as a budgeting number, not an "
            f"invoice number. If you need invoice-grade counts, count with the exact OpenAI tokenizer on the "
            f"<a href=\"/index.html#tool\">main calculator</a> and read the gap as your margin of safety."
        )

    # ---- FAQs, grounded in this model's real numbers
    ctx_txt = f"{esc(m.get('contextWindow'))} tokens" if ct else "its documented maximum"
    faqs = [
        (
            f"How many tokens is a word in {label}?",
            f"About 1.3 tokens per English word for {label} — roughly {cpt:.1f} characters per token. "
            f"Code and CJK text tokenize denser, so a {ctx_txt} window holds fewer words than a prose "
            f"estimate suggests.",
        ),
        (
            f"What does {label} cost per 1M tokens?",
            (
                f"{label} is listed at {money(pin)} per 1M input tokens and {money(pout)} per 1M output "
                f"tokens as of {human}."
                if pin
                else f"{label} is currently free on {vdisp}, at 0 per 1M input and output tokens."
            ),
        ),
        (
            f"What is the {label} context window?",
            (
                f"{label} accepts up to {ctx_txt} of input."
                if ct
                else f"{label} has no widely published fixed context window — check {vdisp}'s current docs."
            ),
        ),
        (
            f"Is the {label} token count on this page exact?",
            (
                f"Yes. TokenCalc runs the official {tok.split(':')[1]} tokenizer, the same one {vdisp} bills with."
                if exact
                else f"No. {vdisp} does not expose its tokenizer, so this is a calibrated estimate at 5–10% accuracy."
            ),
        ),
        (
            f"Does this {label} calculator upload my text?",
            "No. Tokenization runs entirely in your browser over JavaScript. Your text is never sent to "
            "any server, which is why the tool works with client code, unreleased prompts and internal data.",
        ),
    ]
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }
    faq_html = "\n".join(
        f"        <h3>{esc(q)}</h3>\n        <p>{a}</p>" for q, a in faqs
    )

    app_schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": f"{label} Token Calculator",
        "url": url,
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "description": desc,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": {"@type": "Organization", "name": "TokenCalc"},
    }

    intro = (
        f"The <strong>{esc(label)} token calculator</strong> below counts {esc(label)} tokens and prices "
        f"them at {esc(vdisp)}'s published rates — {esc(money(pin))} per 1M input tokens and "
        f"{esc(money(pout))} per 1M output tokens, last verified {human}. "
    )
    if exact:
        intro += (
            f"Because {esc(label)} is billed with OpenAI's <code>{esc(tok.split(':')[1])}</code> tokenizer, "
            f"the number here is <span class=\"exact\">exact</span>, not an estimate. Paste a prompt, a file "
            "or a codebase and read the cost before you send it."
        )
    else:
        intro += (
            f"{esc(vdisp)} does not publish its tokenizer, so the count is a calibrated estimate — stated "
            f"plainly on every table here rather than dressed up as exact. Use it to budget and to compare "
            f"{esc(label)} against other models."
        )

    ctx_para = ""
    # Short notes ("reasoning", "agentic", "cheapest") already appear as the
    # suffix on the calculator's <select> option, so repeating them on the page
    # is noise. Long notes are editorial and carry real caveats — a promotional
    # price with an expiry date, a tokenizer change that inflates real bills —
    # so those get a visible callout instead of being buried.
    note = str(m.get("note") or "").strip()
    if len(note) > 60:
        note_callout = (
            '        <div class="note"><b>Worth knowing.</b> '
            + esc(note)
            + "</div>\n"
        )
    else:
        note_callout = ""

    if ct:
        ctx_para = (
            f"## What fits in the {esc(label)} context window\n\n"
            f"{esc(label)} accepts **{ctx_txt}**. At roughly 1.3 tokens per English word that is about "
            f"**{fmt_int(ct / 1.3)} words**, or roughly "
            f"**{fmt_int(ct * cpt)} characters** of prose. Code and CJK text consume the budget faster: a "
            f"source file or a Chinese document of the same visible length can run 30–60% more tokens, so "
            f"leave headroom rather than budgeting to the exact ceiling."
        ).replace("\n\n", "\n        ")

    body = f"""        <div class="breadcrumb"><a href="/">Home</a> / <a href="/models/">Models</a> / {esc(label)}</div>
        <h1>{esc(label)} Token Calculator</h1>
        <p class="meta">{esc(vdisp)} · {esc(tok.split(':')[-1] if exact else 'calibrated estimate')} · prices verified {human}</p>

<p>{intro}</p>
{note_callout}
        <div class="calc">
          <iframe src="/?embed=1&amp;model={esc(mid)}" title="{esc(label)} token calculator" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
        <p><a href="/?model={esc(mid)}#tool">Open the full {esc(label)} counter with the whole pricing table →</a></p>

        <div class="grid">
{tiles_html}
        </div>

        <h2>{esc(label)} token cost at a glance</h2>
{scen_table}
        <p>Figures are list prices per 1M tokens, verified {human}. Enterprise contracts and volume tiers
        differ — edit the rates in the calculator if your deal is not list.</p>

        <h2>How accurate is the {esc(label)} count?</h2>
        <p>{acc}</p>

{ctx_para}

        <h2>{esc(label)} pricing against the rest of {esc(vdisp)}</h2>
{sib_table}
        <p><a href="/providers/{esc(vslug)}/">All {esc(vdisp)} models and rates →</a></p>

        <h2>More {esc(vdisp)} calculators</h2>
        <div class="links">
{link_html}
        </div>
        <p>Or browse <a href="/models/">all {total} model calculators</a> and
        <a href="/providers/">every provider</a>.</p>

        <h2>{esc(label)} token FAQs</h2>
{faq_html}
      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        List prices last verified {human}.<br>
        <a href="/privacy.html">Privacy Policy</a> · <a href="/models/">All models</a> · <a href="/api.html">Pricing JSON</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""
    return url, body, app_schema, faq_schema, crumbs_json(url, label)


# --------------------------------------------------------------------------- provider page


def build_provider_page(vslug, group, models, vgroups):
    vdisp = VENDOR_DISPLAY.get(vslug, vslug)
    url = f"{SITE_URL}/providers/{vslug}/"
    note = VENDOR_NOTE.get(vslug, "")

    rows = []
    for m in group:
        rows.append(
            f"<tr><td><a href=\"/models/{model_slug(m['id'])}/\">{esc(m['label'])}</a></td>"
            f"<td><span class=\"tag\">{'cl100k' if 'cl100k' in m.get('tokenizer','') else ('o200k' if is_exact(m) else 'estimate')}</span></td>"
            f"<td>{esc(m.get('contextWindow') or '—')}</td>"
            f"<td>{esc(money(m.get('priceInputPer1M')))}</td>"
            f"<td>{esc(money(m.get('priceOutputPer1M')))}</td></tr>"
        )

    # cheapest-first ordering for the comparison blurb
    priced = [m for m in models if m.get("priceInputPer1M")]
    cheapest_in = sorted(priced, key=lambda x: x["priceInputPer1M"])[:5]
    cheapest_in_txt = ", ".join(
        f"{esc(x['label'])} at {money(x['priceInputPer1M'])}/1M" for x in cheapest_in
    )
    biggest_ctx = sorted(
        [m for m in models if ctx_tokens(m)], key=lambda x: ctx_tokens(x), reverse=True
    )[:3]
    biggest_txt = ", ".join(
        f"{esc(x['label'])} ({esc(x['contextWindow'])})" for x in biggest_ctx
    )

    faqs = [
        (
            f"How many {vdisp} models can I count tokens for?",
            f"{len(group)} on TokenCalc, each with its own page and its own preselected calculator: "
            + ", ".join(esc(m["label"]) for m in group[:8])
            + (" and more." if len(group) > 8 else "."),
        ),
        (
            f"Are {vdisp} token counts exact?",
            note or f"{vdisp} does not publish a public tokenizer, so TokenCalc estimates from calibrated "
            "character ratios at 5–10% accuracy.",
        ),
        (
            f"Which {vdisp} model is cheapest per 1M input tokens?",
            f"Among the models tracked here: {cheapest_in_txt}. Prices verified {human}.",
        ),
    ]
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }
    faq_html = "\n".join(f"        <h3>{esc(q)}</h3>\n        <p>{a}</p>" for q, a in faqs)

    table_schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"{vdisp} model token pricing",
        "description": f"Input and output price per 1M tokens for {len(group)} {vdisp} models, "
        f"verified {human}.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "creator": {"@type": "Organization", "name": "TokenCalc"},
        "distribution": {
            "@type": "DataDownload",
            "contentUrl": f"{SITE_URL}/data/model-prices.json",
            "encodingFormat": "application/json",
        },
    }

    if note:
        note_html = f"        <p>{note}</p>\n"
    else:
        note_html = (
            "        <p>Every rate below is list pricing per 1M tokens, cross-checked against "
            f"{esc(vdisp)}'s published docs and re-verified on {human}. The same data is available as "
            "<a href=\"/api.html\">machine-readable JSON under CC BY 4.0</a> if you would rather not scrape it.</p>\n"
        )

    body = f"""        <div class="breadcrumb"><a href="/">Home</a> / <a href="/providers/">Providers</a> / {esc(vdisp)}</div>
        <h1>{esc(vdisp)} Pricing &amp; Token Calculator</h1>
        <p class="meta">{len(group)} models · prices verified {human}</p>

        <p>All {len(group)} {esc(vdisp)} models on one page: context windows, tokenizer behaviour and
        list price per 1M input and output tokens. Each row links to a dedicated calculator already
        preselected to that model.</p>

{note_html}
        <h2>{esc(vdisp)} model pricing table</h2>
        <table>
          <thead><tr><th>Model</th><th>Tokenizer</th><th>Context</th><th>Input / 1M</th><th>Output / 1M</th></tr></thead>
          <tbody>
{chr(10).join('            ' + r for r in rows)}
          </tbody>
        </table>

        <h2>Cheapest {esc(vdisp)} models per 1M input tokens</h2>
        <p>{cheapest_in_txt}. Output rates run several times higher than input rates on most vendors, so a
        token-heavy workflow with long generations is priced by the output column.</p>

        <h2>Largest {esc(vdisp)} context windows</h2>
        <p>{biggest_txt}. Context headroom is usually the binding constraint before price is — check it first.</p>

        <h2>Count tokens for any {esc(vdisp)} model</h2>
        <div class="calc">
          <iframe src="/?embed=1" title="{esc(vdisp)} token calculator" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
        <p>Pick the model from the dropdown, or open any row above for a page preselected to it.</p>

        <h2>{esc(vdisp)} pricing FAQs</h2>
{faq_html}
      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        List prices last verified {human}.<br>
        <a href="/privacy.html">Privacy Policy</a> · <a href="/models/">All models</a> · <a href="/api.html">Pricing JSON</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""
    return url, body, table_schema, faq_schema


# --------------------------------------------------------------------------- hubs


def build_model_hub(models, vgroups):
    url = f"{SITE_URL}/models/"
    rows = []
    for m in models:
        rows.append(
            f"<tr><td><a href=\"/models/{model_slug(m['id'])}/\">{esc(m['label'])}</a></td>"
            f"<td>{esc(VENDOR_DISPLAY.get(vendor_slug(m), vendor_of(m)))}</td>"
            f"<td><span class=\"tag\">{'exact' if is_exact(m) else 'estimate'}</span></td>"
            f"<td>{esc(m.get('contextWindow') or '—')}</td>"
            f"<td>{esc(money(m.get('priceInputPer1M')))}</td>"
            f"<td>{esc(money(m.get('priceOutputPer1M')))}</td></tr>"
        )
    body = f"""        <div class="breadcrumb"><a href="/">Home</a> / Models</div>
        <h1>All {total} AI Model Token Calculators</h1>
        <p class="meta">prices verified {human}</p>

        <p>One page per model, each with a working calculator already set to that model. OpenAI models are
        counted with the official tiktoken tokenizer and return exact counts; every other vendor is marked
        <span class="tag">estimate</span> because no public tokenizer exists to count with.</p>

        <div class="calc">
          <iframe src="/?embed=1" title="AI token calculator" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>

        <h2>Every model</h2>
        <table>
          <thead><tr><th>Model</th><th>Provider</th><th>Counting</th><th>Context</th><th>Input / 1M</th><th>Output / 1M</th></tr></thead>
          <tbody>
{chr(10).join('            ' + r for r in rows)}
          </tbody>
        </table>

        <p>Prefer to browse by vendor? <a href="/providers/">All {len(vgroups)} providers →</a></p>
      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        List prices last verified {human}.<br>
        <a href="/privacy.html">Privacy Policy</a> · <a href="/providers/">All providers</a> · <a href="/api.html">Pricing JSON</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""
    return url, body


def build_provider_hub(vgroups):
    url = f"{SITE_URL}/providers/"
    cards = []
    for vslug, group in sorted(vgroups.items(), key=lambda kv: VENDOR_DISPLAY.get(kv[0], kv[0])):
        disp = VENDOR_DISPLAY.get(vslug, vslug)
        names = ", ".join(esc(m["label"]) for m in group[:5])
        more = f" +{len(group) - 5} more" if len(group) > 5 else ""
        cards.append(
            f"        <div class=\"stat\"><b><a href=\"/providers/{esc(vslug)}/\">{esc(disp)}</a></b>"
            f"<span>{len(group)} models · {names}{esc(more)}</span></div>"
        )
    body = f"""        <div class="breadcrumb"><a href="/">Home</a> / Providers</div>
        <h1>AI API Pricing by Provider</h1>
        <p class="meta">{len(vgroups)} providers · {total} models · prices verified {human}</p>

        <p>Every vendor's list pricing in one place: input and output rate per 1M tokens, context window
        size, and whether TokenCalc can count it exactly or only estimate. Numbers verified {human}.</p>

        <h2>Providers</h2>
        <div class="grid">
{chr(10).join(cards)}
        </div>

        <h2>What these numbers mean</h2>
        <ul>
          <li><strong>List price</strong> — the public rate. Enterprise contracts, committed-use discounts
          and batch tiers are lower and are not reflected here.</li>
          <li><strong>Per 1M tokens</strong> — every vendor bills this way. Multiply by your token count
          divided by a million.</li>
          <li><strong>Output costs more</strong> — on most models the output rate is 3–8× the input rate,
          so long generations dominate the bill.</li>
          <li><strong>Context is a hard ceiling</strong> — exceeding it fails the request; it does not
          bill over. Check it before you optimise price.</li>
        </ul>

        <p>The same data is available as <a href="/api.html\">JSON under CC BY 4.0</a>.</p>
      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        List prices last verified {human}.<br>
        <a href="/models/">All models</a> · <a href="/api.html">Pricing JSON</a> · <a href="/privacy.html">Privacy Policy</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""
    return url, body


def build_404():
    body = f"""        <div class="breadcrumb"><a href="/">Home</a> / 404</div>
        <h1>Page not found</h1>
        <p class="meta">404</p>

        <p>That URL does not exist. The calculator and every model page are one click away:</p>

        <div class="links">
          <a href="/index.html#tool">Token calculator</a>
          <a href="/models/">All {total} models</a>
          <a href="/providers/">All providers</a>
          <a href="/gpt-5-token-calculator.html">GPT-5</a>
          <a href="/claude-token-counter.html">Claude</a>
          <a href="/gemini-token-counter.html">Gemini</a>
          <a href="/deepseek-token-calculator.html">DeepSeek</a>
          <a href="/qwen-token-counter.html">Qwen</a>
          <a href="/llama-token-counter.html">Llama</a>
          <a href="/api.html">Pricing data</a>
          <a href="/embed.html">Embed the calculator</a>
          <a href="/privacy.html">Privacy</a>
        </div>
      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div>
        <strong>TokenCalc — AI Token Calculator</strong><br>
        Free, private token counting and API cost estimation for {total} AI models.
      </div>
      <div>
        <a href="/privacy.html">Privacy Policy</a> · <a href="/models/">All models</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""
    return body


def build_llms_full(models, vgroups):
    out = []
    out.append("# TokenCalc — AI Token Calculator\n")
    out.append(
        f"> Token counting and API cost estimation for {len(models)} AI models across "
        f"{len(vgroups)} providers. All computation runs client-side in the browser; no text is uploaded.\n"
    )
    out.append(f"Home: {SITE_URL}/  ·  Models: {SITE_URL}/models/  ·  Providers: {SITE_URL}/providers/")
    out.append(f"Pricing data (CC BY 4.0): {SITE_URL}/data/model-prices.json")
    out.append(f"List prices last verified {human}. Source of record for citation.\n")
    out.append("## Exact vs estimated counting\n")
    out.append(
        "- **Exact**: OpenAI models, counted with the official tiktoken BPE tokenizer (o200k_base / cl100k_base) in-browser.\n"
        "- **Estimate**: every other vendor, from calibrated character ratios, ~5-10% accurate on English text.\n"
    )
    out.append("## Models\n")
    out.append("| Model | Provider | Counting | Context | Input /1M | Output /1M | Page |")
    out.append("|---|---|---|---|---|---|---|")
    for m in models:
        out.append(
            f"| {m['label']} | {VENDOR_DISPLAY.get(vendor_slug(m), vendor_of(m))} | "
            f"{'exact' if is_exact(m) else 'estimate'} | {m.get('contextWindow') or '—'} | "
            f"{money(m.get('priceInputPer1M'))} | {money(m.get('priceOutputPer1M'))} | "
            f"{SITE_URL}/models/{model_slug(m['id'])}/ |"
        )
    out.append("\n## Provider pages\n")
    for vslug, group in sorted(vgroups.items(), key=lambda kv: VENDOR_DISPLAY.get(kv[0], kv[0])):
        out.append(
            f"- {VENDOR_DISPLAY.get(vslug, vslug)} ({len(group)} models): {SITE_URL}/providers/{vslug}/"
        )
    out.append("\n## Citation\n")
    out.append(f'TokenCalc, "AI Model Token Pricing Data", tokenestimate.com, {human}. CC BY 4.0.')
    return "\n".join(out) + "\n"


def main():
    global total
    raw = DATA.read_text(encoding="utf-8")
    data = json.loads(raw)
    # Dates and counts must be live before the first page is rendered, otherwise
    # every page renders "prices verified ." with nothing after it.
    set_dates(data["_meta"]["lastVerified"])
    models = data["models"]
    total = len(models)

    vgroups = {}
    for m in models:
        vgroups.setdefault(vendor_slug(m), []).append(m)

    # Purge generated trees first: if a model is removed from the JSON its old
    # directory must not linger as an orphan that the sitemap still lists.
    for tree in ("models", "providers"):
        d = SITE / tree
        if d.exists():
            for child in sorted(d.iterdir()):
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()

    sitemap = []
    made = 0

    for m in models:
        url, body, app_s, faq_s, crumb_s = build_model_page(m, models, vgroups)
        page = (
            head_fmt(
                title=esc(title_of(m)),
                desc=desc_of(m, total, human),
                kw=kw_of(m, human),
                url=url,
                schema=dump_schema(app_s, faq_s, crumb_s),
                total=total,
            )
            + body
        )
        # head_fmt already injected body? no -- head ends before <article>; body supplies rest
        p = SITE / "models" / model_slug(m["id"]) / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page, encoding="utf-8")
        sitemap.append((url, "weekly", "0.9"))
        made += 1

    for vslug, group in vgroups.items():
        url, body, tbl_s, faq_s = build_provider_page(vslug, group, models, vgroups)
        crumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Providers", "item": SITE_URL + "/providers/"},
                {"@type": "ListItem", "position": 3, "name": VENDOR_DISPLAY.get(vslug, vslug)},
            ],
        }
        vdisp = VENDOR_DISPLAY.get(vslug, vslug)
        page = (
            head_fmt(
                title=esc(f"{vdisp} Pricing — {len(group)} Models, Rates &amp; Token Calculator (2026)"),
                desc=esc(
                    f"All {len(group)} {vdisp} models: list price per 1M input and output tokens, context "
                    f"windows and tokenizer behaviour, verified {human}. Free in-browser calculators for each model."
                ),
                kw=esc(f"{vdisp} pricing, {vdisp} API pricing, {vdisp} token cost, {vdisp} models list"),
                url=url,
                schema=dump_schema(tbl_s, faq_s, crumb),
                total=total,
            )
            + body
        )
        p = SITE / "providers" / vslug / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page, encoding="utf-8")
        sitemap.append((url, "weekly", "0.8"))
        made += 1

    # hubs
    u, b = build_model_hub(models, vgroups)
    (SITE / "models").mkdir(parents=True, exist_ok=True)
    (SITE / "models" / "index.html").write_text(
        head_fmt(
            title=f"Every AI Model Token Calculator — {total} Models & Prices (2026)",
            desc=f"Browse all {total} AI model token calculators with list pricing per 1M tokens and context "
            f"windows, verified {human}. OpenAI models counted exactly, others estimated.",
            kw="AI model token calculator, all models, LLM pricing comparison, token cost per model",
            url=u,
            schema=dump_schema({"@context": "https://schema.org", "@type": "CollectionPage", "name": "AI model token calculators", "url": u}),
            total=total,
        )
        + b,
        encoding="utf-8",
    )
    sitemap.append((u, "weekly", "0.9"))

    u, b = build_provider_hub(vgroups)
    (SITE / "providers").mkdir(parents=True, exist_ok=True)
    (SITE / "providers" / "index.html").write_text(
        head_fmt(
            title=f"AI API Pricing by Provider — {len(vgroups)} Vendors Compared (2026)",
            desc=f"List pricing for {total} AI models across {len(vgroups)} providers: input and output rate "
            f"per 1M tokens, context windows, exact vs estimated counting. Verified {human}.",
            kw="AI API pricing, LLM pricing comparison, provider pricing, cost per million tokens",
            url=u,
            schema=dump_schema({"@context": "https://schema.org", "@type": "CollectionPage", "name": "AI API pricing by provider", "url": u}),
            total=total,
        )
        + b,
        encoding="utf-8",
    )
    sitemap.append((u, "weekly", "0.8"))

    # 404
    (SITE / "404.html").write_text(
        head_fmt(
            title="Page not found — TokenCalc",
            desc="That page does not exist. Jump to the AI token calculator or any model page.",
            kw="404",
            url=f"{SITE_URL}/404.html",
            schema="",
            total=total,
        )
        + build_404(),
        encoding="utf-8",
    )

    # llms-full.txt
    (SITE / "llms-full.txt").write_text(build_llms_full(models, vgroups), encoding="utf-8")

    # sitemap: new + existing legacy pages
    legacy = [
        (f"{SITE_URL}/", "weekly", "1.0"),
        (f"{SITE_URL}/index.html", "monthly", "0.1"),
        (f"{SITE_URL}/embed.html", "monthly", "0.8"),
        (f"{SITE_URL}/api.html", "weekly", "0.8"),
        (f"{SITE_URL}/privacy.html", "yearly", "0.3"),
        (f"{SITE_URL}/blog/how-many-tokens-per-word.html", "monthly", "0.8"),
        (f"{SITE_URL}/blog/ai-api-pricing-2026.html", "weekly", "0.8"),
    ]
    # The original hand-written calculator articles. They predate /models/ and
    # overlap with it on the same keywords, but they are already linked and
    # possibly indexed, so dropping them from the sitemap would be a silent
    # deindex. Keep them listed; see 交付说明.md for the cannibalization call.
    for slug in (
        "gpt-5-token-calculator",
        "gpt-4o-token-calculator",
        "o1-o3-token-calculator",
        "claude-token-counter",
        "gemini-token-counter",
        "llama-token-counter",
        "deepseek-token-calculator",
        "qwen-token-counter",
    ):
        legacy.append((f"{SITE_URL}/{slug}.html", "monthly", "0.7"))
    all_urls = legacy + sitemap
    seen, uniq = set(), []
    for u, cf, pr in all_urls:
        if u not in seen:
            seen.add(u)
            uniq.append((u, cf, pr))

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, cf, pr in uniq:
        sm.append(
            f"  <url>\n    <loc>{esc(u)}</loc>\n"
            f"    <lastmod>{VERIFIED}</lastmod>\n"
            f"    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        )
    sm.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")

    print(f"models   : {len(models)}")
    print(f"providers: {len(vgroups)}")
    print(f"pages written : {made + 4}")
    print(f"urls in sitemap: {len(uniq)}")


# title/desc/kw helpers reused by both build and head
def title_of(m):
    label, vdisp = m["label"], VENDOR_DISPLAY.get(vendor_slug(m), vendor_of(m))
    if is_exact(m):
        return f"{label} Token Calculator — Count {label} Tokens & API Cost (2026)"
    return f"{label} Token Calculator — {label} Token Count & API Cost (2026)"


def desc_of(m, total, human):
    label, vdisp = m["label"], VENDOR_DISPLAY.get(vendor_slug(m), vendor_of(m))
    pi, po = m.get("priceInputPer1M"), m.get("priceOutputPer1M")
    if is_exact(m):
        return (
            f"Free {label} token calculator. Count {label} tokens with the official "
            f"{m['tokenizer'].split(':')[1]} tokenizer and see exact API cost at {money(pi)}/1M input "
            f"and {money(po)}/1M output. Runs in your browser — nothing is uploaded."
        )
    return (
        f"Free {label} token calculator for {vdisp}. Estimate {label} token counts and API cost at "
        f"{money(pi)}/1M input and {money(po)}/1M output. 100% in-browser, no upload, no sign-up. "
        f"Prices verified {human}."
    )


def kw_of(m, human):
    label, vdisp = m["label"], VENDOR_DISPLAY.get(vendor_slug(m), vendor_of(m))
    if is_exact(m):
        return f"{label} token calculator, {label} token counter, count {label} tokens, {label} API cost, {label} pricing, tiktoken {label}"
    return f"{label} token calculator, {label} token counter, {label} tokens, {label} API pricing, {vdisp} pricing"


if __name__ == "__main__":
    main()








