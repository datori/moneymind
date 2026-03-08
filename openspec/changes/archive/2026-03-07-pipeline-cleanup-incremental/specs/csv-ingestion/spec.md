## MODIFIED Requirements

### Requirement: CSV import does not trigger LLM calls
The `import_csv()` function SHALL import transactions from a CSV file into the database without triggering any LLM categorization or enrichment calls. Auto-categorization is removed from the import path.

#### Scenario: CSV import with ANTHROPIC_API_KEY set
- **WHEN** `finance import` is run with `ANTHROPIC_API_KEY` set in environment
- **THEN** transactions are imported from the CSV file
- **AND** no LLM API calls are made
- **AND** imported transactions have `category = NULL` and `categorized_at = NULL`

#### Scenario: CSV import without ANTHROPIC_API_KEY
- **WHEN** `finance import` is run without `ANTHROPIC_API_KEY` set
- **THEN** transactions are imported normally (same behavior as with key set)
