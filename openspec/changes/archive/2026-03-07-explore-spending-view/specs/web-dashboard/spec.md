## CHANGED Requirements

### Requirement: Spending breakdown page — summary strip
`GET /spending` SHALL render a summary strip between the filter form and the
chart/table area when spending data exists. The strip SHALL display:
- **Total spent**: sum of all spending rows for the selected period (formatted as `$X.XX`)
- **Transactions**: total transaction count across all groups
- **{Group}s**: count of distinct groups (categories/merchants/accounts) returned
- **Avg/day**: total spent divided by the number of days in the selected range, formatted as `$X.XX`

The route SHALL compute `total_spent`, `total_count`, `avg_per_day`, and pass
them to the template. `avg_per_day` SHALL use `max(1, days)` to avoid
division by zero on same-day ranges.

#### Scenario: Summary strip shows totals for current month
- **WHEN** a browser navigates to `/spending` with the default current-month range
- **THEN** the summary strip is visible above the chart, displaying total spent, transaction count, group count, and avg/day

#### Scenario: Summary strip absent when no data
- **WHEN** the selected period has no spending data
- **THEN** the summary strip is not rendered (it is inside `{% if spending %}`)

---

### Requirement: Spending breakdown table — % of Total column
The spending breakdown table SHALL include a fourth column "% of Total"
for each data row. The column SHALL display:
- A percentage value (1 decimal place, e.g. "42.3%")
- A mini horizontal progress bar (indigo, `h-1.5 rounded-full`) showing the
  proportion visually, with width set to the percentage value

The percentage is computed as `row.total / total_spent * 100` in the template.

#### Scenario: % column shows proportions
- **WHEN** the spending page renders with category data
- **THEN** each row shows its percentage of total spending and a corresponding mini bar

---

### Requirement: Spending breakdown table — totals footer row
The spending breakdown table SHALL include a `<tfoot>` row below all data rows
showing: "Total" label | grand total amount | total transaction count | "100%".
The footer row SHALL use a visually distinct top border (`border-t-2`) and
semi-bold font.

#### Scenario: Footer row shows grand total
- **WHEN** the spending page renders with data
- **THEN** the table footer row shows the sum of all amounts and the total transaction count

---

### Requirement: Spending page — group_by auto-submit
The "Group by" `<select>` element on the `/spending` page SHALL include
`onchange="this.form.submit()"` so that changing the selected group triggers
an immediate form submission, consistent with the behavior of the
"Include Financial Activity" checkbox.

#### Scenario: Group by change triggers immediate reload
- **WHEN** the user selects a different value in the "Group by" dropdown
- **THEN** the form submits immediately without requiring the user to click Apply
