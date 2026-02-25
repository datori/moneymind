## Why

The dev server only binds to loopback by default, making it inaccessible from other devices on the local network (e.g. a phone). Additionally, the dashboard was built for desktop and several pages overflow or clip on narrow screens, making it unusable for quick checks on mobile.

## What Changes

- Change `finance-dashboard` default `--host` from `127.0.0.1` to `0.0.0.0` so the server is reachable from any device on the LAN without requiring a flag
- Add a hamburger-style collapsible mobile navigation menu to `base.html` (8 nav items + action button cannot fit in a single row on a phone)
- Wrap all wide data tables in `overflow-x-auto` containers so they scroll horizontally on narrow viewports rather than clipping
- Fix the spending doughnut chart: remove fixed `width:320px` inline style and set `responsive: true` in Chart.js options so it scales with the container

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `web-dashboard`: server default host changes to `0.0.0.0`; navigation, tables, and chart gain mobile-responsive behaviour

## Impact

- `finance/web/app.py`: change `default="127.0.0.1"` → `default="0.0.0.0"` in `argparse` setup
- `finance/web/templates/base.html`: add mobile nav toggle (hamburger button + collapsible menu panel using Tailwind utilities)
- `finance/web/templates/index.html`: fix chart container width and `responsive: false` → `true`
- `finance/web/templates/transactions.html`: wrap table in `overflow-x-auto`
- `finance/web/templates/accounts.html`: wrap table in `overflow-x-auto`
- `finance/web/templates/pipeline.html`: wrap run-history table in `overflow-x-auto`
- `finance/web/templates/recurring.html`: wrap table in `overflow-x-auto` (if applicable)
- `finance/web/templates/review.html`: wrap table in `overflow-x-auto` (if applicable)
- No dependency or schema changes; pure UI/server config changes
