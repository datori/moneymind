## 1. Server Network Binding

- [x] 1.1 In `finance/web/app.py` `main()`, change `argparse` default for `--host` from `"127.0.0.1"` to `"0.0.0.0"`

## 2. Mobile Navigation (base.html)

- [x] 2.1 Add a hamburger `<button>` element to the nav bar, visible only on narrow viewports (`md:hidden`), with an inline SVG icon
- [x] 2.2 Add a collapsible mobile nav panel (`<div id="mobile-menu">`) containing all nav links in a vertical list, hidden by default (`hidden`)
- [x] 2.3 Add a small inline `<script>` that toggles `hidden` on `#mobile-menu` when the hamburger button is clicked
- [x] 2.4 Ensure the Sync Now button is accessible in the mobile menu panel (or remains visible outside the collapsed section)
- [x] 2.5 Verify that `md:` breakpoint classes restore the original horizontal nav for desktop viewports

## 3. Responsive Chart (index.html)

- [x] 3.1 Remove the `style="width:320px"` inline style from the chart container `<div>`
- [x] 3.2 Add `w-full` Tailwind class to the chart container so it fills available space
- [x] 3.3 Change Chart.js config from `responsive: false` to `responsive: true`
- [x] 3.4 Set `maintainAspectRatio: true` in the Chart.js options (or adjust as appropriate so chart height is reasonable)

## 4. Table Horizontal Scroll

- [x] 4.1 In `index.html` — wrap the spending breakdown table in `<div class="overflow-x-auto">`
- [x] 4.2 In `index.html` — wrap the credit utilization table in `<div class="overflow-x-auto">`
- [x] 4.3 In `index.html` — wrap the recent pipeline runs table in `<div class="overflow-x-auto">`
- [x] 4.4 In `transactions.html` — wrap the transactions table in `<div class="overflow-x-auto">`
- [x] 4.5 In `accounts.html` — wrap the accounts table in `<div class="overflow-x-auto">`
- [x] 4.6 In `pipeline.html` — wrap the run history table in `<div class="overflow-x-auto">`
- [x] 4.7 In `recurring.html` — wrap any data table in `<div class="overflow-x-auto">`
- [x] 4.8 In `review.html` — wrap any data table in `<div class="overflow-x-auto">`
