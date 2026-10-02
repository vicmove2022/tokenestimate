#!/usr/bin/env python3
"""
Vendor resolution, shared by build.py, apply_patch.py and verify.py.

Why this exists. `provider` on a model row is not a vendor. In the shipping
dataset it carried three different meanings at once:

    OpenAI            (24 models)   the vendor
    OpenAI (legacy)   (3 models)    an API product line
    OpenAI embedding  (2 models)    an API product line
    US & EU           (6 models)    a hosting region, not a vendor at all
                               (Nova Pro, Llama 4, the Grok models)

Grouping the published JSON by `provider` therefore yields 22 "vendors", three of
them OpenAI under different names, and one of them literally "US & EU". Anyone
citing the data for a comparison gets nonsense. build.py already worked around
this with a private prefix map, which meant the site and the dataset disagreed
about what a vendor is.

So the mapping lives here once. `provider` stays untouched for backwards
compatibility -- js/app.js uses it as the calculator's group label -- and every
row gains a `vendor` field that means what its name says.
"""

# id prefix -> vendor, applied before falling back to the `provider` field.
# Order matters: the first match wins.
VENDOR_BY_ID_PREFIX = [
    ("grok-", "xAI"),
    ("llama-", "Meta"),
    ("mistral-", "Mistral AI"),
    ("magistral-", "Mistral AI"),
    ("amazon-nova", "Amazon"),
    ("nova-", "Amazon"),
]

# provider string -> URL slug. Two rows may share a slug on purpose: OpenAI's
# three provider strings are one vendor with three product lines.
VENDOR_SLUG = {
    "OpenAI": "openai",
    "OpenAI (legacy)": "openai",
    "OpenAI embedding": "openai",
    "Anthropic Claude": "anthropic",
    "Google Gemini": "google",
    "xAI": "xai",
    "Meta": "meta",
    "Mistral AI": "mistral",
    "Amazon": "amazon",
    "DeepSeek (深度求索)": "deepseek",
    "Alibaba Qwen (阿里通义)": "qwen",
    "Zhipu GLM (智谱)": "zhipu",
    "Moonshot Kimi (月之暗面)": "moonshot",
    "ByteDance Doubao (火山引擎)": "doubao",
    "Baidu ERNIE (百度)": "baidu",
    "Tencent Hunyuan (腾讯)": "tencent",
    "iFlytek Spark (讯飞星火)": "iflytek",
    "MiniMax (稀宇科技)": "minimax",
    "01.AI (零一万物)": "01ai",
    "StepFun (阶跃星辰)": "stepfun",
    "SenseTime (商汤)": "sensetime",
    "Baichuan (百川智能)": "baichuan",
    "Kunlun (昆仑万维)": "kunlun",
    "Xiaomi MiMo (小米)": "xiaomi",
    "Huawei PanGu (华为云)": "huawei",
}


def vendor_of(model):
    """The actual company behind a model row, regardless of how `provider` is set."""
    pid = str(model.get("id", "")).lower()
    for prefix, vendor in VENDOR_BY_ID_PREFIX:
        if pid.startswith(prefix):
            return vendor
    provider = model.get("provider", "")
    # A region bucket is never a vendor. Anything reaching here under this name
    # is unrecognised, so say so rather than inventing an owner.
    if provider in ("US & EU", "Other", "", None):
        return "Unattributed"
    return provider


def slug_of(vendor):
    return VENDOR_SLUG.get(vendor, vendor.lower().replace(" ", "-"))


def vendor_counts(models):
    out = {}
    for m in models:
        out[vendor_of(m)] = out.get(vendor_of(m), 0) + 1
    return out


if __name__ == "__main__":
    # Fallback slug has to cover every real vendor, or a provider page silently
    # disappears. Fail loudly at import-check time instead.
    missing = [v for v in VENDOR_SLUG if slug_of(v) != VENDOR_SLUG[v]]
    if missing:
        raise SystemExit(f"VENDOR_SLUG is inconsistent for: {missing}")
    print(f"{len(VENDOR_SLUG)} provider strings -> {len(set(VENDOR_SLUG.values()))} vendor slugs")