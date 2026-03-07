## UPDATED Requirement: Wide tables scroll horizontally on narrow viewports

All data tables in the dashboard SHALL be wrapped in an `overflow-x-auto` container.
Key tables (transactions, accounts, review queue, recurring) SHALL additionally hide
non-essential columns at small breakpoints using Tailwind responsive `hidden {bp}:table-cell`
utilities, so that the most actionable columns remain visible without horizontal scrolling.
All hidden columns become visible on larger viewports.

### Column visibility by page

**Transactions table** (`/transactions`):
- xs (< 640px): Date, Category, Amount
- sm (≥ 640px): + Description
- md (≥ 768px): + Merchant, Account (all 6 columns)

**Accounts table** (`/accounts`):
- xs (< 640px): Account Name, Balance, Actions
- sm (≥ 640px): + Institution, Type, Txns
- lg (≥ 1024px): + Date Range, Last Synced (all 8 columns)

**Review queue table** (`/review`):
- xs (< 640px): Date, Amount, Category (select), Action (Approve)
- sm (≥ 640px): + Reason
- md (≥ 768px): + Description, Merchant (all 7 columns)

**Recurring tables** (`/recurring` — Needs Attention, Active, Likely Cancelled):
- xs (< 640px): Merchant, Typical, Next Due, Status, Cancel
- sm (≥ 640px): + Interval, Times Seen, Total Spent (all 8 columns)

**All other tables** (pipeline, spending, dashboard) remain full-width with
`overflow-x-auto` scroll only.

#### Scenario: Transaction table on mobile (xs)
- **WHEN** the `/transactions` page is viewed on a viewport narrower than 640px
- **THEN** the table shows 3 columns: Date, Category, Amount; Description, Merchant,
  and Account columns are hidden

#### Scenario: Transaction table on sm viewport
- **WHEN** the `/transactions` page is viewed on a viewport between 640px and 767px
- **THEN** Description is visible; Merchant and Account remain hidden

#### Scenario: Transaction table on md+ viewport
- **WHEN** the `/transactions` page is viewed on a viewport 768px or wider
- **THEN** all 6 columns (Date, Description, Merchant, Category, Account, Amount)
  are visible

#### Scenario: Accounts table on mobile
- **WHEN** the `/accounts` page is viewed on a viewport narrower than 640px
- **THEN** the table shows: Account Name, Balance, Actions; all other columns hidden

#### Scenario: Review queue on mobile
- **WHEN** the `/review` page is viewed on a viewport narrower than 640px
- **THEN** the table shows Date, Amount, Category select, and Approve button;
  the form remains fully functional to approve transactions

#### Scenario: Recurring tables on mobile
- **WHEN** `/recurring` is viewed on a viewport narrower than 640px
- **THEN** each recurring table shows Merchant, Typical, Next Due, Status, Cancel;
  Interval, Times Seen, and Total Spent are hidden
