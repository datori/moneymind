# github-publish-readiness Specification

## Purpose
TBD - created by archiving change github-publish-prep. Update Purpose after archive.
## Requirements
### Requirement: git-history-clean
The git history SHALL contain no personal financial data, including account numbers (even partial), account balances, net worth figures, employer names, or loan balances. This is verified by scanning `git log --all -p` output for known sensitive patterns.

#### Scenario: PROPOSAL.md absent from all commits
- **WHEN** a user clones the repository and runs `git log --all --name-only --format=""`
- **THEN** `PROPOSAL.md` does not appear in any commit's file list

#### Scenario: Personal financial figures absent from all commits
- **WHEN** a user clones the repository and scans the full commit diff history for known sensitive patterns
- **THEN** no matches are found in any commit diff

### Requirement: gitignore-covers-sensitive-paths
The `.gitignore` file SHALL include entries that prevent accidental commits of known sensitive file categories:
- `import/` (bank CSV exports)
- `bugs/` (personal financial bug reports)
- `.ralph/` (exploration state)
- `.claude/worktrees/` (Claude worktree state)
- `.claude/*.local.md` (local Claude state files)
- `*.swp` (vim swap files)

#### Scenario: import/ cannot be staged
- **WHEN** a user runs `git add import/` in the repository root
- **THEN** git reports the path as ignored and no files are staged

#### Scenario: bugs/ cannot be staged
- **WHEN** a user runs `git add bugs/` in the repository root
- **THEN** git reports the path as ignored and no files are staged

### Requirement: readme-present
The repository root SHALL contain a `README.md` with at minimum:
- Project description (what it is, what problem it solves)
- Prerequisites (Python version, SimpleFIN account, Anthropic API key optional)
- Setup instructions (clone, install, configure `.env`, run)
- Required environment variables (`SIMPLEFIN_TOKEN`, `ANTHROPIC_API_KEY` optional)
- Screenshot or brief feature list

#### Scenario: README exists and documents setup
- **WHEN** a new user visits the GitHub repository page
- **THEN** they can read the README and follow its steps to get the app running without prior context

### Requirement: license-present
The repository root SHALL contain a `LICENSE` file with the MIT license text.

#### Scenario: LICENSE file present
- **WHEN** a user views the repository on GitHub
- **THEN** GitHub displays the license as "MIT License" in the repository sidebar

### Requirement: legitimate-files-tracked
All application files that are part of the project's intended behavior SHALL be committed to git:
- `finance/web/templates/reports.html`
- `.claude/commands/finance-report.md`
- The `openspec/changes/merchant-category-corrections/` change artifacts

#### Scenario: reports template is tracked
- **WHEN** a user clones the repo fresh and runs the web server
- **THEN** the reports route renders without a missing template error

### Requirement: architecture-doc-replaces-proposal
A `ARCHITECTURE.md` file SHALL be present in the repository root containing the project's architectural overview (component descriptions, data flow, design decisions) but SHALL NOT contain any personal financial data (account numbers, balances, employer names, net worth figures).

#### Scenario: ARCHITECTURE.md contains no PII
- **WHEN** the ARCHITECTURE.md is scanned for financial identifiers
- **THEN** no account numbers, balance amounts, employer names, or net worth figures are found

