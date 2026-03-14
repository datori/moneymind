## Context

The dashboard is a FastAPI app backed by a single SQLite file (`data/finance.db`). All read routes use a `get_db()` FastAPI dependency that opens and yields the DB connection. Analysis functions are pure: they accept a connection and return data. Mutation routes hit the same DB. Two routes make external network calls: `/sync` (SimpleFIN) and `/pipeline/run/stream` (Anthropic API).

## Goals / Non-Goals

**Goals:**
- Any route appended with `?demo=1` renders with synthetic data from `data/demo.db`
- Real database (`data/finance.db`) is never opened, read, or written in demo mode
- Visible banner appears whenever demo mode is active
- `/sync` and `/pipeline/run/stream` return HTTP 400 in demo mode (external calls blocked)
- All other mutations operate normally against `demo.db`
- A seed script generates `demo.db` deterministically

**Non-Goals:**
- Demo mode does not persist across navigation (no cookie, no session)
- No UI button to toggle demo mode
- `demo.db` mutations are not preserved (ephemeral; user re-runs seed to reset)

## Decisions

### Decision 1: Where to detect demo mode

**Chosen:** Inside the existing `get_db()` dependency, add `request: Request` as a parameter. FastAPI injects it automatically. Check `request.query_params.get("demo") == "1"` and return a connection to `demo.db` instead of `finance.db`.

**Alternatives considered:**
- Middleware: Would work but adds a layer just to swap a dependency. The dependency is already the right abstraction boundary.
- Per-route query param: Too verbose — 10+ routes.

**Result:** `get_db` becomes the single enforcement point. Zero changes to analysis functions.

### Decision 2: Demo banner injection

**Chosen:** Add `demo_mode: bool` to every `templates.TemplateResponse(...)` context dict, derived from `request.query_params.get("demo") == "1"`. Banner rendered in `base.html`.

**Alternatives considered:**
- Jinja2 global variable set from middleware: Works but couples template rendering to middleware ordering.
- Template reads `request.query_params` directly: Possible in Jinja2 but `request` is already available — a cleaner approach is explicit `demo_mode` context.

### Decision 3: Blocking dangerous mutations

**Chosen:** At the top of `/sync` and `/pipeline/run/stream` handlers, check `request.query_params.get("demo") == "1"` and raise `HTTPException(400, "Not available in demo mode")`.

No middleware needed — there are only two routes to guard.

### Decision 4: Demo database — file vs in-memory

**Chosen:** `data/demo.db` — a pre-seeded file committed to the repository.

**Alternatives considered:**
- In-memory SQLite (`:memory:`): Clean, but must be re-seeded on every request (slow) or held in a module-level singleton (complicates app lifecycle and concurrency).
- Generated on startup: Adds startup latency; `demo.db` becomes a side-effect of running the app.

**Result:** `finance/demo/seed.py` is a standalone script. Developers run it once to produce `data/demo.db`. File is committed. Reads are fast; mutations to `demo.db` are acceptable and non-dangerous.

### Decision 5: Demo data shape

Realistic synthetic data to make all pages look meaningful:
- 4 accounts: Chase Checking, HYSA Savings, Amex Gold (credit), Schwab Brokerage (investment)
- ~13 months of transactions (~30/month) across realistic categories
- Balance snapshots monthly (net worth chart shows upward trend ~$62k → $72k)
- 6 recurring merchants (Netflix, Spotify, gym, iCloud, AWS, internet)
- 3 transactions flagged `needs_review = 1`
- 1 completed pipeline run in `run_log`

## Risks / Trade-offs

- **demo.db drifts from schema**: If schema migrations are added and `demo.db` isn't regenerated, demo mode may fail or show stale structure. → Mitigation: seed script runs `init_db()` before inserting data, so it always matches the current schema.
- **demo.db mutations accumulate**: Users can delete accounts, approve reviews, etc. against `demo.db`. Over time it diverges from the seeded state. → Accepted trade-off; re-run seed script to reset. Not a safety issue.
- **`demo_mode` context omitted from a new route**: A future route that forgets to pass `demo_mode=True` to its template won't show the banner. → Low severity; doesn't break anything, just omits the visual indicator.
