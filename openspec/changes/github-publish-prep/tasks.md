## 1. Prepare workspace (do first, before history rewrite)

- [x] 1.1 Add `import/`, `bugs/`, `.ralph/`, `.claude/worktrees/`, `.claude/*.local.md`, `*.swp` to `.gitignore`
- [x] 1.2 Stage and commit the `.gitignore` update (normal commit, not squash)
- [x] 1.3 Commit untracked legitimate files: `finance/web/templates/reports.html`, `.claude/commands/finance-report.md`, `openspec/changes/merchant-category-corrections/` directory

## 2. Create replacement documentation

- [x] 2.1 Create `ARCHITECTURE.md` at repo root — copy non-personal content from `PROPOSAL.md` (component descriptions, data flow, design rationale); omit the entire "Account Inventory" section and any dollar amounts or account identifiers
- [x] 2.2 Add `LICENSE` file at repo root with MIT license text (copyright year: 2025, copyright holder: your preferred public name/handle)
- [x] 2.3 Create `README.md` at repo root with: project description, prerequisites, setup steps, env var table (`SIMPLEFIN_TOKEN`, `ANTHROPIC_API_KEY` optional), feature list

## 3. Rewrite git history (destructive — do after all normal commits are done)

- [x] 3.1 Verify `git filter-repo` is installed (`git filter-repo --version`); install if needed (`pip install git-filter-repo`)
- [x] 3.2 Create a backup of the current repo state: `cp -r . ../finance-backup-$(date +%Y%m%d)` (safety net)
- [x] 3.3 Run `git filter-repo --path PROPOSAL.md --invert-paths` to remove `PROPOSAL.md` from all commits across all branches
- [x] 3.4 Sanitize `openspec/changes/archive/2026-02-24-csv-import/proposal.md` in history: use `git filter-repo --blob-callback` (or manual sed callback) to replace `413` and `382` dollar-amount references with `XXX,XXX` in that specific file
- [x] 3.5 Run verification sweep against known sensitive patterns — confirm no matches
- [x] 3.6 Run verification: `git log --all --name-only --format="" | sort -u | grep "PROPOSAL.md"` — confirm no matches

## 4. Final verification and push

- [x] 4.1 Run `git log --oneline | head -10` to confirm history looks intact (92+ commits still present, just rewritten)
- [ ] 4.2 Review `git status` — confirm workspace is clean and all intended files are tracked
- [ ] 4.3 Create new GitHub repository (public) — do NOT push to existing remote if one exists
- [ ] 4.4 Push: `git remote add origin <new-repo-url> && git push -u origin --all`
- [ ] 4.5 Verify on GitHub: check that `PROPOSAL.md` does not appear in any commit, README renders on homepage, LICENSE is detected
