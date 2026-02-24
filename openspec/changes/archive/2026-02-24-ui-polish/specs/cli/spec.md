## MODIFIED Requirements

### Requirement: CLI provides all query commands
The `finance` CLI SHALL expose subcommands matching every MCP tool: `accounts`, `transactions`, `net-worth`, `spending`, `utilization`. The `accounts` command SHALL be implemented as a Click group with an implicit `list` behavior when no subcommand is given.

#### Scenario: accounts command (no subcommand)
- **WHEN** `finance accounts` is run with no subcommand
- **THEN** a formatted table of accounts with names, types, and current balances is printed

#### Scenario: accounts list subcommand
- **WHEN** `finance accounts list` is run
- **THEN** the same formatted table of accounts is printed

#### Scenario: transactions command with filters
- **WHEN** `finance transactions --start 2025-01-01 --end 2025-01-31 --limit 20` is run
- **THEN** up to 20 transactions in that date range are printed

#### Scenario: net-worth command
- **WHEN** `finance net-worth` is run
- **THEN** total net worth and breakdown by account type is printed

#### Scenario: spending command
- **WHEN** `finance spending --start 2025-01-01 --end 2025-01-31` is run
- **THEN** spending by category is printed, sorted by total descending

#### Scenario: utilization command
- **WHEN** `finance utilization` is run
- **THEN** per-card utilization and aggregate percentage is printed

---

### Requirement: CLI credit-limit management
The `finance` CLI SHALL provide commands to view and set credit limits.

#### Scenario: Set credit limit
- **WHEN** `finance set-limit <account-id> <amount>` is run
- **THEN** the `credit_limits` table is updated for that account

#### Scenario: List credit limits
- **WHEN** `finance limits` is run
- **THEN** all configured credit limits are printed alongside account names

---

### Requirement: CLI --json flag for machine-readable output
All query commands SHALL support a `--json` flag that outputs valid JSON instead of a formatted table.

#### Scenario: JSON output
- **WHEN** any query command is run with `--json`
- **THEN** stdout contains valid JSON that can be piped to `jq`

---

### Requirement: CLI accounts delete command
The `finance` CLI SHALL provide a `finance accounts delete <account-id>` command that permanently removes an account and all its dependent data (see `accounts-delete` spec).

#### Scenario: Delete account with confirmation
- **WHEN** `finance accounts delete <account-id>` is run and the user confirms
- **THEN** the account and all dependent rows are deleted and a summary is printed

#### Scenario: Delete account with --confirm flag
- **WHEN** `finance accounts delete <account-id> --confirm` is run
- **THEN** deletion proceeds without an interactive prompt
