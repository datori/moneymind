## ADDED Requirements

### Requirement: get_recurring_spend_timeline function
`get_recurring_spend_timeline(conn, months=13, future_months=3)` in `finance/analysis/review.py` SHALL return monthly recurring spend data per merchant for rendering a timeline chart. The return value SHALL be a dict with:
- `months`: list of `YYYY-MM` strings, sorted ascending, exactly `months` entries (past calendar months ending with the current month)
- `future_months`: list of `YYYY-MM` strings, sorted ascending, exactly `future_months` entries (calendar months after the current month)
- `merchants`: list of dicts, one per merchant with at least 2 recurring charges (sufficient to compute an interval), each with:
  - `name`: merchant_normalized string
  - `actual`: list of floats, length == len(months); absolute dollar amount charged in that month (0.0 if no charge)
  - `ghost`: list of floats, length == len(months); expected-but-missing dollar amount for that month (0.0 if charge occurred or not expected); uses `typical_amount` as the expected value
  - `projected`: list of floats, length == len(future_months); projected charge amount per future month (0.0 if no charge expected); uses `typical_amount`
  - `status`: status string from `get_recurring()` enrichment, including `"likely_cancelled"`
  - `typical_amount`: float (median charge amount)
  - `interval_days`: int

Ghost detection: a past-month slot is marked as ghost (expected-but-missing) when: (a) the projected charge date for that month falls within the window, AND (b) no actual charge exists for that merchant in that month, AND (c) the projected charge date is more than `tolerance = max(3, int(interval_days * 0.35))` days before today.

Projection: a future-month slot is filled with `typical_amount` when the projected charge date (stepping from `last_date` by `interval_days`) falls within that calendar month.

Merchants with fewer than 2 recurring transactions (no computable interval) SHALL be excluded from the result.

#### Scenario: Active merchant shows actual spend and projection
- **WHEN** a monthly merchant has charges in each of the past 13 months
- **THEN** `actual` contains 13 non-zero values, `ghost` is all zeros, and `projected` contains the `typical_amount` in the appropriate future month slots

#### Scenario: Cancelled merchant shows ghost bars for missing months
- **WHEN** a monthly merchant's last charge was 3 months ago (well past its interval)
- **THEN** `ghost` has non-zero values for the 2–3 most recent months where charges were expected but absent, and `projected` is all zeros

#### Scenario: Future months zero-filled when merchant is likely_cancelled
- **WHEN** a merchant has `status == "likely_cancelled"`
- **THEN** `projected` is all zeros (no future charges projected for cancelled merchants)

#### Scenario: Merchant with fewer than 2 charges excluded
- **WHEN** a merchant has only 1 recurring transaction
- **THEN** it does not appear in `merchants` (interval cannot be computed)

#### Scenario: Empty result when no qualifying merchants
- **WHEN** no merchants have 2+ recurring transactions
- **THEN** `merchants` is an empty list, `months` still has 13 entries, `future_months` still has 3 entries

#### Scenario: Custom months and future_months parameters
- **WHEN** `get_recurring_spend_timeline(conn, months=6, future_months=2)` is called
- **THEN** `months` has 6 entries, `future_months` has 2 entries, and all `actual`/`ghost`/`projected` lists match those lengths
