# Adding cases

Only edit `ai-crypto/data/cases.json`. Append new objects to the array using the same fields as existing entries:
slug (unique, kebab-case), title, title_zh, summary, summary_zh, category (ai-fails|agent-news|security|tax|sentiment),
type (incident|news|firsthand|tool), tier (featured|base), tools[], source_url, source_platform, date (YYYY-MM), engagement, vendor.

Rules: slug must be unique; do not add a source_url that already exists; source_url must open; never edit files outside `ai-crypto/`.
