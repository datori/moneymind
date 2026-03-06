---
name: ralph-archive
description: Retrospective OpenSpec archive for a completed Ralph exploration loop. Diffs the explore branch against main, synthesizes what was built, and writes OpenSpec artifacts (proposal, design, tasks, specs) to the archive. Use after a ralph:explore loop has finished.
license: MIT
metadata:
  author: local
  version: "1.0"
---

Generate retrospective OpenSpec artifacts from a completed Ralph exploration branch and archive them.

**Input**: Run on an `explore/` branch after the loop has completed. No arguments needed — everything is derived from the branch and its commit history.

---

## Step 1 — Verify Branch and Collect Context

### 1a — Confirm we're on an explore branch
```bash
git branch --show-current
```

If the current branch does NOT start with `explore/`, abort:
> "This skill must be run on an explore/ branch. Current branch: {branch}. Switch to the explore branch and try again."

### 1b — Extract slug and date
From the branch name `explore/{slug}-{YYYY-MM-DD}`, extract:
- `{slug}` → used for archive directory name
- `{YYYY-MM-DD}` → used for archive directory name (use today's date if not in branch name)

### 1c — Check loop is no longer active
If `.claude/ralph-loop.local.md` exists, warn:
> "The Ralph loop state file still exists — the loop may still be running. Cancel it first with /cancel-ralph, then run /ralph:archive."

Abort unless the user confirms the loop is done.

---

## Step 2 — Reconstruct the Loop's Work

### 2a — Get commit history
```bash
git log main..HEAD --oneline
```

This gives the full sequence of commits made during the exploration. Review them carefully — they are the primary artifact trail.

### 2b — Get diff statistics
```bash
git diff main...HEAD --stat
```

Shows which files were modified and how substantially.

### 2c — Get full diff
```bash
git diff main...HEAD
```

Read the full diff to understand what actually changed at the code level.

### 2d — Read RALPH_PROMPT.md
```bash
cat RALPH_PROMPT.md
```

This is the original objective and prompt used for the loop. It captures intent.

### 2e — Read all modified files in full

For each file shown in the diff stat, read its current state in full using the Read tool. Understand the current implementation — not just what changed, but the full context of what now exists.

---

## Step 3 — Analyze the Exploration

Before writing artifacts, synthesize what the loop actually did:

**Commit sequence analysis**: Read the commits in order. What did each one do? Is there a clear progression, or did the loop scatter? Did later iterations build on earlier ones, or work independently?

**Code analysis**: What patterns emerged? What implicit design decisions were made? What improved, and how?

**Coherence check**: Were any changes contradictory or redundant? If so, note this honestly — the archive should reflect reality.

**Objective alignment**: How well did the loop's work match the original objective in RALPH_PROMPT.md?

---

## Step 4 — Generate OpenSpec Artifacts

Create the archive directory:
```bash
ARCHIVE_DIR="openspec/changes/archive/{YYYY-MM-DD}-explore-{slug}"
mkdir -p "$ARCHIVE_DIR"
```

Where `{YYYY-MM-DD}` is today's date.

If the directory already exists, abort and inform the user.

### 4a — proposal.md

Captures what was explored and why.

```markdown
# Proposal: Explore {slug}

## Objective

{The original exploration objective from RALPH_PROMPT.md, in plain language.}

## Motivation

{Why this area was worth exploring. Infer from the objective and what was found.}

## Scope

Files explored and modified:
{list of modified files}

Focus area:
{description of the bounded domain}

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for {N} iterations with commit-per-iteration discipline.
```

### 4b — design.md

The hardest artifact. Synthesizes the actual design reasoning from the commit sequence and diffs. Must be honest — if the loop was scattered, say so. If it converged on a clear pattern, describe it.

```markdown
# Design: Explore {slug}

## Overview

{1-2 paragraph summary of what the loop actually built and the overall shape
of the changes.}

## Iteration Progression

{Narrate the commit sequence. What did the loop prioritize first? How did
later iterations build on or respond to earlier ones? Were there any pivots?}

## Design Decisions

{For each meaningful decision implicit in the code changes, describe:
- What was decided
- What the alternative might have been
- Why this approach appears to have been chosen (infer from the code/commits)}

## Coherence Assessment

{Honest evaluation: Did the iterations compose well? Were there any
contradictions, redundancies, or areas where the loop seemed to spin?
What would a human architect have done differently?}

## What Was Improved

{Concrete list of what is meaningfully better now than before the loop ran.}

## What Was Not Addressed

{Honest accounting of limitations — things in the focus area that the loop
did not improve, or areas that could benefit from follow-up work.}
```

### 4c — tasks.md

A descriptive record of what was done. All items are pre-checked — this is a record, not a plan.

```markdown
# Tasks: Explore {slug}

All tasks below were completed by the Ralph exploration loop.

{For each meaningful commit or logical unit of work:}
- [x] {Description of what was done — match to commit messages but be more descriptive}
- [x] {Next item}
...

## Loop Metadata

- Iterations: {N}
- Branch: explore/{slug}-{YYYY-MM-DD}
- Commits: {commit count}
```

### 4d — Specs (if applicable)

If the loop modified behavior that is described in existing specs at `openspec/specs/`, update those specs to reflect current behavior.

For each affected spec area:
1. Read the existing spec at `openspec/specs/{area}/spec.md`
2. Identify what has changed in the implementation
3. Write an updated spec that reflects current behavior

Write delta specs to `{ARCHIVE_DIR}/specs/{area}/spec.md`.

If no existing specs are affected, skip this step.

---

## Step 5 — Update Main Specs

For each delta spec written in Step 4d, sync it to the main spec location:
`openspec/specs/{area}/spec.md`

Apply changes carefully — preserve sections that weren't affected by the exploration. Add new sections, update changed sections, remove anything that's no longer accurate.

If there are no delta specs, skip this step.

---

## Step 6 — Commit the Archive

Stage and commit the archive artifacts on the explore branch:

```bash
git add openspec/changes/archive/{YYYY-MM-DD}-explore-{slug}/
git add openspec/specs/  # if any main specs were updated
git commit -m "archive(explore/{slug}): retrospective OpenSpec artifacts

Generated with Claude Code
via Happy

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

Do NOT merge to main. Do NOT delete the branch. Leave that to the human.

---

## Step 7 — Display Summary

```
Archive Complete
────────────────────────────────────────────
Exploration:   {slug}
Branch:        explore/{slug}-{YYYY-MM-DD}
Archived to:   openspec/changes/archive/{YYYY-MM-DD}-explore-{slug}/

Loop summary:
  Iterations:  {N}
  Commits:     {count}
  Files changed: {count}

Artifacts written:
  proposal.md    — objective and approach
  design.md      — synthesis of what was built
  tasks.md       — pre-checked record of work done
  {specs/ — if applicable}

Main specs updated: {yes/no, list if yes}

Next steps:
  Review the changes on this branch, then merge to main when satisfied.
  The branch will not be merged automatically.
────────────────────────────────────────────
```

---

## Guardrails

- Never auto-merge to main
- If the branch has no commits beyond the initial setup commit, warn and abort — there is nothing to archive
- The design.md must be honest about incoherence or failures — do not fabricate a clean narrative if the loop was messy
- Do not modify code files during archive — read only
- Do not touch `.claude/ralph-loop.local.md` — only check for its presence
- If RALPH_PROMPT.md is missing, reconstruct the objective from the commit messages
- Archive directory name format: `YYYY-MM-DD-explore-{slug}` (today's date, not the branch creation date)
