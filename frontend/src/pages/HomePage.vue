<template>
  <div>
    <!-- Hero Section -->
    <v-row class="mb-8">
      <v-col cols="12" class="text-center">
        <h1 class="text-h3 text-md-h2 font-weight-bold mb-4 text-black">
          Discover AI Research Papers
        </h1>
        <p class="text-h6 text-medium-emphasis mb-6">
          Search, explore, and get AI-powered insights from the latest research
        </p>

        <!-- Quick Search -->
        <v-card max-width="600" class="mx-auto glass-panel" elevation="0">
          <v-card-text class="pa-4">
            <v-text-field
              v-model="searchQuery"
              label="Search papers..."
              placeholder="e.g., transformers, GPT, neural networks"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              hide-details
              bg-color="transparent"
              @keyup.enter="handleSearch"
            />
            <v-btn
              color="black"
              size="large"
              block
              class="mt-4"
              elevation="0"
              @click="handleSearch"
            >
              <v-icon start>mdi-magnify</v-icon>
              Search Papers
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mb-8">
      <v-col cols="12" md="4">
        <v-card
          height="100%"
          class="d-flex flex-column glass-panel"
          :to="{ name: 'search' }"
          elevation="0"
        >
          <v-card-text class="text-center flex-grow-1 d-flex flex-column justify-center">
            <v-icon size="64" color="black" class="mb-4">mdi-magnify</v-icon>
            <h3 class="text-h5 mb-2 text-black">Search Papers</h3>
            <p class="text-body-2 text-medium-emphasis">
              Find research papers using hybrid semantic and keyword search
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card
          height="100%"
          class="d-flex flex-column glass-panel"
          :to="{ name: 'ask' }"
          elevation="0"
        >
          <v-card-text class="text-center flex-grow-1 d-flex flex-column justify-center">
            <v-icon size="64" color="black" class="mb-4">mdi-comment-question</v-icon>
            <h3 class="text-h5 mb-2 text-black">Ask Questions</h3>
            <p class="text-body-2 text-medium-emphasis">
              Get AI-powered answers based on research papers with citations
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card
          height="100%"
          class="d-flex flex-column glass-panel"
          :to="{ name: 'browse' }"
          elevation="0"
        >
          <v-card-text class="text-center flex-grow-1 d-flex flex-column justify-center">
            <v-icon size="64" color="black" class="mb-4">mdi-book-open-variant</v-icon>
            <h3 class="text-h5 mb-2 text-black">Browse Papers</h3>
            <p class="text-body-2 text-medium-emphasis">
              Explore the full collection of indexed research papers
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Stats Section -->
    <v-row v-if="stats">
      <v-col cols="12">
        <v-card class="glass-panel" elevation="0">
          <v-card-title class="d-flex align-center text-black">
            <v-icon class="mr-2 text-black">mdi-chart-bar</v-icon>
            System Status
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <div class="text-h4 font-weight-bold text-black">
                    {{ stats.total_papers.toLocaleString() }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">Total Papers</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <v-chip :color="stats.status === 'connected' ? 'success' : 'error'" variant="outlined">
                    {{ stats.status }}
                  </v-chip>
                  <div class="text-body-2 text-medium-emphasis mt-1">Database</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <v-chip :color="stats.redis === 'connected' ? 'success' : 'warning'" variant="outlined">
                    {{ stats.redis }}
                  </v-chip>
                  <div class="text-body-2 text-medium-emphasis mt-1">Cache</div>
                </div>
              </v-col>
              <v-col cols="6" md="3">
                <div class="text-center">
                  <v-chip color="black" variant="outlined">
                    {{ stats.database }}
                  </v-chip>
                  <div class="text-body-2 text-medium-emphasis mt-1">Provider</div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
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
