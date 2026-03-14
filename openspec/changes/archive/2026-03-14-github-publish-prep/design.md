## Context

The repository has been developed privately as a personal finance tool. It contains 92 commits of history. The primary blocker for public publishing is `PROPOSAL.md` — committed since the first commit — which contains a complete financial snapshot with personally identifiable financial data (account numbers, balances, employer name, and loan details). A secondary issue is `openspec/changes/archive/2026-02-24-csv-import/proposal.md` which references net worth figures. Both files are in git history and cannot be removed by simply deleting them.

Application code is clean: all credentials (ANTHROPIC_API_KEY, SimpleFIN token) are read from env vars / `.env` (which is gitignored). Transaction data (`data/`, `import/`) is gitignored or untracked.

## Goals / Non-Goals

**Goals:**
- Remove all personal financial data (PII) from git history
- Close `.gitignore` gaps so future `git add .` cannot accidentally commit sensitive files
- Make the repo approachable for public consumers (README, LICENSE)
- Commit currently-untracked legitimate application files

**Non-Goals:**
- Changing any application behavior
- Cleaning up in-code comments or documentation beyond README
- Publishing to PyPI
- Removing openspec/ history (it's valuable development transparency — just sanitize the personal data references)

## Decisions

### D1: Use `git filter-repo` to rewrite history

**Decision**: Use `git filter-repo --path PROPOSAL.md --invert-paths` to excise `PROPOSAL.md` entirely from all commits. For the csv-import proposal, use `--path-rename` or a blob callback to replace the net worth line.

**Rationale**: Simply deleting files leaves them in git history. `git filter-repo` is the modern, recommended replacement for `git filter-branch`. It rewrites commit SHAs across all branches. Since this is a solo project with no active forks, SHA rewriting is acceptable.

**Alternative rejected**: Starting a fresh repo (loses history). The 92-commit history includes useful exploration and architectural context in openspec — worth preserving.

### D2: Replace PROPOSAL.md with ARCHITECTURE.md

**Decision**: After removing `PROPOSAL.md` from history, create a new `ARCHITECTURE.md` containing only the non-personal content (system design, component descriptions, data flow) without the account inventory snapshot.

**Rationale**: The architectural content of PROPOSAL.md is useful for public readers. The account snapshot (the sensitive part) is ephemeral data that belongs in the running app, not in documentation.

### D3: MIT License

**Decision**: Add `LICENSE` with MIT license.

**Rationale**: MIT is the simplest, most permissive license appropriate for a personal tool shared publicly. No patent concerns, no copyleft requirements.

### D4: Sanitize openspec archive, don't remove it

**Decision**: Rewrite `openspec/changes/archive/2026-02-24-csv-import/proposal.md` in history to replace the specific net worth dollar figure with a non-identifying placeholder. Keep the rest of the openspec archive intact.

**Rationale**: The openspec archive is transparent development history — valuable for the public reader. Only the one specific financial figure is sensitive; the rest of the proposal is design discussion.

### D5: Add `.gitignore` entries before history rewrite

**Decision**: Add `import/`, `bugs/`, `.ralph/`, `.claude/worktrees/`, `.claude/*.local.md`, `*.swp` to `.gitignore` in a normal commit first, then perform history rewrite.

**Rationale**: Ensures the current untracked sensitive directories can never be accidentally committed going forward.

## Risks / Trade-offs

- **SHA rewrite impact**: All commit SHAs change after `git filter-repo`. Any branch pointers or tags need to be updated. Since this is solo, no coordination required — but any existing remote must be force-pushed.
- **`git filter-repo` availability**: Must be installed (`pip install git-filter-repo` or system package). Standard tool, low risk.
- **Incomplete scan**: There could be other personal data in history not yet found. A `git log -p --all | grep -E "<pattern>"` sweep is worth running as a final verification step before pushing public.
