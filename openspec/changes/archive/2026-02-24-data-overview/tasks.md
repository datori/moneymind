## 1. Analysis Layer

- [x] 1.1 Create `finance/analysis/overview.py` with `get_data_overview(conn)` function that queries active accounts LEFT JOIN transactions, sync_state, balances, and institutions to return `{"global": {...}, "per_account": [...]}`
- [x] 1.2 Verify `get_data_overview` handles accounts with no transactions (null dates, zero count), no sync_state row (null last_synced_at), and empty database (zero global counts, empty per_account list)

## 2. Web: Accounts Page Enhancement

- [x] 2.1 Update `finance/web/app.py` `/accounts` route to call `get_data_overview(conn)` and pass the result to the template
- [x] 2.2 Update `finance/web/templates/accounts.html` to add a "Data Coverage" section below the existing balance table, including the global summary header ("X transactions across Y accounts, covering Z months") and a per-account table (columns: name, institution, transaction count, date range as "Mon YY – Mon YY", last sync time relative)
- [x] 2.3 Handle null/zero edge cases in the accounts template: show "—" for missing date ranges, "Never" for null last_synced_at, "0" for zero txn_count

## 3. Web: New Data Page

- [x] 3.1 Add `GET /data` route in `finance/web/app.py` that calls `get_data_overview(conn)` and renders a new template
- [x] 3.2 Create `finance/web/templates/data.html` with the same global summary header and per-account coverage table as the accounts page Data Coverage section (full-page view, with nav and Sync Now button consistent with other pages)
- [x] 3.3 Add a "Data" navigation link to the shared nav across all dashboard templates (or the base layout if one exists)

## 4. CLI: finance data Command

- [x] 4.1 Add `finance data` command to `finance/cli.py` that calls `get_data_overview(conn)`, prints the global summary line, and prints a per-account table (columns: Account, Institution, Transactions, Earliest, Latest, Last Synced as absolute timestamp or "Never")
- [x] 4.2 Support `--json` flag on `finance data` that outputs the raw `get_data_overview` dict as valid JSON (consistent with other CLI commands)
- [x] 4.3 Handle empty-database case: print "No accounts found." when `per_account` is empty

## 5. Verification

- [x] 5.1 Run `finance data` against local database and confirm output matches expected format
- [x] 5.2 Navigate to `/accounts` in browser and confirm Data Coverage section renders correctly including edge cases
- [x] 5.3 Navigate to `/data` in browser and confirm full-page Data view renders correctly
- [x] 5.4 Run `finance data --json | jq .` and confirm valid JSON output with `global` and `per_account` keys
