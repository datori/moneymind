## ADDED Requirements

### Requirement: Accounts page — credit utilization panel

The `GET /accounts` route SHALL call `get_credit_utilization(conn)` and pass the
result as `credit_util` to the `accounts.html` template.

When `credit_util.cards` is non-empty, the template SHALL render a "Credit Utilization"
panel between the global summary bar and the transaction timeline chart.

The panel SHALL include:
- A header "Credit Utilization" with the aggregate dollar amounts ($X used of $Y)
  and aggregate utilization percentage when `aggregate_pct` is not None
- A full-width progress bar colored by utilization: green (<30%), amber (30–70%), red (≥70%)
- When more than one credit card exists: a responsive grid of per-card tiles, each
  showing card name, balance, limit (if configured), utilization percentage, and a
  mini progress bar; cards without a configured limit show "no limit set"

#### Scenario: Credit utilization panel renders when cards exist
- **WHEN** at least one active credit account exists
- **THEN** the accounts page renders a "Credit Utilization" panel above the timeline chart

#### Scenario: Aggregate progress bar color reflects utilization
- **WHEN** aggregate utilization is below 30%
- **THEN** the progress bar is green
- **WHEN** aggregate utilization is between 30% and 70%
- **THEN** the progress bar is amber
- **WHEN** aggregate utilization is 70% or above
- **THEN** the progress bar is red

#### Scenario: Per-card grid shown for multiple cards
- **WHEN** two or more credit accounts exist
- **THEN** a grid of per-card tiles is rendered below the aggregate bar

#### Scenario: Panel hidden when no credit accounts
- **WHEN** no active credit accounts exist
- **THEN** the credit utilization panel is not rendered

---

### Requirement: Accounts page — balance totals in summary bar

The global summary bar on `GET /accounts` SHALL include, in addition to account count,
transaction count, and date range: total assets (sum of positive balances), total
liabilities (sum of absolute values of negative balances), and net worth
(assets − liabilities).

These values SHALL be computed in the route handler from `merged_accounts` and passed
as `total_assets`, `total_liabilities`, and `net_worth` to the template.

Assets and a positive net worth SHALL be styled emerald; liabilities and a negative
net worth SHALL be styled red.

#### Scenario: Summary bar shows balance totals
- **WHEN** a browser navigates to `/accounts`
- **THEN** the summary bar shows "Assets $X · Liabilities $Y · Net $Z" in addition
  to the account count, transaction count, and date range

#### Scenario: Negative net worth shown with deficit label
- **WHEN** total liabilities exceed total assets
- **THEN** the net amount is rendered in red with the word "deficit" appended

---

### Requirement: Accounts table — account type badges

The Type column in the accounts table on `GET /accounts` SHALL render colored pill
badges rather than plain text.

Badge colors by type:
- checking → blue (bg-blue-100 text-blue-700)
- savings → emerald (bg-emerald-100 text-emerald-700)
- credit → orange (bg-orange-100 text-orange-700)
- investment → purple (bg-purple-100 text-purple-700)
- unknown type → gray, capitalized
- null type → em dash

#### Scenario: Account type rendered as colored badge
- **WHEN** the accounts table renders a checking account
- **THEN** the Type column shows a blue pill badge labeled "Checking"

---

### Requirement: Accounts table — available credit sub-line

For accounts with `type == 'credit'` and a non-null `available` field, the Balance
column SHALL display the available credit as a small muted sub-line below the balance
(format: "$X,XXX avail").

#### Scenario: Available credit shown for credit accounts
- **WHEN** a credit account has a non-null `available` value
- **THEN** the Balance cell shows the balance on the first line and "$X,XXX avail"
  in small muted text below it

#### Scenario: Available credit not shown for non-credit accounts
- **WHEN** a checking or savings account has a non-null `available` value
- **THEN** the available sub-line is NOT rendered in the Balance cell
