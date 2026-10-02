#!/usr/bin/env python3
"""
Regenerate the homepage model-pricing table from model-prices.json.

The homepage table was hand-written HTML. That made it silently stale the
moment a price changed, on the single highest-authority URL on the site.
This replaces the <tbody id="model-tbody"> contents with rows generated from
the JSON, keeping the existing markup conventions (group-row, tag ok, mono).

Also fixes the "70 models" / "70+ models" count claims in prose and FAQ.

Idempotent. Run after apply_patch.py + build.py.

Usage:  python sync_homepage.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
INDEX = ROOT / "site" / "index.html"
DATA = ROOT / "site" / "data" / "model-prices.json"

# Provider groups the table already uses, in display order.
GROUP_ORDER = [
    "OpenAI",
    "OpenAI (legacy)",
    "OpenAI embedding",
    "Anthropic Claude",
    "Google Gemini",
    "US & EU",
    "DeepSeek (深度求索)",
    "Alibaba Qwen (阿里通义)",
    "Zhipu GLM (智谱)",
    "Moonshot Kimi (月之暗面)",
    "ByteDance Doubao (火山引擎)",
    "Baidu ERNIE (百度)",
    "Tencent Hunyuan (腾讯)",
    "iFlytek Spark (讯飞星火)",
    "MiniMax (稀宇科技)",
    "01.AI (零一万物)",
    "StepFun (阶跃星辰)",
    "SenseTime (商汤)",
    "Baichuan (百川智能)",
    "Kunlun (昆仑万维)",
    "Xiaomi MiMo (小米)",
    "Huawei PanGu (华为云)",
]

# Slim label for the group header row.
GROUP_SHORT = {
    "OpenAI": "OpenAI",
    "OpenAI (legacy)": "OpenAI (legacy)",
    "OpenAI embedding": "OpenAI embedding",
    "Anthropic Claude": "Anthropic Claude",
    "Google Gemini": "Google Gemini",
    "US & EU": "US & EU",
}


def money(v):
    """Match the homepage's terse style: $5, $1.25, $0.4, Free."""
    if v is None:
        return "&mdash;"
    v = float(v)
    if v == 0:
        return "Free"
    s = f"{v:,.10f}".rstrip("0").rstrip(".")
    if "." in s:
        whole, frac = s.split(".")
        s = f"{whole}.{frac[:4].rstrip('0')}"
    return "$" + s


def build_tbody(models):
    groups = {}
    for m in models:
        groups.setdefault(m["provider"], []).append(m)

    ordered = [g for g in GROUP_ORDER if g in groups] + [
        g for g in groups if g not in GROUP_ORDER
    ]

    out = []
    for g in ordered:
        label = GROUP_SHORT.get(g, g)
        out.append(
            f'            <tr class="group-row"><td colspan="5"><strong>{label}</strong></td></tr>'
        )
        for m in groups[g]:
            exact = str(m.get("tokenizer", "")).startswith("tiktoken")
            tag = (
                '<span class="tag ok">exact tiktoken</span>'
                if exact
                else '<span class="tag">estimate</span>'
            )
            ctx = m.get("contextWindow") or "&mdash;"
            out.append(
                f'            <tr><td class="mono">{m["label"]}</td><td>{tag}</td>'
                f'<td>{ctx}</td><td>{money(m.get("priceInputPer1M"))}</td>'
                f'<td>{money(m.get("priceOutputPer1M"))}</td></tr>'
            )
    return "\n".join(out)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    models = data["models"]
    n = len(models)
    verified = data["_meta"]["lastVerified"]

    html = INDEX.read_text(encoding="utf-8")

    # ---- 1. table body
    m = re.search(r'(<tbody id="model-tbody">)(.*?)(</tbody>)', html, re.S)
    if not m:
        print("  FATAL: could not find <tbody id=\"model-tbody\">")
        return 1
    html = html[: m.start(2)] + "\n" + build_tbody(models) + "\n          " + html[m.end(2) :]
    print(f"  table    : {len(models)} model rows regenerated")

    # ---- 2. count claims in prose / FAQ / meta
    before = html
    html = html.replace("70+ models", f"{n}+ models")
    html = html.replace("70 models plus a custom-pricing slot", f"{n} models plus a custom-pricing slot")
    html = html.replace("We cover 70 models", f"We cover {n} models")
    html = html.replace("Count tokens and estimate costs for 70+ models", f"Count tokens and estimate costs for {n}+ models")
    html = html.replace("70 AI models", f"{n} AI models")
    html = html.replace("for 70 models across", f"for {n} models across")
    html = html.replace('content="Free AI token calculator for 70 models', f'content="Free AI token calculator for {n} models')
    n_changed = sum(1 for a, b in zip(before.split("\n"), html.split("\n")) if a != b)
    print(f"  prose    : {n_changed} line(s) updated to {n} models")

    # ---- 3. verification date wherever it is stated
    for old in ("last verified 2026-09-30", "verified 2026-09-30", "Last verified 2026-09-30"):
        if old in html:
            html = html.replace(old, old.replace("2026-09-30", verified))
    html = html.replace('lastVerified\\":\\"2026-09-30', f'lastVerified\\":\\"{verified}')

    INDEX.write_text(html, encoding="utf-8")
    print(f"  dates    : pinned to lastVerified {verified}")
    print("\nverify: the table should now list GPT-5.6 Sol / Terra / Luna and Claude Opus 4.7 / 4.8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())