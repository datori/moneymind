## 1. Route Computation

- [x] 1.1 In the `/recurring` route (`finance/web/app.py`), after computing `summary_monthly_total`, compute `pending_cancels` — the list of merchants in `non_cancelled` where `cancel_attempt is not None AND cancel_attempt["resolved_at"] is None`
- [x] 1.2 Compute `pending_cancel_count = len(pending_cancels)` and `post_cancel_monthly = max(0.0, round(summary_monthly_total - sum(_monthly_equiv(r) for r in pending_cancels), 2))`
- [x] 1.3 Pass `post_cancel_monthly` and `pending_cancel_count` to the template context

## 2. Template UI

- [x] 2.1 In `finance/web/templates/recurring.html`, add a conditional secondary line to the Monthly summary card: when `pending_cancel_count > 0`, show `"→ ~$X if N cancel(s) work"` (X = post_cancel_monthly rounded to nearest dollar, N = pending_cancel_count) in small muted text below the main monthly figure
