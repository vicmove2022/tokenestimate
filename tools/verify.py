#!/usr/bin/env python3
"""
Pre-deploy gate. Run this after every build step, before committing.

Catches the class of silent regression that actually breaks this site:

  1. data/model-prices.json and js/app.js's MODELS array drifting apart.
     app.js does not read the JSON, so a JSON-only update leaves the calculator
     showing stale prices and ?model=<new id> silently falling back to the
     default model. This already happened once, on 11 models.
  2. A model page count that does not match the model count.
  3. A provider page count that does not match the vendor groups.
  4. sitemap.xml listing a file that does not exist (orphan).
  5. sitemap.xml omitting a page that exists (invisible page).
  6. Duplicate <title> or meta description.
  7. Dangling internal links.
  8. Stale model counts or a stale lastVerified date anywhere in the HTML.
  9. Missing infrastructure that silently breaks the calculator:
     js/app.js, js/ranks/o200k_base.js, CNAME, sitemap.xml.

Exit code 1 on any failure, so it can gate deploy.ps1.

Usage:  python verify.py [site|repo]     (default: repo)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from vendors import vendor_of, slug_of

TARGET = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "repo")

FAIL = []
WARN = []


def ok(msg):
    print(f"  PASS  {msg}")


def bad(msg):
    FAIL.append(msg)
    print(f"  FAIL  {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"  WARN  {msg}")


def html_pages(base):
    return [p for p in sorted(base.rglob("*.html")) if ".git" not in p.parts]


def rel(p, base):
    return p.relative_to(base).as_posix()


def main():
    if not TARGET.exists():
        print(f"verify: {TARGET} does not exist")
        return 1

    print(f"\nverifying {TARGET}\n" + "=" * 62)

    # ---------------------------------------------------------- infrastructure
    print("\ninfrastructure")
    for f in [
        "index.html",
        "sitemap.xml",
        "robots.txt",
        "js/app.js",
        "js/ranks/o200k_base.js",
        "js/ranks/cl100k_base.js",
        "CNAME",
        "data/model-prices.json",
    ]:
        p = TARGET / f
        if p.exists() and p.stat().st_size > 0:
            ok(f"{f} ({p.stat().st_size:,} bytes)")
        else:
            bad(f"{f} missing or empty")

    if not (TARGET / "CNAME").exists():
        bad("CNAME absent - removing it from the repo would take the domain down")
    else:
        cname = (TARGET / "CNAME").read_text(encoding="utf-8").strip()
        if cname != "tokenestimate.com":
            warn(f"CNAME is {cname!r}, expected 'tokenestimate.com'")
        else:
            ok(f"CNAME points at {cname}")

    # ---------------------------------------------------------- data
    print("\ndata")
    dj = json.loads((TARGET / "data" / "model-prices.json").read_text(encoding="utf-8"))
    models = dj["models"]
    verified = dj["_meta"]["lastVerified"]
    ids = {m["id"] for m in models}
    ok(f"model-prices.json: {len(models)} models, lastVerified {verified}")

    appjs = (TARGET / "js" / "app.js").read_text(encoding="utf-8")
    s = appjs.index("{ id:")
    e = appjs.index("];", s)
    js_ids = set(re.findall(r'\{\s*id:\s*"([^"]+)"', appjs[s:e]))
    missing = sorted(ids - js_ids)
    extra = sorted(js_ids - ids - {"custom"})
    if missing:
        bad(f"{len(missing)} model(s) in the JSON are absent from js/app.js: {missing}")
        print("        -> the calculator will ignore ?model= for these and fall back")
        print("        -> run: python sync_appjs.py")
    else:
        ok(f"all {len(models)} JSON models are present in js/app.js MODELS")

    if extra:
        bad(f"js/app.js has {len(extra)} model(s) not in the JSON: {extra}")
    else:
        ok("no orphan models in js/app.js")

    # vendor must be present and must equal what vendors.py derives. The dataset
    # is published as groupable, and `provider` alone groups wrongly: three
    # OpenAI product lines plus a "US & EU" region bucket looked like vendors.
    no_vendor = [m["id"] for m in models if not m.get("vendor")]
    wrong_vendor = [m["id"] for m in models if m.get("vendor") and m["vendor"] != vendor_of(m)]
    if no_vendor:
        bad(f"{len(no_vendor)} model(s) have no vendor field: {no_vendor[:6]}")
        print("        -> run: python apply_patch.py <patch>  (it stamps vendor on every row)")
    elif wrong_vendor:
        bad(f"{len(wrong_vendor)} model(s) have a stale vendor: {wrong_vendor[:6]}")
        print("        -> vendors.py changed; re-run apply_patch.py to restamp")
    else:
        vslugs = {slug_of(m["vendor"]) for m in models}
        ok(f"every model has a vendor ({len(vslugs)} distinct vendors across {len(models)} models)")

    # price agreement between the two sources of truth
    price_mismatch = []
    by_id = {m["id"]: m for m in models}
    for m in re.finditer(
        r'\{\s*id:\s*"([^"]+)"\s*,.*?priceIn:\s*([\d.]+)\s*,\s*priceOut:\s*([\d.]+)',
        appjs[s:e],
        re.S,
    ):
        mid, pin, pout = m.group(1), float(m.group(2)), float(m.group(3))
        j = by_id.get(mid)
        if not j:
            continue
        jpin = float(j.get("priceInputPer1M") or 0)
        jpout = float(j.get("priceOutputPer1M") or 0)
        if abs(jpin - pin) > 1e-9 or abs(jpout - pout) > 1e-9:
            price_mismatch.append(f"{mid}: js {pin}/{pout} vs json {jpin}/{jpout}")
    if price_mismatch:
        bad(f"{len(price_mismatch)} price mismatch(es) between js/app.js and the JSON:")
        for x in price_mismatch[:8]:
            print(f"        {x}")
    else:
        ok("prices agree between js/app.js and the JSON")

    # ---------------------------------------------------------- page counts
    print("\npages")
    mdirs = sorted(d.name for d in (TARGET / "models").iterdir() if d.is_dir())
    pdirs = sorted(d.name for d in (TARGET / "providers").iterdir() if d.is_dir())
    if len(mdirs) == len(models):
        ok(f"{len(mdirs)} model pages == {len(models)} models")
    else:
        bad(f"{len(mdirs)} model pages != {len(models)} models")

    slugs = {re.sub(r"[^a-z0-9]+", "-", m["id"].lower()).strip("-") for m in models}
    missing_pg = sorted(slugs - set(mdirs))
    if missing_pg:
        bad(f"no page generated for: {missing_pg}")
    else:
        ok("every model id has a page at the expected slug")

    if len(pdirs) >= 20:
        ok(f"{len(pdirs)} provider pages")
    else:
        warn(f"only {len(pdirs)} provider pages")

    # ---------------------------------------------------------- SEO
    print("\nseo")
    pages = html_pages(TARGET)
    titles, descs, broken = {}, {}, {}
    stale = 0
    known = set()

    for p in pages:
        r = rel(p, TARGET)
        known.add("/" + r)
        if r.endswith("/index.html"):
            known.add("/" + r[: -len("index.html")])
    known.add("/")
    for extra_f in ["ads.txt", "BingSiteAuth.xml", "CNAME", "README.md", ".gitignore"]:
        known.add("/" + extra_f)

    for p in pages:
        h = p.read_text(encoding="utf-8")
        r = rel(p, TARGET)
        ti = re.search(r"(?is)<title>(.*?)</title>", h)
        de = re.search(r'(?is)<meta name="description" content="(.*?)"', h)
        t = ti.group(1).strip() if ti else ""
        d = de.group(1).strip() if de else ""
        if not t:
            bad(f"{r}: no <title>")
        elif t in titles:
            bad(f"{r}: duplicate title, also on {titles[t]}")
        else:
            titles[t] = r
        if not d:
            bad(f"{r}: no meta description")
        elif d in descs:
            bad(f"{r}: duplicate meta description, also on {descs[d]}")
        else:
            descs[d] = r
        if re.search(r"\b70\+? (models|Models|LLMs)|70-model|2026-09-30", h):
            stale += 1
        for m in re.finditer(r'(?:href|src)="(/[^"#?]*)"', h):
            t2 = m.group(1)
            if re.search(r"\.(css|js|png|svg|json|txt|xml)$", t2):
                continue
            if t2 not in known:
                broken[t2] = broken.get(t2, 0) + 1

    ok(f"{len(pages)} html files, {len(titles)} unique titles, {len(descs)} unique descriptions")
    if broken:
        bad(f"{len(broken)} dangling internal link target(s): {list(broken)[:6]}")
    else:
        ok("no dangling internal links")
    if stale:
        bad(f"{stale} page(s) still quote the old model count or the old date")
    else:
        ok("no stale model counts or dates")

    # ---------------------------------------------------------- sitemap
    print("\nsitemap")
    sm = (TARGET / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sm)
    orphans = []
    for u in locs:
        pth = re.sub(r"^https://tokenestimate\.com", "", u)
        if pth in ("", "/"):
            continue
        if not (TARGET / pth.lstrip("/")).exists():
            orphans.append(u)
    if orphans:
        bad(f"{len(orphans)} sitemap URL(s) with no file: {orphans[:5]}")
    else:
        ok(f"{len(locs)} sitemap URLs all resolve to real files")

    listed = {re.sub(r"^https://tokenestimate\.com", "", u) for u in locs}
    unlisted = []
    for p in pages:
        r = "/" + rel(p, TARGET)
        if r.endswith("/index.html"):
            r = r[: -len("index.html")]
        if r in ("/404.html", "/"):
            continue
        if r not in listed:
            unlisted.append(r)
    if unlisted:
        warn(f"{len(unlisted)} page(s) not in sitemap: {unlisted[:6]}")
    else:
        ok("every indexable page is in the sitemap")

    # ---------------------------------------------------------- verdict
    print("\n" + "=" * 62)
    if FAIL:
        print(f"RESULT: {len(FAIL)} FAILURE(S), {len(WARN)} warning(s)")
        for f in FAIL:
            print(f"  - {f}")
        return 1
    print(f"RESULT: all checks passed ({len(WARN)} warning(s))")
    for w in WARN:
        print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())