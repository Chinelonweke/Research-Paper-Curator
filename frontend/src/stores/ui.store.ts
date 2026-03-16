import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useTheme } from 'vuetify'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
}

export const useUIStore = defineStore('ui', () => {
  // State
  const drawer = ref(true)
  const darkMode = ref(
    localStorage.getItem('theme') === 'dark' ||
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
  )
  const notifications = ref<Notification[]>([])

  // Initialize theme - this will be called after Vuetify is ready
  function initTheme() {
    try {
      const vuetifyTheme = useTheme()
      vuetifyTheme.global.name.value = darkMode.value ? 'dark' : 'light'

      // Watch for changes
      watch(darkMode, (isDark) => {
        vuetifyTheme.global.name.value = isDark ? 'dark' : 'light'
        localStorage.setItem('theme', isDark ? 'dark' : 'light')
      })
    } catch {
      // Vuetify not ready yet, will be initialized later
    }
  }

  // Actions
  function toggleDrawer() {
    drawer.value = !drawer.value
  }

  function setDrawer(value: boolean) {
    drawer.value = value
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    try {
      const vuetifyTheme = useTheme()
      vuetifyTheme.global.name.value = darkMode.value ? 'dark' : 'light'
      localStorage.setItem('theme', darkMode.value ? 'dark' : 'light')
    } catch {
      // Handle outside of Vue context
    }
  }

  function addNotification(type: Notification['type'], message: string) {
    const id = Date.now().toString()
    notifications.value.push({ id, type, message })
    setTimeout(() => removeNotification(id), 5000)
  }

  function removeNotification(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  function showSuccess(message: string) {
    addNotification('success', message)
  }

  function showError(message: string) {
    addNotification('error', message)
  }

  function showWarning(message: string) {
    addNotification('warning', message)
  }

  function showInfo(message: string) {
    addNotification('info', message)
  }

  return {
    drawer,
    darkMode,
    notifications,
    initTheme,
    toggleDrawer,
    setDrawer,
    toggleDarkMode,
    addNotification,
    removeNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo
  }
})
