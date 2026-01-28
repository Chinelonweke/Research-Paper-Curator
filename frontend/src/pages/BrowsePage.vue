<template>
  <v-container fluid class="pa-0">
    <v-row class="mb-8 p-4">
      <v-col cols="12" class="d-flex align-center justify-space-between glass-panel rounded-xl pa-6">
        <div class="d-flex align-center">
          <v-avatar color="primary" variant="tonal" size="56" class="mr-4">
            <v-icon size="32">mdi-book-open-variant</v-icon>
          </v-avatar>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Browse Papers</h1>
            <p class="text-body-1 text-medium-emphasis mb-0">
              Discover the latest breakthroughs in research
            </p>
          </div>
        </div>
        <v-chip
          v-if="papersStore.total"
          color="primary"
          variant="elevated"
          size="large"
          class="font-weight-bold"
        >
          {{ papersStore.total.toLocaleString() }} total papers
        </v-chip>
      </v-col>
    </v-row>

    <!-- Controls -->
    <v-row class="mb-8 px-4">
      <v-col cols="12">
        <v-card class="glass-panel rounded-xl border-0 pa-2">
          <v-card-text class="d-flex align-center flex-wrap gap-4">
            <div style="min-width: 200px">
              <v-select
                v-model="perPage"
                label="Papers per page"
                :items="[10, 25, 50, 100]"
                variant="plain"
                density="compact"
                hide-details
                prepend-inner-icon="mdi-format-list-numbered"
                class="pt-0"
                @update:model-value="loadPapers"
              />
            </div>
            
            <v-spacer />
            
            <v-btn
              color="primary"
              variant="flat"
              rounded="pill"
              size="large"
              class="px-8 font-weight-bold"
              :loading="papersStore.loading"
              @click="loadPapers"
            >
              <v-icon start>mdi-refresh</v-icon>
              Refresh Library
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="papersStore.error" class="mb-6 px-4">
      <v-col cols="12">
        <v-alert
          type="error"
          variant="tonal"
          closable
          @click:close="papersStore.clearError"
          class="rounded-lg shadow-sm"
        >
          {{ papersStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="papersStore.loading" class="px-4">
      <v-col cols="12" class="text-center py-16">
        <v-progress-circular indeterminate color="primary" size="64" width="6" />
        <p class="mt-4 text-h6 font-weight-medium">Accessing the archives...</p>
      </v-col>
    </v-row>

    <!-- Papers List -->
    <v-row v-else class="px-4">
      <v-col
        v-for="paper in papersStore.papers"
        :key="paper.id"
        cols="12"
        md="6"
        lg="4"
      >
        <PaperCard :paper="paper" class="h-100" />
      </v-col>
    </v-row>

    <!-- Pagination -->
    <v-row v-if="totalPages > 1" class="mt-8 mb-12 px-4">
      <v-col cols="12" class="d-flex justify-center">
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          :total-visible="7"
          rounded="pill"
          color="primary"
          @update:model-value="handlePageChange"
        />
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-if="!papersStore.loading && !papersStore.papers.length" justify="center" class="px-4">
      <v-col cols="12" md="8" lg="6" class="text-center py-16">
        <div class="glass-panel rounded-xl pa-12">
          <v-icon size="120" color="grey-lighten-2" class="mb-6">mdi-book-off-outline</v-icon>
          <h2 class="text-h4 font-weight-bold mb-4">No papers found</h2>
          <p class="text-h6 text-medium-emphasis mb-8">
            The knowledge base is currently quiet. Please check back later or try refreshing.
          </p>
          <v-btn
            color="primary"
            size="x-large"
            rounded="pill"
            class="px-8 font-weight-bold"
            @click="loadPapers"
          >
            <v-icon start>mdi-refresh</v-icon>
            Retry Refresh
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
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
