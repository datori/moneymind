## MODIFIED Requirements

### Requirement: Dashboard web server starts
The system SHALL provide a `finance-dashboard` entry point that starts a web server. The default host SHALL be `0.0.0.0` (all interfaces) so the server is reachable from devices on the local network without requiring an explicit flag. The `--host` flag SHALL still be accepted for explicit override.

#### Scenario: Server starts on default host binding to all interfaces
- **WHEN** `uv run finance-dashboard` is executed without a `--host` flag
- **THEN** a web server starts bound to `0.0.0.0:8080` and is accessible from other devices on the local network

#### Scenario: Custom port and host
- **WHEN** `uv run finance-dashboard --port 9090 --host 127.0.0.1` is executed
- **THEN** the server starts on the specified host and port

---

### Requirement: Mobile-responsive navigation
The navigation bar in `base.html` SHALL be usable on screens as narrow as 390px. On viewports narrower than `md` (768px), the navigation links SHALL be hidden by default and toggled by a hamburger button. On `md` and wider viewports, the navigation SHALL display as a standard horizontal bar with no behaviour change.

#### Scenario: Nav on desktop viewport
- **WHEN** a page is loaded on a viewport 768px wide or wider
- **THEN** all navigation links are visible in a single horizontal row alongside the Sync Now button

#### Scenario: Nav on mobile viewport — links hidden by default
- **WHEN** a page is loaded on a viewport narrower than 768px
- **THEN** the navigation links are hidden and a hamburger icon button is visible

#### Scenario: Nav on mobile viewport — links revealed
- **WHEN** the user taps the hamburger button on a narrow viewport
- **THEN** the navigation links appear in a vertical dropdown panel, each link is tappable, and the sync button is accessible

#### Scenario: Nav link closes mobile menu on navigation
- **WHEN** the user taps a navigation link in the open mobile menu
- **THEN** the browser navigates to that page (the menu closes naturally on page load)

---

### Requirement: Wide tables scroll horizontally on narrow viewports
All data tables in the dashboard SHALL be wrapped in an `overflow-x-auto` container so that on narrow viewports the table can be scrolled horizontally rather than clipping or overflowing the page layout. No table columns SHALL be hidden or removed. All existing data remains accessible.

#### Scenario: Transaction table on mobile
- **WHEN** the `/transactions` page is viewed on a viewport narrower than 768px
- **THEN** the full 7-column table is accessible via horizontal scroll; no columns are hidden

#### Scenario: Pipeline run history table on mobile
- **WHEN** the `/pipeline` page is viewed on a viewport narrower than 768px
- **THEN** the full 8-column run history table is accessible via horizontal scroll

#### Scenario: Accounts table on mobile
- **WHEN** the `/accounts` page is viewed on a viewport narrower than 768px
- **THEN** the accounts table is accessible via horizontal scroll

#### Scenario: Review and recurring tables on mobile
- **WHEN** `/review` or `/recurring` is viewed on a narrow viewport
- **THEN** any data table on those pages is accessible via horizontal scroll

---

### Requirement: Spending chart is responsive
The spending doughnut chart on the dashboard home page (`GET /`) SHALL scale with its container. The chart container SHALL NOT have a fixed inline `width` style. The Chart.js configuration SHALL use `responsive: true` so the chart redraws to fill available space when the viewport changes.

#### Scenario: Chart renders at full container width on desktop
- **WHEN** the dashboard home page is loaded on a desktop viewport
- **THEN** the spending chart fills the width of its container card

#### Scenario: Chart renders correctly on narrow viewport
- **WHEN** the dashboard home page is loaded on a viewport narrower than 768px
- **THEN** the spending chart renders without clipping or horizontal overflow, fitting within the screen width
