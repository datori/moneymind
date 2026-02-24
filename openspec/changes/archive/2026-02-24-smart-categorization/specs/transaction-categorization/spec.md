## MODIFIED Requirements

### Requirement: Automatic categorization after sync and import
The system SHALL automatically categorize uncategorized transactions after `finance sync` and `finance import` complete. After categorization completes, the system SHALL also call `enrich_transactions(conn)` if `ANTHROPIC_API_KEY` is set.

#### Scenario: New transactions categorized post-sync
- **WHEN** `finance sync` runs and inserts new transactions
- **THEN** `categorize_uncategorized(conn)` is called before the sync command exits
- **AND** newly inserted transactions have their `category` and `categorized_at` populated

#### Scenario: Enrichment runs after post-sync categorization
- **WHEN** `finance sync` completes and `ANTHROPIC_API_KEY` is set
- **THEN** `enrich_transactions(conn)` is called after `categorize_uncategorized(conn)` completes

#### Scenario: Categorization failure does not fail sync
- **WHEN** the Claude API returns an error during categorization
- **THEN** sync still reports success
- **AND** affected transactions remain with `category=NULL` and `categorized_at=NULL`

#### Scenario: Enrichment failure does not fail sync
- **WHEN** `enrich_transactions(conn)` raises an exception
- **THEN** sync still reports success
- **AND** the enrichment error is logged as a warning but not shown to the user as a fatal error

#### Scenario: Enrichment skipped without API key
- **WHEN** `ANTHROPIC_API_KEY` is not set
- **THEN** `enrich_transactions` is not called during sync or categorize
