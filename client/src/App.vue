<template>
  <div class="app">
    <SidebarNav
      :open="drawerOpen"
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />

    <!-- Click-away scrim; only rendered while the drawer is open (mobile) -->
    <div v-if="drawerOpen" class="drawer-scrim" @click="closeDrawer()"></div>

    <div class="content">
      <div class="topbar">
        <button
          ref="menuButton"
          type="button"
          class="menu-button"
          :aria-label="drawerOpen ? t('nav.closeMenu') : t('nav.menu')"
          :aria-expanded="drawerOpen"
          aria-controls="app-sidebar"
          @click="drawerOpen = !drawerOpen"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true" focusable="false">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span class="topbar-title">{{ t('nav.companyName') }}</span>
      </div>

      <FilterBar />

      <main class="page">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import SidebarNav from './components/SidebarNav.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileDetailsModal,
    TasksModal,
    SidebarNav
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Mobile drawer state. CSS (max-width: 900px) decides whether it has any visual effect.
    const drawerOpen = ref(false)
    const menuButton = ref(null)
    const route = useRoute()

    const closeDrawer = (returnFocus = false) => {
      drawerOpen.value = false
      if (returnFocus) nextTick(() => menuButton.value && menuButton.value.focus())
    }
    const onKeydown = (e) => {
      if (e.key === 'Escape' && drawerOpen.value) closeDrawer(true)
    }
    // Navigating from the drawer should reveal the page
    watch(() => route.fullPath, () => closeDrawer())

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      document.addEventListener('keydown', onKeydown)
    })
    onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

    return {
      t,
      drawerOpen,
      menuButton,
      closeDrawer,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--font-size-base);
  background: var(--color-bg);
  color: var(--color-text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Keyboard focus ring for anything without its own treatment */
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* ---- Shell: sidebar | content ---- */
.app {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
}

/* Sticky + full height keeps the sidebar in view while the page scrolls.
   Positioning for the drawer variant lives in SidebarNav.vue. */
.app > .sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  /* Sticky creates a stacking context; without this the sticky filter bar (z 90) paints over footer popovers. */
  z-index: var(--z-sidebar);
}

/* min-width: 0 lets this grid item shrink below its content so wide tables scroll
   inside .table-container instead of stretching the page. */
.content {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.page {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  padding: var(--space-6);
}

/* Mobile top bar and scrim only exist below the breakpoint */
.topbar,
.drawer-scrim {
  display: none;
}

/* 900px breakpoint: keep in sync with SidebarNav.vue and FilterBar.vue (media queries can't use var()). */
@media (max-width: 900px) {
  .app {
    grid-template-columns: minmax(0, 1fr);
  }

  /* The sidebar becomes a fixed off-canvas drawer (see SidebarNav.vue); remove it from the grid flow. */
  .app > .sidebar {
    position: fixed;
    height: auto;
  }

  .content {
    /* FilterBar sticks just below the top bar */
    --filterbar-top: var(--topbar-height);
  }

  .topbar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: var(--topbar-height);
    padding: 0 var(--space-4);
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    /* Above the filter bar (90), below the scrim (99) and drawer (100) */
    z-index: var(--z-topbar);
  }

  .topbar-title {
    font-weight: 700;
    color: var(--color-text);
  }

  /* Scrim sits just under the drawer (z-sidebar) and over every sticky bar */
  .drawer-scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--color-overlay);
    z-index: var(--z-overlay);
  }

  .page {
    padding: var(--space-4);
  }
}

.menu-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--color-surface-hover);
}

.menu-button svg {
  width: var(--space-5);
  height: var(--space-5);
}

/* ---- Page header ---- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
}

/* ---- Stats ---- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 17.5rem), 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--font-size-stat);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--color-orange); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-accent); }

/* ---- Card ---- */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

/* ---- Tables ---- */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-surface-hover);
  color: var(--color-text-body);
  font-size: var(--font-size-base);
}

tbody tr:hover {
  background: var(--color-bg);
}

/* ---- Badges: soft fill + strong text of the same hue ---- */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  background: var(--color-surface-hover);
  color: var(--color-text-body);
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-strong);
}

.badge.warning,
.badge.medium {
  background: var(--color-orange-soft);
  color: var(--color-orange-strong);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger-strong);
}

.badge.info,
.badge.low {
  background: var(--color-accent-soft);
  color: var(--color-accent-strong);
}

.badge.stable {
  background: var(--color-indigo-soft);
  color: var(--color-indigo-strong);
}

/* ---- Feedback ---- */
.loading {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
}

.error {
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger);
  color: var(--color-danger-strong);
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: var(--font-size-base);
}
</style>
