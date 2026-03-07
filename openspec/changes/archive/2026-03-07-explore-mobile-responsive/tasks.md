# Tasks: Explore mobile-responsive

All tasks below were completed by the Ralph exploration loop.

- [x] Make spending page summary strip wrap gracefully on mobile — replace `flex items-center gap-6` with `flex flex-wrap gap-x-6 gap-y-2`; hide pipe separators on xs with `hidden sm:block`
- [x] Fix recurring page header on narrow screens — change `flex items-center justify-between` to `flex flex-wrap items-center gap-3` so filter chips wrap below the heading instead of overflowing
- [x] Fix recurring page summary strip — change `grid grid-cols-3` to `grid grid-cols-1 sm:grid-cols-3` so Monthly/Annual/Due Soon cards stack on mobile
- [x] Reduce report detail page padding on mobile — change `p-8` to `p-4 sm:p-8` on the narrative card
- [x] Make report detail page markdown tables scrollable — add `.table-wrap { overflow-x: auto }` CSS and a JS post-render pass that wraps each `<table>` in a `.table-wrap` div
- [x] Fix spending page chart/table layout on mobile — replace `flex gap-6 flex-wrap` with `flex flex-col lg:flex-row gap-6`; give each panel `w-full` on mobile, `lg:flex-1` on large screens
- [x] Fix dashboard home spending section layout on mobile — replace `flex gap-6 flex-wrap` with `flex flex-col md:flex-row gap-6`; give table `w-full md:flex-1`

## Loop Metadata

- Iterations: 5
- Branch: explore/mobile-responsive-2026-03-06
- Commits: 5 (excluding setup commit)
- Files changed: 4 templates
