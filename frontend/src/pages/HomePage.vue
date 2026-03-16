<template>
  <v-container fluid class="pa-0">
    <!-- Hero Section -->
    <v-row class="mb-12 pt-8 pb-12 px-4 shadow-hero" justify="center">
      <v-col cols="12" md="10" lg="8" class="text-center">
        <h1 class="text-h3 text-md-h2 font-weight-black mb-4 text-black tracking-tight">
          Discover Research Papers
        </h1>
        <p class="text-h6 text-medium-emphasis mb-10 max-w-2xl mx-auto">
          Search, explore, and synthesize AI-powered insights from a vast library of indexed research.
        </p>

        <!-- Quick Search -->
        <v-card max-width="700" class="mx-auto glass-panel rounded-pill pa-2 border-0 shadow-lg" elevation="0">
          <v-row no-gutters align="center">
            <v-col class="flex-grow-1">
              <v-text-field
                v-model="searchQuery"
                placeholder="Search by keywords, authors, or topics..."
                variant="plain"
                class="px-6 text-h6"
                hide-details
                @keyup.enter="handleSearch"
              />
            </v-col>
            <v-col cols="auto" class="pa-1">
              <v-btn
                color="primary"
                size="x-large"
                rounded="pill"
                class="px-8 font-weight-bold"
                elevation="4"
                @click="handleSearch"
              >
                <v-icon start>mdi-magnify</v-icon>
                <span class="d-none d-sm-inline">Search Papers</span>
              </v-btn>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mb-12 px-4" justify="center">
      <v-col cols="12" md="4" lg="3">
        <v-card
          class="glass-panel hover-lift rounded-xl pa-4 text-center h-100 d-flex flex-column border-0"
          :to="{ name: 'search' }"
        >
          <v-card-text class="flex-grow-1 d-flex flex-column align-center justify-center">
            <v-avatar color="primary" variant="tonal" size="80" class="mb-6">
              <v-icon size="40">mdi-magnify</v-icon>
            </v-avatar>
            <h3 class="text-h5 font-weight-bold mb-3">Hybrid Search</h3>
            <p class="text-body-2 text-medium-emphasis mb-0">
              Combine semantic and keyword search to find the most relevant papers.
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" lg="3">
        <v-card
          class="glass-panel hover-lift rounded-xl pa-4 text-center h-100 d-flex flex-column border-0"
          :to="{ name: 'ask' }"
        >
          <v-card-text class="flex-grow-1 d-flex flex-column align-center justify-center">
            <v-avatar color="secondary" variant="tonal" size="80" class="mb-6">
              <v-icon size="40">mdi-comment-question</v-icon>
            </v-avatar>
            <h3 class="text-h5 font-weight-bold mb-3">AI Inquisitor</h3>
            <p class="text-body-2 text-medium-emphasis mb-0">
              Get direct answers with citations from the latest AI research.
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" lg="3">
        <v-card
          class="glass-panel hover-lift rounded-xl pa-4 text-center h-100 d-flex flex-column border-0"
          :to="{ name: 'browse' }"
        >
          <v-card-text class="flex-grow-1 d-flex flex-column align-center justify-center">
            <v-avatar color="accent" variant="tonal" size="80" class="mb-6">
              <v-icon size="40">mdi-book-open-variant</v-icon>
            </v-avatar>
            <h3 class="text-h5 font-weight-bold mb-3">Discovery</h3>
            <p class="text-body-2 text-medium-emphasis mb-0">
              Explore the full landscape of indexed research documents.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Stats Monitor -->
    <v-row v-if="stats" class="px-4 mb-12" justify="center">
      <v-col cols="12" lg="10" xl="9">
        <v-card class="glass-panel rounded-xl pa-6 border-0 shadow-sm" elevation="0">
          <div class="d-flex align-center mb-6">
            <v-avatar color="black" variant="tonal" size="32" class="mr-3">
              <v-icon size="18">mdi-pulse</v-icon>
            </v-avatar>
            <span class="text-h6 font-weight-bold">System Status</span>
            <v-spacer />
            <v-chip size="small" variant="tonal" color="success" class="font-weight-bold">OPERATIONAL</v-chip>
          </div>

          <v-row>
            <v-col cols="12" sm="6" md="3">
              <div class="stat-card glass-panel rounded-xl pa-4 text-center border-0">
                <div class="text-h4 font-weight-black text-primary mb-1">
                  {{ stats.total_papers.toLocaleString() }}
                </div>
                <div class="text-caption font-weight-bold text-medium-emphasis text-uppercase tracking-widest">
                  Total Papers
                </div>
              </div>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <div class="stat-card glass-panel rounded-xl pa-4 text-center border-0">
                <v-chip
                  :color="stats.status === 'connected' ? 'success' : 'error'"
                  variant="flat"
                  size="small"
                  class="mb-2 font-weight-bold"
                >
                  {{ stats.status.toUpperCase() }}
                </v-chip>
                <div class="text-caption font-weight-bold text-medium-emphasis text-uppercase tracking-widest">
                  Main Engine
                </div>
              </div>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <div class="stat-card glass-panel rounded-xl pa-4 text-center border-0">
                <v-chip
                  :color="stats.redis === 'connected' ? 'success' : 'warning'"
                  variant="flat"
                  size="small"
                  class="mb-2 font-weight-bold"
                >
                  {{ stats.redis.toUpperCase() }}
                </v-chip>
                <div class="text-caption font-weight-bold text-medium-emphasis text-uppercase tracking-widest">
                  Context Cache
                </div>
              </div>
            </v-col>

            <v-col cols="12" sm="6" md="3">
              <div class="stat-card glass-panel rounded-xl pa-4 text-center border-0">
                <div class="text-subtitle-1 font-weight-black text-black mb-1">
                  {{ stats.database }}
                </div>
                <div class="text-caption font-weight-bold text-medium-emphasis text-uppercase tracking-widest">
                  Knowledge Hub
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { StatsResponse } from '@/types'
import papersService from '@/services/api/papers.service'

const router = useRouter()
const searchQuery = ref('')
const stats = ref<StatsResponse | null>(null)

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ name: 'search', query: { q: searchQuery.value } })
  }
}

onMounted(async () => {
  try {
    stats.value = await papersService.getStats()
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
})
</script>
