# Finance

A local, self-hosted personal finance dashboard with AI-powered transaction categorization. Syncs accounts and transactions via [SimpleFIN Bridge](https://www.simplefin.org/), stores everything in a local SQLite database, and serves a web dashboard for spending analysis, net worth tracking, and recurring charge detection.

![Finance Dashboard](screenshots/recurring-demo.png)

## Features

- **Daily sync** — pulls balances and transactions from all linked accounts via SimpleFIN
- **CSV import** — import historical data from Chase, Citi, Amex, Discover, Apple Card, and more
- **AI categorization** — LLM pipeline (Claude) normalizes merchants, assigns categories, detects recurring charges
- **Web dashboard** — spending breakdowns, net worth history, account overview, transaction search
- **Recurring detection** — identifies subscriptions and regular charges with next-due estimates
- **MCP server** — expose financial data to Claude sessions for natural-language queries
- **100% local** — no cloud sync, no telemetry; all data stays on your machine

## Screenshots

| Spending | Transactions |
|----------|--------------|
| ![Spending breakdown](screenshots/spending-demo.png) | ![Transaction browser](screenshots/transactions-demo.png) |

| Recurring charges | Accounts |
|-------------------|----------|
| ![Recurring charges](screenshots/recurring-demo.png) | ![Account overview](screenshots/accounts-demo.png) |

## Prerequisites

- Python 3.11+
- A [SimpleFIN Bridge](https://beta-bridge.simplefin.org/) account (~$15/year) — provides read-only access to your bank/card accounts
- An [Anthropic API key](https://console.anthropic.com/) — optional, required only for AI categorization

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/finance.git
cd finance
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure environment

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required: SimpleFIN access token
# Get this by claiming your SimpleFIN Setup Token at https://beta-bridge.simplefin.org/
SIMPLEFIN_TOKEN=https://user:token@beta-bridge.simplefin.org/simplefin

# Optional: Anthropic API key for AI categorization
# Without this, transactions sync but are not auto-categorized
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run initial sync

```bash
finance sync          # pull accounts + transactions from SimpleFIN
finance categorize    # run AI categorization (requires ANTHROPIC_API_KEY)
```

### 4. Start the web dashboard

```bash
finance web
# Open http://localhost:8000
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SIMPLEFIN_TOKEN` | Yes | SimpleFIN access URL (includes credentials) |
| `ANTHROPIC_API_KEY` | No | Enables AI transaction categorization and enrichment |

## CSV Import

For accounts SimpleFIN can't reach (some brokerages, fintech apps), export a CSV from your institution's website and import it:

```bash
finance import --file ~/Downloads/chase-2025.csv --account "Chase Prime Visa"
```

Supported formats are auto-detected from column headers. Currently supports: Chase, Citi, Amex, Discover, Apple Card, Capital One.

## CLI Reference

```
finance sync          Sync accounts and transactions from SimpleFIN
finance categorize    Run AI categorization on uncategorized transactions
finance import        Import transactions from a CSV file
finance web           Start the web dashboard (default: port 8000)
finance server        Start the MCP server (for Claude integration)
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed overview of the system design, data schema, and component structure.

## Privacy

- All transaction data is stored in a local SQLite file (`data/finance.db`) — never uploaded anywhere
- `data/` and `import/` directories are gitignored
- SimpleFIN token and API keys are stored in `.env` (gitignored)
- When AI categorization is enabled, transaction descriptions are sent to Anthropic's API; no data is retained beyond the API call per [Anthropic's policy](https://www.anthropic.com/legal/privacy)

## License

MIT — see [LICENSE](LICENSE).
