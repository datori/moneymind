## Context

The current dashboard has four issues this change addresses:

**Redundant pages:** `GET /accounts` renders `accounts.html` (account list + a data coverage section powered by `get_data_overview()`). `GET /data` renders `data.html` (per-account txn counts, date ranges, last synced). Both pages call `get_data_overview(conn)`. The data page is a strict subset of what the accounts page already shows, displayed with slightly different formatting. This duplication confuses navigation.

**No web-based account deletion:** `finance accounts delete <id> --confirm` exists in the CLI but there is no way to delete an account from the browser. Stale/test accounts require dropping to the terminal.

**No category filter on transactions:** `GET /transactions` accepts `start`, `end`, and `limit` query params. The underlying `get_transactions()` function already supports a `category` parameter, but the route doesn't expose it and the template has no dropdown.

**Financial noise in spending:** `GET /spending` calls `get_spending_summary()` which aggregates all debits (`amount < 0`). Investment accounts (M1) generate dividend income (positive) and financial charges like margin interest (negative) — these are not "spending" in the consumer sense. They inflate category totals and obscure real spending patterns.

Current file state:
- `finance/web/app.py` — `GET /accounts` calls `get_accounts()` + `get_data_overview()`; `GET /data` calls only `get_data_overview()`; `GET /transactions` route does not pass `category`; `GET /spending` calls `get_spending_summary()` without filtering
- `finance/analysis/spending.py` — `get_spending_summary(conn, start_date, end_date, group_by='category')` has no `exclude_categories` parameter
- `finance/analysis/overview.py` — `get_data_overview(conn)` returns `{"global": {...}, "per_account": [...]}`; per_account entries include `account_id`, `account_name`, `txn_count`, `earliest_txn`, `latest_txn`, `last_synced_at`, `last_balance_at`
- `finance/ai/categories.py` — `CATEGORIES` list of 15 strings

## Goals / Non-Goals

**Goals:**
- Merge `/accounts` and `/data` into a unified `/accounts` page; convert `/data` to a 301 redirect.
- Add `POST /accounts/{id}/delete` with cascade and inline confirmation UI on the accounts page.
- Add `?category=` filter to `/transactions` route and template.
- Add `?include_financial=` toggle to `/spending` route; modify `get_spending_summary()` to accept `exclude_categories`.
- Remove "Data" nav link; keep "Accounts" nav link.

**Non-Goals:**
- Multi-category filter on transactions (single-category is sufficient for now).
- Soft-delete / undo for account deletion — hard delete only.
- Session or cookie persistence for spending toggle state — URL param is sufficient and shareable.
- Changing `get_data_overview()` signature or return shape.
- Adding balance counts to `get_data_overview()` — the delete confirmation fetches counts inline via a separate query in the route.

## Decisions

### Decision 1: Unified accounts page column layout

The merged per-account table needs columns from two sources:
- `get_accounts(conn)` → account `id`, `name`, `type`, `mask`, `institution_name`, latest `balance`
- `get_data_overview(conn)["per_account"]` → `txn_count`, `earliest_txn`, `latest_txn`, `last_synced_at`

**Approach:** The route handler calls both functions and merges by `account_id`. Since `get_data_overview` returns a list, build a lookup dict `{account_id: overview_row}` and merge in the template or route. Merging in the route (producing a combined list of dicts) is simpler for the template.

Final merged row shape passed to template per account:
```
id, name, institution_name, type, mask, balance, txn_count,
earliest_txn, latest_txn, last_synced_at,
txn_count (for delete confirmation), balance_count (new)
```

`balance_count` is needed for the delete confirmation text. It is **not** in `get_data_overview()`. Rather than modifying that function, the route runs a single additional query:
```sql
SELECT account_id, COUNT(*) as balance_count
FROM balances
GROUP BY account_id
```
This is joined into the merged list in the route handler.

### Decision 2: Inline delete confirmation (no separate page)

**Options considered:**
- A: Navigate to `/accounts/{id}/delete-confirm` page showing impact, then confirm.
- B: Inline expansion within the accounts table row using a hidden div toggled by JS.

**Chosen: B.** For a personal single-user tool, inline confirmation is faster and avoids a page navigation. The template renders the impact counts (pre-loaded from context) inside a hidden `<div>` per row. A single JS `onclick` toggles visibility. The `<form>` inside the div POSTs to `/accounts/{id}/delete` on confirm. No JavaScript fetch is required — all counts are already in the template context.

The hidden div pattern (Tailwind `hidden` / `block`):
```html
<div id="del-{account.id}" class="hidden">
  This will permanently delete {{ account.txn_count }} transactions
  and {{ account.balance_count }} balance snapshots.
  <form method="post" action="/accounts/{{ account.id }}/delete">
    <button type="submit">Confirm Delete</button>
  </form>
  <button onclick="document.getElementById('del-{{ account.id }}').classList.add('hidden')">Cancel</button>
</div>
```

### Decision 3: POST /accounts/{id}/delete cascade order

SQLite does not enforce foreign key constraints unless `PRAGMA foreign_keys = ON` (not set in `db.py`). Regardless, deletes proceed in dependency order within a single transaction:

1. `DELETE FROM credit_limits WHERE account_id = ?`
2. `DELETE FROM sync_state WHERE account_id = ?`
3. `DELETE FROM transactions WHERE account_id = ?`
4. `DELETE FROM balances WHERE account_id = ?`
5. `DELETE FROM accounts WHERE id = ?`

The handler captures `txn_count` and `balance_count` **before** deletion (from the initial query) for use in the flash message.

### Decision 4: Category filter — single vs. multi-category

**Chosen: Single category** (`WHERE t.category = ?`). Multi-category would require a `WHERE t.category IN (?)` with proper parameterization and a multi-select UI. The single-category dropdown covers the immediate use case (filter to a specific category) with no additional query complexity. Multi-category can be added later.

### Decision 5: Spending toggle — URL param vs. cookie vs. session

**Chosen: URL param** (`?include_financial=1`). URL params are stateless, shareable, and bookmark-able. The default (absent param) means "exclude financial" — the safer, more useful default for daily use. The form on the spending page includes a hidden input for `include_financial` so existing date/group_by params are preserved when the checkbox is toggled and the form is submitted.

### Decision 6: get_spending_summary signature change

Add `exclude_categories: list[str] | None = None` parameter:

```python
def get_spending_summary(conn, start_date, end_date, group_by='category',
                         exclude_categories=None):
```

When `exclude_categories` is a non-empty list, add `AND t.category NOT IN (...)` to the WHERE clause using SQLite's parameterized `IN` with a placeholder per element. When `None` (default), no additional filter is applied — fully backward compatible.

The `/spending` route constructs `exclude_categories = ['Financial', 'Income', 'Investment']` when `include_financial` is absent or `'0'`, and `None` when `include_financial == '1'`.

The `/` (index) route also calls `get_spending_summary()` for the dashboard card. It should also apply the default exclusion (Financial/Income/Investment) so the dashboard spending summary matches the spending page default.

## Risks / Trade-offs

- **Merged table query count:** The unified accounts page now runs 3 queries (`get_accounts`, `get_data_overview`, balance_count query). For a personal tool with <20 accounts this is negligible.
- **Delete pre-counts may be stale:** The impact counts shown in the confirmation (from page load) could differ from actual counts at the moment of deletion if a sync ran between page load and confirm click. The flash message after deletion uses the actual deleted row counts, which are the source of truth. The confirmation text is informational only.
- **Spending toggle state not persisted:** If the user checks "Include Financial Activity" and then navigates to another page and back, the toggle resets to off. URL params solve this for links/bookmarks but not for in-session navigation. Acceptable trade-off for a personal tool.
- **index.html spending now excludes financial:** The dashboard spending summary will change behavior (Financial/Income/Investment excluded by default). This is the intended outcome but is a behavioral change to an existing page.

## Migration Plan

No schema changes. No data migrations. All changes are to Python source and HTML templates:
1. Modify `finance/analysis/spending.py` (add `exclude_categories` param).
2. Modify `finance/web/app.py` (route changes: accounts, data redirect, transactions, spending, new delete route).
3. Rewrite `finance/web/templates/accounts.html`.
4. Modify `finance/web/templates/transactions.html` (add category dropdown).
5. Modify `finance/web/templates/spending.html` (add toggle).
6. Modify `finance/web/templates/base.html` (remove "Data" link).

Rollback: revert the file edits. No DB state is changed by these code changes.
