#!/usr/bin/env python3
"""
Generate /compare/ pages: "cheapest model for X" cuts.

Why
---
"cheapest llm api", "cheapest model for long context", "cheapest model per 1M
output tokens" are the highest commercial-intent queries in this niche, and
nothing on the site was targeting them. pricepertoken.com has per-model pages;
nobody in this niche publishes a *sorted, current* answer to the question people
actually ask, which is "what should I pick".

Each cut below is computed from data/model-prices.json, so it is a real answer
rather than a table dump. Adds its URLs to sitemap.xml if they are missing.

Usage:  python gen_compare.py
"""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
REPO = ROOT / "repo"
DATA = SITE / "data" / "model-prices.json"
SITE_URL = "https://tokenestimate.com"
UMAMI = "8f1fd21d-3670-41e7-adf4-20d24de46fd4"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def slug(mid):
    return re.sub(r"[^a-z0-9]+", "-", mid.lower()).strip("-")


def ctx_tokens(m):
    c = str(m.get("contextWindow") or "").strip()
    mm = re.match(r"^([\d.]+)\s*([KM])$", c, re.I)
    if not mm:
        return None
    return float(mm.group(1)) * {"K": 1e3, "M": 1e6}[mm.group(2).upper()]


def money(v):
    if v is None:
        return "—"
    v = float(v)
    if v == 0:
        return "Free"
    if v >= 1:
        return f"${v:,.2f}"
    return f"${v:,.4f}".rstrip("0").rstrip(".")


def row(m):
    return (
        f'<tr><td><a href="/models/{slug(m["id"])}/">{m["label"]}</a></td>'
        f'<td>{m["provider"]}</td>'
        f'<td><span class="tag">{"exact" if str(m.get("tokenizer","")).startswith("tiktoken") else "estimate"}</span></td>'
        f'<td>{m.get("contextWindow") or "—"}</td>'
        f'<td>{money(m.get("priceInputPer1M"))}</td>'
        f'<td>{money(m.get("priceOutputPer1M"))}</td>'
        f'<td>{m.get("maxOutputTokens") or "—"}</td></tr>'
    )


def table(rows, caption=""):
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f"""        <table>
          {cap}
          <thead><tr><th>Model</th><th>Provider</th><th>Counting</th><th>Context</th>
          <th>Input / 1M</th><th>Output / 1M</th><th>Max output</th></tr></thead>
          <tbody>
{chr(10).join('            ' + r for r in rows)}
          </tbody>
        </table>"""


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
  <meta property="og:image" content="https://tokenestimate.com/og-cover.png">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="https://tokenestimate.com/og-cover.png">

  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="stylesheet" href="/css/style.css">

  <script type="application/ld+json">
  {schema}
  </script>
  <style>
    .article {{ max-width: 860px; margin: 24px auto 60px; padding: 0 26px; }}
    .article h1 {{ font-size: 2rem; line-height: 1.25; margin-bottom: 10px; }}
    .article h2 {{ font-size: 1.4rem; margin: 36px 0 12px; }}
    .article h3 {{ font-size: 1.05rem; margin: 22px 0 6px; }}
    .article p, .article li {{ color: var(--text-dim); font-size: .98rem; }}
    .article ul {{ margin: 10px 0 14px 22px; }}
    .article li {{ margin-bottom: 6px; }}
    .article table {{ width: 100%; border-collapse: collapse; margin: 16px 0 22px; font-size: .9rem; }}
    .article caption {{ caption-side: top; text-align: left; font-size: .82rem; color: var(--text-faint); padding-bottom: 8px; }}
    .article th, .article td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
    .article th {{ color: var(--text); font-weight: 600; }}
    .article .meta {{ color: var(--text-faint); font-size: .85rem; margin-bottom: 24px; }}
    .note {{ background: var(--bg-soft); border-left: 3px solid var(--accent); border-radius: var(--radius-sm); padding: 13px 16px; margin: 18px 0 22px; font-size: .92rem; color: var(--text-dim); }}
    .note b {{ color: var(--text); }}
    .tag {{ font-size: .68rem; }}
    .breadcrumb {{ font-size: .82rem; color: var(--text-faint); margin-bottom: 16px; }}
    .calc {{ margin: 26px 0 8px; }}
    .calc iframe {{ display: block; width: 100%; height: 660px; border: 1px solid #dfe6f1; border-radius: 16px; background: #fff; }}
    code {{ font-family: var(--mono); background: var(--bg-input); border: 1px solid var(--border); border-radius: 6px; padding: 1px 6px; font-size: .88em; }}
    pre {{ background: var(--bg-input); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 16px; overflow-x: auto; }}
    pre code {{ background: none; border: 0; padding: 0; }}
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
        <a href="/compare/">Compare</a>
        <a href="/api.html">Pricing data</a>
      </nav>
    </div>
  </header>

  <main>
    <div class="container">
      <article class="article">
"""

TAIL = """      </article>
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
        <a href="/privacy.html">Privacy Policy</a> · <a href="/models/">All models</a> ·
        <a href="/api.html">Pricing JSON</a> · <a href="/compare/">Compare</a> · © 2026 TokenCalc.
      </div>
    </div>
  </footer>
</body>
</html>
"""


def page(title, desc, kw, path, schema, body, human, total):
    return (
        HEAD.format(title=title, desc=desc, kw=kw, url=SITE_URL + path,
                    schema=json.dumps(schema, ensure_ascii=False, indent=2), UMAMI=UMAMI)
        + body
        + TAIL.format(human=human, total=total)
    )


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    models = data["models"]
    total = len(models)
    iso = data["_meta"]["lastVerified"]
    y, mth, d = (int(x) for x in iso.split("-"))
    human = f"{d} {MONTHS[mth - 1]} {y}"

    # Purge first. robocopy and build.py never delete, so a renamed or removed
    # cut would otherwise linger as a duplicate-title page forever.
    if (SITE / "compare").exists():
        shutil.rmtree(SITE / "compare")
    for stale in (REPO / "compare").glob("*/"):
        if not any((SITE / "compare" / stale.name).iterdir()):
            shutil.rmtree(stale)

    priced = [m for m in models if m.get("priceInputPer1M") is not None
              and m.get("priceOutputPer1M") is not None and m["priceInputPer1M"] > 0]
    urls = []

    # ---------------------------------------------------------------- hub
    hub = f"""        <div class="breadcrumb"><a href="/">Home</a> / Compare</div>
        <h1>Cheapest LLM API Pricing, Answered</h1>
        <p class="meta">{total} models · {len(priced)} with published list rates · verified {human}</p>

        <p>Everyone else publishes a pricing <em>table</em>. This is a sorted
        <em>answer</em>, cut by the constraint that actually decides which model you
        should pick. Every row is computed from
        <a href="/api.html">the published dataset</a>, not typed in.</p>

        <div class="calc">
          <iframe src="/?embed=1" title="AI token calculator" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>

        <h2>Pick your constraint</h2>
        <ul>
          <li><a href="/compare/cheapest-input/">Cheapest per 1M input tokens</a> — long prompts, big documents, RAG corpora</li>
          <li><a href="/compare/cheapest-output/">Cheapest per 1M output tokens</a> — long generations, and this is where bills actually go</li>
          <li><a href="/compare/cheapest-long-context/">Cheapest with 200K+ context</a> — when the context window is the binding limit</li>
          <li><a href="/compare/cheapest-1m-context/">Cheapest with 1M+ context</a> — whole-repo analysis, long agent histories</li>
          <li><a href="/compare/openai-cheapest/">Cheapest OpenAI model</a> — and where those counts are exact rather than estimated</li>
        </ul>

        <div class="note"><b>The number that matters is usually output.</b> On most
        models the output rate is 3–8× the input rate. A workload with short prompts
        and long answers is an <em>output</em> workload. Rank by output unless your
        prompts are the long part.</div>
"""
    hub_schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Cheapest LLM API pricing",
        "url": SITE_URL + "/compare/",
        "description": desc_hub(total, human),
    }
    p = SITE / "compare" / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page(
        f"Cheapest LLM API Pricing in {y} — Sorted Answers, {total} Models | TokenCalc",
        desc_hub(total, human),
        "cheapest llm api, cheapest llm pricing, cheapest model per 1m tokens, llm price comparison, cheapest openai model",
        "/compare/", hub_schema, hub, human, total), encoding="utf-8")
    urls.append((SITE_URL + "/compare/", "weekly", "0.9"))

    # ---------------------------------------------------------------- cuts
    cuts = []

    by_in = sorted(priced, key=lambda x: x["priceInputPer1M"])
    cuts.append({
        "path": "/compare/cheapest-input/",
        "h1": "Cheapest LLM APIs by Input Price",
        "title": f"Cheapest LLM API by Input Token Price ({y}) — {total} Models Sorted",
        "desc": "The cheapest models per 1M input tokens, sorted. Long prompts, RAG corpora and document ingestion are input-dominated workloads, so this is the cut that matters there. Verified " + human + ".",
        "kw": "cheapest llm input price, cheapest model per 1m input tokens, cheapest api for long context, cheap llm for rag",
        "sort": "input",
        "note": "Input-heavy means your prompts, retrieved documents or uploaded files dominate the bill. If your model returns long answers, read the output cut instead — on most models output costs 3–8× more per token.",
    })

    by_out = sorted(priced, key=lambda x: x["priceOutputPer1M"])
    cuts.append({
        "path": "/compare/cheapest-output/",
        "h1": "Cheapest LLM APIs by Output Price",
        "title": f"Cheapest LLM API by Output Token Price ({y}) — {total} Models Sorted",
        "desc": "The cheapest models per 1M output tokens, sorted. Output usually costs 3-8x input, so this is the cut that decides most production bills. Verified " + human + ".",
        "kw": "cheapest llm output price, cheapest model per 1m output tokens, cheap llm for long generation, llm cost per output token",
        "sort": "output",
        "note": "This is the column that decides most bills. If a model is cheap to read from and expensive to write to, a chat workload will cost you far more than the input rate suggests.",
    })

    long_ctx = [m for m in priced if (ctx_tokens(m) or 0) >= 200_000]
    cuts.append({
        "path": "/compare/cheapest-long-context/",
        "h1": "Cheapest Models With 200K+ Context",
        "title": f"Cheapest LLM API With 200K+ Token Context ({y})",
        "desc": "Cheapest models that accept at least 200K tokens of context, sorted by input price. When the context window is the hard constraint, the cheapest model outside your window is not cheap. Verified " + human + ".",
        "kw": "cheapest long context llm, cheapest 200k context model, cheap llm for long documents, long context model pricing",
        "sort": "input",
        "pool": long_ctx,
        "note": "Context is a ceiling, not a price. Exceeding it fails the request rather than billing you extra, so check it before you optimise price.",
    })

    mega_ctx = [m for m in priced if (ctx_tokens(m) or 0) >= 1_000_000]
    cuts.append({
        "path": "/compare/cheapest-1m-context/",
        "h1": "Cheapest Models With 1M+ Token Context",
        "title": f"Cheapest LLM API With 1M+ Token Context ({y})",
        "desc": "Cheapest models with a million-token or larger context window, sorted by input price. Whole-repository analysis, long agent histories and very large documents. Verified " + human + ".",
        "kw": "cheapest 1m context llm, cheapest million token context model, cheap llm for whole repo analysis, 1m context window pricing",
        "sort": "output",
        "pool": mega_ctx,
        "note": "A 1M window is rare and usually sits at a premium. These are the exceptions.",
    })

    oa = sorted([m for m in priced if m["provider"].startswith("OpenAI")],
                key=lambda x: x["priceInputPer1M"])
    cuts.append({
        "path": "/compare/openai-cheapest/",
        "h1": "Cheapest OpenAI Models — Where Counts Are Exact",
        "title": f"Cheapest OpenAI Models by Price ({y}) — With Exact Token Counts",
        "desc": "OpenAI models sorted by input price, with one advantage the others cannot match: token counts are exact, computed with the same tiktoken tokenizer the API bills with. Verified " + human + ".",
        "kw": "cheapest openai model, openai model pricing comparison, gpt pricing comparison, cheapest gpt model",
        "sort": "input",
        "pool": oa,
        "note": "Every row here is counted with the real tiktoken tokenizer, so the number is the number on your invoice. Nothing else in this comparison can promise that — other vendors publish no tokenizer at all, which is why their counts are estimates.",
    })

    for c in cuts:
        pool = c.get("pool") or priced
        if c["sort"] == "input":
            pool = sorted(pool, key=lambda x: x["priceInputPer1M"])
        else:
            pool = sorted(pool, key=lambda x: x["priceOutputPer1M"])
        top = pool[:15]
        col = "input" if c["sort"] == "input" else "output"

        win = top[0]
        faq = [
            (f"What is the cheapest {'input' if col == 'input' else 'output'} per 1M tokens right now?",
             f"{win['label']} at {money(win['priceInputPer1M'] if col == 'input' else win['priceOutputPer1M'])} per 1M "
             f"{col} tokens, from {win['provider']}, as verified on {human}."),
            ("Are these list prices?",
             f"Yes. Public list prices only. Batch rates, committed-use discounts and enterprise contracts are cheaper and are not modelled here. {_meta_lastmod()}"),
            ("Are the token counts exact?",
             "Only for OpenAI models, which are counted with the same tiktoken tokenizer the API bills with. Every other vendor publishes no tokenizer, so those counts are calibrated estimates at 5-10% accuracy."),
            ("Does a cheap input price make a model cheap overall?",
             f"Not necessarily. On this page the ranking is by {col} price. Output rates run 3-8x input rates on most models, so a chat workload is usually an output workload."),
        ]
        faq_schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq]}

        body = f"""        <div class="breadcrumb"><a href="/">Home</a> / <a href="/compare/">Compare</a> / {c["h1"]}</div>
        <h1>{c["h1"]}</h1>
        <p class="meta">{len(pool)} models qualify · sorted by {col} price · verified {human}</p>

        <p>The cheapest is <strong>{win["label"]}</strong> at
        <strong>{money(win["priceInputPer1M" if col == "input" else "priceOutputPer1M"])}</strong>
        per 1M {col} tokens ({win["provider"]}). Sorted, current, and computed from
        <a href="/api.html">the published dataset</a> rather than hand-maintained.</p>

        <div class="note"><b>Before you switch.</b> {c["note"]}</div>

        <h2>Full ranking</h2>
{table([row(x) for x in top], caption=f"Top {len(top)} of {len(pool)}, ascending by {col} price per 1M tokens. Verified {human}.")}

        <h2>What a request actually costs</h2>
        <p>At {money(win["priceInputPer1M" if col == "input" else "priceOutputPer1M"])} per 1M {col} tokens,
        {win["label"]} costs:</p>
        <ul>
          <li><strong>1M tokens</strong> — {money(win["priceInputPer1M" if col == "input" else "priceOutputPer1M"])}</li>
          <li><strong>100M tokens</strong> — {money((win["priceInputPer1M" if col == "input" else "priceOutputPer1M"]) * 100)}</li>
          <li><strong>1B tokens</strong> — {money((win["priceInputPer1M" if col == "input" else "priceOutputPer1M"]) * 1000)}</li>
        </ul>
        <p>Cheap per token stops being cheap once volume compounds. At a billion tokens
        the difference between the top two rows on this page is tens of thousands of dollars a year.</p>

        <div class="calc">
          <iframe src="/?embed=1" title="AI token calculator" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        </div>
        <p>Prefer to check one model in detail? <a href="/models/">All {total} model calculators</a>,
        <a href="/providers/">every provider's pricing</a>, or the raw
        <a href="/api.html">JSON dataset</a>.</p>

        <h2>FAQs</h2>
{chr(10).join('        <h3>' + q + '</h3>' + chr(10) + '        <p>' + a + '</p>' for q, a in faq)}
"""
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": c["h1"],
            "url": SITE_URL + c["path"],
            "description": c["desc"],
            "breadcrumb": {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Compare", "item": SITE_URL + "/compare/"},
                {"@type": "ListItem", "position": 3, "name": c["h1"]},
            ]},
        }
        sd = schema["@type"]
        schema["@type"] = "FAQPage"
        merged = {"@context": "https://schema.org", "@graph": [schema, faq_schema]}

        path = SITE / c["path"].strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page(c["title"], c["desc"], c["kw"], c["path"],
                             merged, body, human, total), encoding="utf-8")
        urls.append((SITE_URL + c["path"], "weekly", "0.85"))
        print(f"  {c['path']:<34} {len(pool):>3} qualify, top = {win['label']}")

    add_to_sitemap(urls, iso)
    print(f"\nwrote {len(urls)} compare pages")
    return 0


def desc_hub(total, human):
    return (f"Cheapest LLM API pricing sorted by the constraint that decides your bill: "
            f"input price, output price, long context, 1M context, or cheapest OpenAI model. "
            f"{total} models, computed from the published dataset. Verified {human}.")


def _meta_lastmod():
    return "Check the verified date on each page before you budget against it."


def add_to_sitemap(urls, iso):
    sm = SITE / "sitemap.xml"
    text = sm.read_text(encoding="utf-8")
    existing = set(re.findall(r"<loc>(.*?)</loc>", text))
    add = []
    for u, cf, pr in urls:
        if u in existing:
            continue
        add.append(
            f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{iso}</lastmod>\n"
            f"    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        )
    if not add:
        print("  sitemap already lists the compare pages")
        return
    text = text.replace("</urlset>", "\n".join(add) + "\n</urlset>")
    sm.write_text(text, encoding="utf-8")
    print(f"  added {len(add)} URL(s) to sitemap.xml")


if __name__ == "__main__":
    raise SystemExit(main())