## MODIFIED Requirements

### Requirement: Supported institution normalizers
The system SHALL support the following institutions with correct column mapping and amount sign normalization.

| Institution | Key | Amount sign rule |
|-------------|-----|-----------------|
| Chase | `chase` | Amount column; negative = debit |
| Discover (credit) | `discover` | Amount column; negative = debit |
| Discover (debit) | `discover-debit` | Amount column; negative = debit |
| Citi | `citi` | Separate Debit/Credit cols; debit = negative |
| Amex | `amex` | Amount column; negative = debit |
| Robinhood | `robinhood` | Amount column; buys = negative |
| M1 | `m1` | Amount column; buys = negative |
| Apple Card | `apple` | `Amount (USD)` column; positive = charge → negate to debit; skip Type=="Payments" rows |

#### Scenario: Citi Debit/Credit column merge
- **WHEN** a Citi CSV row has a value in the `Debit` column
- **THEN** the stored amount is `-(abs(debit_value))`

#### Scenario: Citi credit row
- **WHEN** a Citi CSV row has a value in the `Credit` column
- **THEN** the stored amount is `+abs(credit_value)`

#### Scenario: Apple Card purchase row
- **WHEN** an Apple Card CSV row has `Type` other than `"Payments"` and `Amount (USD)` of `"45.99"`
- **THEN** the stored amount is `-45.99` and `merchant_name` is populated from the `Merchant` column

#### Scenario: Apple Card payment row skipped
- **WHEN** an Apple Card CSV row has `Type == "Payments"`
- **THEN** the row is skipped and not inserted into the database
