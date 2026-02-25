## MODIFIED Requirements

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
- `status` (str | None): One of `"upcoming"`, `"due_soon"`, `"due_any_day"`, `"past_due"`, or `None` (when interval cannot be computed). Derived as:
  - `days_until_next > 7` → `"upcoming"`
  - `1 <= days_until_next <= 7` → `"due_soon"`
  - `-tolerance <= days_until_next <= 0` → `"due_any_day"` where `tolerance = max(3, int(interval_days * 0.35))`
  - `days_until_next < -tolerance` → `"past_due"`

Results SHALL be sorted by urgency: `"past_due"` first (most overdue first), then `"due_any_day"`, then `"due_soon"` (fewest days first), then `"upcoming"` (fewest days first), then `None` status last.

#### Scenario: Recurring merchants returned with enriched fields
- **WHEN** three transactions share `merchant_normalized="Netflix"` with `is_recurring=1` and dates `2025-12-15`, `2026-01-15`, `2026-02-15`
- **THEN** `get_recurring(conn)` includes an entry with `merchant_normalized="Netflix"`, `count=3`, `interval_label="Monthly"`, `last_date="2026-02-15"`, `next_due_date="2026-03-17"` (±1 day for 30d interval), and a `status` of `"upcoming"` or `"past_due"` depending on today's date

#### Scenario: Single-charge merchant has no interval data
- **WHEN** a merchant has only one transaction with `is_recurring=1`
- **THEN** its dict has `interval_days=None`, `interval_label=None`, `next_due_date=None`, `days_until_next=None`, `status=None`

#### Scenario: Past due merchant detection
- **WHEN** a monthly merchant's last charge was 60 days ago (well beyond the ~10-day tolerance)
- **THEN** its `status` is `"past_due"` and it appears first in the sorted result list

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

### Requirement: GET /recurring web route — enriched display

The `GET /recurring` route SHALL render an enriched table with columns: Merchant, Interval, Typical Amount, Total Spent, Occurrences, Status. The Status cell SHALL be color-coded:

- `"upcoming"` → gray text "Due in {n}d" (or "Due in {n}mo" if > 30 days)
- `"due_soon"` → amber/yellow "Due in {n}d"
- `"due_any_day"` → blue "Due any day"
- `"past_due"` → red "Past due {abs(n)}d" (or "Past due ~{months}mo" if > 60 days overdue)
- `None` → gray "—"

Rows SHALL be sorted by urgency as returned by `get_recurring()`. The merchant name cell SHALL link to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc` so the user can view all transactions for that merchant.

#### Scenario: Recurring page loads with enriched data
- **WHEN** `GET /recurring` is requested and recurring merchants exist
- **THEN** an HTML table is returned with columns Merchant, Interval, Typical Amount, Total Spent, Occurrences, Status

#### Scenario: Past due row shown in red
- **WHEN** a merchant's status is `"past_due"`
- **THEN** its Status cell renders in red (e.g., "Past due 45d")

#### Scenario: Upcoming row shown in gray
- **WHEN** a merchant's status is `"upcoming"` with `days_until_next=20`
- **THEN** its Status cell renders "Due in 20d" in gray text

#### Scenario: Due > 30 days shown in months
- **WHEN** `days_until_next=65`
- **THEN** the Status cell renders "Due in ~2mo"

#### Scenario: Past due > 60 days shown in months
- **WHEN** `days_until_next=-90`
- **THEN** the Status cell renders "Past due ~3mo" in red

#### Scenario: Merchant name links to transactions search
- **WHEN** the user clicks a merchant name on the recurring page
- **THEN** the browser navigates to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`

#### Scenario: Empty recurring page
- **WHEN** `GET /recurring` is requested and no recurring charges exist
- **THEN** the page renders a message: "No recurring charges detected."
