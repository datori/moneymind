# Proposal: simplefin-sync

## Problem / Motivation

The primary data source for this system is SimpleFIN Bridge — a $15/year service that aggregates bank/card data without Plaid's approval friction. We need a client that can authenticate with SimpleFIN, pull account/balance/transaction data, and upsert it into the local SQLite database.

## Goals

- Implement `finance/ingestion/simplefin.py`: a SimpleFIN API client
- Handle the SimpleFIN auth flow: Setup Token → Access Token (one-time claim)
- Fetch `/accounts` endpoint: accounts + current balances + recent transactions
- Upsert accounts, balance snapshots, and transactions into SQLite
- Track last sync time in `sync_state` table
- Expose a `finance sync` CLI command
- Gracefully handle accounts that return no transactions (balance-only accounts)

## Non-goals

- CSV import — that's `csv-import`
- Determining which accounts are supported by SimpleFIN (manual verification, done by user)
- Retry logic or scheduling — the `sync` command is called manually or via cron
- Transaction categorization — that's `ai-categorize`

## Approach

### SimpleFIN Auth Flow

```
1. User gets a Setup Token from simplefin.org (one-time URL)
2. POST to Setup Token URL → returns Access URL (stored in .env)
3. All subsequent requests: GET <ACCESS_URL>/accounts
   with basic auth (username="", password=access_token)
```

The Setup Token claim is a one-time operation. After that, only the Access URL is needed.

### `/accounts` Response Shape

```json
{
  "accounts": [
    {
      "org": { "domain": "chase.com", "name": "Chase", "sfin-url": "..." },
      "id": "chase:abc123",
      "name": "Chase Sapphire",
      "currency": "USD",
      "balance": "-1248.73",
      "available-balance": null,
      "balance-date": 1708800000,
      "transactions": [
        {
          "id": "txn_abc",
          "posted": 1708700000,
          "amount": "-45.00",
          "description": "WHOLE FOODS"
        }
      ]
    }
  ]
}
```

### Sync Logic

1. Fetch `/accounts` (with `start-date` = last sync timestamp for that account, or 90 days ago if first sync)
2. For each account:
   - Upsert `institutions` row
   - Upsert `accounts` row
   - Insert `balances` snapshot (always append)
   - Upsert each transaction (INSERT OR IGNORE on `id` for dedup)
   - Update `sync_state.last_synced_at`
3. Print summary: accounts updated, new transactions found

### CLI

```
finance sync              # sync all accounts
finance sync --account <id>  # sync specific account
```

## Open Questions

- Should we store the Access URL in `.env` or in a local config file? `.env` is simplest.
- Transaction `start-date` window: use last sync time, or always fetch last 90 days? Last sync time is correct — avoids re-fetching thousands of old transactions on every run. But 90 days on first sync covers recent history.
- SimpleFIN returns `balance-date` as unix seconds. Balances table uses unix ms. Convert on ingest.
