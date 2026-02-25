## MODIFIED Requirements

### Requirement: get_data_overview() is unchanged
`get_data_overview(conn)` in `finance/analysis/overview.py` SHALL continue to return the same dict structure and values as specified in its original ADDED spec. No signature changes, no return-shape changes, no behavioral changes.

#### Scenario: Function signature is unchanged
- **WHEN** `get_data_overview(conn)` is called
- **THEN** it accepts exactly one positional argument (an open `sqlite3.Connection`) and returns a dict with keys `global` and `per_account`, identical to the original spec

#### Scenario: All original scenarios still pass
- **WHEN** any scenario from the original `data-overview` ADDED spec is exercised
- **THEN** the result is identical to the original specification

---

### Requirement: /accounts route calls get_data_overview()
`GET /accounts` in `finance/web/app.py` SHALL call `get_data_overview(conn)` and use its result to populate the global summary bar and the per-account txn/date-range/last-synced columns in the unified accounts table.

#### Scenario: /accounts route uses overview data
- **WHEN** a browser navigates to `/accounts`
- **THEN** the global summary bar values (total accounts, total transactions, date range) match the values returned by `get_data_overview(conn)["global"]`

#### Scenario: Per-account txn columns sourced from overview
- **WHEN** a browser navigates to `/accounts`
- **THEN** each account row's Txn Count, Date Range, and Last Synced values match the corresponding entry in `get_data_overview(conn)["per_account"]`

---

### Requirement: /data route is deprecated (redirect only)
The `/data` route SHALL be converted to a `GET /data` that returns HTTP 301 to `/accounts`. The `data.html` template is no longer rendered.

#### Scenario: /data route redirects
- **WHEN** a browser navigates to `/data`
- **THEN** the server responds with HTTP 301 and `Location: /accounts`; the `data.html` template is not rendered

#### Scenario: data.html template not actively used
- **WHEN** the application is running
- **THEN** no route renders `data.html`; the file may remain on disk but is inert
