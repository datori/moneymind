## 1. Category Color Badges — Macro

- [x] 1.1 Create `finance/web/templates/_macros.html` with the `{% macro category_badge(cat) %}` block — full 15-category if/elif chain and gray fallback for unknown/None values. **Not in `base.html`** — defining the macro there and importing it from child templates causes `UndefinedError: 'request' is undefined` because Jinja2 loads `base.html` in module mode (without request context) when it is both extended and imported in the same template.
- [x] 1.2 Verify the macro renders correct Tailwind classes for a sample of categories (Food & Dining → orange, Income → emerald, Other → gray)

## 2. Category Color Badges — Transactions Template

- [x] 2.1 Import the `category_badge` macro at the top of `finance/web/templates/transactions.html` using `{% from "_macros.html" import category_badge %}`
- [x] 2.2 Replace the plain `{{ txn.category or '—' }}` cell in the transactions table with `{{ category_badge(txn.category) }}`
- [x] 2.3 Load `/transactions` in a browser and confirm colored badges appear for categorized transactions and a gray dash for uncategorized ones

## 3. Category Color Badges — Spending Template

- [x] 3.1 Import the `category_badge` macro at the top of `finance/web/templates/spending.html` using `{% from "_macros.html" import category_badge %}`
- [x] 3.2 Update the spending table label cell to conditionally render `{{ category_badge(row.label) }}` when `group_by == 'category'` and plain `{{ row.label }}` otherwise
- [x] 3.3 Load `/spending?group_by=category` and confirm badges appear; load `/spending?group_by=merchant` and confirm plain text is used

## 4. Apple Card CSV Normalizer

- [x] 4.1 Add `normalize_apple(row, account_id)` function to `finance/ingestion/csv_import.py` following the same signature as existing normalizers
- [x] 4.2 Implement column extraction: `Transaction Date` → date, `Merchant` → merchant_name, `Description` → description, `Amount (USD)` → amount (negated), `Type` → skip if `"Payments"`
- [x] 4.3 Register `"apple": normalize_apple` in the `NORMALIZERS` dict
- [x] 4.4 Run `finance institutions` and confirm `apple` appears in the output
- [x] 4.5 Test with a sample Apple Card CSV (real or synthetic): confirm payment rows are skipped, purchase rows are imported with negated amounts and correct merchant_name

## 5. CLI — Convert `accounts` to Group

- [x] 5.1 In `finance/cli.py`, change `@main.command("accounts")` to `@main.group("accounts", invoke_without_command=True)` with a `@click.pass_context` decorator
- [x] 5.2 Move the existing accounts listing logic into a helper function `_accounts_list(conn, as_json)` callable from both default invocation and the explicit `list` subcommand
- [x] 5.3 Add a `@accounts.command("list")` subcommand that accepts `--json` and calls `_accounts_list`
- [x] 5.4 Wire up the `invoke_without_command=True` path so `finance accounts` (no subcommand) calls `_accounts_list` directly
- [x] 5.5 Run `finance accounts` and `finance accounts list` and confirm both produce identical account tables

## 6. CLI — `accounts delete` Subcommand

- [x] 6.1 Add `@accounts.command("delete")` with `ACCOUNT_ID` argument and `--confirm` flag (is_flag=True)
- [x] 6.2 Implement account existence check: query `accounts` table by ID; print error and exit non-zero if not found
- [x] 6.3 If `--confirm` not set, prompt `"Delete account '<name>' and all associated data? [y/N]"` and abort cleanly on non-yes input
- [x] 6.4 Execute the 5-step cascade delete inside a single `BEGIN`/`COMMIT` transaction: credit_limits → sync_state → transactions → balances → accounts
- [x] 6.5 Print success message including account name and per-table deleted row counts
- [x] 6.6 Test: run `finance accounts delete <nonexistent-id>` and confirm error + non-zero exit
- [x] 6.7 Test: run `finance accounts delete <valid-id>` and type `n` at prompt; confirm no rows deleted
- [x] 6.8 Test: run `finance accounts delete <valid-id> --confirm` and confirm all rows deleted across all 5 tables
