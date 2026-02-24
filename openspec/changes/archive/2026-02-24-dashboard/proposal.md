# Proposal: dashboard

## Problem / Motivation

The MCP server and CLI give programmatic access to financial data, but some things are better visualized than queried. A local web dashboard provides at-a-glance views of net worth trends, spending by category, and credit utilization without needing to ask Claude a question.

## Goals

- Local web server (runs on localhost, no auth needed — it's LAN-only)
- Net worth over time chart
- Spending by category (current month + trailing)
- Credit utilization gauges
- Account list with current balances
- Data served from the same SQLite database — no duplication

## Non-goals

- Authentication / multi-user
- Mobile-responsive design (desktop only is fine)
- Real-time updates / websockets
- Public deployment
- Replicate the full feature set of commercial apps (Monarch, Copilot)

## Approach

### Stack

- **FastAPI** + **Jinja2** templates — simple, Python-native, no build step
- **Chart.js** via CDN — no npm, no bundler, just `<script>` tag
- Served via `uv run finance-dashboard` (new entry point in `pyproject.toml`)
- Data: read directly from SQLite via the existing analysis layer

### Pages / Views

```
/                   → dashboard home (net worth + spending summary + utilization)
/accounts           → account list with balances
/transactions       → filterable transaction table
/net-worth          → net worth history chart (all time)
/spending           → spending breakdown (by category, by month)
```

### Serving

```
finance-dashboard [--port 8080] [--host 127.0.0.1]
```

Can be run manually or as a systemd service on the homelab box.

## Open Questions

- FastAPI vs Flask? Both are fine. FastAPI has slightly nicer async support and auto-docs. Flask is simpler for pure template rendering. Either works — FastAPI is the better long-term choice.
- Should the dashboard be read-only, or include a "sync now" button? A sync button would be convenient. Since this is single-user local, it's fine to add write capability.
- Decide on chart library: Chart.js (simple, CDN) vs Plotly (more powerful, also CDN-available). Chart.js is sufficient for these use cases.
