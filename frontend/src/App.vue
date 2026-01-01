<template>
  <v-app>
    <router-view />

    <!-- Global notifications -->
    <v-snackbar
      v-for="notification in uiStore.notifications"
      :key="notification.id"
      :model-value="true"
      :color="notification.type"
      location="top right"
      timeout="5000"
    >
      {{ notification.message }}
      <template #actions>
        <v-btn
          variant="text"
          @click="uiStore.removeNotification(notification.id)"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUIStore } from '@/stores/ui.store'
import { useAuthStore } from '@/stores/auth.store'

const uiStore = useUIStore()
const authStore = useAuthStore()

onMounted(async () => {
  // Initialize auth state from stored token
  if (authStore.token) {
    await authStore.fetchCurrentUser()
  }
})
</script>
