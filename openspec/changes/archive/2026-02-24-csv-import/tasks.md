## 1. Normalizer Framework

- [x] 1.1 Create `finance/ingestion/csv_import.py` with a `Transaction` dataclass (or TypedDict) matching the `transactions` table columns
- [x] 1.2 Define the `NORMALIZERS: dict[str, Callable]` registry mapping institution key → normalizer function
- [x] 1.3 Implement `normalize_row(institution: str, row: dict, account_id: str) -> Transaction | None` — looks up normalizer in registry, calls it, returns result or None
- [x] 1.4 Implement `generate_csv_id(account_id: str, date: str, amount: str, description: str) -> str` — `sha256(f"{account_id}|{date}|{amount}|{description}".encode()).hexdigest()[:16]`

## 2. Institution Normalizers

- [x] 2.1 Implement `normalize_chase(row, account_id)` — columns: `Transaction Date`, `Amount`, `Description`; amount is already signed
- [x] 2.2 Implement `normalize_discover(row, account_id)` — columns: `Trans. Date`, `Amount`, `Description`; amount sign: negative = debit
- [x] 2.3 Implement `normalize_discover_debit(row, account_id)` — columns: `Date`, `Amount`, `Description`; verify sign convention with real export
- [x] 2.4 Implement `normalize_citi(row, account_id)` — columns: `Date`, `Debit`, `Credit`, `Description`; merge: `amount = -abs(debit)` if debit else `+abs(credit)`
- [x] 2.5 Implement `normalize_amex(row, account_id)` — columns: `Date`, `Amount`, `Description`; verify sign convention (Amex may invert)
- [x] 2.6 Implement `normalize_robinhood(row, account_id)` — columns: `Activity Date`, `Amount`, `Description`; buys = negative
- [x] 2.7 Implement `normalize_m1(row, account_id)` — columns: TBD from real export; best-effort implementation

## 3. Import Orchestration

- [x] 3.1 Implement `import_csv(conn, filepath: str, institution: str, account_id: str) -> dict` — opens CSV with `csv.DictReader`, normalizes each row, runs `INSERT OR IGNORE INTO transactions`; returns `{rows_read, rows_imported, rows_skipped}`
- [x] 3.2 Implement account auto-creation path: if `account_id` is None, prompt user for account name and create a new account record with `source='csv'`, return the new `account_id`

## 4. CLI Commands

- [x] 4.1 Add `finance import <file>` command to `cli.py` — accepts `--institution` (required), `--account` (optional); calls `import_csv()`; prints import summary
- [x] 4.2 Add `finance institutions` command — iterates `NORMALIZERS.keys()`, prints one per line
- [x] 4.3 Wire auto-categorization: after `import_csv()` succeeds, call `finance.ai.categorize.categorize_uncategorized(conn)` (no-op if `ANTHROPIC_API_KEY` not set)

## 5. Verification

- [x] 5.1 Verify `finance institutions` lists all 7 supported institution keys
- [x] 5.2 Verify `finance import --institution unknown file.csv` exits non-zero with a clear error
- [x] 5.3 Import a real Chase CSV export and verify transactions appear in DB with correct dates, amounts, and signs
- [x] 5.4 Re-import the same Chase CSV and verify 0 new rows are inserted (dedup working)
- [x] 5.5 Verify Citi Debit/Credit column merge produces correct sign (import a Citi CSV with known debit row)
