<template>
  <v-layout>
    <!-- App Bar -->
    <v-app-bar class="glass-panel" flat>
      <v-app-bar-nav-icon
        class="d-md-none text-black"
        @click="uiStore.toggleDrawer"
      />

      <v-app-bar-title>
        <router-link to="/" class="text-black text-decoration-none d-flex align-center font-weight-bold">
          <v-icon class="mr-2 text-black">mdi-book-open-page-variant</v-icon>
          Research Paper Curator
        </router-link>
      </v-app-bar-title>

      <v-spacer />

      <!-- Desktop Navigation -->
      <div class="d-none d-md-flex align-center">
        <v-btn
          v-for="item in mainNavItems"
          :key="item.to"
          :to="item.to"
          variant="text"
          color="black"
          class="mx-1"
        >
          <v-icon start>{{ item.icon }}</v-icon>
          {{ item.title }}
        </v-btn>
      </div>

      <v-spacer />

      <!-- Theme toggle -->
      <v-btn icon @click="uiStore.toggleDarkMode" class="mr-2 text-black">
        <v-icon>
          {{ uiStore.darkMode ? 'mdi-weather-sunny' : 'mdi-weather-night' }}
        </v-icon>
        <v-tooltip activator="parent" location="bottom">
          {{ uiStore.darkMode ? 'Light mode' : 'Dark mode' }}
        </v-tooltip>
      </v-btn>

      <!-- User menu -->
      <template v-if="authStore.isAuthenticated">
        <v-menu>
          <template #activator="{ props }">
            <v-btn icon v-bind="props" class="text-black">
              <v-avatar color="grey-lighten-2" size="36">
                <span class="text-h6 text-black">{{ userInitial }}</span>
              </v-avatar>
            </v-btn>
          </template>
          <v-list min-width="200" class="glass-panel">
            <v-list-item>
              <v-list-item-title class="font-weight-bold">
                {{ authStore.user?.username }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ authStore.user?.email }}
              </v-list-item-subtitle>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'profile' }" prepend-icon="mdi-account">
              <v-list-item-title>Profile</v-list-item-title>
            </v-list-item>
            <v-list-item :to="{ name: 'collections' }" prepend-icon="mdi-bookmark">
              <v-list-item-title>My Collections</v-list-item-title>
            </v-list-item>
            <v-list-item :to="{ name: 'history' }" prepend-icon="mdi-history">
              <v-list-item-title>Search History</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item @click="handleLogout" prepend-icon="mdi-logout">
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
      <template v-else>
        <v-btn :to="{ name: 'login' }" variant="text" color="black" class="mr-2">
          Login
        </v-btn>
        <v-btn :to="{ name: 'register' }" variant="flat" color="black">
          Register
        </v-btn>
      </template>
    </v-app-bar>

    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-model="uiStore.drawer"
      temporary
      class="d-md-none"
    >
      <v-list nav>
        <v-list-item
          v-for="item in allNavItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          @click="uiStore.setDrawer(false)"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main>
      <v-container fluid class="pa-4 pa-md-6">
        <router-view />
      </v-container>
    </v-main>

    <!-- Footer -->
    <v-footer app class="text-center d-flex flex-column">
      <div class="text-body-2">
        Research Paper Curator &copy; {{ new Date().getFullYear() }}
      </div>
    </v-footer>
  </v-layout>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui.store'
import { useAuthStore } from '@/stores/auth.store'
import { useRouter } from 'vue-router'

const uiStore = useUIStore()
const authStore = useAuthStore()
const router = useRouter()

const mainNavItems = [
  { to: '/search', icon: 'mdi-magnify', title: 'Search' },
  { to: '/ask', icon: 'mdi-comment-question', title: 'Ask' },
  { to: '/browse', icon: 'mdi-book-open-variant', title: 'Browse' }
]

const allNavItems = computed(() => {
  const items = [
    { to: '/', icon: 'mdi-home', title: 'Home' },
    ...mainNavItems
  ]

  if (authStore.isAuthenticated) {
    items.push(
      { to: '/collections', icon: 'mdi-bookmark', title: 'Collections' },
      { to: '/history', icon: 'mdi-history', title: 'History' }
    )
  }

  return items
})

const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0).toUpperCase() || 'U'
})

function handleLogout() {
  authStore.logout()
  router.push('/')
}

onMounted(() => {
  uiStore.initTheme()
})
</script>
