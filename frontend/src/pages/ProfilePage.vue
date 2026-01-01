<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-6">
          <v-icon class="mr-2">mdi-account</v-icon>
          Profile
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Account Information</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <template #prepend>
                  <v-avatar color="primary" size="64">
                    <span class="text-h4">{{ userInitial }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-h6">
                  {{ authStore.user?.username }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ authStore.user?.email }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <v-divider class="my-4" />

            <div class="d-flex flex-column gap-2">
              <div class="d-flex justify-space-between">
                <span class="text-medium-emphasis">Full Name</span>
                <span>{{ authStore.user?.full_name || 'Not set' }}</span>
              </div>
              <div class="d-flex justify-space-between">
                <span class="text-medium-emphasis">Account Status</span>
                <v-chip
                  :color="authStore.user?.is_active ? 'success' : 'error'"
                  size="small"
                >
                  {{ authStore.user?.is_active ? 'Active' : 'Inactive' }}
                </v-chip>
              </div>
              <div class="d-flex justify-space-between">
                <span class="text-medium-emphasis">Role</span>
                <v-chip
                  :color="authStore.user?.is_admin ? 'primary' : 'default'"
                  size="small"
                >
                  {{ authStore.user?.is_admin ? 'Admin' : 'User' }}
                </v-chip>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Quick Links</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item :to="{ name: 'collections' }" prepend-icon="mdi-bookmark">
                <v-list-item-title>My Collections</v-list-item-title>
                <v-list-item-subtitle>View saved papers</v-list-item-subtitle>
              </v-list-item>

              <v-list-item :to="{ name: 'history' }" prepend-icon="mdi-history">
                <v-list-item-title>Search History</v-list-item-title>
                <v-list-item-subtitle>View past searches</v-list-item-subtitle>
              </v-list-item>

              <v-divider class="my-2" />

              <v-list-item @click="handleLogout" prepend-icon="mdi-logout" class="text-error">
                <v-list-item-title>Logout</v-list-item-title>
                <v-list-item-subtitle>Sign out of your account</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

const router = useRouter()
const authStore = useAuthStore()

const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0).toUpperCase() || 'U'
})

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>
