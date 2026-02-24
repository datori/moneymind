## ADDED Requirements

### Requirement: CLI provides all query commands
The `finance` CLI SHALL expose subcommands matching every MCP tool: `accounts`, `transactions`, `net-worth`, `spending`, `utilization`.

#### Scenario: accounts command
- **WHEN** `finance accounts` is run
- **THEN** a formatted table of accounts with names, types, and current balances is printed

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

### Requirement: CLI --json flag for machine-readable output
All query commands SHALL support a `--json` flag that outputs valid JSON instead of a formatted table.

#### Scenario: JSON output
- **WHEN** any query command is run with `--json`
- **THEN** stdout contains valid JSON that can be piped to `jq`

---

### Requirement: CLI credit-limit management
The `finance` CLI SHALL provide commands to view and set credit limits.

#### Scenario: Set credit limit
- **WHEN** `finance set-limit <account-id> <amount>` is run
- **THEN** the `credit_limits` table is updated for that account

#### Scenario: List credit limits
- **WHEN** `finance limits` is run
- **THEN** all configured credit limits are printed alongside account names
