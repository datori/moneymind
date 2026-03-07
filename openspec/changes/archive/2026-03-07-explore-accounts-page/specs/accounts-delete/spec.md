## UPDATED Requirements

### Requirement: Flash message rendered in accounts template

The `accounts.html` template SHALL render the `msg` template variable when it is
non-empty. The message SHALL appear as a green (emerald) alert banner immediately
below the page heading and above the summary bar.

This fulfills the existing `POST /accounts/{id}/delete` redirect behavior which
already sets `?msg=...` in the redirect URL — the message was previously passed to
the template context but never rendered.

#### Scenario: Flash message displays after deletion
- **WHEN** the browser follows the redirect to `/accounts?msg=...` after a successful
  account deletion
- **THEN** an emerald alert banner appears at the top of the page content showing
  the deletion confirmation message (e.g., "Deleted 'My Checking' (47 transactions,
  12 balances removed).")

#### Scenario: No banner when msg is absent
- **WHEN** `/accounts` is loaded without a `msg` query parameter
- **THEN** no alert banner is rendered
