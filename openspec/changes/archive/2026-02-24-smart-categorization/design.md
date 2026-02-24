## Context

The system already runs a one-pass LLM categorization pipeline (`finance/ai/categorize.py`) that batches transactions to `claude-haiku-4-5-20251001` and writes a `category` label back to SQLite. This pipeline runs after `finance sync` and `finance categorize`. There is no existing mechanism to:

- Detect recurring/subscription patterns across transactions.
- Flag individual transactions for human review (unusual amounts, possible duplicates, price changes, unfamiliar merchants).
- Normalize merchant names for grouping.

The owner syncs daily and uses the CLI and web dashboard. ANTHROPIC_API_KEY is always set in the normal workflow.

## Goals / Non-Goals

**Goals:**

- Add a second LLM pass that normalizes merchant names and identifies recurring charges and review-worthy transactions across the whole dataset.
- Persist enrichment results in the DB with four new columns on `transactions`.
- Surface results through two new CLI commands (`finance review`, `finance recurring`) and two new web routes (`GET /review`, `GET /recurring`).
- Make the enrichment pass idempotent and non-fatal — failures must never break sync or categorize.
- Migrate the existing live database safely without destroying any data.

**Non-Goals:**

- Real-time enrichment on individual transaction insert (batch-only).
- Machine-learning models or embeddings for merchant clustering (LLM + regex normalization is sufficient).
- Multi-user support or API authentication.
- Changing existing Pass 1 categorization behavior.

## Decisions

### Decision 1: Schema migration via conditional ALTER TABLE

**Choice:** In `db.py` `init_db()`, after `executescript(_SCHEMA)`, execute four individual `ALTER TABLE transactions ADD COLUMN` statements wrapped in a try/except that silences `OperationalError: duplicate column name`. This is idiomatic SQLite migration for a single-user local database.

**Alternatives considered:**

- `PRAGMA table_info` check before each ALTER — more explicit but more verbose; the try/except approach is the SQLite community standard for this case.
- Schema versioning table — overkill for a single-user tool with no team deploys.
- Dropping and recreating the table — would destroy production data.

### Decision 2: Merchant normalization in Python before LLM call

**Choice:** Apply a lightweight Python normalization step first (lowercase, strip trailing `*SUFFIX`, strip `.COM`, collapse whitespace, strip leading/trailing punctuation) to produce a `merchant_key` used for grouping. Then send each cluster's raw description variants to the LLM for canonical display name production (`merchant_normalized`).

**Rationale:** Reduces the number of LLM calls significantly. The Python step handles mechanical noise ("NETFLIX.COM *1234" → "netflix"); the LLM step handles semantic normalization and produces a clean display name ("Netflix").

**Alternatives considered:**

- Pure LLM normalization on every transaction — too expensive and slow for large datasets.
- Pure regex normalization — misses ambiguous cases where LLM judgment improves quality.

### Decision 3: Single LLM call per merchant cluster batch for enrichment

**Choice:** Gather all merchant clusters (normalized key + list of transaction IDs + sample amounts + descriptions), batch up to 40 clusters per LLM call, and ask the model to return: `{merchant_key, canonical_name, is_recurring, transactions: [{id, needs_review, review_reason}]}`.

**Rationale:** The whole-dataset view is what enables recurring detection — the model needs to see multiple occurrences to infer subscription behavior. Batching by cluster (not by transaction) minimizes calls while keeping context coherent.

**Alternatives considered:**

- Per-transaction enrichment in Pass 1 prompt — clutters the categorization prompt and can't detect cross-transaction patterns.
- Separate call per cluster — too many small API calls for datasets with many distinct merchants.

### Decision 4: Enrichment module lives in `finance/ai/enrich.py`

**Choice:** New file `finance/ai/enrich.py` containing `enrich_transactions(conn)` — the entry point called from CLI hooks. Internal helpers: `_normalize_merchant_key(raw)`, `_build_clusters(conn)`, `_enrich_batch(clusters)`, `_write_results(conn, results)`.

**Rationale:** Consistent with existing `finance/ai/categorize.py` pattern. Keeps AI logic isolated from analysis queries.

### Decision 5: Analysis queries in `finance/analysis/review.py`

**Choice:** Pure query functions, no AI, no network — consistent with the `analysis/` module contract.

- `get_review_queue(conn)` → list of dicts for `needs_review=1`, ordered by date DESC.
- `get_recurring(conn)` → list of dicts: `{merchant_normalized, count, typical_amount}` for `is_recurring=1`, ordered by count DESC.

### Decision 6: CLI review command uses interactive single-item triage

**Choice:** `finance review` iterates flagged transactions one at a time. For each: show description, merchant, amount, date, category, review_reason. Prompt: `[a]ccept / [r]eclassify / [s]kip`. Accept sets `needs_review=0`. Reclassify prompts for new category then sets `needs_review=0` and updates `category`. Skip moves to next without writing.

`finance review --list` bypasses interaction and prints a table (non-destructive read).

**Rationale:** Single-item triage matches the personal use pattern — the owner reviews a handful of flagged items after each sync. A table-only mode is useful for a quick overview before triaging.

### Decision 7: Web /review uses POST for approve action

**Choice:** `GET /review` renders the table. Each row has a category `<select>` and an "Approve" button that submits `POST /review/{id}/approve` with optional `category` override. Approve sets `needs_review=0` (and updates category if changed).

**Rationale:** Follows the existing pattern in `app.py` (`POST /sync` → redirect). Avoids JavaScript for a simple single-user tool.

## Risks / Trade-offs

- **LLM cost per enrichment run** — re-running enrichment re-evaluates all transactions. For large datasets (thousands of transactions, hundreds of distinct merchants) this could incur non-trivial API cost. Mitigation: Enrichment only runs if `ANTHROPIC_API_KEY` is set; user can skip by not setting the key. Future optimization (skip unchanged clusters) is explicitly out of scope for this change.
- **LLM hallucinated review reasons** — the model may flag benign transactions or miss genuine issues. Mitigation: The review queue is purely advisory; the owner makes the final accept/reclassify decision.
- **SQLite ALTER TABLE is not transactional for schema changes** — if the process dies mid-migration, the DB may have some but not all new columns. Mitigation: Each `ADD COLUMN` is independent; re-running `init_db` will add missing columns and skip already-added ones.
- **Merchant normalization false positives** — different merchants may share a normalized key (e.g., "AMAZON" for both Amazon.com purchases and Amazon Web Services). Mitigation: The LLM sees raw description variants and can distinguish; clusters are keyed loosely but labeled precisely by the model.

## Migration Plan

1. `init_db(conn)` gains four `ALTER TABLE transactions ADD COLUMN` calls with `OperationalError` suppression. This runs on every `get_connection()` flow — existing databases migrate on first use after upgrade.
2. Existing `transactions` rows will have `needs_review=0`, `review_reason=NULL`, `is_recurring=0`, `merchant_normalized=NULL` after migration (SQLite default values apply to existing rows as NULL; `DEFAULT 0` applies to new inserts).
3. Running `finance sync` or `finance categorize` after upgrade will trigger the enrichment pass which populates `merchant_normalized`, `is_recurring`, and `needs_review` for all existing transactions.
4. No rollback strategy needed — this is a local single-user tool; columns can be dropped manually if needed.

## Open Questions

- None. All decisions are made; no external dependencies or team sign-offs required.
