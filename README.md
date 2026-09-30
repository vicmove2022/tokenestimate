# TokenCalc — AI Token Calculator

Free AI token calculator and API cost estimator that runs entirely in the browser.
Live site: **https://tokenestimate.com**

Counts tokens for **70 models across 22 providers** and estimates input/output cost per 1M tokens. OpenAI models are counted with the **official tiktoken BPE tokenizer** (`o200k_base`, `cl100k_base`) via [js-tiktoken](https://github.com/dqbd/tiktoken), so the number you see is the number the API bills. Other providers use a calibrated character-ratio estimate (~5–10% off), labelled in the UI.

## What it does

- Exact token counts for GPT-5.5 → GPT-5 nano, GPT-4o, GPT-4.1, o1/o3/o4 and the embedding models
- Estimated counts and costs for Claude Opus 5.5 / Sonnet 5 / Haiku 4.5, Gemini 3.1 Pro → Flash-Lite, DeepSeek V4, Qwen3, Llama 4, GLM, Kimi, Doubao, ERNIE, Hunyuan, Spark, Grok, Mistral, Amazon Nova and more
- Live cost per run and per 1M tokens, with **every price editable in the UI** (custom-pricing slot included)
- Character / word / line / byte counts alongside the token total
- `?model=<id>` deep links, e.g. `https://tokenestimate.com/?model=claude-opus-5-5`

## Privacy

There is no backend. Text is never uploaded, no API key and no account is required, and tokenization happens in the page — the dictionary is cached in `localStorage` after a one-time download. Analytics is cookie-less (Umami). See [privacy.html](https://tokenestimate.com/privacy.html).

## Embed it

One line puts the calculator on your own site — free, commercial use included, no key, no rate limit:

```html
<script src="https://tokenestimate.com/js/embed.js" data-model="gpt-5.5" data-height="640"></script>
```

Options (`data-model`, `data-height`, `data-credit`), a script-free iframe variant and a live preview: **[https://tokenestimate.com/embed.html](https://tokenestimate.com/embed.html)**

## Pricing data

The table behind the calculator is published as one static JSON file — 70 models, USD per 1M input/output tokens, context window and tokenizer per model, plus a `lastVerified` date:

```
https://tokenestimate.com/data/model-prices.json
```

Licensed **CC BY 4.0**, CORS-open, no key. Field schema and citation on the landing page: **[https://tokenestimate.com/api.html](https://tokenestimate.com/api.html)**

## AI crawlers and citation

`robots.txt` explicitly allows GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended and others; the whole site is server-rendered static HTML, and [`llms.txt`](https://tokenestimate.com/llms.txt) carries the key facts, page map and citation string.

> Cite as: TokenCalc, "AI Token Calculator", tokenestimate.com, 2026.
> Dataset: TokenCalc, "AI Model Token Pricing Data", tokenestimate.com, 2026.

## Repository layout

Plain static files — no build step, no dependencies to install, deploy by serving the directory.

| Path | Contents |
|---|---|
| `index.html` | The calculator plus the full 70-model pricing table |
| `*-token-calculator.html`, `*-token-counter.html` | Per-provider landing pages (pricing table, guide, FAQ) |
| `blog/` | Pricing overview and tokens-per-word reference |
| `js/app.js` | Tokenizer loading, model catalog, cost math |
| `js/ranks/` | Vendored `o200k_base` / `cl100k_base` rank data so counts work offline |
| `js/embed.js` | Widget loader used by third-party sites |
| `data/model-prices.json` | The CC BY pricing dataset |
| `css/style.css` | Single stylesheet, no framework |

## Prices are a dated snapshot

All prices are public list prices, last verified against provider pages on **2026-09-30**. Batch, cached-input, long-context surcharge and contract rates are not modelled. Check `_meta.lastVerified` in the dataset, or the "prices verified" line on the page, before quoting a number.
