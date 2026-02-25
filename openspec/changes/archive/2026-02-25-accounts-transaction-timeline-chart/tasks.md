## 1. Analysis Layer

- [x] 1.1 Add `get_transaction_timeline(conn, account_id=None, months=13)` to `finance/analysis/accounts.py` — query transactions grouped by `strftime('%Y-%m', date)` and `account_id`, then Python-fill zeros for missing months to produce exactly `months` entries per account
- [x] 1.2 Verify the function returns correct structure: `{"months": [...], "accounts": [{"id", "name", "counts": [...]}]}`

## 2. Web Route

- [x] 2.1 Update `/accounts` route in `finance/web/app.py` to accept optional `account_id: str | None = None` query parameter
- [x] 2.2 Call `get_transaction_timeline(conn, account_id=account_id)` and serialize result to `chart_data_json` (JSON string compatible with Chart.js stacked bar format: labels + datasets array)
- [x] 2.3 Pass `chart_data_json`, `selected_account_id`, and the merged accounts list to the template

## 3. Template

- [x] 3.1 Add account selector `<select>` form above the chart in `finance/web/templates/accounts.html` — "All accounts" option + one option per account, pre-selects current `selected_account_id`, submits GET to `/accounts`
- [x] 3.2 Add Chart.js canvas element and initialization script — stacked bar when multiple accounts, single-dataset bar when one account is selected
- [x] 3.3 Assign a fixed 10-color palette deterministically by account index (consistent colors per account)
- [x] 3.4 Render month labels as `Mon 'YY` (e.g., "Jan '25") in the chart X-axis for readability
- [x] 3.5 Add a guard: if `chart_data_json` has no datasets or all counts are zero, show a "No transaction data" placeholder instead of an empty chart
