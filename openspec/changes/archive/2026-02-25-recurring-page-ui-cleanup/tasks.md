## 1. Route — server-side grouping

- [x] 1.1 In `finance/web/app.py` `/recurring` route, split the `get_recurring()` result into three lists: `attention` (status in past_due, due_any_day, due_soon), `active` (status in upcoming, None), and `cancelled` (status == likely_cancelled), and pass all three to the template

## 2. Template — sectioned table

- [x] 2.1 In `finance/web/templates/recurring.html`, replace the existing flat `<table>` with a "Needs Attention" section: a card with section header, rendered only when `attention` is non-empty, containing a 5-column table (Merchant, Interval, Typical, Next Due, Status) with colored left-border stripes per urgency (red for past_due, blue for due_any_day, amber for due_soon)
- [x] 2.2 Add "Active Subscriptions" section: a card with section header, rendered only when `active` is non-empty, containing the same 5-column table with standard rows (no left borders)
- [x] 2.3 Add "Likely Cancelled" section: a `<details><summary>` collapsed by default, with summary showing count (e.g. "Likely Cancelled (2)"), containing the same 5-column table with the existing grey text + "Cancelled?" badge styling

## 3. Template — column updates

- [x] 3.1 Replace the old Status cell logic (which was shared across all rows in a single loop) with the same color-coded status rendering in each of the three new section loops; replace the Total Spent and Occurrences columns with a Next Due column showing `item.next_due_date` or "—"
