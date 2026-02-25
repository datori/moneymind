## MODIFIED Requirements

### Requirement: GET /recurring web route — enriched display

The `GET /recurring` route SHALL render the recurring charges table grouped into three visual sections, ordered top-to-bottom: **Needs Attention**, **Active Subscriptions**, and **Likely Cancelled**. The route SHALL pre-group data server-side and pass three separate lists to the template: `attention` (merchants with `status` in `past_due`, `due_any_day`, `due_soon`), `active` (merchants with `status` in `upcoming`, `None`), and `cancelled` (merchants with `status == "likely_cancelled"`).

**Columns** (all sections): Merchant, Interval, Typical Amount, Next Due, Status.

The **Next Due** column SHALL display the value of `next_due_date` (ISO date string `YYYY-MM-DD`) or `"—"` when `next_due_date` is `None`.

**Needs Attention section** (rendered only when `attention` is non-empty):
- Each row SHALL display a 4px colored left-border stripe: red (`border-red-500`) for `past_due`, blue (`border-blue-500`) for `due_any_day`, amber (`border-amber-500`) for `due_soon`

**Active Subscriptions section** (rendered only when `active` is non-empty):
- Standard rows with no urgency indicator

**Likely Cancelled section** (rendered using a native HTML `<details>` element, collapsed by default):
- The `<summary>` SHALL display the count, e.g., "Likely Cancelled (2)"

**Status cell color-coding:**
- `"upcoming"` → gray text "Due in {n}d" (or "Due in ~{n}mo" if > 30 days)
- `"due_soon"` → amber/yellow "Due in {n}d"
- `"due_any_day"` → blue "Due any day"
- `"past_due"` → red "Past due {abs(n)}d" (or "Past due ~{months}mo" if > 60 days overdue)
- `"likely_cancelled"` → gray secondary text "Last ~{interval_label}" + red "Cancelled?" badge
- `None` → gray "—"

The merchant name cell SHALL link to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`.

#### Scenario: Needs Attention section renders for urgent merchants

- **WHEN** one or more merchants have `status` in `past_due`, `due_any_day`, or `due_soon`
- **THEN** a "Needs Attention" section header appears above a table containing only those merchants

#### Scenario: Active Subscriptions section renders for healthy merchants

- **WHEN** one or more merchants have `status` in `upcoming` or `None`
- **THEN** an "Active Subscriptions" section header appears above a table containing only those merchants

#### Scenario: Needs Attention section absent when no urgent merchants

- **WHEN** all merchants have `status` in `upcoming`, `None`, or `likely_cancelled`
- **THEN** no "Needs Attention" section header or table is rendered

#### Scenario: Likely Cancelled section is collapsed by default

- **WHEN** one or more merchants have `status == "likely_cancelled"`
- **THEN** a `<details>` element is rendered at the bottom of the page; its `<summary>` shows the cancelled count; it is collapsed on initial page load

#### Scenario: Past due row has red left border

- **WHEN** a merchant with `status == "past_due"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px red left border

#### Scenario: Due any day row has blue left border

- **WHEN** a merchant with `status == "due_any_day"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px blue left border

#### Scenario: Due soon row has amber left border

- **WHEN** a merchant with `status == "due_soon"` is rendered in the Needs Attention section
- **THEN** its table row displays a 4px amber left border

#### Scenario: Next Due column shows ISO date when available

- **WHEN** a merchant has a non-null `next_due_date`
- **THEN** the Next Due cell displays the date as `YYYY-MM-DD`

#### Scenario: Next Due column shows dash when unavailable

- **WHEN** a merchant has `next_due_date == None`
- **THEN** the Next Due cell displays "—"

#### Scenario: Merchant name links to transaction search

- **WHEN** the user clicks a merchant name on the recurring page
- **THEN** the browser navigates to `/transactions?search={merchant_normalized}&sort_by=amount&sort_dir=desc`

#### Scenario: Empty recurring page

- **WHEN** `GET /recurring` is requested and no recurring charges exist
- **THEN** the page renders a message: "No recurring charges detected."
