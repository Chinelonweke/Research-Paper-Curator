<template>
  <v-app>
    <ThreeBackground />
    <v-main class="d-flex align-center justify-center auth-background">
      <v-container class="position-relative" style="z-index: 1">
        <v-row justify="center">
          <v-col cols="12" sm="8" md="6" lg="4">
            <!-- Logo/Brand -->
            <div class="text-center mb-8">
              <router-link to="/" class="text-decoration-none">
                <v-icon size="64" color="black">mdi-book-open-page-variant</v-icon>
                <h1 class="text-h4 mt-4 text-black">Research Paper Curator</h1>
                <p class="text-h6 text-medium-emphasis mt-2">
                  Unlock the future with AI-powered research insights
                </p>
              </router-link>
            </div>

            <!-- Auth Form Card -->
            <v-card elevation="0" class="pa-6 border glass-panel">
              <router-view />
            </v-card>

            <!-- Footer Links -->
            <div class="text-center mt-6">
              <router-link to="/" class="text-decoration-none text-medium-emphasis">
                <v-icon size="small">mdi-arrow-left</v-icon>
                Back to Home
              </router-link>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUIStore } from '@/stores/ui.store'
import ThreeBackground from '@/components/ThreeBackground.vue'

const uiStore = useUIStore()

onMounted(() => {
  uiStore.initTheme()
})
</script>

<style scoped>
.auth-background {
  background-color: transparent;
  min-height: 100vh;
}
</style>
