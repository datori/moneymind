## ADDED Requirements

### Requirement: Category dropdown on transactions filter bar

The `/transactions` page filter bar SHALL include a category dropdown, a text search input, and sort controls alongside the existing date and limit controls. The dropdown SHALL contain an "All Categories" option (value `""`) and one option per canonical category from `finance/ai/categories.py` (`CATEGORIES`). The selected category is reflected in the `?category=` URL query parameter.

The filter bar SHALL also include a text input labeled "Search" with `name="search"` and `placeholder="merchant or description"` reflecting the current `?search=` param.

The `GET /transactions` route in `finance/web/app.py` SHALL accept `category: str | None`, `search: str | None`, `sort_by: str` (default `"date"`), and `sort_dir: str` (default `"desc"`) query parameters and pass them all to `get_transactions()`. The route SHALL pass `CATEGORIES`, the current `category`, `search`, `sort_by`, and `sort_dir` values to the template context.

#### Scenario: No category filter applied
- **WHEN** a browser navigates to `/transactions` with no `category` param
- **THEN** the dropdown shows "All Categories" as the selected option and all transactions within the date range are returned

#### Scenario: Empty string category treated as no filter
- **WHEN** the filter form is submitted with "All Categories" selected (sending `?category=` as an empty string)
- **THEN** the route normalizes `""` to `None` before calling `get_transactions()` and all transactions within the date range are returned (no category WHERE clause applied)

#### Scenario: Category filter applied
- **WHEN** a browser navigates to `/transactions?category=Groceries`
- **THEN** the dropdown shows "Groceries" as the selected option and only transactions with `category = 'Groceries'` are returned

#### Scenario: Dropdown preserves other filter params on submit
- **WHEN** the user selects "Food & Dining" from the dropdown while start/end date, limit, search, and sort params are also set
- **THEN** submitting the form produces a URL with all params intact

#### Scenario: Unknown category value ignored gracefully
- **WHEN** a URL is manually crafted with `?category=NotACategory`
- **THEN** `get_transactions()` returns an empty list (no transactions match); no error is raised

#### Scenario: Month navigation on transactions page
- **WHEN** the transactions page is showing March 2026 and the user clicks ‹
- **THEN** the page reloads for February 2026 with all other filter params (category, search, sort_by, sort_dir, limit) preserved

---

### Requirement: Category list sourced from CATEGORIES constant

The dropdown options SHALL be generated from the `CATEGORIES` list in `finance/ai/categories.py` (the same 15-entry list used by the categorization pipeline). The route handler SHALL import and pass `CATEGORIES` to the template; the template SHALL iterate over it to render `<option>` elements.

#### Scenario: All 15 categories appear in dropdown
- **WHEN** the `/transactions` page is loaded
- **THEN** the category dropdown contains exactly 16 options: "All Categories" plus one option for each entry in `CATEGORIES`

#### Scenario: Category values match stored data
- **WHEN** a category such as "Food & Dining" is selected in the dropdown
- **THEN** the value sent in the URL and compared against `t.category` in the SQL query is the exact string `"Food & Dining"`, matching the stored value
