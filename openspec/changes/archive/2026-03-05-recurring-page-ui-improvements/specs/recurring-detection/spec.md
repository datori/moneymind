## ADDED Requirements

### Requirement: Recurring page summary stats
The `/recurring` route in `finance/web/app.py` SHALL compute and pass the following summary values to the template:

- `summary_monthly_total` (float): Sum of `typical_amount / (interval_days / 30.44)` for all active (non-cancelled) merchants with a known `interval_days`. Represents estimated total monthly recurring spend.
- `summary_annual_total` (float): `summary_monthly_total * 12`.
- `summary_due_soon_count` (int): Count of items in `attention` where `status` is `"due_soon"`, `"due_any_day"`, or `"past_due"` and `days_until_next` is not None and `abs(days_until_next) <= 7`.

#### Scenario: Summary stats computed from active items
- **WHEN** the page loads with 2 monthly ($10/mo) and 1 annual ($120/yr) active subscription
- **THEN** `summary_monthly_total` ≈ $30.00 and `summary_annual_total` ≈ $360.00

#### Scenario: Due-soon count reflects attention items within 7 days
- **WHEN** 2 items have `days_until_next` in range [-7, 7] and status in the attention set
- **THEN** `summary_due_soon_count` is 2

### Requirement: Recurring page cadence grouping
The `/recurring` route SHALL group items in the `active` list by billing cadence and pass `active_groups` to the template. Each group SHALL have:

- `label` (str): One of `"Weekly"`, `"Monthly"`, `"Quarterly"`, `"Annual"`, `"Other"`.
- `items` (list): Recurring items belonging to this cadence.
- `subtotal_monthly` (float): Sum of per-item monthly-equivalent cost (`typical_amount / (interval_days / 30.44)`), rounded to 2 decimal places.

Cadence bucketing by `interval_days`:
- `<= 10` → `"Weekly"`
- `<= 45` → `"Monthly"`
- `<= 100` → `"Quarterly"`
- `<= 400` → `"Annual"`
- `> 400` or `None` → `"Other"`

Groups with zero items SHALL be omitted. The `active` template variable SHALL remain for backwards compatibility (not removed).

#### Scenario: Monthly and annual items grouped separately
- **WHEN** active items contain a 30-day and a 365-day subscription
- **THEN** `active_groups` has a "Monthly" group and an "Annual" group, each with one item

#### Scenario: Empty groups omitted
- **WHEN** no active items have quarterly interval
- **THEN** `active_groups` does not contain a "Quarterly" group

#### Scenario: Subtotal is monthly-equivalent
- **WHEN** an Annual group contains one $120/yr item (interval_days ≈ 365)
- **THEN** `subtotal_monthly` for the Annual group is approximately $10.00

### Requirement: get_recurring returns dominant category
`get_recurring(conn)` SHALL only consider debit transactions (`amount < 0`) — income and credits are excluded from recurring charge detection. `get_recurring(conn)` SHALL include a `category` field in each returned dict: the most common (dominant) `category` value across all `is_recurring=1` debit transactions for that merchant. If all categories are NULL, `category` SHALL be `None`.

#### Scenario: Category reflects dominant transaction category
- **WHEN** a merchant has 3 transactions categorized "Software" and 1 as "Financial"
- **THEN** `category` is `"Software"`

#### Scenario: Null category when no category set
- **WHEN** all a merchant's recurring transactions have NULL category
- **THEN** `category` is `None`

### Requirement: Financial category exclusion from recurring page
Items returned by `get_recurring()` with `category = 'Financial'` SHALL be excluded from the `/recurring` page's `attention`, `active`, `cancelled`, `active_groups` lists and all summary stat calculations (`summary_monthly_total`, `summary_annual_total`, `summary_due_soon_count`). These items represent credit card autopayments that double-count spending already tracked via the underlying card transactions.

#### Scenario: Credit card autopay excluded from summary
- **WHEN** a merchant with `category = 'Financial'` and `typical_amount = $3000` is in the recurring data
- **THEN** it does not appear in any section of the recurring page and does not contribute to `summary_monthly_total`

#### Scenario: Non-financial recurring items unaffected
- **WHEN** a merchant with `category = 'Software'` is in the recurring data
- **THEN** it appears normally in the appropriate section and is included in summary stats
