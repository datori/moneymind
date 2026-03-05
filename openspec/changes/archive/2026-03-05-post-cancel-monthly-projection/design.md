## Context

The recurring page summary strip has three cards: Monthly, Annual, Due Soon. The Monthly card shows `summary_monthly_total` — the sum of monthly-equivalent costs across all active (non-cancelled) merchants. Users can now track cancellation attempts per merchant via the `recurring_cancel_attempts` table and the `cancel_attempt` enrichment on each merchant dict.

The proposed feature adds a projected-post-cancel figure to the Monthly card as a secondary annotation.

## Goals / Non-Goals

**Goals:**
- Compute the projected monthly spend assuming all unresolved cancel attempts succeed
- Display it as a secondary line in the existing Monthly card (no new card)
- Only show when at least one pending cancel exists in the current filtered view
- Include zombies in the savings estimate (they represent cancellation intent even if the attempt so far has failed)

**Non-Goals:**
- Separate "savings" card or annual projection of savings
- Tracking which cancellations have been confirmed to save money
- Any backend persistence — this is a pure computation at render time

## Decisions

### 1. What counts as a "pending cancel"

**Decision**: A merchant in `non_cancelled` (attention or active) where `cancel_attempt is not None AND cancel_attempt["resolved_at"] is None`.

Includes zombies (cancel attempted, still charging) — they represent user intent to cancel.
Excludes resolved attempts (`resolved_at` is set) — already done.
Excludes `likely_cancelled` merchants already in the `cancelled` list — they're not in `non_cancelled`.

### 2. Computation

```python
pending_cancels = [
    r for r in non_cancelled
    if r.get("cancel_attempt") and r["cancel_attempt"]["resolved_at"] is None
]
pending_cancel_count = len(pending_cancels)
cancel_savings = round(sum(_monthly_equiv(r) for r in pending_cancels), 2)
post_cancel_monthly = round(summary_monthly_total - cancel_savings, 2)
```

`post_cancel_monthly` may be 0 or slightly negative (edge case: merchant with no interval_days contributes 0 to both totals). Clamp to 0 in template.

### 3. Display location

**Decision**: Secondary line inside the existing Monthly card, not a new card.

Rationale: The projection is context for the Monthly figure, not an independent metric. Placing it adjacent in the same card keeps the strip compact and makes the relationship obvious.

Template sketch:
```
┌──────────────────────┐
│ MONTHLY              │
│ ~$638                │
│ → ~$580 if 2 cancel  │  ← shown only when pending_cancel_count > 0
└──────────────────────┘
```

### 4. Label format

`"→ ~$X if N cancel(s) work"` — concise, uses `→` as visual direction indicator. N is `pending_cancel_count`.

## Risks / Trade-offs

- **Over-counts savings for merchants with no `interval_days`**: Those contribute 0 to monthly_equiv anyway, so they don't inflate the savings figure.
- **Filters not reflected**: The projection only considers merchants currently displayed (filtered by housing/education/health toggles), which is the correct behavior — projection matches the visible set.
