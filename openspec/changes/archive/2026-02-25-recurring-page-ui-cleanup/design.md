## Context

The recurring page currently renders a single flat table of all merchants sorted by urgency. The most critical field (Status) is the last column, every urgency tier has identical visual weight, and `likely_cancelled` entries compete visually with active subscriptions. Users can't tell at a glance what needs action.

No changes to the analysis layer are needed — `get_recurring()` already returns all the data required. This is a pure presentation rework.

## Goals / Non-Goals

**Goals:**
- Make urgent merchants (past_due, due_any_day, due_soon) immediately visible on page load via a distinct "Needs Attention" section
- Remove `likely_cancelled` entries from the default view by collapsing them
- Simplify the column set (drop rarely-actionable Total Spent and Occurrences; add Next Due date)
- Add row-level urgency color signals via left-border stripes in the Needs Attention section

**Non-Goals:**
- No changes to `get_recurring()` or any analysis function
- No new database queries or routes
- No changes to the spend timeline chart
- No alert cards or other structural changes beyond sectioned tables

## Decisions

### 1. Server-side grouping into three lists

Split `recurring` into `attention` (past_due, due_any_day, due_soon), `active` (upcoming, None), and `cancelled` (likely_cancelled) in `app.py` before passing to the template.

**Why**: Jinja2 cannot maintain stateful section transitions cleanly inside a single `{% for %}`. Server-side grouping yields three simple loops in the template — no conditionals needed to detect group boundaries.

**Alternative**: Jinja2 `selectattr` filters on a single list. Works but clutters the template with filter expressions and still requires three separate table/header blocks.

### 2. `<details><summary>` for Likely Cancelled

Use native HTML `<details>`/`<summary>` for the collapsed cancelled section.

**Why**: Zero JS, no state management, keyboard-accessible by default. The browser handles collapsed state natively. Alternative (JS toggle) adds event listener complexity for no functional benefit on a personal dashboard.

### 3. Column set: Merchant · Interval · Typical · Next Due · Status

Drop Total Spent and Occurrences; add Next Due (ISO date string from `next_due_date`).

**Why**: Total Spent is already visible in the spend timeline chart. Occurrences is low-value metadata. Next Due ("2026-03-15") is directly actionable — users can correlate with their bank statement date. Show "—" when `next_due_date` is None.

### 4. Left-border color stripes in Needs Attention

Within the Needs Attention section, each row gets a 4px left border: `border-l-4 border-red-500` for past_due, `border-l-4 border-blue-500` for due_any_day, `border-l-4 border-amber-500` for due_soon.

**Why**: Instant visual scan — users can read urgency from color alone without parsing the Status cell text. Standard Tailwind utility classes, no custom CSS needed.

### 5. Conditional section rendering

"Needs Attention" section header renders only when `attention` list is non-empty. "Active Subscriptions" header renders only when `active` list is non-empty.

**Why**: A user with all healthy subscriptions sees only "Active Subscriptions" — no confusing empty "Needs Attention" header. Keeps the page clean in the common steady-state case.

## Risks / Trade-offs

- **Column removal**: Dropping Total Spent and Occurrences may be a surprise. Mitigation: both remain accessible via the merchant link → transaction search. The chart shows historical spend.
- **Likely Cancelled collapsed by default**: Users may miss cancelled items. Mitigation: the `<summary>` element shows the count (e.g., "Likely Cancelled (2)"), making it visible without expanding.
- **Next Due as ISO string**: No locale-aware formatting needed for a personal tool; ISO date is unambiguous.
