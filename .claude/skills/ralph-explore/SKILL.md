---
name: ralph-explore
description: Start an exploration Ralph loop — dynamically generates a tailored prompt, creates an isolated git branch, and launches an iterative improvement loop. Use when the user wants to explore and improve a focused area of the codebase with minimal upfront structure.
license: MIT
metadata:
  author: local
  version: "1.0"
---

Start an exploration Ralph loop on a focused area of the codebase.

**Input**: Optionally pass a short description of what to explore as an argument. If omitted, ask once.

---

## Step 1 — Collect the Objective

If the user provided a description (as skill args or in their message), use it directly.

If not, use the **AskUserQuestion tool** to ask:
> "What area do you want to explore and improve? Describe it in a sentence or two — be loose, not precise."

Do NOT ask follow-up questions at this stage. Proceed with what you have.

---

## Step 2 — Derive a Slug

From the objective description, derive a short kebab-case slug (2-4 words). Examples:
- "improve the recurring detection UI" → `recurring-ui`
- "clean up the pipeline categorization logic" → `pipeline-categorization`
- "improve SimpleFin sync reliability" → `simplefin-sync`

This slug is used for the branch name and archive directory.

---

## Step 3 — Read the Codebase

Based on the objective, identify the relevant parts of this codebase:

**Project structure** (finance app — Python/FastAPI/SQLite):
- `finance/` — core package (models, db, config)
- `finance/pipeline/` — ingestion, categorization, recurring detection, SimpleFin sync
- `finance/web/` — FastAPI routes and Jinja2 templates
- `finance/web/templates/` — HTML templates
- `openspec/specs/` — canonical specs for current behavior

Read the files most relevant to the focus area. Also read any specs in `openspec/specs/` that describe the affected functionality.

For shared files (templates, base models, utilities) — include them in scope if they're relevant to the objective. No read-only exceptions.

---

## Step 4 — Infer Scope and Fences

**Scope paths**: List the specific files and directories the loop should work within. Include shared files if relevant.

**Scope fences** (do not touch): Infer what is clearly unrelated to the focus area. Common fences include:
- `finance/db/` schema/migration files (unless the focus area is explicitly data model changes)
- Ingestion/sync modules unrelated to the focus area
- Unrelated pipeline stages
- `openspec/` directory (loop should not touch specs — that's for archive)
- `.claude/` directory

Be reasonable — don't fence off everything, don't fence off nothing.

---

## Step 5 — Present Proposed Config for Confirmation

Show the proposed run configuration in this format:

```
Proposed Exploration
────────────────────────────────────────────
Slug:         {slug}
Branch:       explore/{slug}-{YYYY-MM-DD}
Objective:    {objective, 1-3 sentences}

In scope:
  {file or directory}
  {file or directory}
  ...

Fenced — do not touch:
  {file or directory}
  ...

Max iterations:  10
Stop signal:     <promise>EXPLORATION COMPLETE</promise>
────────────────────────────────────────────
Confirm, or tell me what to adjust.
```

Use the **AskUserQuestion tool** to collect the response. Accept free-form adjustments ("change max to 5", "also include X", "remove Y from scope").

If adjustments are requested, apply them and re-present the config. Repeat until confirmed.

---

## Step 6 — Generate the Loop Prompt

Construct the full prompt that will be fed to each iteration of the loop. This prompt must be completely self-contained — each iteration starts fresh with only this text and whatever is in files/git.

The prompt structure:

```markdown
# Exploration: {objective_title}

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

{For each in-scope file: brief description of what it currently does,
key functions/classes, and anything notable. 2-5 lines per file.
Read from the actual file content — do not hallucinate.}

## Objective

{objective_description}

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- {scope_paths_space_separated}`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore({slug}): <what changed and why in one line>`

## In Scope

{List each in-scope path on its own line}

## Do Not Touch

{List each fenced path on its own line}
- openspec/ (specs are written during archive, not during exploration)
- .claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
```

---

## Step 7 — Execute Setup

Run these steps in order:

### 7a — Create and check out the branch
```bash
git checkout -b explore/{slug}-{YYYY-MM-DD}
```

### 7b — Write the loop state file

Use Bash to write `.claude/ralph-loop.local.md` with the correct format:

```bash
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > .claude/ralph-loop.local.md << 'STATE_EOF'
---
active: true
iteration: 1
session_id: SESSION_ID_PLACEHOLDER
max_iterations: MAX_ITERATIONS_PLACEHOLDER
completion_promise: "EXPLORATION COMPLETE"
started_at: "STARTED_AT_PLACEHOLDER"
---

PROMPT_PLACEHOLDER
STATE_EOF
```

Then use `sed` to replace the placeholders with actual values. Or write the file directly using the Write tool with all values substituted inline.

**State file format** (substitute all values before writing):
```
---
active: true
iteration: 1
session_id: {value of $CLAUDE_CODE_SESSION_ID, or empty}
max_iterations: {confirmed max iterations, integer}
completion_promise: "EXPLORATION COMPLETE"
started_at: "{ISO8601 UTC timestamp}"
---

{full prompt text from Step 6}
```

### 7c — Write RALPH_PROMPT.md (reference copy)

Write the same prompt text to `RALPH_PROMPT.md` in the repo root. This is a human-readable reference that persists on the branch. It is NOT used by the loop machinery — the state file drives the loop.

### 7d — Stage and commit setup files
```bash
git add RALPH_PROMPT.md
git commit -m "explore({slug}): start exploration loop

Generated with Claude Code
via Happy

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

Do NOT add `.claude/ralph-loop.local.md` to git — it is ephemeral loop state.

---

## Step 8 — Report and Exit

Output a brief summary:

```
Exploration loop started.

Branch:     explore/{slug}-{YYYY-MM-DD}
Objective:  {objective}
Iterations: up to {max}

The loop will begin on next exit. Each iteration makes one focused commit.
Run /ralph:archive when the loop finishes to generate OpenSpec artifacts.

To cancel early: /cancel-ralph
```

Then exit. The stop hook fires on exit, reads the state file, and begins iteration 1.

---

## Guardrails

- Do NOT start the loop without user confirmation of the config
- Do NOT add `.claude/ralph-loop.local.md` to git
- Do NOT write code changes — setup only
- The prompt in the state file must be fully self-contained and self-describing
- If the branch already exists, abort and ask the user to choose a different slug or delete the existing branch
- If `.claude/ralph-loop.local.md` already exists, warn the user that a loop is already active before overwriting
