## ADDED Requirements

### Requirement: get_transactions supports sort_by and sort_dir parameters

`get_transactions()` in `finance/analysis/spending.py` SHALL accept two new optional parameters: `sort_by: str` (default `"date"`) and `sort_dir: str` (default `"desc"`). The `ORDER BY` clause SHALL be selected from a safe allowlist:

- `sort_by="date"`, `sort_dir="desc"` → `ORDER BY t.date DESC, t.id`
- `sort_by="date"`, `sort_dir="asc"` → `ORDER BY t.date ASC, t.id`
- `sort_by="amount"`, `sort_dir="desc"` → `ORDER BY ABS(t.amount) DESC, t.date DESC`
- `sort_by="amount"`, `sort_dir="asc"` → `ORDER BY ABS(t.amount) ASC, t.date DESC`

Any unrecognized `sort_by` or `sort_dir` value SHALL fall back to the default (`date DESC`). Values SHALL NOT be interpolated directly into SQL strings.

#### Scenario: Default sort is date descending
- **WHEN** `get_transactions(conn, start_date="2026-02-01")` is called with no sort params
- **THEN** results are ordered newest-first (date DESC)

#### Scenario: Sort by amount descending
- **WHEN** `get_transactions(conn, start_date="2026-02-01", sort_by="amount", sort_dir="desc")` is called
- **THEN** results are ordered by absolute amount, largest first

#### Scenario: Sort by amount ascending
- **WHEN** `get_transactions(conn, start_date="2026-02-01", sort_by="amount", sort_dir="asc")` is called
- **THEN** results are ordered by absolute amount, smallest first

#### Scenario: Invalid sort_by falls back to date
- **WHEN** `get_transactions(conn, sort_by="injected_sql", sort_dir="desc")` is called
- **THEN** results use `ORDER BY t.date DESC, t.id` (default behavior, no SQL injection)

---

### Requirement: Transactions page sort controls in filter bar and column headers

The `GET /transactions` route SHALL accept `sort_by` (default `"date"`) and `sort_dir` (default `"desc"`) query parameters and pass them to `get_transactions()`. The route SHALL also pass `sort_by` and `sort_dir` as template context variables.

The Date and Amount column headers in the transactions table SHALL render as `<a>` links. Clicking an inactive column header SHALL sort by that column descending. Clicking the active column header SHALL toggle between ascending and descending. The active sort column SHALL display a directional arrow indicator (▲ for ASC, ▼ for DESC). All existing filter params (start, end, limit, category, search) SHALL be preserved in the sort link URLs.

#### Scenario: Clicking Amount column header sorts by amount
- **WHEN** the transactions page is loaded with default sort (date desc) and the user clicks the Amount column header
- **THEN** the page reloads with `?sort_by=amount&sort_dir=desc` and all other params preserved; results are largest-amount-first

#### Scenario: Clicking active sort column toggles direction
- **WHEN** the transactions page is loaded with `?sort_by=amount&sort_dir=desc` and the user clicks Amount again
- **THEN** the page reloads with `?sort_by=amount&sort_dir=asc`; results are smallest-amount-first

#### Scenario: Active sort column shows arrow indicator
- **WHEN** the transactions page is loaded with `?sort_by=amount&sort_dir=desc`
- **THEN** the Amount column header shows a ▼ indicator; the Date column header shows no indicator

#### Scenario: Sort params preserved with other filters
- **WHEN** the transactions page is loaded with `?start=2026-02-01&end=2026-02-28&category=Groceries&sort_by=amount&sort_dir=desc`
- **THEN** clicking the Date column header produces `?start=2026-02-01&end=2026-02-28&category=Groceries&sort_by=date&sort_dir=desc`
