## Context

The MCP server and CLI provide programmatic access to financial data. A local web dashboard provides at-a-glance visualization without requiring a Claude session. It runs on localhost, reads from the same SQLite database via the same analysis layer, and is served by a lightweight Python web server.

This change builds on all previous changes — it consumes data from `simplefin-sync` and `csv-import`, analysis functions from `mcp-server`, and categories from `ai-categorize`.

## Goals / Non-Goals

**Goals:**
- Local web server on `localhost:8080` (default)
- Dashboard home: net worth summary, monthly spending by category, credit utilization
- Accounts list with current balances
- Transaction browser with filtering
- Net worth history chart
- Spending breakdown chart
- "Sync now" button
- New entry point: `finance-dashboard`

**Non-Goals:**
- Authentication (LAN-only, single user)
- Mobile-responsive design
- Public deployment
- Real-time updates (page refresh is sufficient)
- Full feature parity with Monarch/Copilot

## Decisions

### D1: FastAPI + Jinja2 (not Flask)

**Decision:** Use FastAPI with Jinja2 templates for server-side rendering.

**Rationale:** FastAPI has cleaner async support (useful if we want background sync), automatic OpenAPI docs for free, and is the more actively maintained choice going into 2026. Jinja2 is the same template engine used by Flask, so template syntax is identical. Both are SSR — no JS framework needed.

**Alternatives considered:** Flask (simpler but less future-proof), Starlette directly (too low-level).

---

### D2: Chart.js via CDN, Tailwind CSS via CDN

**Decision:** No npm, no bundler. Both Chart.js and Tailwind CSS are loaded via `<script>`/`<link>` from CDN.

**Rationale:** This is a local personal tool. Build tooling adds maintenance burden for zero benefit. CDN scripts load from the internet on page open — acceptable for a LAN-only tool with internet access.

**Alternatives considered:** Plotly (heavier, more features than needed), Alpine.js (not needed for static pages with form submissions).

---

### D3: Analysis layer reused directly (no REST API layer)

**Decision:** FastAPI route handlers call `finance.analysis.*` functions directly, passing a DB connection opened per-request.

**Rationale:** Adding an intermediate REST API layer would add indirection without benefit. The web server is in the same process as the analysis layer — direct calls are simpler and faster.

---

### D4: "Sync now" button posts to `/sync`, redirects back

**Decision:** A `POST /sync` endpoint triggers `sync_all()` and redirects back to the referring page. No AJAX.

**Rationale:** Simple HTML form POST → redirect is sufficient. No JavaScript required. The sync takes <5 seconds which is fine for a synchronous HTTP request.

---

### D5: Separate `finance-dashboard` entry point

**Decision:** Dashboard runs as a separate process from the MCP server, invoked via `uv run finance-dashboard [--port 8080] [--host 127.0.0.1]`.

**Rationale:** Keeps MCP server and web server independent. User can run one, both, or neither. Dashboard doesn't need to be running for Claude to query data.

---

### D6: DB connection per request via FastAPI dependency

**Decision:** Use a FastAPI dependency that opens and closes a SQLite connection per HTTP request.

**Rationale:** Avoids connection state leaking between requests. SQLite connection open/close is fast (no network round-trip). Thread-safe by default since each request gets its own connection.

## Risks / Trade-offs

- **CDN dependency** → If CDN is unreachable (offline), charts won't render. Acceptable for a personal tool; data is still present in table form.
- **No auth** → Anyone on the LAN can access the dashboard. Acceptable given it's personal homelab. If exposed externally, would need auth added.
- **Sync blocks request** → `POST /sync` is synchronous and blocks the HTTP response until sync completes. For <5 seconds this is fine. If sync takes longer (many accounts, slow connection), this should be made async.

## Open Questions

None — all decisions resolved.
