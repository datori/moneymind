# finance-report — Generate a Monthly Spending Report

Generate a detailed narrative spending report for a given month, save it to the database, and confirm it is visible in the dashboard.

## Usage

```
/finance-report 2026-02
```

If no month is provided, default to the **previous calendar month**.

---

## Steps

### 1. Determine the target month

Parse the argument as `YYYY-MM`. If omitted, compute the previous month from today's date.

Derive:
- `{YYYY-MM}` — target month
- `{last_day}` — last calendar day of that month (e.g. 28, 30, or 31)
- `{PRIOR_YYYY-MM}` — the month immediately before the target
- `{PRIOR_last_day}` — last calendar day of the prior month

### 2. Check for an existing report

Call `get_report(month)`.

- If a report **already exists**, show the user:
  ```
  A report for {Month Name} {Year} already exists (generated {generated_at date}).
  Regenerate and overwrite it? [y/N]
  ```
  Wait for confirmation. If the user says no (or anything other than `y`/`yes`), stop here.

- If no report exists, continue.

### 3. Gather data via MCP tools

Fire all of the following in parallel:

**Target month:**
- `get_spending_summary(start_date="{YYYY-MM}-01", end_date="{YYYY-MM}-{last_day}", group_by="category")`
- `get_spending_summary(start_date="{YYYY-MM}-01", end_date="{YYYY-MM}-{last_day}", group_by="merchant")`
- `get_transactions(start_date="{YYYY-MM}-01", end_date="{YYYY-MM}-{last_day}", limit=500)`

**Prior month (for comparison):**
- `get_spending_summary(start_date="{PRIOR_YYYY-MM}-01", end_date="{PRIOR_YYYY-MM}-{PRIOR_last_day}", group_by="category")`
- `get_transactions(start_date="{PRIOR_YYYY-MM}-01", end_date="{PRIOR_YYYY-MM}-{PRIOR_last_day}", limit=500)`

**Context:**
- `get_net_worth()`
- `get_accounts()`

### 4. Compute summary statistics

#### 3a. General spending

- **Total spend**: sum of debit amounts in target month, excluding categories Financial, Income, Investment
- **Top 5 categories** by total spend
- **Top 10 merchants** by total spend (with transaction count each)
- **Month-over-month delta**: per-category and total, vs. prior month (absolute $ and %)
- **Notable one-time transactions**: any single charge ≥ $200, or `needs_review=1`
- **Daily average**: total spend / days in month

#### 3b. Recurring charges deep-dive

From the target month's transactions, isolate all rows where `is_recurring=1`. Then:

1. **By category** — group recurring transactions by their `category` field. For each category compute:
   - Total monthly amount
   - List of distinct merchants (with individual amounts)
   - Annualized cost (monthly total × 12)
   - % of total recurring spend

2. **New this month** — merchants with `is_recurring=1` in the target month that do NOT appear as recurring in the prior month's transactions. These are newly detected subscriptions.

3. **Dropped / missing** — merchants with `is_recurring=1` in the prior month that do NOT appear in the target month at all. These may have been cancelled or lapsed.

4. **Price changes** — merchants present as recurring in both months but with a materially different amount (> 5% change). Note old vs. new amount.

5. **Totals**:
   - Total recurring spend this month
   - Total recurring spend prior month
   - Delta ($ and %)
   - Recurring as % of total spend
   - Annualized recurring run rate

### 5. Write the narrative

Write a well-structured Markdown report. Be specific and personal — reference actual dollar amounts, merchant names, and percentage changes. Avoid filler language.

```markdown
# {Month Name} {Year} Spending Report

## Summary
2–3 sentences covering total spend, the biggest driver, and one headline vs. prior month.
Include a one-sentence note on recurring charges as a share of total.

## Spending by Category
Ranked table with columns: Category | Amount | % of Total | vs. Prior Month.
Use ▲ / ▼ with the delta amount for the comparison column.

## Top Merchants
Ordered list of top 10 merchants: merchant name, total charged, transaction count.

## Recurring Charges

### Overview
- Total recurring this month: $X (Y% of total spend)
- Total recurring last month: $X (▲/▼ $delta)
- Annualized run rate: $X/yr

### By Category
Table with columns: Category | Merchants | Monthly Total | Annualized | % of Recurring.
List the specific merchant names under each category row or in a sub-list.

### New This Month
Bullet list of newly detected recurring charges (merchant + amount). Note "none detected" if empty.

### Dropped / No Longer Seen
Bullet list of recurring charges from last month that didn't appear this month. Flag whether likely cancelled or just delayed. Note "none" if empty.

### Price Changes
Bullet list of recurring charges where the amount changed materially vs. last month: merchant, old amount → new amount, % change. Note "none detected" if empty.

## Notable Transactions
Flag any single charges ≥ $200 or needs_review transactions: date, merchant, amount, brief note.

## Month-over-Month
Overall delta vs. prior month ($ and %). Call out the 2–3 largest category swings with context.

## Observations & Recommendations
4–6 actionable, specific bullets. Ground each in the actual data. Prioritize:
- Any concerning recurring charge trends (e.g. creeping subscription costs)
- Categories with large MoM increases
- Specific merchants or patterns worth addressing
- Opportunities to reduce the annualized recurring run rate
```

### 6. Save the report

Call `save_report` with:
- `month`: `"YYYY-MM"`
- `title`: `"{Month Name} {Year} Spending Report"`
- `narrative_md`: the full Markdown from step 4
- `model_used`: the model you are running on (e.g. `"claude-sonnet-4-6"`)
- `raw_data`: a JSON string of the key aggregated statistics from steps 3a and 3b

### 7. Confirm

After saving, call `get_report(month)` to verify persistence, then output:

```
Report saved: {Month Name} {Year} Spending Report
View at: http://localhost:8000/reports/{YYYY-MM}
```
