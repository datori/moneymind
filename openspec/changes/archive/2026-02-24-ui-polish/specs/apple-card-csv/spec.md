## ADDED Requirements

### Requirement: Apple Card CSV normalizer
The system SHALL support Apple Card CSV exports via institution key `"apple"` registered in the `NORMALIZERS` dict in `finance/ingestion/csv_import.py`.

Apple Card CSV columns: `Transaction Date`, `Clearing Date`, `Description`, `Merchant`, `Category`, `Type`, `Amount (USD)`.

Column mapping rules:
- `date` ← `Transaction Date` (parsed via `_parse_date`)
- `merchant_name` ← `Merchant`
- `description` ← `Description`
- `amount` ← `-(float("Amount (USD)"))` (Apple: positive = charge; canonical: negative = debit)
- Rows where `Type == "Payments"` SHALL be skipped (return `None`)

#### Scenario: Normal purchase row is imported
- **WHEN** an Apple Card CSV row has `Type` of `"Purchase"` (or any value other than `"Payments"`)
- **THEN** a `Transaction` is returned with `amount` equal to the negated value of `Amount (USD)`, `merchant_name` from `Merchant`, and `description` from `Description`

#### Scenario: Payment row is skipped
- **WHEN** an Apple Card CSV row has `Type == "Payments"`
- **THEN** `normalize_apple` returns `None` and no transaction is inserted for that row

#### Scenario: Amount sign is negated
- **WHEN** an Apple Card CSV row contains `Amount (USD)` of `"45.99"`
- **THEN** the stored `amount` is `-45.99`

#### Scenario: Apple institution is listed by `finance institutions`
- **WHEN** `finance institutions` is run
- **THEN** `apple` appears in the output list

#### Scenario: Missing required columns skips row gracefully
- **WHEN** an Apple Card CSV row is missing `Transaction Date` or `Amount (USD)`
- **THEN** `normalize_apple` returns `None` and the row is counted as skipped
