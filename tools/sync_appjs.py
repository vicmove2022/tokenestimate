#!/usr/bin/env python3
"""
Surgically add models to js/app.js's hardcoded MODELS array.

Why this exists
---------------
js/app.js carries its OWN copy of the pricing data in a MODELS array literal.
It does not read data/model-prices.json. Patching the JSON alone silently
leaves the calculator's dropdown and its ?model= lookup on stale data: any model
present in the JSON but absent from the array makes this line fall through
without any error or log,

    if (requested && MODELS.some((m) => m.id === requested)) state.modelId = requested;

so the widget quietly renders the default model instead. On the 2026-10-02
patch that affected 11 models, including the three GPT-5.6 tiers the new
landing pages advertise.

Why surgical rather than regenerating
-------------------------------------
Estimate entries carry calibration constants that exist ONLY in this array:

    { id: "...", ..., type: "est", est: { cjk: 1.2, ascii: 4 } }

There is no `est` block anywhere in model-prices.json, so regenerating the
array from the JSON would silently discard every calibration ratio. This script
inserts new entries and leaves existing ones byte-for-byte untouched.

Rules
-----
- Never rewrites an entry that already exists.
- Estimate models inherit { cjk, ascii } from a named sibling in the same family.
- Exact models inherit `encoding` from the tokenizer field in the JSON.
- The <select> option text uses SHORT_NOTE, not the long editorial `note` from
  the JSON; long notes belong on the landing page.
- Idempotent: re-running adds nothing.

Usage:  python sync_appjs.py            (patch repo/js/app.js)
        python sync_appjs.py --check    (report only, change nothing)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT / "repo"
SITE = ROOT / "site"
REPO_APPJS = REPO / "js" / "app.js"
# site/js/app.js is the unpatched upstream mirror that site/ was built from.
# Writing to both makes an overwrite of one by the other harmless; this drift
# has silently broken the calculator three times.
MIRROR_APPJS = SITE / "js" / "app.js"
DATA = ROOT / "site" / "data" / "model-prices.json"

CHECK = "--check" in sys.argv

# For each new model: which existing entry donates its { cjk, ascii } ratios.
# Chosen from the same family so the calibration is defensible.
EST_INHERIT = {
    "claude-opus-4.7": "claude-opus-4.6",
    "claude-opus-4.8": "claude-opus-4.6",
    "claude-fable-5.1": "claude-fable-5",
    "grok-4.5": "grok-4.1",
    "grok-4.3": "grok-4.1",
    "claude-sonnet-5.5": "claude-sonnet-5",
    "claude-mythos-5": "claude-fable-5",
    "claude-opus-5-fast": "claude-opus-5",
    "gemini-3.8-flash": "gemini-3.6-flash",
    "gemini-3.7-flash": "gemini-3.6-flash",
    "gemini-3.1-flash-lite": "gemini-3.5-flash-lite",
}

# Short suffix for the <select> option text. The JSON's `note` fields are
# editorial paragraphs for the landing page; existing app.js entries follow the
# short convention, e.g. "Grok 4.1 (xAI)", "DeepSeek V4 Pro — deepseek-chat".
SHORT_NOTE = {
    "gpt-5.6-sol": "promo price",
    "gpt-5.6-terra": "price cut Jul 2026",
    "gpt-5.6-luna": "cheapest GPT-5.6",
    "claude-opus-4.7": "tokenizer changed",
    "claude-opus-4.8": "Fast Mode available",
    "claude-fable-5.1": "latest Fable",
    "grok-4.5": "xAI flagship",
    "grok-4.3": "bigger context, cheaper",
    "gemini-3.8-flash": "promo until Dec 31",
    "gemini-3.7-flash": "promo until Dec 31",
    "gemini-3.6-flash": "promo until Dec 31",
}


def js_num(v):
    """1.0 -> 1.0, 20 -> 20, so the emitted file matches the existing style."""
    f = float(v)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(f)


def js_str(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def est_ratios(src, donor_id):
    m = re.search(
        r'\{\s*id:\s*"'
        + re.escape(donor_id)
        + r'".*?est:\s*\{\s*cjk:\s*([\d.]+)\s*,\s*ascii:\s*([\d.]+)\s*\}',
        src,
        re.S,
    )
    if not m:
        raise SystemExit(f"could not read est ratios from donor '{donor_id}' in app.js")
    return m.group(1), m.group(2)


def build_entry(m, src):
    tok = str(m.get("tokenizer", ""))
    exact = tok.startswith("tiktoken")
    enc = tok.split(":")[1] if ":" in tok else "o200k_base"
    pid = m.get("priceInputPer1M")
    pout = m.get("priceOutputPer1M") or 0
    ctx = m.get("contextWindow") or "—"

    parts = [
        "{ id: " + js_str(m["id"]),
        "label: " + js_str(m["label"]),
        "group: " + js_str(m["provider"]),
    ]

    if exact:
        parts.append('type: "exact"')
        parts.append("encoding: " + js_str(enc))
        parts.append("priceIn: %s, priceOut: %s" % (js_num(pid), js_num(pout)))
        parts.append("ctx: " + js_str(ctx))
    else:
        donor = EST_INHERIT.get(m["id"])
        if not donor:
            raise SystemExit(
                "no est-ratio donor registered for '%s'.\n"
                "  Add it to EST_INHERIT in sync_appjs.py before running." % m["id"]
            )
        cjk, ascii_ = est_ratios(src, donor)
        parts.append('type: "est"')
        # priceIn/priceOut/ctx are added so the in-widget pricing table shows
        # real numbers for estimated models too. They were previously undefined
        # and rendered as em-dashes, which reads as "price failed to load".
        parts.append("priceIn: %s, priceOut: %s" % (js_num(pid), js_num(pout)))
        parts.append("ctx: " + js_str(ctx))
        parts.append("est: { cjk: %s, ascii: %s }" % (cjk, ascii_))

    short = SHORT_NOTE.get(m["id"])
    if short:
        parts.append("note: " + js_str(short))

    parts.append("}")
    return ", ".join(parts)


def _entry_spans(block):
    """Yield (start, stop, id) for each object literal in the MODELS array.

    Entries nest an `est: { cjk, ascii }` object, so a non-greedy regex would
    stop at the wrong brace. Slicing on the positions of the next `{ id:`
    (or the array terminator) is unambiguous.
    """
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'\{\s*id:\s*"([^"]+)"', block)]
    tail = block.rindex("];")
    for i, (pos, mid) in enumerate(starts):
        stop = starts[i + 1][0] if i + 1 < len(starts) else tail
        yield pos, stop, mid


def reconcile(block, by_id):
    """Rewrite priceIn / priceOut / ctx on entries that already exist.

    This used to be insert-only, so a correction in the JSON never reached the
    calculator: gemini-3.6-flash sat at 1.50/7.50 in app.js while the JSON said
    0.75/3.75, and the widget quoted the old number to every visitor. The JSON is
    the source of truth, so existing entries get pulled back into line rather than
    assumed correct. Entries with no JSON counterpart (the `custom` row) are left
    alone, and est ratios are never touched.
    """
    edits = []
    out = []
    cursor = 0
    for pos, stop, mid in _entry_spans(block):
        m = by_id.get(mid)
        if not m:
            continue
        seg = block[pos:stop]
        new = seg
        pid = m.get("priceInputPer1M")
        pout = m.get("priceOutputPer1M") or 0
        if pid is not None and "priceIn:" in new:
            want_in, want_out = "priceIn: " + js_num(pid), "priceOut: " + js_num(pout)
            got = re.search(r"priceIn:\s*([\d.eE+-]+),\s*priceOut:\s*([\d.eE+-]+)", new)
            # Compare as floats. js_num renders 3.0 as "3", so a text comparison
            # would flag every trailing-zero entry in the file as a correction
            # and bury the one model whose price actually moved.
            if got and (float(got.group(1)) != float(pid) or float(got.group(2)) != float(pout)):
                new = re.sub(
                    r"priceIn:\s*[\d.eE+-]+,\s*priceOut:\s*[\d.eE+-]+",
                    want_in + ", " + want_out,
                    new,
                    count=1,
                )
                edits.append("%s %s/%s -> %s/%s" % (mid, got.group(1), got.group(2), js_num(pid), js_num(pout)))
        ctx = m.get("contextWindow")
        if ctx and 'ctx: "' in new:
            got = re.search(r'ctx:\s*"([^"]*)"', new)
            if got and got.group(1) != ctx:
                new = new.replace(got.group(0), 'ctx: "%s"' % ctx, 1)
                edits.append("%s ctx %s -> %s" % (mid, got.group(1), ctx))
        if new != seg:
            out.append(block[cursor:pos])
            out.append(new)
            cursor = stop
    if not edits:
        return block, []
    out.append(block[cursor:])
    return "".join(out), edits


def main():
    if not REPO_APPJS.exists():
        raise SystemExit("repo/js/app.js not found")
    src = REPO_APPJS.read_text(encoding="utf-8")

    start = src.index("{ id:")
    end = src.index("];", start)
    block = src[start : end + 2]
    existing = set(re.findall(r'\{\s*id:\s*"([^"]+)"', block))

    data = json.loads(DATA.read_text(encoding="utf-8"))
    wanted = [m["id"] for m in data["models"]]
    by_id = {m["id"]: m for m in data["models"]}

    todo = [m for m in data["models"] if m["id"] not in existing]
    print("app.js MODELS entries : %d" % len(existing))
    print("model-prices.json     : %d" % len(wanted))
    print("to insert             : %d" % len(todo))

    block, edits = reconcile(block, by_id)
    for e in edits:
        print("  ~ %s" % e)
    if not edits:
        print("  ~ prices already match the JSON")

    if not todo and not edits:
        # Still mirror repo -> site. site/js/app.js is the stale copy that
        # site/ was built from, and an overwrite in either direction must be
        # harmless; skipping this write is what made the drift come back.
        MIRROR_APPJS.parent.mkdir(parents=True, exist_ok=True)
        MIRROR_APPJS.write_text(src, encoding="utf-8")
        print("\nnothing to insert - app.js already in sync")
        for f in (REPO_APPJS, MIRROR_APPJS):
            print("mirrored    : %s" % f.relative_to(ROOT))
        return 0

    lines = []
    for m in todo:
        lines.append(build_entry(m, src))
        print("  + %s" % m["label"])

    tail = block.rstrip()
    if not tail.endswith("];"):
        raise SystemExit("unexpected array terminator: %r" % tail[-20:])
    body = tail[:-2]

    if lines:
        new_block = body + ",\n" + ",\n".join(lines) + "\n];"
    else:
        new_block = body + "\n];"
    out = src[:start] + new_block + src[end + 2 :]

    if CHECK:
        print("\n--check: nothing written")
        return 0

    REPO_APPJS.write_text(out, encoding="utf-8")
    MIRROR_APPJS.parent.mkdir(parents=True, exist_ok=True)
    MIRROR_APPJS.write_text(out, encoding="utf-8")

    chk = REPO_APPJS.read_text(encoding="utf-8")
    s2 = chk.index("{ id:")
    e2 = chk.index("];", s2)
    now = re.findall(r'\{\s*id:\s*"([^"]+)"', chk[s2:e2])
    still_missing = [i for i in wanted if i not in now]
    donors_ok = all(d in now for d in EST_INHERIT.values())

    print("\ninserted    : %d" % len(todo))
    print("reconciled  : %d" % len(edits))
    print("now present : %d" % len(now))
    print("donors kept : %s" % ("yes" if donors_ok else "NO - INVESTIGATE"))
    if still_missing:
        raise SystemExit("post-write verification failed, missing: %s" % still_missing)

    # The whole point of reconcile: after writing, app.js must agree with the
    # JSON on price, not merely contain the same ids.
    final = re.findall(r'\{\s*id:\s*"([^"]+)"[^}]*?priceIn:\s*([\d.eE+-]+),\s*priceOut:\s*([\d.eE+-]+)', chk)
    have = {i: (a, b) for i, a, b in final}
    drift = []
    for m in data["models"]:
        if m["id"] not in have or m.get("priceInputPer1M") is None:
            continue
        a, b = have[m["id"]]
        if float(a) != float(m["priceInputPer1M"]) or float(b) != float(m.get("priceOutputPer1M") or 0):
            drift.append("%s app %s/%s vs json %s/%s" % (m["id"], a, b, js_num(m["priceInputPer1M"]), js_num(m.get("priceOutputPer1M") or 0)))
    if drift:
        raise SystemExit("price drift after write:\n  " + "\n  ".join(drift))
    print("price check : app.js agrees with the JSON")
    for f in (REPO_APPJS, MIRROR_APPJS):
        print("written     : %s" % f.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
