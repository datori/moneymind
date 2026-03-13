## Why

The finance project is a fully functional personal finance dashboard but has never been prepared for public distribution — it contains personal financial data in git history, missing gitignore entries, no README, and no license. This change makes the repository safe and useful for public GitHub publishing.

## What Changes

- **CRITICAL**: Rewrite git history to remove `PROPOSAL.md` (contains personal financial data) using `git filter-repo`
- **CRITICAL**: Sanitize `openspec/changes/archive/2026-02-24-csv-import/proposal.md` git history (contains a net worth figure)
- Add missing `.gitignore` entries: `import/`, `bugs/`, `.ralph/`, `.claude/worktrees/`, `.claude/*.local.md`, `*.swp`
- Add `README.md` explaining the project, setup, and configuration
- Add `LICENSE` file (MIT recommended for a personal tool)
- Commit currently-untracked legitimate files: `finance/web/templates/reports.html`, `.claude/commands/finance-report.md`, `openspec/changes/merchant-category-corrections/`
- Delete or rename `PROPOSAL.md` — replace with `ARCHITECTURE.md` (sanitized, no personal data)

## Capabilities

### New Capabilities
- `github-publish-readiness`: Repository is safe to publish publicly — no PII, no secrets in history, proper ignore rules, documented setup

### Modified Capabilities
_(none — no existing spec-level behavior changes)_

## Impact

- Git history will be rewritten — all commit SHAs change, any existing clones/forks must re-clone
- No application code changes
- `.gitignore` additions prevent accidental future commits of sensitive data
- `README.md` and `LICENSE` establish project identity for public consumers
