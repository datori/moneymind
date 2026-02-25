## ADDED Requirements

### Requirement: Category dropdown on transactions filter bar

The `/transactions` page filter bar SHALL include a category dropdown alongside the existing date and limit controls. The dropdown SHALL contain an "All Categories" option (value `""`) and one option per canonical category from `finance/ai/categories.py` (`CATEGORIES`). The selected category is reflected in the `?category=` URL query parameter.

The `GET /transactions` route in `finance/web/app.py` SHALL accept a `category: str | None = None` query parameter and pass it to `get_transactions()`. The route SHALL also pass the full `CATEGORIES` list and the current `category` value to the template context so the dropdown can render the correct selected state.

`get_transactions()` in `finance/analysis/spending.py` already supports `category` filtering via `WHERE t.category = ?`; no changes to the analysis function are required.

#### Scenario: No category filter applied
- **WHEN** a browser navigates to `/transactions` with no `category` param
- **THEN** the dropdown shows "All Categories" as the selected option and all transactions within the date range are returned

#### Scenario: Category filter applied
- **WHEN** a browser navigates to `/transactions?category=Groceries`
- **THEN** the dropdown shows "Groceries" as the selected option and only transactions with `category = 'Groceries'` are returned

#### Scenario: Dropdown preserves other filter params on submit
- **WHEN** the user selects "Food & Dining" from the dropdown while start/end date and limit are also set
- **THEN** submitting the form produces a URL with all params intact: `?start=...&end=...&limit=...&category=Food+%26+Dining`

#### Scenario: Unknown category value ignored gracefully
- **WHEN** a URL is manually crafted with `?category=NotACategory`
- **THEN** `get_transactions()` returns an empty list (no transactions match); no error is raised; the dropdown shows "NotACategory" as the selected value if it appears in the select element, or falls back to "All Categories"

---

### Requirement: Category list sourced from CATEGORIES constant

The dropdown options SHALL be generated from the `CATEGORIES` list in `finance/ai/categories.py` (the same 15-entry list used by the categorization pipeline). The route handler SHALL import and pass `CATEGORIES` to the template; the template SHALL iterate over it to render `<option>` elements.

#### Scenario: All 15 categories appear in dropdown
- **WHEN** the `/transactions` page is loaded
- **THEN** the category dropdown contains exactly 16 options: "All Categories" plus one option for each entry in `CATEGORIES`

#### Scenario: Category values match stored data
- **WHEN** a category such as "Food & Dining" is selected in the dropdown
- **THEN** the value sent in the URL and compared against `t.category` in the SQL query is the exact string `"Food & Dining"`, matching the stored value
