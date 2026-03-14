## 1. Demo seed script and database

- [x] 1.1 Create `finance/demo/__init__.py` (empty module marker)
- [x] 1.2 Create `finance/demo/seed.py` — generates `data/demo.db` with `init_db()` then inserts: 4 accounts (Chase Checking, HYSA Savings, Amex Gold credit, Schwab Brokerage), 13 months of transactions (~30/month across realistic categories), monthly balance snapshots, 6 recurring merchants, 3 `needs_review` transactions, 1 pipeline `run_log` entry
- [x] 1.3 Run `python -m finance.demo.seed` and verify `data/demo.db` is created without errors

## 2. Demo-mode database dependency

- [x] 2.1 In `finance/web/app.py`, add `request: Request` parameter to `get_db()` so FastAPI injects it automatically
- [x] 2.2 In `get_db()`, check `request.query_params.get("demo") == "1"` and open `data/demo.db` instead of `data/finance.db` when true

## 3. Block dangerous mutations

- [x] 3.1 In the `/sync` POST handler, add an early guard: if `request.query_params.get("demo") == "1"` raise `HTTPException(400, "Not available in demo mode")`
- [x] 3.2 In the `/pipeline/run/stream` GET handler, add the same guard

## 4. Thread demo_mode into template contexts

- [x] 4.1 Add helper `_is_demo(request: Request) -> bool` returning `request.query_params.get("demo") == "1"` in `app.py`
- [x] 4.2 Add `"demo_mode": _is_demo(request)` to every `templates.TemplateResponse(...)` context dict across all GET route handlers (index, accounts, transactions, net_worth, spending, review, recurring, pipeline, reports, report_detail)

## 5. Demo banner in base template

- [x] 5.1 In `finance/web/templates/base.html`, add a demo banner just above the flash messages block: rendered only when `{{ demo_mode }}` is truthy — yellow/amber background, text "Demo Mode — viewing synthetic data", visible on all pages
