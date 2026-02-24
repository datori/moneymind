## ADDED Requirements

### Requirement: `finance accounts delete` command
The system SHALL provide a `finance accounts delete <account-id>` CLI command that permanently deletes an account and all rows dependent on it.

Rows deleted (in order, within a single transaction):
1. `credit_limits` WHERE `account_id = <id>`
2. `sync_state` WHERE `account_id = <id>`
3. `transactions` WHERE `account_id = <id>`
4. `balances` WHERE `account_id = <id>`
5. `accounts` WHERE `id = <id>`

The command SHALL print a confirmation prompt before deleting unless `--confirm` is passed.

#### Scenario: Delete with interactive confirmation accepted
- **WHEN** `finance accounts delete <account-id>` is run and the user types `y` at the prompt
- **THEN** all dependent rows and the account row are deleted, and a success message is printed showing the account name and counts of deleted rows per table

#### Scenario: Delete with interactive confirmation rejected
- **WHEN** `finance accounts delete <account-id>` is run and the user types `n` at the prompt
- **THEN** no rows are deleted and the command exits 0 with the message `"Aborted."`

#### Scenario: Delete with --confirm flag skips prompt
- **WHEN** `finance accounts delete <account-id> --confirm` is run
- **THEN** deletion proceeds immediately without any prompt

#### Scenario: Non-existent account ID
- **WHEN** `finance accounts delete <nonexistent-id>` is run
- **THEN** an error message is printed (`"Error: account '<id>' not found."`) and the command exits non-zero; no rows are deleted

#### Scenario: Success message includes deleted row counts
- **WHEN** an account with N transactions, M balances, and a credit limit is deleted
- **THEN** stdout reports the count of deleted rows for each affected table (transactions, balances, credit_limits, sync_state)

---

### Requirement: `finance accounts` group preserves existing list behavior
The conversion of `finance accounts` from a plain command to a Click group SHALL preserve backward compatibility: invoking `finance accounts` without a subcommand SHALL still list all accounts.

#### Scenario: `finance accounts` without subcommand lists accounts
- **WHEN** `finance accounts` is run with no subcommand
- **THEN** a formatted table of accounts is printed, identical to the previous behavior

#### Scenario: `finance accounts list` is an explicit alias
- **WHEN** `finance accounts list` is run
- **THEN** the same account listing is printed
