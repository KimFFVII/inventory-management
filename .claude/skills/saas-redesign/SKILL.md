---
name: saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a left vertical navigation sidebar, design tokens, consistent spacing, and a polished professional look. Use when asked to redesign or modernize a Vue 3 app, replace a top nav bar with a sidebar, or unify spacing and styling across views.
---

# SaaS Redesign for Vue 3

Audit a Vue 3 app, then restyle its shell and views into a modern SaaS interface: left sidebar navigation, a single set of design tokens, consistent spacing, responsive behavior.

## Scope

**In scope:** layout, navigation shell, CSS, tokens, responsive behavior, accessibility of the shell, i18n labels for new UI.

**Out of scope:** routes, API client, server code, data flow, business logic, new dependencies (ask first).

## Rules

- Delegate every `.vue` create or significant edit to the `vue-expert` agent (project rule). Run `code-reviewer` after the shell and views are done.
- Keep the project palette. In this repo: slate/gray (#0f172a, #64748b, #e2e8f0), status colors green/blue/yellow/red.
- No emojis in the UI. Use inline SVG icons.
- Use tokens only. Do not add new hardcoded hex values, pixel gaps, or radii.
- Comment non-obvious logic (for example why a breakpoint or z-index value was chosen).
- Do not commit. Leave git to the user.
- Work in passes (tokens, shell, views, responsive) so each diff stays reviewable.

## Workflow

### 1. Audit (report before editing)

Read the shell component (usually `App.vue`), the router, global styles, and every view. Report a short findings list:

- Nav structure: where links, switchers, and profile menu live; manual active-class logic
- Where global CSS lives and whether CSS variables exist
- Spacing variance: grid gaps, card padding, section margins that differ per view
- Conflicting redefinitions of shared classes (`.card`, `.card-header`, `.page-header`)
- Inline styles and hardcoded colors
- Hardcoded UI strings that bypass i18n
- Missing `@media` rules and fixed-column grids that will overflow
- Sticky or fixed elements that depend on the old top-nav height

Stop and show the findings to the user before step 2 if the audit reveals anything that changes scope.

### 2. Design tokens

Create one global stylesheet (for example `src/styles/tokens.css`) imported once in `main.js`. Map existing values onto tokens rather than inventing a new palette.

```css
:root {
  /* Color */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-accent: #2563eb;
  --color-accent-soft: #eff6ff;
  --color-success: #059669;
  --color-warning: #ca8a04;
  --color-danger: #dc2626;

  /* Spacing scale (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Shape and depth */
  --radius-sm: 6px;
  --radius-md: 10px;
  --shadow-card: 0 1px 2px rgb(15 23 42 / 0.06);

  /* Type */
  --font-size-sm: 0.8125rem;
  --font-size-base: 0.875rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.5rem;

  /* Layout */
  --sidebar-width: 15rem;
  --sidebar-width-collapsed: 4rem;
  --content-max-width: 1400px;
  --z-sidebar: 100;
  --z-filterbar: 90;
}
```

Adjust values to match the app's existing palette. Two spacing values are enough for most layouts: `--space-4` for gaps inside a card, `--space-6` between cards and sections.

### 3. App shell

Replace the top nav with a CSS Grid shell: `sidebar | content`.

```vue
<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ open: drawerOpen }">
      <div class="sidebar-brand"><!-- logo + product name --></div>
      <nav class="sidebar-nav" aria-label="Primary">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="nav-link">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path :d="item.icon" /></svg>
          <span class="nav-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <!-- language switcher, profile menu -->
      </div>
    </aside>

    <div class="content">
      <!-- slim sticky filter bar, then page -->
      <main class="page"><router-view /></main>
    </div>
  </div>
</template>
```

```css
.app-shell { display: grid; grid-template-columns: var(--sidebar-width) 1fr; min-height: 100vh; }
.sidebar { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column;
           background: var(--color-surface); border-right: 1px solid var(--color-border);
           z-index: var(--z-sidebar); }
.sidebar-nav { flex: 1; display: grid; gap: var(--space-1); padding: var(--space-4); align-content: start; }
.nav-link { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3);
            border-radius: var(--radius-sm); color: var(--color-text-muted); text-decoration: none; }
.nav-link:hover { background: var(--color-bg); color: var(--color-text); }
/* router-link adds this class itself, so no manual :class binding is needed */
.nav-link.router-link-exact-active { background: var(--color-accent-soft); color: var(--color-accent); }
.nav-link:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
.nav-icon { width: 1.25rem; height: 1.25rem; fill: none; stroke: currentColor; stroke-width: 1.75; }
.content { min-width: 0; } /* min-width: 0 lets wide tables scroll instead of stretching the grid */
.page { max-width: var(--content-max-width); padding: var(--space-6) var(--space-8); }
```

Requirements:

- Drive nav from a `navItems` array. Labels come from i18n keys, never literals.
- Use `router-link-exact-active` for `/` and `router-link-active` for nested routes. Remove manual `$route.path ===` class logic.
- Put the filter bar at the top of the content column as a slim horizontal bar, sticky at `top: 0` with `--z-filterbar`. Remove its old `top: 70px` offset.
- Move the language switcher and profile menu into the sidebar footer. Check that their dropdowns open upward or inward and are not clipped by the sidebar.
- Only include nav items for routes that exist in the router.

### 4. Normalize views

- Define `.page-header`, `.card`, `.card-header`, `.card-title`, `.stats-grid`, `.table-container`, `.badge` once in global styles, using tokens.
- Delete per-view redefinitions that conflict with them. If a view needs a variant, add a modifier class (`.card--flat`) instead of redefining the base.
- Replace one-off gaps and margins with `--space-4` (inside cards) and `--space-6` (between cards and sections).
- Replace inline styles with classes.
- Replace hardcoded status colors with the `--color-*` tokens.
- Keep scoped CSS in a view only for layout unique to that view.

### 5. Responsive

- Below about 900px, collapse the sidebar to an off-canvas drawer with a menu button in a slim top bar. An icon rail (`--sidebar-width-collapsed`) is an acceptable alternative for mid widths.
- Replace fixed `repeat(2, 1fr)` chart grids with `repeat(auto-fit, minmax(min(100%, 22rem), 1fr))`.
- Let the filter bar wrap or scroll horizontally on narrow screens.
- Keep `overflow-x: auto` on `.table-container`.

```css
@media (max-width: 900px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { position: fixed; inset: 0 auto 0 0; width: var(--sidebar-width);
             transform: translateX(-100%); transition: transform 0.2s ease; }
  .sidebar.open { transform: translateX(0); }
}
```

### 6. Accessibility

- `<nav aria-label="Primary">`, icons `aria-hidden="true"`.
- Visible `:focus-visible` rings on all interactive elements.
- Drawer toggle is a real `<button>` with `aria-expanded` and `aria-controls`. Escape closes the drawer. Close it on route change.
- Check text/background contrast of the token pairs (4.5:1 for body text).

### 7. i18n

- Every new label uses `t()`.
- Add any missing keys to every locale file (this repo: `locales/en.js`, `locales/ja.js`). Fix existing nav links that are hardcoded.
- Check that long and short labels in each locale do not break the sidebar width.

### 8. Verify

1. Start the servers with the `start` skill if they are not running.
2. With Playwright MCP, visit every route at desktop width and at about 390px width. Take a screenshot of each.
3. Check the console for errors.
4. Change a filter and confirm the data on the page changes.
5. Confirm the active nav item highlights on each route.
6. Switch language and confirm labels and layout hold.
7. Open and close the drawer at the narrow width.
8. Run `code-reviewer` on the changed files.

Report what was verified and what was not.

## Worked example: this repository

Findings from the original audit of `client/src`:

- `App.vue` holds a sticky 70px `.top-nav` (logo, `.nav-tabs`, `LanguageSwitcher`, `ProfileMenu`), then `FilterBar` (sticky at `top: 70px`), then `<main class="main-content">`. All global CSS is in the unscoped `<style>` of `App.vue`, with no CSS variables.
- Manual `:class="{active: $route.path === ...}"` on each nav link.
- The Reports link label is hardcoded (no `nav.reports` key in `locales/en.js` and `locales/ja.js`). Backlog has no nav link and no route.
- Reports redefines `.card` (12px radius, shadow, no border) and `.card-header`. Inventory overrides `.card-header` padding. Backlog uses inline styles.
- Grid gaps vary: Dashboard 1rem and 1.25rem, Spending and Demand 1.5rem.
- No `@media` queries anywhere; `.charts-grid` is a fixed two-column grid.
- Status colors (#2563eb, #ea580c, #059669) are hardcoded in several views. The orange and blue accents sit outside the slate palette, so decide with the user whether to keep them as tokens.
- Demand uses `↑` as a text icon. Replace it with an SVG to follow the no-emoji rule.

Target structure:

- `client/src/styles/tokens.css`, imported in `client/src/main.js`
- `client/src/components/SidebarNav.vue` for the nav, with `App.vue` reduced to the grid shell and `<router-view />`
- Global component classes stay in `App.vue` (or move to `client/src/styles/base.css`)
- Filter bar remains `components/FilterBar.vue`, restyled as the slim top bar

Constraints that still apply: filters drive all data through `useFilters` and `api.js` (do not touch them), and use unique keys in `v-for` (not `index`).
