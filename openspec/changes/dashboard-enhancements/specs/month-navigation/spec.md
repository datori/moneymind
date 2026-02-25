## ADDED Requirements

### Requirement: Month prev/next navigation on spending and transactions pages

The spending page (`GET /spending`) and transactions page (`GET /transactions`) filter bars SHALL each include a pair of prev/next month navigation buttons rendered adjacent to the date inputs. Clicking the "previous month" button (`‹`) SHALL set `start` and `end` to the first and last day of the month preceding the currently displayed month and submit the form. Clicking the "next month" button (`›`) SHALL do the same for the following month. The buttons SHALL be implemented entirely in client-side JavaScript with no additional backend routes or query parameters.

The current month label (e.g., "Feb 2026") SHALL be displayed between the two buttons, derived from the current `start` value.

#### Scenario: Previous month navigation from spending page
- **WHEN** the spending page is showing February 2026 (`start=2026-02-01&end=2026-02-28`) and the user clicks ‹
- **THEN** the page reloads with `start=2026-01-01&end=2026-01-31` and the chart updates for January 2026

#### Scenario: Next month navigation from spending page
- **WHEN** the spending page is showing January 2026 (`start=2026-01-01&end=2026-01-31`) and the user clicks ›
- **THEN** the page reloads with `start=2026-02-01&end=2026-02-28`

#### Scenario: Leap year February handled correctly
- **WHEN** navigating to February in a leap year (e.g., 2028)
- **THEN** `end` is set to `2028-02-29` (the correct last day of February 2028)

#### Scenario: Month label shown between buttons
- **WHEN** the spending page is loaded with `start=2026-03-01`
- **THEN** the month label between ‹ and › reads "Mar 2026"

#### Scenario: Month nav on transactions page
- **WHEN** the transactions page is showing March 2026 and the user clicks ‹
- **THEN** the page reloads with `start=2026-02-01&end=2026-02-28`

#### Scenario: Other filter params preserved during month navigation
- **WHEN** the spending page has `group_by=merchant&include_financial=1` and the user clicks ‹
- **THEN** the resulting URL retains `group_by=merchant&include_financial=1` alongside the updated date params
