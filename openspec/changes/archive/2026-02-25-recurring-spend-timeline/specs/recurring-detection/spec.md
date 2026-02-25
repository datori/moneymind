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
