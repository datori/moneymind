## 1. Analysis Layer — get_transactions() enhancements

- [x] 1.1 Add `sort_by: str = "date"` and `sort_dir: str = "desc"` params to `get_transactions()` in `finance/analysis/spending.py`; construct `ORDER BY` from a safe allowlist (no raw interpolation)
- [x] 1.2 Add `search: str | None = None` param to `get_transactions()`; append `AND (t.description LIKE ? OR t.merchant_name LIKE ? OR t.merchant_normalized LIKE ?)` with `%search%` when provided

## 2. Analysis Layer — get_recurring() enrichment

- [x] 2.1 Rewrite `get_recurring()` in `finance/analysis/review.py` to also fetch `date` per recurring transaction
- [x] 2.2 Compute per-merchant: `last_date`, `interval_days` (median gap), `interval_label` (classified), `next_due_date`, `days_until_next`, `status`, `total_spent`
- [x] 2.3 Sort result by urgency: `past_due` first (most overdue first), then `due_any_day`, then `due_soon` (fewest days first), then `upcoming` (fewest days first), then `None` last

## 3. Web Route — /transactions updates

- [x] 3.1 Add `sort_by`, `sort_dir`, and `search` query params to the `GET /transactions` route handler in `finance/web/app.py`; pass all to `get_transactions()` and to template context

## 4. Web Route — /recurring updates

- [x] 4.1 Update `GET /recurring` route in `finance/web/app.py` to pass enriched `get_recurring()` result to template (no route logic change needed beyond that)

## 5. Template — transactions.html

- [x] 5.1 Add month prev/next navigation buttons (‹ / ›) and month label to the transactions filter bar using JS that updates `start`/`end` inputs and submits the form; preserve all other params
- [x] 5.2 Add `search` text input (`name="search"`, placeholder "merchant or description") to the filter bar
- [x] 5.3 Make Date and Amount column headers into sort-toggle `<a>` links; show ▲/▼ on active sort column; preserve all other filter params in sort URLs

## 6. Template — spending.html

- [x] 6.1 Add month prev/next navigation buttons (‹ / ›) and month label to the spending filter bar using JS; preserve `group_by` and `include_financial` params
- [x] 6.2 When `group_by=category`, wrap each table row label in an `<a>` linking to `/transactions?start={start}&end={end}&category={label}&sort_by=amount&sort_dir=desc`
- [x] 6.3 When `group_by=merchant`, wrap each table row label in an `<a>` linking to `/transactions?start={start}&end={end}&search={label}&sort_by=amount&sort_dir=desc`

## 7. Template — recurring.html

- [x] 7.1 Add Interval, Total Spent, and Status columns to the recurring table; remove old Occurrences-only layout
- [x] 7.2 Color-code Status cell: gray for `upcoming`, amber for `due_soon`, blue for `due_any_day`, red for `past_due`, gray dash for `None`
- [x] 7.3 Format Status text: "Due in {n}d" / "Due in ~{n}mo" / "Due any day" / "Past due {n}d" / "Past due ~{n}mo"
- [x] 7.4 Make merchant name a link to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`
