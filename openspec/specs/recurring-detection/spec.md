## ADDED Requirements

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
