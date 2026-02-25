## 1. get_spending_summary: add exclude_categories parameter

- [ ] 1.1 In `finance/analysis/spending.py`, update `get_spending_summary()` signature:
  ```python
  def get_spending_summary(
      conn: sqlite3.Connection,
      start_date: str,
      end_date: str,
      group_by: str = "category",
      exclude_categories: list[str] | None = None,
  ) -> list[dict]:
  ```
- [ ] 1.2 After the existing `WHERE t.amount < 0 AND t.date >= ? AND t.date <= ?` clause, add exclusion logic: if `exclude_categories` is a non-empty list, append `AND t.category NOT IN ({placeholders})` and extend `params` with the list values. Use `", ".join("?" * len(exclude_categories))` for the placeholder string.
- [ ] 1.3 Update the docstring to document the new parameter.
- [ ] 1.4 Verify backward compat: calling `get_spending_summary(conn, start, end)` without `exclude_categories` returns the same result as before.
- [ ] 1.5 Verify exclusion: calling with `exclude_categories=['Financial', 'Income', 'Investment']` returns no rows with those labels.

---

## 2. /spending route: include_financial toggle

- [ ] 2.1 In `finance/web/app.py`, update `GET /spending` route signature to add `include_financial: str = "0"` query parameter.
- [ ] 2.2 Compute `exclude_cats`: if `include_financial != "1"`, set `exclude_cats = ['Financial', 'Income', 'Investment']`; otherwise `exclude_cats = None`.
- [ ] 2.3 Pass `exclude_categories=exclude_cats` to `get_spending_summary()`.
- [ ] 2.4 Pass `include_financial=include_financial` to the template context.
- [ ] 2.5 In `finance/web/templates/spending.html`, add an "Include Financial Activity" checkbox to the filter form:
  - The checkbox `name="include_financial"` and `value="1"`
  - Checked state: `{% if include_financial == '1' %}checked{% endif %}`
  - The form should use `method="get"` (already the case) so all params appear in the URL
  - Add a hidden input to preserve `group_by` when the form is submitted via the checkbox (or ensure the form already has `group_by` as a visible select/hidden field)
- [ ] 2.6 Load `/spending` — confirm Financial/Income/Investment rows absent from table by default.
- [ ] 2.7 Check "Include Financial Activity" and submit — confirm those categories appear and `include_financial=1` is in the URL.

---

## 3. /spending route on index: exclude financial by default

- [ ] 3.1 In `finance/web/app.py`, update the `GET /` route to pass `exclude_categories=['Financial', 'Income', 'Investment']` when calling `get_spending_summary()` for the dashboard spending card.
- [ ] 3.2 Load `/` and confirm the spending summary table on the dashboard no longer shows Financial/Income/Investment rows.

---

## 4. /transactions route: category filter

- [ ] 4.1 In `finance/web/app.py`, update `GET /transactions` route signature to add `category: str | None = None` query parameter.
- [ ] 4.2 Pass `category=category` to `get_transactions()`.
- [ ] 4.3 Add `from finance.ai.categories import CATEGORIES` to the imports in `app.py` (if not already imported).
- [ ] 4.4 Pass `categories=CATEGORIES` and `category=category or ""` to the template context.
- [ ] 4.5 In `finance/web/templates/transactions.html`, add a category `<select>` to the filter form:
  - First option: `<option value="">All Categories</option>` (selected when `category == ""`)
  - Remaining options: `{% for cat in categories %}<option value="{{ cat }}" {% if cat == category %}selected{% endif %}>{{ cat }}</option>{% endfor %}`
  - The select element `name="category"`
- [ ] 4.6 Load `/transactions` — confirm the dropdown appears with "All Categories" selected and all transactions show.
- [ ] 4.7 Select "Groceries" and submit — confirm only Groceries transactions appear and `?category=Groceries` is in the URL.
- [ ] 4.8 Confirm navigating back (browser back button) restores the filter state from the URL.

---

## 5. Unified /accounts page

- [ ] 5.1 In `finance/web/app.py`, update `GET /accounts` route to:
  - Call `get_accounts(conn)` → `accounts`
  - Call `get_data_overview(conn)` → `overview`
  - Run a balance count query:
    ```python
    balance_rows = conn.execute(
        "SELECT account_id, COUNT(*) as cnt FROM balances GROUP BY account_id"
    ).fetchall()
    balance_counts = {r["account_id"]: r["cnt"] for r in balance_rows}
    ```
  - Build a lookup `{acct["id"]: overview_row}` from `overview["per_account"]`
  - Merge into a single list `merged_accounts` where each entry is a dict combining fields from `accounts[i]` with the matching overview entry and `balance_counts.get(id, 0)`:
    ```python
    merged_accounts = []
    for acct in accounts:
        ov = ov_lookup.get(acct["id"], {})
        merged_accounts.append({
            **dict(acct),
            "txn_count": ov.get("txn_count", 0),
            "earliest_txn": ov.get("earliest_txn"),
            "latest_txn": ov.get("latest_txn"),
            "last_synced_at": ov.get("last_synced_at"),
            "balance_count": balance_counts.get(acct["id"], 0),
        })
    ```
  - Pass `merged_accounts`, `overview` (for global summary bar) to the template.

- [ ] 5.2 Rewrite `finance/web/templates/accounts.html` to extend `base.html` and show:
  - **Global summary bar** at top: `{{ overview.global.account_count }} accounts · {{ overview.global.txn_count }} transactions · {{ overview.global.earliest_txn or '—' }} – {{ overview.global.latest_txn or '—' }}`
  - **Single rich table** with columns: Account Name, Institution, Type, Balance, Txns, Date Range, Last Synced, Actions
    - Account Name: `{{ acct.name }}{% if acct.mask %} ···{{ acct.mask }}{% endif %}`
    - Balance: formatted `$X,XXX.XX` in red if negative, gray dash if null
    - Txns: `{{ acct.txn_count }}`
    - Date Range: `{{ acct.earliest_txn or '—' }} – {{ acct.latest_txn or '—' }}`
    - Last Synced: human-readable (or `Never` if null)
    - Actions: `[Delete]` button

- [ ] 5.3 For each row, add an inline delete confirmation section (hidden by default):
  ```html
  <tr id="confirm-{{ acct.id }}" class="hidden bg-red-50">
    <td colspan="8" class="px-4 py-3 text-sm text-red-800">
      Permanently delete <strong>{{ acct.name }}</strong>?
      This removes {{ acct.txn_count }} transactions and {{ acct.balance_count }} balance snapshots.
      <form method="post" action="/accounts/{{ acct.id }}/delete" class="inline">
        <button type="submit" class="ml-4 ...">Confirm Delete</button>
      </form>
      <button onclick="document.getElementById('confirm-{{ acct.id }}').classList.add('hidden')" class="ml-2 ...">Cancel</button>
    </td>
  </tr>
  ```
  The [Delete] button in the Actions column: `onclick="document.getElementById('confirm-{{ acct.id }}').classList.remove('hidden')"`.

- [ ] 5.4 Load `/accounts` — confirm global summary bar and rich per-account table render correctly, including txn counts and date ranges.

---

## 6. POST /accounts/{id}/delete route

- [ ] 6.1 In `finance/web/app.py`, add:
  ```python
  @app.post("/accounts/{account_id}/delete")
  async def delete_account(
      account_id: str,
      request: Request,
      conn: sqlite3.Connection = Depends(get_db),
  ):
  ```
- [ ] 6.2 Look up the account by `id`; return `HTTPException(status_code=404)` if not found. Capture `account_name` for the flash message.
- [ ] 6.3 Capture counts before deletion:
  ```python
  txn_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE account_id=?", (account_id,)).fetchone()[0]
  bal_count = conn.execute("SELECT COUNT(*) FROM balances WHERE account_id=?", (account_id,)).fetchone()[0]
  ```
- [ ] 6.4 Execute cascade delete inside a single transaction:
  ```python
  conn.execute("BEGIN")
  conn.execute("DELETE FROM credit_limits WHERE account_id=?", (account_id,))
  conn.execute("DELETE FROM sync_state WHERE account_id=?", (account_id,))
  conn.execute("DELETE FROM transactions WHERE account_id=?", (account_id,))
  conn.execute("DELETE FROM balances WHERE account_id=?", (account_id,))
  conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
  conn.commit()
  ```
- [ ] 6.5 Build flash message: `f"Deleted '{account_name}' ({txn_count} transactions, {bal_count} balances removed)."`
- [ ] 6.6 Return `RedirectResponse(f"/accounts?msg={msg}", status_code=303)`.
- [ ] 6.7 Test: delete a real (or test) account and confirm the redirect shows the flash message and the account no longer appears in the table.
- [ ] 6.8 Test: POST to `/accounts/nonexistent-id/delete` and confirm 404.

---

## 7. /data redirect and nav cleanup

- [ ] 7.1 In `finance/web/app.py`, replace the `GET /data` route body with:
  ```python
  return RedirectResponse("/accounts", status_code=301)
  ```
  Remove the `get_data_overview` call and template render from this route.
- [ ] 7.2 In `finance/web/templates/base.html`, remove the `<a href="/data">Data</a>` nav link. Confirm "Accounts" link points to `/accounts`.
- [ ] 7.3 Verify: `curl -I http://localhost:8080/data` returns `HTTP/1.1 301` with `Location: /accounts`.
- [ ] 7.4 Verify: navigating to `/data` in the browser lands on the unified accounts page.

---

## 8. Verification

- [ ] 8.1 Load all dashboard pages and confirm no broken links or template errors.
- [ ] 8.2 On `/accounts`: global summary bar shows correct counts; per-account table shows txn counts, date ranges, balance; delete button expands confirmation row; confirming deletion removes the account.
- [ ] 8.3 On `/transactions`: category dropdown shows 16 options; selecting a category filters correctly; "All Categories" clears the filter.
- [ ] 8.4 On `/spending`: "Include Financial Activity" checkbox is unchecked by default; Financial/Income/Investment rows absent; checking and submitting shows those rows.
- [ ] 8.5 On `/` (dashboard): spending card does not show Financial/Income/Investment rows.
- [ ] 8.6 Nav bar: "Data" link absent; "Accounts" link present and routes to unified page.
