---
name: screenshots
description: Generate polished UI screenshots of the Finance Dashboard using demo data and update the README. Use when the user wants to refresh screenshots, update the README hero images, or capture the current state of the UI.
metadata:
  author: local
  version: "1.1"
---

Generate fresh screenshots of the Finance Dashboard and update the README.

## Steps

**1. Check prerequisites**

Verify `data/demo.db` exists. If it does not, regenerate it first:

```bash
.venv/bin/python3 -m finance.demo.seed
```

Verify `node_modules/` exists at the project root. If it does not, install dependencies:

```bash
npm install
```

**2. Run the screenshot script**

```bash
node scripts/screenshots.mjs
```

This starts the finance-dashboard server pointed at `data/demo.db` (via `?demo=1`), captures five pages with February 2026 date range for full data, polishes each with a dark framed wrapper, and writes them to `screenshots/`:
- `dashboard-demo.png` — home page (net worth, spending summary, credit utilization)
- `spending-demo.png` — spending breakdown with bar chart and category table (Feb 2026)
- `transactions-demo.png` — transaction browser with filters and daily spending chart (Feb 2026)
- `recurring-demo.png` — recurring charges with 13-month timeline
- `accounts-demo.png` — account overview with transaction volume history

If the command fails, report the error and stop.

**3. Display the screenshots to the user**

Read and display all five output files so the user can see the results inline:
1. `screenshots/dashboard-demo.png`
2. `screenshots/spending-demo.png`
3. `screenshots/transactions-demo.png`
4. `screenshots/recurring-demo.png`
5. `screenshots/accounts-demo.png`

**4. Ensure the README has a prominent screenshots section**

Read `README.md` and verify it contains:

A hero image right after the introductory paragraph and before the Features section:
```markdown
![Finance Dashboard](screenshots/dashboard-demo.png)
```

And a 2×2 screenshot grid in the Screenshots section:
```markdown
| Spending | Transactions |
|----------|--------------|
| ![Spending breakdown](screenshots/spending-demo.png) | ![Transaction browser](screenshots/transactions-demo.png) |

| Recurring charges | Accounts |
|-------------------|----------|
| ![Recurring charges](screenshots/recurring-demo.png) | ![Account overview](screenshots/accounts-demo.png) |
```

If either block is missing or paths are wrong, update `README.md` to match. Do not change anything else.

**5. Confirm**

Tell the user which files were written and confirm the README is up to date. Keep it brief.
