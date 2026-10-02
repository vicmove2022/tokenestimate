<div align="center">

# TokenCalc

**Free, CC BY 4.0 pricing data for 92 LLM models — plus an in-browser token counter that needs no backend.**

[![CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![prices verified](https://img.shields.io/badge/prices%20verified-2026--10--02-brightgreen.svg)](https://tokenestimate.com/api.html)
[![no build step](https://img.shields.io/badge/build-none%20%7C%20serve%20the%20folder-informational.svg)](#repository-layout)
[![no backend](https://img.shields.io/badge/backend-none-success.svg)](https://tokenestimate.com/privacy.html)

[**Live calculator**](https://tokenestimate.com) · [**Pricing data**](https://tokenestimate.com/api.html) · [**Changelog**](CHANGELOG.md) · [**Compare**](https://tokenestimate.com/compare/) · [**Embed it**](https://tokenestimate.com/embed.html)

</div>

---

## Why this exists

LLM prices change constantly and almost nobody publishes the *movement*.
OpenAI cut GPT-5.6 Sol's input price 20% and its output price 33% on
2026-08-21, and published that rate as promotional only through 2026-11-21.
Anthropic cut Luna-tier pricing 80% in July. A cost model built on a
three-month-old table is quietly wrong, and there is usually no way to tell.

So this repo publishes three things:

| | |
|---|---|
| **A dated snapshot** | [`data/model-prices.json`](data/model-prices.json) — 92 models, CC BY 4.0, CORS-open, no key |
| **A change log** | [`CHANGELOG.md`](CHANGELOG.md) — every price movement and correction, with the source URL for each |
| **A counter** | [tokenestimate.com](https://tokenestimate.com) — counts tokens in the browser, uploads nothing |

Every figure in the dataset carries a source. `_meta.lastVerified` moves only
when someone has actually re-checked a provider page — it is a claim, not a
build timestamp.

## Quickstart

No install, no build, no dependencies.

```bash
curl -s https://tokenestimate.com/data/model-prices.json \
  | jq '.models[] | select(.provider=="OpenAI") | {id, priceInputPer1M}'
```

```python
import requests

data = requests.get("https://tokenestimate.com/data/model-prices.json").json()

# Cheapest models that accept at least 200K tokens of context
long_ctx = [m for m in data["models"] if m.get("contextWindow", "").endswith(("K", "M"))]
affordable = [
    m for m in long_ctx
    if m["priceInputPer1M"] and m["priceOutputPer1M"]
]
affordable.sort(key=lambda m: m["priceInputPer1M"])

for m in affordable[:5]:
    print(f"{m['label']:<24} {m['contextWindow']:>6}  "
          f"${m['priceInputPer1M']}/${m['priceOutputPer1M']} per 1M")

print("verified:", data["_meta"]["lastVerified"])
```

```js
const res = await fetch("https://tokenestimate.com/data/model-prices.json");
const { models, _meta } = await res.json();
console.log(`${models.length} models, verified ${_meta.lastVerified}`);
// → 92 models, verified 2026-10-02
```

## Schema

```jsonc
{
  "id":                    "gpt-5.6-sol",       // API model id, also the ?model= deep-link value
  "label":                 "GPT-5.6 Sol",
  "provider":              "OpenAI",
  "tokenizer":             "tiktoken:o200k_base", // or "estimate"
  "contextWindow":         "1M",
  "priceInputPer1M":       4,                   // USD, public list price
  "priceOutputPer1M":      20,
  "priceCachedInputPer1M": 0.4,                 // optional
  "maxOutputTokens":       "128K",              // optional
  "note":                  "Promotional rate…"  // optional
}
```

**`tokenizer` is not cosmetic — read it before you use the counts.**

- `tiktoken:o200k_base` / `tiktoken:cl100k_base` → the count is **exact**. Same
  Byte-Pair-Encoding tokenizer OpenAI bills with, so the number equals the
  number on your invoice.
- `estimate` → **no vendor publishes a tokenizer**, so these come from calibrated
  character ratios, roughly 5–10% accurate on English and wider on code or
  mixed Chinese-English input.

Do not mix the two in one evaluation. If you need invoice-grade fidelity,
count with the exact tokenizer and treat the estimate gap as your safety margin.

All prices are **public list prices**. Batch rates, committed-use discounts,
long-context surcharges and enterprise contracts are not modelled.

## Accuracy, stated plainly

| Claim | Truth |
|---|---|
| OpenAI counts | Exact. `js/ranks/` vendors the real tiktoken rank tables, so it works offline. |
| Everyone else's counts | Estimate, ~5–10%. Labelled as such everywhere, never dressed up as exact. |
| Price accuracy | Only as good as `_meta.lastVerified`. Check it. |
| Coverage | 92 models, 23 vendors. Not exhaustive, and we say so rather than padding it. |

## Citations

> TokenCalc, "AI Model Token Pricing Data", tokenestimate.com, 2026. CC BY 4.0.
>
> TokenCalc, "LLM Pricing Changelog", tokenestimate.com, 2026-10-02.

## Embed the counter

One line, no backend, no key, commercial use allowed:

```html
<script src="https://tokenestimate.com/js/embed.js" data-model="gpt-5.6-sol" data-height="640"></script>
```

Script-free iframe, deep links (`?model=<id>`), and a live preview:
**[tokenestimate.com/embed.html](https://tokenestimate.com/embed.html)**

Embedding the widget puts a link to us on your page. That is the whole deal.

## The calculator

Runs entirely client-side. No backend, no upload, no key, no account.
Worth knowing:

- `https://tokenestimate.com/?embed=1` strips the page chrome for embedding
- `https://tokenestimate.com/?model=<id>` preselects a model
- Tokenizer dictionaries are cached in `localStorage` after a one-time download

Per-model landing pages (`/models/gpt-5-6-sol/`), per-vendor pricing
(`/providers/anthropic/`) and sorted "cheapest for X" answers
(`/compare/cheapest-long-context/`) each open with the right model selected.

## Repository layout

Plain static files. No build step, no dependencies. Serve the directory.

| Path | Contents |
|---|---|
| `index.html` | The calculator and the full 81-model pricing table |
| `models/<id>/` | 81 per-model landing pages, calculator preselected |
| `providers/<vendor>/` | 23 per-vendor pricing pages |
| `compare/<cut>/` | Sorted "cheapest model for X" answers |
| `data/model-prices.json` | **The CC BY 4.0 dataset** |
| `pricing-patch/` | Dated, sourced pricing patches — the provenance for every figure |
| `CHANGELOG.md` | Generated price-movement log with sources |
| `tools/` | The pipeline that regenerates every page from the data |
| `blog/` | Pricing overview, tokens-per-word reference |
| `js/app.js` | Tokenizer loading, model catalogue, cost maths |
| `js/ranks/` | Vendored `o200k_base` / `cl100k_base` ranks so counts work offline |
| `js/embed.js` | Widget loader used by third-party sites |
| `llms.txt`, `llms-full.txt` | Key facts for AI crawlers |
| `css/style.css` | Single stylesheet, no framework |

## Contributing a price correction

Corrections are welcome and credited. Two rules:

1. **A source URL is required.** A number without a link is not a correction.
2. **If you cannot verify it, say so.** Add it to `flagged_not_changed` rather
   than guessing. A wrong rate is worse than a missing row, because people
   budget against it.

The pipeline, from the `tools/` directory:

```bash
cd tools

# 1. write a sourced patch, then apply it (refuses to run if `from` does not match)
python apply_patch.py ../pricing-patch/pricing-patch-YYYY-MM-DD.json

# 2. regenerate everything that is derived from the data
python build.py             # 92 model pages, 23 provider pages, hubs, sitemap
python gen_compare.py       # the /compare/ cuts
python sync_homepage.py     # homepage pricing table from the data
python sweep_legacy.py      # clear stale counts from hand-written pages
python sync_appjs.py        # sync js/app.js's separate model catalogue
python gen_changelog.py     # regenerate CHANGELOG.md from the patch files

# 3. gate: refuses to let you ship a regression
python verify.py ..
```

`verify.py` fails the build if the dataset and `js/app.js` disagree. They are two
separate copies of the same facts and they drift silently — that has already
happened once, on 11 models, and it is why `sync_appjs.py` exists.

## Licence

Content and data: **CC BY 4.0**. Vendored tiktoken rank data remains under its
upstream licence. Model names and logos are trademarks of their respective
owners.