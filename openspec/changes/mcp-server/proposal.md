# Proposal: mcp-server

## Problem / Motivation

With data in SQLite, we need a way to query and reason over it. The primary interface is an MCP server that exposes financial tools to any Claude session. A CLI provides the same capabilities for testing, scripting, and cron use.

The analysis layer (pure query functions) lives here too — it's only valuable once something calls it, so it ships together with the server.

## Goals

- Implement `finance/analysis/` — pure Python functions that query SQLite and return structured data
- Implement `finance/server.py` — MCP server exposing all analysis functions as tools
- Implement `finance/cli.py` — Click CLI with subcommands mirroring the MCP tools
- MCP server runnable via `uv run finance-mcp`
- CLI runnable via `uv run finance <command>`

## Non-goals

- AI/LLM features — that's `ai-categorize`
- CSV import — that's `csv-import`
- Web dashboard — that's `dashboard`
- The `sync` command is already in `simplefin-sync`; this change adds read-only query commands

## MCP Tools

### `get_accounts()`
Returns all active accounts with their most recent balance.
```
→ [{ id, name, type, institution, balance, available, currency, mask, last_updated }]
```

### `get_transactions(start_date?, end_date?, account_id?, category?, min_amount?, max_amount?, limit?)`
Filtered transaction list. Defaults: last 30 days, limit 100.
```
→ [{ id, date, amount, description, merchant_name, category, account_id, account_name, pending }]
```

### `get_net_worth(as_of_date?)`
Current net worth broken down by account type.
```
→ { total, assets, liabilities, by_type: { checking, savings, investment, credit, loan }, as_of }
```

### `get_spending_summary(start_date, end_date, group_by?)`
Aggregate spending. `group_by`: "category" | "merchant" | "account". Default: "category".
```
→ [{ label, total, count }]
```

### `get_credit_utilization()`
Per-card and aggregate credit utilization.
```
→ { aggregate_pct, total_balance, total_limit, cards: [{ name, balance, limit, utilization_pct }] }
```

### `sync()`
Triggers a SimpleFIN sync (delegates to ingestion layer).
```
→ { accounts_updated, new_transactions, duration_ms, synced_at }
```

## CLI Commands

```
finance accounts                          # table of accounts + balances
finance transactions [--start] [--end] [--account] [--category] [--limit]
finance net-worth [--as-of]
finance spending [--start] [--end] [--group-by]
finance utilization
finance sync
```

## Analysis Layer

```
finance/analysis/
├── __init__.py
├── accounts.py     # get_accounts(), get_account_by_id()
├── spending.py     # get_spending_summary(), get_transactions()
└── net_worth.py    # get_net_worth(), get_balance_history()
```

Functions take a sqlite3 `Connection` as their first argument (no global state). Returns are plain dicts or dataclasses.

## Open Questions

- Credit limit data: SimpleFIN may not provide credit limits for all cards. `get_credit_utilization()` may need to fall back to manually-configured limits (stored in a config table or `.env`). Worth adding a `credit_limits` config mechanism.
- `sync()` as an MCP tool: useful for "Claude, sync my accounts" but adds write capability to the MCP server. Fine for personal use.
