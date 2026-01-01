<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h4">
          <v-icon class="mr-2">mdi-history</v-icon>
          Search History
        </h1>
      </v-col>
    </v-row>

    <!-- Q&A History from Store -->
    <v-row v-if="qaStore.history.length">
      <v-col cols="12">
        <v-card>
          <v-card-title>Recent Questions</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="(item, index) in qaStore.history"
                :key="index"
                :to="{ name: 'ask' }"
                class="mb-2"
              >
                <template #prepend>
                  <v-icon color="secondary">mdi-comment-question</v-icon>
                </template>
                <v-list-item-title>{{ item.question }}</v-list-item-title>
                <v-list-item-subtitle class="d-flex align-center gap-2">
                  <span>{{ formatDate(item.timestamp) }}</span>
                  <v-chip size="x-small" v-if="item.sources.length">
                    {{ item.sources.length }} sources
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Placeholder for API-based history -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Search Analytics</span>
            <v-spacer />
            <v-chip color="info" size="small">Coming Soon</v-chip>
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal">
              <p class="mb-0">
                Full search history and analytics will be available once the backend
                endpoints are implemented. This will include:
              </p>
              <ul class="mt-2">
                <li>Complete search history with timestamps</li>
                <li>Trending topics and popular queries</li>
                <li>Search result statistics</li>
                <li>Personal search patterns</li>
              </ul>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-if="!qaStore.history.length">
      <v-col cols="12" class="text-center py-12">
        <v-icon size="64" color="grey">mdi-history</v-icon>
        <p class="text-h6 mt-4">No search history yet</p>
        <p class="text-body-2 text-medium-emphasis mb-6">
          Your questions and searches will appear here
        </p>
        <v-btn color="primary" :to="{ name: 'ask' }">
          <v-icon start>mdi-comment-question</v-icon>
          Ask a Question
        </v-btn>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import { useQAStore } from '@/stores/qa.store'

const qaStore = useQAStore()

function formatDate(date: Date): string {
  return format(date, 'MMM d, yyyy h:mm a')
}
</script>
