<template>
  <aside id="app-sidebar" class="sidebar" :class="{ 'sidebar-open': open }">
    <div class="brand">
      <span class="brand-name">{{ t('nav.companyName') }}</span>
      <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav aria-label="Primary" class="nav">
      <ul class="nav-list">
        <li v-for="item in navItems" :key="item.to">
          <router-link :to="item.to" class="nav-link">
            <svg
              class="nav-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
              focusable="false"
            >
              <path v-for="d in item.paths" :key="d" :d="d" />
            </svg>
            <span class="nav-label">{{ t(item.labelKey) }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="emit('show-profile-details')"
        @show-tasks="emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script setup>
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

defineProps({
  // Drawer state, only meaningful below the mobile breakpoint (owned by App.vue)
  open: { type: Boolean, default: false }
})
const emit = defineEmits(['show-profile-details', 'show-tasks'])

const { t } = useI18n()

// Only routes registered in main.js. `paths` are 24x24 stroke path data.
const navItems = [
  { to: '/', labelKey: 'nav.overview', paths: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'] },
  { to: '/inventory', labelKey: 'nav.inventory', paths: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
  { to: '/orders', labelKey: 'nav.orders', paths: ['M9 3h6v3H9z', 'M15 4.5h2a2 2 0 012 2V20a1 1 0 01-1 1H6a1 1 0 01-1-1V6.5a2 2 0 012-2h2', 'M9 12h6', 'M9 16h6'] },
  { to: '/spending', labelKey: 'nav.finance', paths: ['M3 7h18v12H3z', 'M3 11h18', 'M7 15h3'] },
  { to: '/demand', labelKey: 'nav.demandForecast', paths: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
  { to: '/reports', labelKey: 'nav.reports', paths: ['M6 3h9l4 4v14H6z', 'M14 3v5h5', 'M9 13h7', 'M9 17h7'] }
]
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-4);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  /* No overflow clipping here: footer dropdowns open upward inside this column. */
}

.brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
}

.brand-name {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.brand-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto; /* nav scrolls on short viewports; footer stays pinned */
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--font-size-base);
  font-weight: 500;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.nav-link:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.nav-link.router-link-exact-active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 600;
}

.nav-link:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.nav-icon {
  width: var(--space-5);
  height: var(--space-5);
  flex-shrink: 0;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

/* Drawer mode. Breakpoint 900px must match App.vue and cannot be a var() in a media query. */
@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    width: var(--sidebar-width);
    max-width: 85vw;
    z-index: var(--z-sidebar);
    box-shadow: var(--shadow-drawer);
    transform: translateX(-100%);
    /* visibility keeps off-screen links out of the tab order while closed */
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0.2s;
  }

  .sidebar.sidebar-open {
    transform: translateX(0);
    visibility: visible;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar { transition: none; }
}
</style>
