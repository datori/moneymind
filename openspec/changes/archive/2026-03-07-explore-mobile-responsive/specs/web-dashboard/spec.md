## ADDED Requirements

### Requirement: Spending page summary strip wraps on mobile
The summary strip on `GET /spending` SHALL use a wrapping flex layout
(`flex flex-wrap`) so that on narrow viewports the four stats (Total spent,
Transactions, Groups, Avg/day) can flow onto multiple lines rather than
overflowing or squeezing to illegible widths. The pipe separator dividers
between stats SHALL be hidden on xs viewports (`hidden sm:block`) to avoid
orphaned separators when items wrap.

#### Scenario: Summary strip on mobile viewport
- **WHEN** the `/spending` page is viewed on a viewport narrower than 640px
- **THEN** the four summary stats wrap onto multiple lines without horizontal overflow; pipe dividers are not visible

#### Scenario: Summary strip on tablet/desktop viewport
- **WHEN** the `/spending` page is viewed on a viewport 640px or wider
- **THEN** all four stats appear in a single horizontal row separated by pipe dividers

---

### Requirement: Spending page chart and table stack on mobile
On `GET /spending`, the bar chart and breakdown table SHALL be arranged in a
vertical stack on mobile (`flex-col`) and side-by-side on large viewports
(`lg:flex-row`). Each panel SHALL be full-width below the `lg` breakpoint.

#### Scenario: Spending layout on mobile
- **WHEN** the `/spending` page is viewed on a viewport narrower than 1024px
- **THEN** the bar chart appears above the breakdown table, each taking full width; no horizontal overflow occurs

#### Scenario: Spending layout on large viewport
- **WHEN** the `/spending` page is viewed on a viewport 1024px or wider
- **THEN** the chart and table appear side-by-side in a two-column flex row

---

### Requirement: Dashboard home spending section stacks on mobile
On `GET /`, the spending category table and doughnut chart SHALL be arranged
vertically on mobile (`flex-col`) and side-by-side on medium viewports
(`md:flex-row`). The table SHALL be full-width below `md`; the chart retains
its fixed `md:w-80` width on medium and larger viewports.

#### Scenario: Dashboard spending section on mobile
- **WHEN** the `/` page is viewed on a viewport narrower than 768px
- **THEN** the spending category table appears above the doughnut chart, each at full width

#### Scenario: Dashboard spending section on desktop
- **WHEN** the `/` page is viewed on a viewport 768px or wider
- **THEN** the spending table and doughnut chart appear side-by-side

---

### Requirement: Recurring page header wraps on mobile
The recurring page header SHALL use a wrapping flex layout so that the filter
chips (Housing, Education, Health) wrap below the page heading on narrow
viewports instead of overflowing or colliding with the heading text.

#### Scenario: Recurring header on mobile viewport
- **WHEN** the `/recurring` page is viewed on a viewport narrower than the combined width of the heading and all three chips
- **THEN** the chip group wraps to a new line below the heading; no overflow occurs

---

### Requirement: Recurring page summary strip stacks on mobile
The recurring summary strip (Monthly, Annual, Due Soon cards) SHALL use a
responsive grid that collapses to a single column on mobile
(`grid-cols-1 sm:grid-cols-3`).

#### Scenario: Recurring summary on mobile
- **WHEN** the `/recurring` page is viewed on a viewport narrower than 640px
- **THEN** the Monthly, Annual, and Due Soon cards stack vertically

#### Scenario: Recurring summary on tablet/desktop
- **WHEN** the `/recurring` page is viewed on a viewport 640px or wider
- **THEN** the three summary cards appear in a single horizontal row

---

### Requirement: Report detail page — reduced mobile padding
The narrative card on `GET /reports/{month}` SHALL use responsive padding:
`p-4` on mobile and `p-8` on `sm` and wider viewports, so that text is not
edge-to-edge on narrow screens.

#### Scenario: Report detail padding on mobile
- **WHEN** a report detail page is viewed on a viewport narrower than 640px
- **THEN** the narrative card has 1rem (16px) padding on all sides

#### Scenario: Report detail padding on larger viewports
- **WHEN** a report detail page is viewed on a viewport 640px or wider
- **THEN** the narrative card has 2rem (32px) padding on all sides

---

### Requirement: Report detail page — markdown tables scroll horizontally
On `GET /reports/{month}`, markdown tables rendered from the narrative SHALL be
individually wrapped in a scrollable container (`overflow-x: auto`) so that
wide tables do not cause the entire page to overflow. This wrapping SHALL be
applied via JavaScript post-render after marked.js processes the narrative
source.

#### Scenario: Wide markdown table on mobile
- **WHEN** the narrative contains a table wider than the viewport
- **THEN** the table scrolls horizontally within its container; the rest of the page does not scroll horizontally

#### Scenario: Narrow markdown table unaffected
- **WHEN** the narrative contains a table narrower than the viewport
- **THEN** the table renders normally with no visible scroll bar
