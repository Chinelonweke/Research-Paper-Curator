<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h1 class="text-h4">
          <v-icon class="mr-2">mdi-book-open-variant</v-icon>
          Browse Papers
        </h1>
        <v-chip v-if="papersStore.total" color="primary">
          {{ papersStore.total.toLocaleString() }} total papers
        </v-chip>
      </v-col>
    </v-row>

    <!-- Controls -->
    <v-row class="mb-6">
      <v-col cols="12" md="4">
        <v-select
          v-model="perPage"
          label="Papers per page"
          :items="[10, 25, 50, 100]"
          @update:model-value="loadPapers"
        />
      </v-col>
      <v-col cols="12" md="8" class="d-flex align-center justify-end">
        <v-btn
          color="primary"
          :loading="papersStore.loading"
          @click="loadPapers"
        >
          <v-icon start>mdi-refresh</v-icon>
          Refresh
        </v-btn>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="papersStore.error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="papersStore.clearError">
          {{ papersStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="papersStore.loading">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="mt-4">Loading papers...</p>
      </v-col>
    </v-row>

    <!-- Papers List -->
    <v-row v-else>
      <v-col
        v-for="paper in papersStore.papers"
        :key="paper.id"
        cols="12"
      >
        <PaperCard :paper="paper" />
      </v-col>
    </v-row>

    <!-- Pagination -->
    <v-row v-if="totalPages > 1" class="mt-6">
      <v-col cols="12" class="d-flex justify-center">
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          :total-visible="7"
          @update:model-value="handlePageChange"
        />
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-if="!papersStore.loading && !papersStore.papers.length">
      <v-col cols="12" class="text-center py-12">
        <v-icon size="64" color="grey">mdi-book-off-outline</v-icon>
        <p class="text-h6 mt-4">No papers found</p>
        <p class="text-body-2 text-medium-emphasis">
          The database appears to be empty
        </p>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePapersStore } from '@/stores/papers.store'
import PaperCard from '@/components/papers/PaperCard.vue'

const papersStore = usePapersStore()

const currentPage = ref(1)
const perPage = ref(25)

const totalPages = computed(() => {
  return Math.ceil(papersStore.total / perPage.value)
})

async function loadPapers() {
  const skip = (currentPage.value - 1) * perPage.value
  await papersStore.fetchPapers(skip, perPage.value)
}

function handlePageChange() {
  loadPapers()
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  loadPapers()
})
</script>
