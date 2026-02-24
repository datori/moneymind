## 1. Category Taxonomy

- [ ] 1.1 Create `finance/ai/categories.py` defining `CATEGORIES: list[str]` with all 15 categories: Food & Dining, Groceries, Transportation, Shopping, Entertainment, Travel, Health & Fitness, Home & Utilities, Subscriptions & Software, Personal Care, Education, Financial, Income, Investment, Other
- [ ] 1.2 Export `CATEGORIES_STR = ", ".join(CATEGORIES)` for use in prompts

## 2. Categorization Engine

- [ ] 2.1 Create `finance/ai/categorize.py` with `ANTHROPIC_API_KEY` loading from env
- [ ] 2.2 Implement `categorize_batch(transactions: list[dict]) -> list[dict]` — sends up to 50 transactions to `claude-haiku-4-5-20251001`; prompt asks for JSON array of `{id, category}`; returns parsed results; raises on API error
- [ ] 2.3 Implement `categorize_uncategorized(conn) -> int` — queries `WHERE categorized_at IS NULL`; processes in batches of 50 via `categorize_batch()`; updates `category` and `categorized_at = now()` for each result; returns total count updated; logs and skips batches that fail
- [ ] 2.4 Implement `categorize_all(conn) -> int` — same as `categorize_uncategorized` but queries all transactions (no `WHERE` filter)
- [ ] 2.5 Validate returned category values against `CATEGORIES` list; fall back to "Other" for any unrecognized value

## 3. Integration with Sync and Import

- [ ] 3.1 In `finance/ingestion/simplefin.py`: after `sync_all()` completes upserts, call `categorize_uncategorized(conn)` if `ANTHROPIC_API_KEY` is set; catch and log any exception without failing sync
- [ ] 3.2 In `finance/ingestion/csv_import.py`: after `import_csv()` completes, call `categorize_uncategorized(conn)` if `ANTHROPIC_API_KEY` is set; catch and log without failing import

## 4. CLI Commands

- [ ] 4.1 Add `finance categorize` command to `cli.py` — runs `categorize_uncategorized(conn)` by default; accepts `--all` flag to run `categorize_all(conn)`; prints count of transactions categorized
- [ ] 4.2 Add `finance fix-category <transaction-id> <category>` command — validates category is in `CATEGORIES`; runs `UPDATE transactions SET category=?, categorized_at=? WHERE id=?`
- [ ] 4.3 Handle missing `ANTHROPIC_API_KEY` in `finance categorize`: print clear error message and exit non-zero

## 5. Verification

- [ ] 5.1 Verify `finance categorize` exits with clear error when `ANTHROPIC_API_KEY` is not set
- [ ] 5.2 With `ANTHROPIC_API_KEY` set, run `finance categorize` against real transactions and verify `category` and `categorized_at` are populated
- [ ] 5.3 Verify all assigned categories are members of `CATEGORIES` (no hallucinated values)
- [ ] 5.4 Re-run `finance categorize` and verify 0 transactions are re-processed (incremental run respects `categorized_at`)
- [ ] 5.5 Run `finance categorize --all` and verify all transactions are re-categorized
- [ ] 5.6 Verify `finance spending --start ... --end ...` now shows meaningful category labels (not all null/Other)
