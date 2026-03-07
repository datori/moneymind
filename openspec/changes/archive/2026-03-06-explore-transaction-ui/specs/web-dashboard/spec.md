# Delta spec: web-dashboard — transaction table column count

## Changed scenario

**Scenario: Transaction table on mobile** (under "Wide tables scroll horizontally on narrow viewports")

The Pending column has been removed from the transaction table and replaced with
an inline yellow dot indicator in the Date cell. The table now has 6 columns
(Date, Description, Merchant, Category, Account, Amount) rather than 7.

### Updated scenario text

#### Scenario: Transaction table on mobile
- **WHEN** the `/transactions` page is viewed on a viewport narrower than 768px
- **THEN** the full 6-column table (Date, Description, Merchant, Category, Account, Amount) is accessible via horizontal scroll; no columns are hidden

### Also: pending status display

Pending transactions are no longer shown as a text badge in a dedicated Pending
column. Instead, a small yellow dot (`●`, implemented as a Tailwind circle span
with `title="Pending"`) appears inline after the date value in the Date cell.
This applies only when `txn.pending` is truthy.
