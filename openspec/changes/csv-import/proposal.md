# Proposal: csv-import

## Problem / Motivation

SimpleFIN coverage for brokerage and fintech accounts (M1, Robinhood, Empower, Guideline) is uncertain. These accounts hold the majority of net worth (a significant majority). CSV export is the universal fallback — every institution supports it. We need a normalizer pipeline that can ingest CSVs from multiple institutions with different column formats.

## Goals

- Implement `finance/ingestion/csv_import.py` with per-institution normalizers
- Support initial target institutions: Chase, Discover, Citi, Amex (credit cards / bank)
- Support investment/brokerage CSVs: Robinhood, M1 (transaction format TBD)
- Deduplicate against existing transactions using the same hash-based ID scheme
- Expose a `finance import <file> --institution <name>` CLI command
- Handle historical backfill (importing months/years of past data)

## Non-goals

- Automatic institution detection from file contents (explicitly specify `--institution`)
- OFX or QFX format support
- Handling every institution's edge cases perfectly on first pass — add normalizers incrementally

## Approach

### Normalizer Design

Each institution has a normalizer function:
```python
def normalize_chase(row: dict) -> Transaction | None:
    ...

NORMALIZERS = {
    "chase": normalize_chase,
    "discover": normalize_discover,
    "citi": normalize_citi,
    "amex": normalize_amex,
    "robinhood": normalize_robinhood,
    "m1": normalize_m1,
}
```

Each normalizer maps institution-specific CSV columns to the canonical transaction schema. Returns `None` for rows that should be skipped (headers, pending, duplicates already filtered by caller).

### Transaction ID for CSV Rows

Since CSV transactions have no stable ID, we hash a combination of:
```
sha256(account_id + date + amount + description)[:16]
```
This is deterministic — re-importing the same file won't create duplicates.

### Account Matching

CSV rows need to be associated with an `account_id`. For CSV imports, the user specifies the account:
```
finance import chase_jan2025.csv --institution chase --account <account_id>
```

On first import for an account not yet in the DB, a new account record is created automatically.

### CLI

```
finance import <file> --institution <name> --account <id>
finance import <file> --institution <name>  # creates account if needed
finance institutions                         # list supported institution names
```

### CSV Column Maps (known formats)

| Institution | Date col | Amount col | Description col |
|-------------|----------|------------|-----------------|
| Chase | Transaction Date | Amount | Description |
| Discover | Trans. Date | Amount | Description |
| Citi | Date | Debit / Credit | Description |
| Amex | Date | Amount | Description |
| Robinhood | Activity Date | Amount | Description |

## Open Questions

- Citi uses separate Debit/Credit columns — need to combine into signed amount
- Amex amounts may already be signed or may require sign inversion depending on export type
- Investment CSVs from Robinhood/M1 are more complex (buy/sell/dividend rows) — treat as transactions or handle separately? Treating them as transactions (with buy = debit, dividend = credit) keeps the schema simple for now.
- Should `finance import` print a summary of what was imported vs skipped as duplicates? Yes, useful for verifying backfills.
