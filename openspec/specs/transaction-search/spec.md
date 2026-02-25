## ADDED Requirements

### Requirement: get_transactions supports search parameter

`get_transactions()` in `finance/analysis/spending.py` SHALL accept a new optional `search: str | None` parameter (default `None`). When provided and non-empty, the query SHALL append:

```sql
AND (t.description LIKE ? OR t.merchant_name LIKE ? OR t.merchant_normalized LIKE ?)
```

with the value `%{search}%` bound to all three placeholders. SQLite LIKE is case-insensitive for ASCII characters, which is sufficient for merchant and description data.

#### Scenario: Search filters by description substring
- **WHEN** `get_transactions(conn, start_date="2026-01-01", search="spotify")` is called
- **THEN** only transactions where description, merchant_name, or merchant_normalized contains "spotify" (case-insensitive) are returned

#### Scenario: Search with no matches returns empty list
- **WHEN** `get_transactions(conn, start_date="2026-01-01", search="zzz_no_match")` is called
- **THEN** an empty list is returned

#### Scenario: Search=None returns unfiltered results
- **WHEN** `get_transactions(conn, start_date="2026-01-01", search=None)` is called
- **THEN** all transactions within the date range are returned, unchanged from prior behavior

#### Scenario: Search combined with category filter
- **WHEN** `get_transactions(conn, start_date="2026-01-01", search="whole", category="Groceries")` is called
- **THEN** only transactions matching both the search string and the Groceries category are returned

---

### Requirement: Transactions page search input in filter bar

The `GET /transactions` route SHALL accept a `search: str | None` query parameter (default `None`) and pass it to `get_transactions()`. The route SHALL pass the current `search` value to the template as context.

The filter bar in `transactions.html` SHALL include a text input labeled "Search" with `name="search"` and `placeholder="merchant or description"`. The input's value SHALL reflect the current `search` query param. On form submission, the `search` param is included in the GET request alongside all other filter params.

#### Scenario: Search input appears in filter bar
- **WHEN** a browser navigates to `/transactions`
- **THEN** a text search input is visible in the filter bar

#### Scenario: Search filters displayed transactions
- **WHEN** the user types "netflix" in the search input and submits the form
- **THEN** the page reloads with `?search=netflix` and only transactions matching "netflix" in description, merchant_name, or merchant_normalized are shown

#### Scenario: Search preserved with other filters
- **WHEN** the transactions page is loaded with `?start=2026-02-01&category=Entertainment&search=netflix`
- **THEN** the search input shows "netflix", the category dropdown shows "Entertainment", and results match both filters

#### Scenario: Empty search returns all results (no filter applied)
- **WHEN** the user clears the search input and submits (sending `?search=` as an empty string)
- **THEN** the route normalizes `""` to `None`, no LIKE filter is applied, and all transactions in the date range are shown
