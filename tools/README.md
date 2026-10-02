# tools/

The scripts that produced this site. They are here to be read and audited, not to
be run from this directory — they expect a working tree layout that does not
exist inside the published repo.

## Layout they expect

```
<workspace>/
  _baseline/data/model-prices.json   pristine copy, patches are applied on top
  site/                              generated output, the thing that gets published
  repo/                              this directory's parent, the GitHub Pages repo
  tools/                             these scripts
```

Running `build.py` from here fails with `FileNotFoundError: _baseline/data/model-prices.json`,
which means "wrong directory", not "broken script".

## Order matters

```
python apply_patch.py pricing-patch-<date>.json   # data changes, one dated file per pass
python build.py                                    # rewrites site/ AND site/sitemap.xml
python gen_compare.py                              # appends the compare/ URLs to the sitemap
python sync_appjs.py                               # JSON and js/app.js are two copies of one truth
python gen_changelog.py                            # CHANGELOG.md from the patch files
python wire_homepage.py
```

`gen_compare.py` must run **after** `build.py`. `build.py` regenerates the
sitemap from scratch and knows nothing about the compare pages; `gen_compare.py`
appends them. Run them in the other order and six URLs silently vanish from
`robots.txt`'s sitemap target with no error anywhere.

## The two-copy trap

`data/model-prices.json` and `js/app.js` hold the same facts. They drift, and
the drift is invisible until a user quotes a stale price from the calculator.

- `sync_appjs.py` inserts new rows **and** reconciles the price and context of
  rows that already exist. Before that second half existed, a correction in the
  JSON never reached the widget.
- `sync_appjs.py` writes both `repo/js/app.js` and `site/js/app.js`, so an
  overwrite in either direction is harmless.
- `gen_changelog.py` writes `CHANGELOG.md` to both `repo/` and `site/` for the
  same reason: `deploy.ps1` robocopies `site/` over `repo/`, so whichever copy is
  stale wins.
- `verify.py` fails the build on any disagreement, and on a missing or stale
  `vendor` field.

## `provider` is not a vendor

`provider` on a model row also carries API product lines (`OpenAI (legacy)`,
`OpenAI embedding`) and, historically, a hosting region (`US & EU`, which held
Nova Pro, Llama 4 and the Grok models). Grouping by it yields nonsense.

`vendors.py` resolves the real company and every row also carries a `vendor`
field. **Group by `vendor`.** `apply_patch.py` re-stamps it on every run, and
`verify.py` fails if it is missing or stale.

## Files

| File | What it does |
|---|---|
| `vendors.py` | Shared vendor resolution. Imported by build, apply_patch and verify. |
| `apply_patch.py` | Applies a dated pricing patch. Refuses corrections to unknown ids, never mutates the baseline, stamps `vendor`, records the change in `_meta.revisions`. |
| `build.py` | Generates the per-model and per-provider pages, the sitemap, `llms-full.txt`. |
| `gen_compare.py` | Generates the "cheapest X" comparison pages and appends them to the sitemap. |
| `sync_appjs.py` | Reconciles `js/app.js` against the JSON, inserting new rows and updating existing ones. |
| `gen_changelog.py` | Generates `CHANGELOG.md` from the patch files. |
| `wire_homepage.py` | Links the landing page to every model and provider page. |
| `sweep_legacy.py` | Keeps the older calculator pages' model counts in step. |
| `sync_homepage.py` | Homepage counters. |
| `verify.py` | The build gate. Fails on disagreement, dangling links, duplicate titles, stale counts. |
| `check-live.ps1` | Fetches every URL in the live sitemap and checks status. |
| `fix_outreach_copy.py` | Keeps the model count in the outreach copy equal to the dataset. |

## The dataset's contract

`data/model-prices.json` is the asset. It is published under CC BY 4.0 and is
meant to be cited and grouped.

- Every price change is a dated patch file in `pricing-patch/`, carrying the
  source URL each figure came from. `CHANGELOG.md` is generated from them.
- `_meta.lastVerified` moves only when a provider page has actually been
  re-checked. It is the authoritative date.
- Figures that could not be verified are left **out**, and recorded under
  `flagged_not_changed` in the patch, rather than guessed. Three OpenAI GPT-6
  models sat in that list for one pass because two trackers appeared to
  disagree; the resolution was that one tracker applies a flat 20% discount to
  its whole catalogue, so the numbers had never actually conflicted.
- `_meta.fields` documents what each key means.