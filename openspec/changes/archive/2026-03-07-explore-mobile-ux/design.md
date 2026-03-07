# Design: Explore mobile-ux

## Overview

The loop applied a single, consistent design pattern across four data-heavy pages:
use Tailwind's responsive `hidden {breakpoint}:table-cell` utilities to hide
non-essential table columns on smaller screens, revealing them progressively as
viewport width increases. Every modified page now has a usable mobile layout
(typically 3-5 columns) while preserving the full column set on desktop.

The changes are purely presentational — no backend routes, data models, or JS logic
were modified. The pattern is minimal, reversible, and consistent across all pages.

## Iteration Progression

**Iteration 1 — transactions.html**: The most frequently visited page. The 6-column
table (Date, Description, Merchant, Category, Account, Amount) was reduced to 3 columns
on mobile (Date, Category, Amount) by hiding Description at `sm` and Merchant/Account
at `md`. Category and Amount are the highest-signal columns for a quick mobile scan.

**Iteration 2 — accounts.html**: The 8-column accounts table was addressed next.
Institution, Type, and Txns are hidden until `sm`; Date Range and Last Synced until
`lg`. This leaves Account Name, Balance, and Actions visible on mobile — the minimum
needed to understand what an account is worth and take action (delete).

**Iteration 3 — review.html**: The review queue is the most interaction-critical page.
Its 7-column table contains an embedded HTML form spanning two cells (Category select
opening in one `<td>`, Approve button closing in another). A full card-layout rewrite
was not chosen because the form's multi-cell span would require significant duplication.
Instead, Description and Merchant are hidden at `md`, Reason at `sm` — leaving Date,
Amount, Category select, and Approve visible on mobile, which is sufficient to action
every item in the queue.

**Iteration 4 — recurring.html**: The three recurring tables (Needs Attention, Active
Subscriptions, Likely Cancelled) each use 8 columns via a shared `table_header()` Jinja2
macro. Interval, Times Seen, and Total Spent are hidden at `sm` across all three sections
and in the macro. This was done via a Python script to ensure all 9 affected cells
(3 columns × 3 sections) were updated consistently. The actionable columns — Merchant,
Typical, Next Due, Status, Cancel — remain visible on mobile.

## Design Decisions

**Column selection for hiding**: Each page kept the columns most critical for a quick
mobile scan or for taking action:
- Transactions: Date + Category + Amount (scan)
- Accounts: Account Name + Balance + Actions (take action)
- Review: Date + Amount + Category select + Approve (take action)
- Recurring: Merchant + Typical + Next Due + Status + Cancel (scan + take action)

The alternative (hiding everything behind a "details" expansion) was not chosen because
it would require JavaScript state management and would make the tables harder to scan.

**Breakpoint choices**: The loop used `sm` (640px) and `md` (768px) consistently, with
`lg` (1024px) reserved for the least essential metadata (Date Range, Last Synced on
accounts). This matches the existing breakpoint conventions in the project (`md:flex-row`,
`md:hidden` nav, etc.).

**No card-layout rewrite for review queue**: The review queue's form structure (opening
`<form>` in one `<td>`, closing `</form>` in another two cells later) means a card
layout on mobile would require duplicating the entire form structure — once for cards,
once for the table. The column-hiding approach avoids this duplication at the cost of
a slightly less rich mobile layout. The tradeoff is acceptable given the queue is
typically short.

**Recurring macro consistency**: The `table_header()` macro applies column hiding to
the headers, but the data rows are rendered inline in three separate sections. A Python
replacement script was used to ensure all matching cell patterns were updated together,
avoiding the risk of mismatched header/cell visibility that would produce broken
column alignment.

## Coherence Assessment

The loop was well-focused and converged cleanly. Each iteration addressed exactly one
page, used the same Tailwind pattern, and did not revisit earlier decisions. The
breakpoint choices are internally consistent across all four pages.

The one area of mild complexity is the review queue, where the multi-cell form structure
forced a compromise (column hiding rather than card layout). This is noted in the
design decision above. A future improvement could add a proper mobile card layout
using `sm:hidden` cards alongside a `hidden sm:block` table, but that was beyond this
loop's scope.

## What Was Improved

- **Transactions table**: From 6 columns (always, horizontal scroll on mobile) to
  3 columns on mobile / 4 on sm / 6 on md+. Eliminates horizontal scrolling on phones.
- **Accounts table**: From 8 columns to 3 on mobile / 6 on sm / 8 on lg+.
- **Review queue**: From 7 columns (embedded form, nearly unusable on mobile) to
  4 columns on mobile (Date, Amount, Category, Approve) — sufficient to action items.
- **Recurring tables**: From 8 columns to 5 on mobile / 8 on sm+, across all three
  sections (Needs Attention, Active Subscriptions, Likely Cancelled).

## What Was Not Addressed

- **Filter forms**: The transactions and spending filter forms have fixed-width inputs
  (`w-48`, `w-24`) that could be made full-width on mobile. Not addressed in this loop.
- **Review queue card layout**: A proper stacked card layout on mobile would be more
  touch-friendly but requires HTML duplication due to the form structure.
- **Recurring cancel inline form**: The "Track Cancel" collapsible form expands inside
  a table cell, which remains cramped on mobile. Not addressed.
- **Dashboard pipeline runs table**: The Started timestamp uses a raw unix-ms integer
  on the server side (not yet formatted) — noted in the prompt but not improved.
