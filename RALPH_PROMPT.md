# Exploration: Transaction List UI

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard built with Jinja2 templates
and Tailwind CSS (loaded from CDN).

### Current State of Focus Area

**finance/web/templates/transactions.html**
Main transaction browser page. Contains:
- Filter bar: month navigation buttons (prev/next with JS), start/end date
  inputs, search text field, category dropdown, limit input, and a submit button
- Sortable table: columns for Date, Description, Merchant, Category, Account,
  Amount (right-aligned, color-coded red/green), Pending
- Amount formatting: manual `{% if txn.amount < 0 %}-{% endif %}${{ "%.2f"|format(txn.amount | abs) }}`
- Sort links in Date/Amount headers; sort direction arrows (down/up) for active column
- Inline JS: month nav buttons update start/end inputs and auto-submit the form;
  updateLabel() shows "Mar 2026" style label
- Trailing count line: "Showing N transaction(s)."

**finance/web/templates/_macros.html**
Single macro: `category_badge(cat)`. Long if/elif chain mapping category names
to Tailwind colored pills (bg-*-100 text-*-700). Falls back to gray for unknown
categories. Used in the transactions table and potentially elsewhere.

**finance/web/templates/base.html**
HTML shell + Tailwind CDN + Chart.js CDN. Navigation bar with desktop links
and mobile hamburger menu. Flash message area (green/red). Main content block.
Active link highlighting via request.url.path comparisons.

## Objective

Improve the transaction list UI — tighten up display, formatting, and UX.
This is intentionally open-ended. Focus on quality, clarity, and user experience.
Good candidates include: visual hierarchy, amount formatting readability,
filter bar layout, table density, active sort indicator clarity, empty states,
or any other meaningful polish.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/transactions.html finance/web/templates/_macros.html finance/web/templates/base.html`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(transaction-ui): <what changed and why in one line>`

## In Scope

finance/web/templates/transactions.html
finance/web/templates/_macros.html
finance/web/templates/base.html

## Do Not Touch

finance/web/app.py
finance/pipeline/
finance/db/
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
