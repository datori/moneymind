## Why

Transaction categorization today is a one-pass label assignment. There is no mechanism to detect recurring/subscription charges or flag transactions that deserve a second look (unusual amounts, possible duplicates, price changes, unfamiliar merchants). Adding a whole-dataset enrichment pass on top of the existing categorization pipeline closes this gap and surfaces the intelligence the single-user owner actually cares about after a sync.

## What Changes

- **New enrichment pipeline (Pass 2):** After Pass 1 categorization completes, group all transactions by fuzzy-normalized merchant name and send merchant clusters to `claude-haiku-4-5-20251001` to identify recurring/subscription charges and transactions needing review. Results written back to the DB. Idempotent — re-running re-evaluates everything.
- **Schema migration:** Four new columns added to `transactions` (migration via `ALTER TABLE … ADD COLUMN IF NOT EXISTS`-style guard, safe for existing databases):
  - `needs_review INTEGER DEFAULT 0`
  - `review_reason TEXT`
  - `is_recurring INTEGER DEFAULT 0`
  - `merchant_normalized TEXT`
- **New analysis module:** `finance/analysis/review.py` — pure query functions `get_review_queue(conn)` and `get_recurring(conn)`.
- **New CLI commands:** `finance review` (interactive triage) / `finance review --list` (table view) / `finance recurring` (summary table).
- **New web routes:** `GET /review` and `GET /recurring`.
- **Integration hook:** Enrichment pass triggered automatically at the end of `finance sync` and `finance categorize` when `ANTHROPIC_API_KEY` is set; failures are non-fatal.

## Capabilities

### New Capabilities

- `merchant-enrichment`: Two-pass LLM pipeline — merchant normalization, fuzzy clustering, recurring detection, and needs-review flagging. Covers the new `finance/ai/enrich.py` module and schema migration logic.
- `review-queue`: Analysis queries and CLI/web UX for surfacing and triaging flagged transactions (`get_review_queue`, `finance review`, `GET /review`).
- `recurring-detection`: Analysis query and CLI/web UX for summarizing detected recurring merchant clusters (`get_recurring`, `finance recurring`, `GET /recurring`).

### Modified Capabilities

- `transaction-categorization`: Enrichment pass (Pass 2) is triggered after Pass 1 completes in both `finance sync` and `finance categorize`. No existing categorization requirement changes — only new post-categorization behavior added.

## Impact

- **finance/db.py** — `init_db` must apply column migrations for the four new `transactions` columns.
- **finance/ai/categorize.py** — no logic changes; enrichment is called from CLI hooks, not from within categorize.py.
- **finance/ai/enrich.py** — new module (merchant normalization, cluster construction, LLM call, DB writes).
- **finance/analysis/review.py** — new module (pure query functions).
- **finance/cli.py** — two new top-level commands (`review`, `recurring`); post-categorization hook added to `sync` and `categorize` commands.
- **finance/web/app.py** — two new routes (`/review`, `/recurring`).
- **finance/web/templates/** — two new Jinja2 templates.
- **Dependencies:** No new packages required (anthropic SDK already present).
