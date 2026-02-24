## 1. Project Setup

- [x] 1.1 Add `fastapi`, `jinja2`, `uvicorn`, and `python-multipart` to `pyproject.toml` dependencies
- [x] 1.2 Add `finance-dashboard = "finance.web.app:main"` entry point to `pyproject.toml`
- [x] 1.3 Run `uv sync` to update lockfile
- [x] 1.4 Create `finance/web/__init__.py` and `finance/web/app.py` with a FastAPI app instance and `main()` entry point that runs `uvicorn`

## 2. Templates and Styles

- [x] 2.1 Create `finance/web/templates/base.html` — HTML shell with Tailwind CSS CDN, Chart.js CDN, nav links (Dashboard, Accounts, Transactions, Net Worth, Spending), "Sync Now" button form
- [x] 2.2 Create `finance/web/templates/index.html` extending base — net worth summary cards, spending by category table/chart, credit utilization section
- [x] 2.3 Create `finance/web/templates/accounts.html` extending base — table of all accounts
- [x] 2.4 Create `finance/web/templates/transactions.html` extending base — transaction table with date range filter form
- [x] 2.5 Create `finance/web/templates/net_worth.html` extending base — Chart.js line chart of net worth history
- [x] 2.6 Create `finance/web/templates/spending.html` extending base — Chart.js bar chart of spending by category, with month selector form

## 3. FastAPI Routes

- [x] 3.1 Implement DB dependency `get_db()` — yields a `sqlite3.Connection`, closes on exit
- [x] 3.2 Implement `GET /` — calls `get_net_worth()`, `get_spending_summary()` (current month), `get_credit_utilization()`; renders `index.html`
- [x] 3.3 Implement `GET /accounts` — calls `get_accounts()`; renders `accounts.html`
- [x] 3.4 Implement `GET /transactions` — accepts query params `start`, `end`, `limit`; calls `get_transactions()`; renders `transactions.html`
- [x] 3.5 Implement `GET /net-worth` — calls `get_balance_history()`; aggregates daily net worth; renders `net_worth.html` with Chart.js data as JSON in template
- [x] 3.6 Implement `GET /spending` — accepts `start`, `end`, `group_by` query params; calls `get_spending_summary()`; renders `spending.html`
- [x] 3.7 Implement `POST /sync` — calls `sync_all(conn)`; stores result in flash message (or query param); redirects to `Referer` header URL (or `/`)

## 4. CLI Entry Point

- [x] 4.1 Implement `main()` in `finance/web/app.py` — parses `--port` (default 8080) and `--host` (default 127.0.0.1) CLI args; calls `uvicorn.run(app, host=host, port=port)`

## 5. Verification

- [x] 5.1 Verify `uv run finance-dashboard --help` exits 0
- [x] 5.2 Verify `uv run finance-dashboard` starts server and `curl http://localhost:8080/` returns 200
- [x] 5.3 Navigate to `http://localhost:8080/` in browser and verify dashboard home renders with real data
- [x] 5.4 Verify `/transactions` date filter form works (change dates, page reloads with filtered results)
- [x] 5.5 Verify `/net-worth` shows a Chart.js line chart with data points
- [x] 5.6 Verify "Sync Now" button triggers sync and redirects back to home page
