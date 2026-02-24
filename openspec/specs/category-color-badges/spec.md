## ADDED Requirements

### Requirement: Category badge macro
The system SHALL define a Jinja2 macro `category_badge(cat)` in `finance/web/templates/_macros.html` that renders a color-coded pill/badge `<span>` for a given category string.

The macro SHALL NOT be defined in `base.html`. Child templates that do both `{% extends "base.html" %}` and `{% from "base.html" import ... %}` cause Jinja2 to load `base.html` in module mode without the request context, producing `UndefinedError: 'request' is undefined`. The dedicated `_macros.html` file avoids this entirely.

The macro SHALL apply the following Tailwind color classes (background + text) for each of the 15 canonical categories:

| Category | Background class | Text class |
|---|---|---|
| Food & Dining | `bg-orange-100` | `text-orange-700` |
| Groceries | `bg-green-100` | `text-green-700` |
| Transportation | `bg-blue-100` | `text-blue-700` |
| Shopping | `bg-purple-100` | `text-purple-700` |
| Entertainment | `bg-pink-100` | `text-pink-700` |
| Travel | `bg-teal-100` | `text-teal-700` |
| Health & Fitness | `bg-red-100` | `text-red-700` |
| Home & Utilities | `bg-yellow-100` | `text-yellow-700` |
| Subscriptions & Software | `bg-indigo-100` | `text-indigo-700` |
| Personal Care | `bg-rose-100` | `text-rose-700` |
| Education | `bg-cyan-100` | `text-cyan-700` |
| Financial | `bg-slate-100` | `text-slate-700` |
| Income | `bg-emerald-100` | `text-emerald-700` |
| Investment | `bg-lime-100` | `text-lime-700` |
| Other | `bg-gray-100` | `text-gray-600` |

Unknown or `None` category values SHALL render a gray badge with the text "—".

The badge span SHALL always include base pill classes: `inline-block px-2 py-0.5 rounded-full text-xs font-medium`.

#### Scenario: Known category renders colored badge
- **WHEN** `category_badge("Food & Dining")` is called in a template
- **THEN** a `<span>` is rendered with classes `inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700` containing the text `Food & Dining`

#### Scenario: Unknown category renders gray badge
- **WHEN** `category_badge("Uncategorized")` is called in a template
- **THEN** a `<span>` is rendered with the gray fallback classes containing the literal text passed in

#### Scenario: None/empty category renders dash badge
- **WHEN** `category_badge(None)` or `category_badge("")` is called
- **THEN** a gray badge with text `—` is rendered

---

### Requirement: Transactions page uses category badges
The transactions page (`GET /transactions`) SHALL render the category column using the `category_badge` macro instead of plain text.

#### Scenario: Category cell shows pill badge
- **WHEN** a browser navigates to `/transactions` and transactions with categories are present
- **THEN** each category cell displays a colored pill badge matching the category color map

#### Scenario: Transaction with no category shows dash badge
- **WHEN** a transaction has no category set
- **THEN** the category cell displays a gray `—` badge

---

### Requirement: Spending page uses category badges
The spending breakdown table on the spending page (`GET /spending`) SHALL render the label column using the `category_badge` macro when `group_by=category`.

#### Scenario: Spending table category rows show badges
- **WHEN** a browser navigates to `/spending` with `group_by=category`
- **THEN** each row's label cell displays a colored pill badge matching the category color map

#### Scenario: Non-category group_by renders plain text
- **WHEN** the spending page is viewed with `group_by=merchant` or `group_by=account`
- **THEN** the label cell renders as plain text (no badge styling applied)
