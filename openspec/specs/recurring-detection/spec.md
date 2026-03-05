## ADDED Requirements

### Requirement: apply_recurring_overrides deterministic pass
`apply_recurring_overrides(conn)` in `finance/analysis/review.py` SHALL set `is_recurring=1` for any transaction whose `(merchant_normalized, ROUND(ABS(amount), 2))` pair appears in 3 or more distinct calendar months (`SUBSTR(date, 1, 7)`).

Only debit transactions (`amount < 0`) with a non-null `merchant_normalized` are considered. Transactions already flagged `is_recurring=1` SHALL be left unchanged (idempotent).

The function SHALL return the count of rows updated.

This function SHALL be called as the final step of `run_pipeline()` after all LLM enrich batches complete, to correct LLM false-negatives.

#### Scenario: Payment-plan charge correctly flagged
- **WHEN** the same merchant+amount appears in 3+ distinct months with `is_recurring=0`
- **THEN** `apply_recurring_overrides(conn)` sets all matching rows to `is_recurring=1` and returns a count > 0

#### Scenario: Idempotent on already-flagged transactions
- **WHEN** all matching transactions already have `is_recurring=1`
- **THEN** `apply_recurring_overrides(conn)` returns 0 (no rows updated)

#### Scenario: Fewer than 3 months not promoted
- **WHEN** a merchant+amount pair appears in only 2 distinct months
- **THEN** `apply_recurring_overrides(conn)` does not change their `is_recurring` flag

---

### Requirement: get_recurring analysis function
`get_recurring(conn)` in `finance/analysis/review.py` SHALL return a list of enriched dicts for distinct `merchant_normalized` values where at least one transaction has `is_recurring=1`. Each dict SHALL include:

- `merchant_normalized` (str): The normalized merchant name.
- `count` (int): Number of transactions with `is_recurring=1` for this merchant.
- `typical_amount` (float): Median absolute amount across all recurring charges.
- `total_spent` (float): Sum of absolute amounts across all recurring charges.
- `last_date` (str | None): ISO date string (`YYYY-MM-DD`) of the most recent charge, or `None` if no dates available.
- `interval_days` (int | None): Median gap in days between consecutive charges, or `None` if fewer than 2 charges.
- `interval_label` (str | None): Human-readable label derived from `interval_days` using this mapping: 5–9 → `"Weekly"`, 13–17 → `"Bi-weekly"`, 25–35 → `"Monthly"`, 85–95 → `"Quarterly"`, 175–190 → `"Semi-annual"`, 355–375 → `"Annual"`, else `"Every ~{interval_days}d"`. `None` if `interval_days` is `None`.
- `next_due_date` (str | None): ISO date string of `last_date + timedelta(days=interval_days)`, or `None` if `interval_days` is `None`.
- `days_until_next` (int | None): `(next_due_date - today).days`, or `None` if `next_due_date` is `None`.
- `status` (str | None): One of `"upcoming"`, `"due_soon"`, `"due_any_day"`, `"past_due"`, `"likely_cancelled"`, or `None` (when interval cannot be computed). Derived as:
  - `days_until_next > 7` → `"upcoming"`
  - `1 <= days_until_next <= 7` → `"due_soon"`
  - `-tolerance <= days_until_next <= 0` → `"due_any_day"` where `tolerance = max(3, int(interval_days * 0.35))`
  - `-interval_days < days_until_next < -tolerance` → `"past_due"`
  - `days_until_next <= -interval_days` → `"likely_cancelled"`

Results SHALL be sorted by urgency: `"past_due"` first (most overdue first), then `"likely_cancelled"` (most overdue first), then `"due_any_day"`, then `"due_soon"` (fewest days first), then `"upcoming"` (fewest days first), then `None` status last.

#### Scenario: Recurring merchants returned with enriched fields
- **WHEN** three transactions share `merchant_normalized="Netflix"` with `is_recurring=1` and dates `2025-12-15`, `2026-01-15`, `2026-02-15`
- **THEN** `get_recurring(conn)` includes an entry with `merchant_normalized="Netflix"`, `count=3`, `interval_label="Monthly"`, `last_date="2026-02-15"`, `next_due_date="2026-03-17"` (±1 day for 30d interval), and a `status` of `"upcoming"` or `"past_due"` depending on today's date

#### Scenario: Single-charge merchant has no interval data
- **WHEN** a merchant has only one transaction with `is_recurring=1`
- **THEN** its dict has `interval_days=None`, `interval_label=None`, `next_due_date=None`, `days_until_next=None`, `status=None`

#### Scenario: Past due merchant detection
- **WHEN** a monthly merchant's last charge was 35 days ago (beyond tolerance but within one interval)
- **THEN** its `status` is `"past_due"` and it appears before `likely_cancelled` merchants in the sorted result

#### Scenario: Likely cancelled merchant detection
- **WHEN** a monthly merchant's last charge was 65 days ago (more than one full 30-day interval)
- **THEN** its `status` is `"likely_cancelled"`

#### Scenario: Likely cancelled appears after past_due in sort order
- **WHEN** both a `"past_due"` and a `"likely_cancelled"` merchant exist
- **THEN** the `"past_due"` merchant appears first in the result list

#### Scenario: Non-recurring merchants excluded
- **WHEN** a merchant has `is_recurring=0` for all its transactions
- **THEN** it does not appear in the result of `get_recurring(conn)`

#### Scenario: Empty result
- **WHEN** no transactions have `is_recurring=1`
- **THEN** `get_recurring(conn)` returns an empty list

#### Scenario: total_spent reflects all charges
- **WHEN** a merchant has 3 charges of $9.99, $9.99, and $10.99
- **THEN** `total_spent` is `30.97`

---

### Requirement: finance recurring CLI command
The system SHALL provide a `finance recurring` CLI command that prints a plain-text summary table of detected recurring charges. Columns: Merchant, Count, Typical Amount.

#### Scenario: Table printed when recurring charges exist
- **WHEN** `finance recurring` is run and recurring merchants exist
- **THEN** a table is printed with one row per recurring merchant, ordered by count DESC

#### Scenario: Empty message when none detected
- **WHEN** `finance recurring` is run and no recurring charges have been detected
- **THEN** stdout shows "No recurring charges detected. Run `finance sync` to enrich transactions."

---

### Requirement: GET /recurring web route — enriched display

The `GET /recurring` route SHALL render the recurring charges table grouped into three visual sections, ordered top-to-bottom: **Needs Attention**, **Active Subscriptions**, and **Likely Cancelled**. The route SHALL pre-group data server-side and pass three separate lists to the template: `attention` (merchants with `status` in `past_due`, `due_any_day`, `due_soon`), `active` (merchants with `status` in `upcoming`, `None`), and `cancelled` (merchants with `status == "likely_cancelled"`).

**Columns** (all sections): Merchant, Interval, Typical Amount, Next Due, Status.

The **Next Due** column SHALL display the value of `next_due_date` (ISO date string `YYYY-MM-DD`) or `"—"` when `next_due_date` is `None`.

**Needs Attention section** (rendered only when `attention` is non-empty):
- Each row SHALL display a 4px colored left-border stripe: red (`border-red-500`) for `past_due`, blue (`border-blue-500`) for `due_any_day`, amber (`border-amber-500`) for `due_soon`

**Active Subscriptions section** (rendered only when `active` is non-empty):
- Standard rows with no urgency indicator

**Likely Cancelled section** (rendered using a native HTML `<details>` element, collapsed by default):
- The `<summary>` SHALL display the count, e.g., "Likely Cancelled (2)"

**Status cell color-coding:**
- `"upcoming"` → gray text "Due in {n}d" (or "Due in ~{n}mo" if > 30 days)
- `"due_soon"` → amber/yellow "Due in {n}d"
- `"due_any_day"` → blue "Due any day"
- `"past_due"` → red "Past due {abs(n)}d" (or "Past due ~{months}mo" if > 60 days overdue)
- `"likely_cancelled"` → gray secondary text "Last ~{interval_label}" + red "Cancelled?" badge
- `None` → gray "—"

The merchant name cell SHALL link to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`.

#### Scenario: Needs Attention section renders for urgent merchants

- **WHEN** one or more merchants have `status` in `past_due`, `due_any_day`, or `due_soon`
- **THEN** a "Needs Attention" section header appears above a table containing only those merchants

#### Scenario: Active Subscriptions section renders for healthy merchants

- **WHEN** one or more merchants have `status` in `upcoming` or `None`
- **THEN** an "Active Subscriptions" section header appears above a table containing only those merchants

#### Scenario: Needs Attention section absent when no urgent merchants

- **WHEN** all merchants have `status` in `upcoming`, `None`, or `likely_cancelled`
- **THEN** no "Needs Attention" section header or table is rendered

#### Scenario: Likely Cancelled section is collapsed by default

- **WHEN** one or more merchants have `status == "likely_cancelled"`
- **THEN** a `<details>` element is rendered at the bottom of the page; its `<summary>` shows the cancelled count; it is collapsed on initial page load

#### Scenario: Past due row has red left border

- **WHEN** a merchant with `status == "past_due"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px red left border

#### Scenario: Due any day row has blue left border

- **WHEN** a merchant with `status == "due_any_day"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px blue left border

#### Scenario: Due soon row has amber left border

- **WHEN** a merchant with `status == "due_soon"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px amber left border

#### Scenario: Next Due column shows ISO date when available

- **WHEN** a merchant has a non-null `next_due_date`
- **THEN** the Next Due cell displays the date as `YYYY-MM-DD`

#### Scenario: Next Due column shows dash when unavailable

- **WHEN** a merchant has `next_due_date == None`
- **THEN** the Next Due cell displays "—"

#### Scenario: Merchant name links to transaction search

- **WHEN** the user clicks a merchant name on the recurring page
- **THEN** the browser navigates to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`

#### Scenario: Empty recurring page

- **WHEN** `GET /recurring` is requested and no recurring charges exist
- **THEN** the page renders a message: "No recurring charges detected."

---

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
