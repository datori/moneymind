## 1. Schema Migration

- [x] 1.1 Add `ALTER TABLE transactions ADD COLUMN` calls for `needs_review`, `review_reason`, `is_recurring`, and `merchant_normalized` to `init_db()` in `finance/db.py`, each wrapped in `try/except OperationalError` to be idempotent on existing databases
- [x] 1.2 Verify migration runs cleanly on a live database with existing transactions (no data loss, no error)
- [x] 1.3 Verify migration is a no-op when columns already exist (re-running `init_db` is safe)

## 2. Merchant Normalization Helper

- [x] 2.1 Create `finance/ai/enrich.py` with `_normalize_merchant_key(merchant_name: str | None, description: str | None) -> str` that applies lowercase, `*SUFFIX` stripping, `.com`/`.net`/`.org` stripping, and whitespace collapse
- [x] 2.2 Write inline tests or a manual smoke test confirming `"NETFLIX.COM *1234"` → `"netflix"`, `"NETFLIX*"` → `"netflix"`, `"Netflix"` → `"netflix"`, and description fallback works

## 3. Merchant Cluster Builder

- [x] 3.1 Add `_build_clusters(conn) -> list[dict]` to `finance/ai/enrich.py` that queries all transactions, groups by `merchant_key`, and returns a list of cluster dicts: `{merchant_key, raw_samples, transaction_ids, amounts}`
- [x] 3.2 Ensure clusters with a single transaction are included (single-occurrence merchants can still be recurring or need review)

## 4. LLM Enrichment Batch Call

- [x] 4.1 Add `_enrich_batch(clusters: list[dict]) -> list[dict]` to `finance/ai/enrich.py` that sends up to 40 clusters per call to `claude-haiku-4-5-20251001`, requesting JSON output with fields `merchant_key`, `canonical_name`, `is_recurring`, and `transactions: [{id, needs_review, review_reason}]`
- [x] 4.2 Implement markdown fence stripping and JSON parse error handling (mirror the pattern from `categorize.py`)
- [x] 4.3 Wrap each batch in `try/except` that logs a warning and skips the batch on `anthropic.APIError` or `ValueError`

## 5. DB Write-back and Entry Point

- [x] 5.1 Add `_write_results(conn, results: list[dict]) -> None` to `finance/ai/enrich.py` that updates `merchant_normalized`, `is_recurring`, `needs_review`, and `review_reason` for each transaction ID returned by the model, then commits
- [x] 5.2 Add `enrich_transactions(conn: sqlite3.Connection) -> int` as the public entry point: calls `_build_clusters`, iterates batches via `_enrich_batch`, calls `_write_results`, returns total transactions written
- [x] 5.3 Confirm that `merchant_normalized` is written for all transactions (not just flagged ones) — every transaction gets a canonical merchant name

## 6. Analysis Layer

- [x] 6.1 Create `finance/analysis/review.py` with `get_review_queue(conn) -> list[dict]` returning all transactions where `needs_review=1` ordered by `date DESC`, with fields: `id`, `date`, `amount`, `description`, `merchant_name`, `merchant_normalized`, `category`, `review_reason`, `account_id`
- [x] 6.2 Add `get_recurring(conn) -> list[dict]` to `finance/analysis/review.py` returning distinct `merchant_normalized` entries where `is_recurring=1`, with `count` and `typical_amount` (median or mode of absolute amounts), ordered by `count DESC`

## 7. CLI Integration Hook

- [x] 7.1 In `finance/cli.py` `sync` command: after `sync_all` and categorization complete, call `enrich_transactions(conn)` if `ANTHROPIC_API_KEY` is set; catch and log any exception without re-raising
- [x] 7.2 In `finance/cli.py` `categorize` command: after `categorize_uncategorized`/`categorize_all` completes, call `enrich_transactions(conn)` if `ANTHROPIC_API_KEY` is set; catch and log any exception without re-raising

## 8. CLI: finance review

- [x] 8.1 Add `finance review` command to `finance/cli.py` with `--list` flag option
- [x] 8.2 Implement `--list` mode: call `get_review_queue(conn)` and print a table with columns Date, Amount, Merchant, Category, Reason; show "No transactions flagged for review." if empty
- [x] 8.3 Implement interactive mode (no `--list`): iterate flagged transactions one at a time, display fields, prompt `[a]ccept / [r]eclassify / [s]kip`
- [x] 8.4 Implement accept action: set `needs_review=0`, commit
- [x] 8.5 Implement reclassify action: prompt for category name, validate against `CATEGORIES`, set `needs_review=0` and update `category`, commit; re-prompt on invalid input
- [x] 8.6 Implement skip action: no DB write, advance to next
- [x] 8.7 Print summary at end: "Reviewed N transaction(s). Accepted: X. Reclassified: Y. Skipped: Z."

## 9. CLI: finance recurring

- [x] 9.1 Add `finance recurring` command to `finance/cli.py` that calls `get_recurring(conn)` and prints a table with columns Merchant, Count, Typical Amount
- [x] 9.2 Show "No recurring charges detected. Run `finance sync` to enrich transactions." when the list is empty

## 10. Web: GET /review

- [x] 10.1 Add `GET /review` route to `finance/web/app.py` that calls `get_review_queue(conn)` and renders a new `review.html` Jinja2 template
- [x] 10.2 Create `finance/web/templates/review.html` extending `base.html`, showing a table with columns: Date, Amount, Description, Merchant, Category (dropdown of all CATEGORIES), Reason, and an "Approve" button per row
- [x] 10.3 Add `POST /review/{transaction_id}/approve` route that sets `needs_review=0`, updates `category` to the submitted value if changed, commits, and redirects to `GET /review`
- [x] 10.4 Render "No transactions flagged for review." message when `get_review_queue` returns empty

## 11. Web: GET /recurring

- [x] 11.1 Add `GET /recurring` route to `finance/web/app.py` that calls `get_recurring(conn)` and renders a new `recurring.html` Jinja2 template
- [x] 11.2 Create `finance/web/templates/recurring.html` extending `base.html`, showing a table with columns: Merchant, Occurrences, Typical Amount
- [x] 11.3 Render "No recurring charges detected." message when `get_recurring` returns empty

## 12. Navigation and Polish

- [x] 12.1 Add "Review" and "Recurring" links to the nav bar in `base.html`
- [x] 12.2 Manual end-to-end test: run `finance sync`, confirm enrichment runs, check `finance review --list` and `finance recurring` output, verify web routes load
